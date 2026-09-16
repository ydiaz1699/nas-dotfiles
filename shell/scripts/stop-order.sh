#!/usr/bin/env bash
# Apagado escalonado de Compose por capas, en ORDEN INVERSO al arranque.
#
# Contraparte de boot-order.sh: lee el mismo $dkco/scripts/layers.conf y baja
# los servicios empezando por la última capa (dependientes) hacia la primera
# (base de datos), para que nada quede escribiendo contra una DB ya detenida.
#
# Uso:
#   stop-order.sh            # baja todos los servicios de layers.conf (svc down)
#   stop-order.sh --stop     # solo detiene (svc stop), sin eliminar contenedores
#
# Respeta el marcador .no-boot: un servicio excluido del arranque igual se baja
# si está corriendo (para dejar el sistema limpio), con aviso.
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

: "${NAS_DOTFILES:=$REPO_ROOT}"
: "${DOCKER_BASE:=${dkco:-/docker}}"
export NAS_DOTFILES DOCKER_BASE

CONFIG_FILE="${BOOT_ORDER_CONFIG:-$DOCKER_BASE/scripts/layers.conf}"
LOG_FILE="${STOP_ORDER_LOG:-$DOCKER_BASE/scripts/stop-order.log}"
# Acción por defecto: down (elimina contenedores). Con --stop solo detiene.
ACTION="down"

for arg in "$@"; do
  case "$arg" in
    --stop) ACTION="stop" ;;
    --down) ACTION="down" ;;
    -h|--help)
      grep '^#' "$0" | sed 's/^# \{0,1\}//'
      exit 0 ;;
    *) echo "Argumento no reconocido: $arg" >&2; exit 2 ;;
  esac
done

mkdir -p "$(dirname "$LOG_FILE")"
touch "$LOG_FILE"

log() {
  printf '[%s] %s\n' "$(date '+%F %T')" "$*" | tee -a "$LOG_FILE"
}

svc_cli() {
  NAS_CLI=bash "$NAS_DOTFILES/docker/cli/svc.sh" "$@"
}

compose_file() {
  local svc="$1" name
  for name in compose.yml compose.yaml docker-compose.yml docker-compose.yaml; do
    if [[ -f "$DOCKER_BASE/$svc/$name" ]]; then
      printf '%s/%s\n' "$DOCKER_BASE/$svc" "$name"
      return 0
    fi
  done
  return 1
}

is_running() {
  local svc="$1" ids
  ids=$(svc_cli ps "$svc" -q 2>/dev/null || true)
  [[ -n "$ids" ]]
}

trim() {
  local value="$1"
  value="${value#"${value%%[![:space:]]*}"}"
  value="${value%"${value##*[![:space:]]}"}"
  printf '%s' "$value"
}

# Parseo de capas idéntico a boot-order.sh.
LAYER_SERVICES=()
CURRENT_LAYER=()
flush_layer() {
  if ((${#CURRENT_LAYER[@]} > 0)); then
    LAYER_SERVICES+=("${CURRENT_LAYER[*]}")
    CURRENT_LAYER=()
  fi
}
load_layers() {
  [[ -f "$CONFIG_FILE" ]] || { echo "ERROR: no existe $CONFIG_FILE" >&2; exit 1; }
  local raw line
  while IFS= read -r raw || [[ -n "$raw" ]]; do
    line="$(trim "$raw")"
    [[ -z "$line" ]] && { flush_layer; continue; }
    [[ "$line" == \#* ]] && continue
    line="$(trim "${line%%#*}")"
    [[ -z "$line" ]] && continue
    CURRENT_LAYER+=("$line")
  done < "$CONFIG_FILE"
  flush_layer
}

load_layers
((${#LAYER_SERVICES[@]} > 0)) || { echo "ERROR: $CONFIG_FILE sin capas" >&2; exit 1; }

log "Apagado escalonado iniciado (acción: svc $ACTION, orden inverso)."

# Recorrer las capas de la ÚLTIMA a la PRIMERA.
for ((i = ${#LAYER_SERVICES[@]} - 1; i >= 0; i--)); do
  read -r -a services <<< "${LAYER_SERVICES[$i]}"
  log "Bajando capa: ${services[*]}"
  for svc in "${services[@]}"; do
    compose_file "$svc" >/dev/null 2>&1 || { log "  OMITIDO: $svc no existe en $DOCKER_BASE."; continue; }
    if ! is_running "$svc"; then
      log "  $svc ya estaba detenido."
      continue
    fi
    if svc_cli "$ACTION" "$svc" >> "$LOG_FILE" 2>&1; then
      log "  $svc: svc $ACTION OK."
    else
      log "  AVISO: svc $ACTION $svc devolvió error (se continúa)."
    fi
  done
done

log "Apagado completo."
