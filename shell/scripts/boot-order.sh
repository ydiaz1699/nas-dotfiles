#!/usr/bin/env bash
# Arranque escalonado de Compose por capas.
#
# El código vive en NAS_DOTFILES; la configuración y los logs viven en
# DOCKER_BASE/scripts para que agregar/quitar un servicio no requiera cambiar
# la unidad systemd.
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

: "${NAS_DOTFILES:=$REPO_ROOT}"
: "${DOCKER_BASE:=${dkco:-/docker}}"
export NAS_DOTFILES DOCKER_BASE

CONFIG_FILE="${BOOT_ORDER_CONFIG:-$DOCKER_BASE/scripts/layers.conf}"
LOG_FILE="${BOOT_ORDER_LOG:-$DOCKER_BASE/scripts/boot-order.log}"
LOCK_FILE="${BOOT_ORDER_LOCK:-$DOCKER_BASE/scripts/boot-order.lock}"
HEALTH_TIMEOUT="${BOOT_ORDER_HEALTH_TIMEOUT:-480}"
DAEMON_TIMEOUT="${BOOT_ORDER_DAEMON_TIMEOUT:-60}"
REQUIRE_ALL="${BOOT_ORDER_REQUIRE_ALL:-1}"
ALLOW_MISSING="${BOOT_ORDER_ALLOW_MISSING:-0}"
# Espera inicial antes de la primera capa: deja que el sistema recién booteado
# (kernel, systemd, dockerd) se estabilice antes de cargar CPU con contenedores.
INITIAL_DELAY="${BOOT_ORDER_INITIAL_DELAY:-30}"
# Pausa tras dejar listo cada servicio, antes del siguiente: da margen a que su
# consumo de CPU se asiente. Clave en hardware con pocos cores.
SETTLE_DELAY="${BOOT_ORDER_SETTLE_DELAY:-10}"

for _v in HEALTH_TIMEOUT DAEMON_TIMEOUT INITIAL_DELAY SETTLE_DELAY; do
  if [[ ! "${!_v}" =~ ^[0-9]+$ ]]; then
    echo "ERROR: BOOT_ORDER_${_v} debe ser un entero (valor: ${!_v})." >&2
    exit 2
  fi
done

mkdir -p "$(dirname "$CONFIG_FILE")" "$(dirname "$LOG_FILE")" "$(dirname "$LOCK_FILE")"
touch "$LOG_FILE"

# Evita dos arranques simultáneos, por ejemplo systemd + una prueba manual.
exec 9>"$LOCK_FILE"
if ! flock -n 9; then
  printf '[%s] Ya hay otro arranque escalonado en ejecución; saliendo.\n' "$(date '+%F %T')" >&2
  exit 0
fi

log() {
  printf '[%s] %s\n' "$(date '+%F %T')" "$*" | tee -a "$LOG_FILE"
}

fail() {
  log "ERROR: $*"
  exit 1
}

svc_cli() {
  # Se fija Bash para que systemd no dependa de NAS_CLI ni del entorno del usuario.
  NAS_CLI=bash "$NAS_DOTFILES/docker/cli/svc.sh" "$@"
}

compose_file() {
  local svc="$1"
  local name
  for name in compose.yml compose.yaml docker-compose.yml docker-compose.yaml; do
    if [[ -f "$DOCKER_BASE/$svc/$name" ]]; then
      printf '%s/%s\n' "$DOCKER_BASE/$svc" "$name"
      return 0
    fi
  done
  return 1
}

discovered_services() {
  find "$DOCKER_BASE" -mindepth 2 -maxdepth 2 -type f \
    \( -name compose.yml -o -name compose.yaml \
       -o -name docker-compose.yml -o -name docker-compose.yaml \) \
    -printf '%h\n' 2>/dev/null \
    | awk -F/ '{print $NF}' | sort -u
}

