#!/usr/bin/env bash
set -e

BASE="/docker"

source "$BASE/cli/lib/discovery.sh"
source "$BASE/cli/lib/docker.sh"
source "$BASE/cli/lib/health.sh"
source "$BASE/cli/lib/backup.sh"
source "$BASE/cli/lib/extras.sh"
source "$BASE/cli/lib/menu.sh"
source "$BASE/cli/lib/help.sh"

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
  echo "  Servicio '$servicio' no encontrado en /docker/"
  echo ""
  echo "  Servicios disponibles:"
  svc_list | while read -r s; do echo "    - $s"; done
  echo ""
  exit 1
fi

case "$cmd" in
  up)
    echo -e "\033[0;32m  Levantando $servicio...\033[0m"
    docker compose -f "$COMPOSE_FILE" up -d "$@"
    ;;
  down)
    echo -e "\033[0;31m  Bajando $servicio...\033[0m"
    docker compose -f "$COMPOSE_FILE" down "$@"
    ;;
  restart)
    echo -e "\033[1;33m  Reiniciando $servicio...\033[0m"
    docker compose -f "$COMPOSE_FILE" restart "$@"
    ;;
  stop)
    echo -e "\033[1;33m  Deteniendo $servicio...\033[0m"
    docker compose -f "$COMPOSE_FILE" stop "$@"
    ;;
  start)
    echo -e "\033[0;32m  Iniciando $servicio...\033[0m"
    docker compose -f "$COMPOSE_FILE" start "$@"
    ;;
  kill)
    echo -e "\033[0;31m  Forzando parada de $servicio...\033[0m"
    docker compose -f "$COMPOSE_FILE" kill "$@"
    ;;
  update)
    echo -e "\033[0;36m  Actualizando $servicio...\033[0m"
    docker compose -f "$COMPOSE_FILE" pull
    docker compose -f "$COMPOSE_FILE" up -d --remove-orphans
    echo -e "\033[0;32m  $servicio actualizado\033[0m"
    ;;
  logs)
    if [[ $# -eq 0 ]]; then
      docker compose -f "$COMPOSE_FILE" logs -f --tail=200
    else
      docker compose -f "$COMPOSE_FILE" logs "$@"
    fi
    ;;
  backup)
    svc_backup "$servicio"
    ;;
  restore)
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
    docker compose -f "$COMPOSE_FILE" "$cmd" "$@"
    ;;
esac
