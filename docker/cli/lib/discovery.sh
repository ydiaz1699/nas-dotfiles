# /docker/cli/lib/discovery.sh
# Deteccion de servicios Docker Compose en /docker/

DOCKER_BASE="${DOCKER_BASE:-/docker}"

# Detecta servicios buscando compose files
svc_list() {
  find "$DOCKER_BASE" -mindepth 2 -maxdepth 2 \
    \( -name "docker-compose.yml" -o -name "docker-compose.yaml" \
       -o -name "compose.yml"     -o -name "compose.yaml" \) \
    2>/dev/null \
    | awk -F/ '{print $(NF-1)}' | sort -u
}

# Devuelve el path real del compose file de un servicio
svc_compose_file() {
  local svc="$1"
  for name in docker-compose.yml docker-compose.yaml compose.yml compose.yaml; do
    if [[ -f "$DOCKER_BASE/$svc/$name" ]]; then
      echo "$DOCKER_BASE/$svc/$name"
      return
    fi
  done
}

# Lista servicios con estado activo/detenido
svc_lista() {
  echo ""
  echo -e "\033[0;34mServicios en $DOCKER_BASE:\033[0m"
  echo ""
  for s in $(svc_list); do
    local f
    f=$(svc_compose_file "$s")
    if docker compose -f "$f" ps -q 2>/dev/null | grep -q .; then
      echo -e "  \033[0;32m● activo   \033[0m  $s"
    else
      echo -e "  \033[0;31m○ detenido \033[0m  $s"
    fi
  done
  echo ""
}