trim() {
  local value="$1"
  value="${value#"${value%%[![:space:]]*}"}"
  value="${value%"${value##*[![:space:]]}"}"
  printf '%s' "$value"
}

LAYER_SERVICES=()
CURRENT_LAYER=()

flush_layer() {
  if ((${#CURRENT_LAYER[@]} > 0)); then
    LAYER_SERVICES+=("${CURRENT_LAYER[*]}")
    CURRENT_LAYER=()
  fi
}

load_layers() {
  [[ -f "$CONFIG_FILE" ]] || fail "no existe $CONFIG_FILE; copia layers.conf.example y ajústalo al NAS."

  local raw line
  while IFS= read -r raw || [[ -n "$raw" ]]; do
    line="$(trim "$raw")"
    [[ -z "$line" ]] && { flush_layer; continue; }
    [[ "$line" == \#* ]] && continue

    # Permite comentarios al final de una línea sin aceptar texto como servicio.
    line="$(trim "${line%%#*}")"
    [[ -z "$line" ]] && continue

    [[ "$line" =~ ^[a-zA-Z0-9][a-zA-Z0-9._-]*$ ]] || \
      fail "nombre inválido en $CONFIG_FILE: '$line'"
    CURRENT_LAYER+=("$line")
  done < "$CONFIG_FILE"
  flush_layer
  ((${#LAYER_SERVICES[@]} > 0)) || fail "$CONFIG_FILE no contiene ninguna capa."
}

declare -A CONFIGURED=()

declare -A DISCOVERED=()

validate_layers() {
  local layer svc
  local -a services

  while IFS= read -r svc; do
    [[ -n "$svc" ]] && DISCOVERED["$svc"]=1
  done < <(discovered_services)

  for layer in "${LAYER_SERVICES[@]}"; do
    read -r -a services <<< "$layer"
    for svc in "${services[@]}"; do
      if [[ -n "${CONFIGURED[$svc]+x}" ]]; then
        fail "servicio repetido en más de una capa: $svc"
      fi
      CONFIGURED["$svc"]=1

      if ! compose_file "$svc" >/dev/null; then
        if [[ "$ALLOW_MISSING" == "1" ]]; then
          log "AVISO: $svc está en layers.conf pero no tiene Compose; se omitirá."
        else
          fail "$svc está en layers.conf pero no existe en $DOCKER_BASE."
        fi
      fi
    done
  done

  if [[ "$REQUIRE_ALL" == "1" ]]; then
    for svc in "${!DISCOVERED[@]}"; do
      if [[ -z "${CONFIGURED[$svc]+x}" ]]; then
        log "ERROR: '$svc' existe en $DOCKER_BASE pero no está en $CONFIG_FILE."
        log "  Arréglalo con UNA de estas opciones:"
        log "    1) Añádelo a una capa:  nano $CONFIG_FILE   (agrega la línea: $svc)"
        log "    2) Exclúyelo del boot:  svc no-boot $svc"
        log "  Luego reintenta:  NAS_CLI=bash $NAS_DOTFILES/shell/scripts/boot-order.sh"
        fail "servicio '$svc' sin registrar en layers.conf (ver instrucciones arriba)."
      fi
    done
  else
    for svc in "${!DISCOVERED[@]}"; do
      [[ -n "${CONFIGURED[$svc]+x}" ]] || \
        log "AVISO: $svc existe en $DOCKER_BASE pero no está configurado; no se levantará."
    done
  fi
}

wait_for_docker() {
  local started elapsed
  started=$(date +%s)
  while ! docker info >/dev/null 2>&1; do
    elapsed=$(( $(date +%s) - started ))
    ((elapsed >= DAEMON_TIMEOUT)) && fail "Docker no respondió tras ${DAEMON_TIMEOUT}s."
    sleep 2
  done
}

wait_service_ready() {
  local svc="$1"
  local started now state health exit_code restart_policy cid
  local -a containers

  mapfile -t containers < <(svc_cli ps "$svc" -q 2>/dev/null || true)
  ((${#containers[@]} > 0)) || { log "ERROR: $svc no creó contenedores."; return 1; }

  for cid in "${containers[@]}"; do
    started=$(date +%s)
    while :; do
      state=$(docker inspect -f '{{.State.Status}}' "$cid" 2>/dev/null || echo missing)
      health=$(docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{end}}' "$cid" 2>/dev/null || true)
      exit_code=$(docker inspect -f '{{.State.ExitCode}}' "$cid" 2>/dev/null || echo 1)
      restart_policy=$(docker inspect -f '{{.HostConfig.RestartPolicy.Name}}' "$cid" 2>/dev/null || true)

      case "$state" in
        running)
          if [[ -z "$health" || "$health" == "healthy" ]]; then
            log "$svc ($cid): listo${health:+, health=$health}."
            break
          fi
          # 'unhealthy' o 'starting' durante el arranque en frío puede ser
          # transitorio: los primeros health checks tardan/fallan mientras el
          # servicio aún inicializa (dentro de su start_period/retries). NO se
          # aborta aquí; se sigue esperando hasta agotar HEALTH_TIMEOUT y solo
          # entonces se considera fallo (ver comprobación de timeout abajo).
          ;;
        exited)
          # Jobs one-shot como lobehub-rustfs-init terminan correctamente y no
          # deben bloquear el resto del proyecto.
          if [[ "$restart_policy" == "no" && "$exit_code" == "0" ]]; then
            log "$svc ($cid): job completado correctamente."
            break
          fi
          log "ERROR: $svc ($cid) terminó con estado $exit_code."
          return 1
          ;;
        created|restarting|paused)
          ;;
        missing)
          log "ERROR: no se pudo inspeccionar $svc ($cid)."
          return 1
          ;;
        *)
          log "ERROR: $svc ($cid) tiene estado inesperado: $state."
          return 1
          ;;
      esac

      now=$(( $(date +%s) - started ))
      if ((now >= HEALTH_TIMEOUT)); then
        log "ERROR: $svc ($cid) no llegó a ready tras ${HEALTH_TIMEOUT}s (state=$state health=${health:-none})."
        return 1
      fi
      sleep 3
    done
  done
}

svc_up_one() {
  local svc="$1"
  if svc_cli up "$svc" >> "$LOG_FILE" 2>&1; then
    printf '[%s] %s: svc up OK\n' "$(date '+%F %T')" "$svc" >> "$LOG_FILE"
    return 0
  fi
  printf '[%s] %s: svc up FALLÓ\n' "$(date '+%F %T')" "$svc" >> "$LOG_FILE"
  return 1
}

# Un servicio queda fuera del boot (saltar-con-aviso) si el usuario lo detuvo
# a propósito. Marcador explícito: $DOCKER_BASE/<svc>/.no-boot (lo crea
# `svc no-boot <svc>` y lo borra `svc boot-enable <svc>`).
is_no_boot() {
  local svc="$1"
  [[ -f "$DOCKER_BASE/$svc/.no-boot" ]]
}

# Devuelve 0 si el servicio debe procesarse; 1 si hay que saltarlo. El salto no
# bloquea la capa ni cuenta como fallo: el arranque continúa con el siguiente.
should_start() {
  local svc="$1"
  [[ -f "$(compose_file "$svc" 2>/dev/null || true)" ]] || return 1
  if is_no_boot "$svc"; then
    log "OMITIDO: $svc tiene .no-boot; no se arranca (svc boot-enable $svc para reactivar)."
    return 1
  fi
  return 0
}

# Serial (default): arranca y espera ready servicio por servicio. Minimiza el
# pico de I/O a costa de un boot más lento. Para arrancar toda la capa en
# paralelo, usar BOOT_ORDER_SERIAL=0.
run_layer_serial() {
  local svc
  local -a services=("$@")
  local svc first=1
  for svc in "${services[@]}"; do
    should_start "$svc" || continue
    # Pausa de asentamiento ANTES de arrancar el siguiente (no antes del
    # primero de la capa): deja que el CPU del servicio anterior se estabilice.
    if ((first == 0 && SETTLE_DELAY > 0)); then
      log "  (pausa de ${SETTLE_DELAY}s para estabilizar CPU antes de $svc)"
      sleep "$SETTLE_DELAY"
    fi
    first=0
    svc_up_one "$svc" || { log "ERROR: falló \`svc up $svc\`."; return 1; }
    wait_service_ready "$svc" || return 1
  done
}

# Paralelo (BOOT_ORDER_SERIAL=0): arranca todos los servicios de la capa a la
# vez y luego espera la readiness de cada uno. La siguiente capa no empieza
# hasta terminar la actual.
run_layer_parallel() {
  local svc pid index failed=0
  local -a started=() pids=()

  for svc in "$@"; do
    should_start "$svc" || continue
    started+=("$svc")
    svc_up_one "$svc" &
    pids+=("$!")
  done

  for index in "${!pids[@]}"; do
    pid="${pids[$index]}"
    if ! wait "$pid"; then
      failed=1
      log "ERROR: falló \`svc up ${started[$index]}\`."
    fi
  done
  ((failed == 0)) || return 1

  for svc in "${started[@]}"; do
    wait_service_ready "$svc" || return 1
  done
}

run_layer() {
  local layer="$1"
  local -a services=()

  read -r -a services <<< "$layer"
  ((${#services[@]} > 0)) || return 0
  log "Iniciando capa: ${services[*]}"

  if [[ "${BOOT_ORDER_SERIAL:-1}" == "0" ]]; then
    run_layer_parallel "${services[@]}" || return 1
  else
    run_layer_serial "${services[@]}" || return 1
  fi

  log "Capa lista: ${services[*]}"
}

load_layers
validate_layers
wait_for_docker

log "Arranque escalonado iniciado (configuración: $CONFIG_FILE)."

# Espera inicial: el sistema recién booteado (kernel, systemd, dockerd) aún está
# cargando. Darle margen antes de sumar la carga de los contenedores evita
# saturar la CPU en hardware con pocos cores. Se omite si el arranque es manual
# con BOOT_ORDER_INITIAL_DELAY=0.
if ((INITIAL_DELAY > 0)); then
  log "Esperando ${INITIAL_DELAY}s a que el sistema se estabilice antes de la primera capa..."
  sleep "$INITIAL_DELAY"
fi

_layer_num=0
for layer in "${LAYER_SERVICES[@]}"; do
  # Pausa de asentamiento entre capas (no antes de la primera).
  if ((_layer_num > 0 && SETTLE_DELAY > 0)); then
    log "  (pausa de ${SETTLE_DELAY}s para estabilizar CPU antes de la siguiente capa)"
    sleep "$SETTLE_DELAY"
  fi
  _layer_num=$((_layer_num + 1))
  run_layer "$layer" || fail "se aborta el arranque para no iniciar capas dependientes."
done
log "Arranque completo."
