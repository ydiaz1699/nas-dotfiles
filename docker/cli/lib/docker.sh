# docker/cli/lib/docker.sh
# update-all con confirmacion y uso correcto de svc_compose_file

svc_update_all() {
  local auto_yes=false

  # Parsear flags
  for arg in "$@"; do
    case "$arg" in
      -y|--yes) auto_yes=true ;;
    esac
  done

  local services
  services=$(svc_list)
  local count
  count=$(echo "$services" | wc -l | tr -d ' ')

  echo ""
  echo -e "\033[0;36m  Actualizar todos los servicios ($count encontrados)\033[0m"
  echo ""

  # Mostrar que se va a actualizar
  for svc in $services; do
    local f
    f=$(svc_compose_file "$svc")
    if [[ -n "$f" ]]; then
      if docker compose -f "$f" ps -q 2>/dev/null | grep -q .; then
        echo -e "    \033[0;32m●\033[0m $svc"
      else
        echo -e "    \033[0;31m○\033[0m $svc (detenido, se actualizara imagen)"
      fi
    fi
  done

  echo ""

  # Confirmacion
  if ! $auto_yes; then
    read -rp "  Continuar? [y/N] " confirm
    if [[ ! "$confirm" =~ ^[yY]$ ]]; then
      echo "  Cancelado."
      return 0
    fi
  fi

  echo ""

  local ok=0 fail=0
  for svc in $services; do
    local f
    f=$(svc_compose_file "$svc")

    if [[ -z "$f" ]]; then
      echo -e "  \033[1;33m⚠  $svc: compose file no encontrado\033[0m"
      ((fail++))
      continue
    fi

    echo -e "\033[1;33m  -- $svc --\033[0m"

    # Pull nuevas imagenes
    if docker compose -f "$f" pull 2>/dev/null; then
      # Solo recrear si estaba corriendo
      if docker compose -f "$f" ps -q 2>/dev/null | grep -q .; then
        docker compose -f "$f" up -d --remove-orphans 2>/dev/null
      fi
      ((ok++))
    else
      echo -e "  \033[0;31m  Error en pull de $svc\033[0m"
      ((fail++))
    fi

    echo ""
  done

  echo -e "\033[0;32m  $ok actualizados\033[0m"
  [[ $fail -gt 0 ]] && echo -e "\033[0;31m  $fail con error\033[0m"
  echo ""
}
