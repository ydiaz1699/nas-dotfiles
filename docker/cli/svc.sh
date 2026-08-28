#!/usr/bin/env bash
set -e

# ── Auto-detectar ubicación del CLI via BASH_SOURCE ────────────────────────
CLI_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# DOCKER_BASE = carpeta de DATOS de servicios (no del código)
BASE="${DOCKER_BASE:-/docker}"

source "$CLI_DIR/lib/discovery.sh"
source "$CLI_DIR/lib/docker.sh"
source "$CLI_DIR/lib/health.sh"
source "$CLI_DIR/lib/backup.sh"
source "$CLI_DIR/lib/extras.sh"
source "$CLI_DIR/lib/menu.sh"
source "$CLI_DIR/lib/lobehub.sh"
source "$CLI_DIR/lib/help.sh"

cmd="$1"
shift || true

# ── Comandos globales (no requieren servicio) ──────────────────────────────
case "$cmd" in
  health)      svc_health ;       exit 0 ;;
  update-all)  svc_update_all "$@" ; exit 0 ;;
  lista)       svc_lista ;        exit 0 ;;
  menu)        svc_menu ;         exit 0 ;;
  port-map)    svc_port_map ;     exit 0 ;;
  size)        svc_size ;         exit 0 ;;
  net)         svc_net ;          exit 0 ;;
  watch)       svc_watch ;        exit 0 ;;
  create)      svc_create "$@" ;  exit 0 ;;
  doctor)      svc_doctor ;       exit 0 ;;
  diff)
    if [[ "${1:-}" == "--all" || "${1:-}" == "-a" ]]; then
      # Comparación catálogo ↔ despliegues locales, sin entrar en cada servicio.
      python3 "${NAS_DOTFILES:-/nas-dotfiles}/agent/tools/compare_tools.py" --all
      exit $?
    fi
    svc_diff "$@" ; exit $? ;;
  catalog-sync) source "$CLI_DIR/lib/catalog-sync.sh" ; catalog_sync "$@" ; exit 0 ;;
  capabilities) python3 "${NAS_DOTFILES:-/nas-dotfiles}/agent/tools/capabilities.py" "$@" ; exit $? ;;
  lobehub) svc_lobehub "$@" ; exit $? ;;
  scan) python3 "${NAS_DOTFILES:-/nas-dotfiles}/agent/tools/project_scanner.py" "$@" ; exit $? ;;
  backup-all) svc_backup_all "$@" ; exit 0 ;;
  logs-grep) svc_logs_grep "$@" ; exit 0 ;;
  clone) svc_clone "$@" ; exit 0 ;;
  cron) svc_cron "$@" ; exit 0 ;;
  doctor-history) svc_doctor_history "$@" ; exit 0 ;;
  lock) svc_lock "$1" ; exit 0 ;;
  unlock) svc_unlock "$1" ; exit 0 ;;
  snapshot) svc_snapshot "$1" ; exit 0 ;;
  rollback) svc_rollback "$1" ; exit 0 ;;
  ""|"-h"|"--help") _svc_ayuda ; exit 0 ;;
esac

# ── Comandos que requieren un servicio ─────────────────────────────────────
servicio="$1"
shift || true

if [[ -z "$servicio" ]]; then
  echo ""
  echo "  Debes indicar un servicio."
  echo "     Uso: svc $cmd <servicio> [argumentos]"
  echo ""
  echo "  Servicios disponibles:"
  svc_list | while read -r s; do echo "    - $s"; done
  echo ""
  exit 1
fi

COMPOSE_FILE=$(svc_compose_file "$servicio")

if [[ -z "$COMPOSE_FILE" ]]; then
  echo ""
  echo "  Servicio '$servicio' no encontrado en $BASE/"
  echo ""
  echo "  Servicios disponibles:"
  svc_list | while read -r s; do echo "    - $s"; done
  echo ""
  exit 1
fi

# ── Env files para interpolación del compose.yml ──────────────────────────
# Docker Compose necesita --env-file para interpolar ${VAR} en labels, ports, etc.
# El .env local del servicio (env_file: .env) solo inyecta DENTRO del contenedor.
# Orden: global primero, local después (local sobreescribe si hay conflicto).
ENV_ARGS=()
if [[ -f "$BASE/.env" ]]; then
  ENV_ARGS+=(--env-file "$BASE/.env")
fi
SVC_DIR=$(dirname "$COMPOSE_FILE")
if [[ -f "$SVC_DIR/.env" ]]; then
  ENV_ARGS+=(--env-file "$SVC_DIR/.env")
fi

case "$cmd" in
  up)
    echo -e "\033[0;32m  Levantando $servicio...\033[0m"
    docker compose "${ENV_ARGS[@]}" -f "$COMPOSE_FILE" up -d "$@"
    ;;
  down)
    _svc_lock_guard "$servicio" "down" || exit 0
    echo -e "\033[0;31m  Bajando $servicio...\033[0m"
    docker compose "${ENV_ARGS[@]}" -f "$COMPOSE_FILE" down "$@"
    ;;
  restart)
    echo -e "\033[1;33m  Reiniciando $servicio...\033[0m"
    docker compose "${ENV_ARGS[@]}" -f "$COMPOSE_FILE" restart "$@"
    ;;
  stop)
    _svc_lock_guard "$servicio" "stop" || exit 0
    echo -e "\033[1;33m  Deteniendo $servicio...\033[0m"
    docker compose "${ENV_ARGS[@]}" -f "$COMPOSE_FILE" stop "$@"
    ;;
  start)
    echo -e "\033[0;32m  Iniciando $servicio...\033[0m"
    docker compose "${ENV_ARGS[@]}" -f "$COMPOSE_FILE" start "$@"
    ;;
  kill)
    _svc_lock_guard "$servicio" "kill" || exit 0
    echo -e "\033[0;31m  Forzando parada de $servicio...\033[0m"
    docker compose "${ENV_ARGS[@]}" -f "$COMPOSE_FILE" kill "$@"
    ;;
  update)
    echo -e "\033[0;36m  Actualizando $servicio...\033[0m"
    docker compose "${ENV_ARGS[@]}" -f "$COMPOSE_FILE" pull
    docker compose "${ENV_ARGS[@]}" -f "$COMPOSE_FILE" up -d --remove-orphans
    echo -e "\033[0;32m  $servicio actualizado\033[0m"
    ;;
  logs)
    if [[ $# -eq 0 ]]; then
      docker compose "${ENV_ARGS[@]}" -f "$COMPOSE_FILE" logs -f --tail=200
    else
      docker compose "${ENV_ARGS[@]}" -f "$COMPOSE_FILE" logs "$@"
    fi
    ;;
  backup)
    svc_backup "$servicio"
    ;;
  restore)
    _svc_lock_guard "$servicio" "restore" || exit 0
    svc_restore "$servicio" "$@"
    ;;
  depends)
    svc_depends "$servicio"
    ;;
  open)
    svc_open "$servicio"
    ;;
  env)
    svc_env "$servicio" "$@"
    ;;
  *)
    # Passthrough a docker compose
    docker compose "${ENV_ARGS[@]}" -f "$COMPOSE_FILE" "$cmd" "$@"
    ;;
esac
