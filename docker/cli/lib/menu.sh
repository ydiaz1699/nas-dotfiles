svc_menu() {
  # ── Verificar fzf ──────────────────────────────────────────────────────────
  if ! command -v fzf &>/dev/null; then
    echo ""
    echo "  El menu TUI requiere fzf."
    echo ""
    echo "  Instalar:"
    echo "    Debian/Ubuntu:  sudo apt install fzf"
    echo "    Synology NAS:   opkg install fzf   (necesita Entware)"
    echo "    Manual:         https://github.com/junegunn/fzf#installation"
    echo ""
    return 1
  fi

  # Usar DOCKER_BASE (datos) y CLI_DIR (código) ya definidos
  local docker_dir="${DOCKER_BASE:-/docker}"
  local cli_dir="${CLI_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"

  export DOCKER_DIR="$docker_dir"

  # Preview exportado para fzf
  _svc_preview() {
    local svc
    svc=$(echo "$1" | awk '{print $NF}')
    echo "-- Contenedores --"
    local compose=""
    for name in docker-compose.yml docker-compose.yaml compose.yml compose.yaml; do
      [[ -f "${DOCKER_DIR}/${svc}/${name}" ]] && compose="${DOCKER_DIR}/${svc}/${name}" && break
    done
    if [[ -n "$compose" ]]; then
      docker compose -f "$compose" ps 2>/dev/null || echo "(sin datos)"
      echo ""
      echo "-- Imagenes --"
      docker compose -f "$compose" images 2>/dev/null || echo "(sin datos)"
    else
      echo "(compose file no encontrado)"
    fi
  }
  export -f _svc_preview


  # Lista servicios con indicador de estado
  _svc_status_list() {
    while IFS= read -r svc; do
      local f
      f=$(svc_compose_file "$svc" 2>/dev/null)
      [[ -z "$f" ]] && continue
      if docker compose -f "$f" ps -q 2>/dev/null | grep -q .; then
        printf "\033[0;32m● activo  \033[0m  %s\n" "$svc"
      else
        printf "\033[0;31m○ detenido\033[0m  %s\n" "$svc"
      fi
    done
  }

  # Acciones disponibles
  ACCIONES=(
    "up         -> levantar contenedores"
    "down       -> bajar y eliminar"
    "restart    -> reiniciar"
    "start      -> iniciar detenido"
    "stop       -> detener"
    "kill       -> forzar parada"
    "pause      -> pausar"
    "unpause    -> reanudar pausado"
    "logs       -> ver logs en vivo"
    "stats      -> uso CPU/RAM"
    "top        -> procesos corriendo"
    "exec       -> abrir shell"
    "build      -> construir imagen"
    "pull       -> descargar imagen"
    "update     -> pull + recrear"
    "images     -> listar imagenes"
    "rm         -> eliminar detenidos"
    "config     -> ver configuracion"
    "volumes    -> listar volumenes"
    "events     -> eventos en tiempo real"
    "backup     -> exportar volumenes a tar.gz"
    "restore    -> restaurar backup"
    "depends    -> ver servicios y dependencias"
    "env        -> ver variables de entorno"
    "open       -> abrir URL del servicio"
  )


  while true; do
    # 1. Seleccion de servicio con preview en vivo
    service_line=$(
      svc_list | _svc_status_list | \
      fzf \
        --ansi \
        --prompt="  Servicio > " \
        --header="up/down: navegar | Enter: seleccionar | Esc: salir" \
        --preview='bash -c "_svc_preview \"{}\"" ' \
        --preview-window=right:45%:wrap \
        --bind "esc:abort"
    ) || break

    [[ -z "$service_line" ]] && break

    service=$(echo "$service_line" | awk '{print $NF}')

    # 2. Seleccion de accion
    action_line=$(
      printf '%s\n' "${ACCIONES[@]}" "<- volver" | \
      fzf \
        --ansi \
        --prompt="  Accion > " \
        --header="Servicio: $service" \
        --bind "esc:abort"
    ) || continue

    [[ -z "$action_line" || "$action_line" == "<- volver" ]] && continue

    # Extrae solo el comando (antes del ->)
    action=$(echo "$action_line" | awk '{print $1}')

    # Para exec: abrir shell directamente
    if [[ "$action" == "exec" ]]; then
      local compose_f
      compose_f=$(svc_compose_file "$service")
      local container
      container=$(docker compose -f "$compose_f" ps --services | head -n1)
      docker compose -f "$compose_f" exec "$container" sh 2>/dev/null \
        || docker compose -f "$compose_f" exec "$container" bash
      continue
    fi

    # 3. Ejecutar via svc.sh (auto-detecta su ubicación)
    echo ""
    echo -e "\033[0;36m  > ${action} ${service}\033[0m"
    echo "  ──────────────────────────────────"
    "$cli_dir/svc.sh" "$action" "$service"
    echo ""

    read -r -t 3 -p "  Volviendo al menu en 3s... (Enter para continuar)" || true
    echo ""
  done
}
