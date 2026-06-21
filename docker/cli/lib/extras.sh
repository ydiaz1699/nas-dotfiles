# /docker/cli/lib/extras.sh
# Comandos adicionales: open, depends, port-map, size, net, env, create, watch

# ── svc depends ────────────────────────────────────────────────────────────
svc_depends() {
  local svc="$1"
  local compose_file
  compose_file=$(svc_compose_file "$svc")

  echo ""
  echo -e "\033[0;34m  Servicios en '$svc':\033[0m"
  docker compose -f "$compose_file" config --services 2>/dev/null \
    | sed 's/^/    - /'

  echo ""
  echo -e "\033[0;34m  Dependencias (depends_on):\033[0m"

  if grep -q "depends_on" "$compose_file" 2>/dev/null; then
    grep -B3 -A8 "depends_on" "$compose_file" \
      | grep -v "^--$" \
      | sed 's/^/    /'
  else
    echo "    (ninguna dependencia definida)"
  fi

  echo ""
}

# ── svc open ───────────────────────────────────────────────────────────────
svc_open() {
  local svc="$1"
  local compose_file
  compose_file=$(svc_compose_file "$svc")

  # Intento 1: leer del contenedor corriendo
  local port
  port=$(docker compose -f "$compose_file" ps --format "{{.Ports}}" 2>/dev/null \
    | grep -oP '0\.0\.0\.0:\K[0-9]+' | sort -n | head -1)

  # Intento 2: leer del compose file directamente
  if [[ -z "$port" ]]; then
    port=$(grep -A3 "ports:" "$compose_file" 2>/dev/null \
      | grep -oP '"?\K[0-9]+(?=:[0-9]+"?)' | head -1)
  fi

  if [[ -z "$port" ]]; then
    echo ""
    echo -e "  \033[1;33m  No se detecto ningun puerto expuesto en '$svc'\033[0m"
    echo "     Usa: svc port $svc <puerto_interno>  para ver el puerto asignado"
    echo ""
    return 1
  fi

  # Obtener IP del host
  local host_ip
  host_ip=$(hostname -I 2>/dev/null | awk '{print $1}')
  [[ -z "$host_ip" ]] && host_ip="localhost"

  local url="http://${host_ip}:${port}"
  echo ""
  echo -e "\033[0;36m  $svc\033[0m  ->  $url"

  # Copiar al clipboard si esta disponible
  if command -v xclip &>/dev/null; then
    echo -n "$url" | xclip -selection clipboard
    echo "  (copiado al clipboard)"
  elif command -v xsel &>/dev/null; then
    echo -n "$url" | xsel --clipboard
    echo "  (copiado al clipboard)"
  fi

  # QR code si qrencode esta disponible (util para movil)
  if command -v qrencode &>/dev/null; then
    echo ""
    qrencode -t UTF8 "$url" 2>/dev/null | sed 's/^/  /'
  fi

  # Abrir browser si hay entorno grafico
  if command -v xdg-open &>/dev/null; then
    xdg-open "$url" &>/dev/null &
  elif command -v open &>/dev/null; then
    open "$url"
  fi

  echo ""
}

# ── svc port-map — mapa global de puertos ──────────────────────────────────
svc_port_map() {
  echo ""
  printf "  \033[1m%-8s %-20s %-25s %s\033[0m\n" \
    "PUERTO" "SERVICIO" "CONTENEDOR" "PROTOCOLO"
  echo "  ───────────────────────────────────────────────────────────────"

  for svc in $(svc_list); do
    local compose_file
    compose_file=$(svc_compose_file "$svc")
    [[ -z "$compose_file" ]] && continue

    # Obtener puertos de contenedores corriendo
    docker compose -f "$compose_file" ps --format "{{.Names}}\t{{.Ports}}" 2>/dev/null \
      | while IFS=$'\t' read -r name ports; do
          [[ -z "$ports" ]] && continue
          # Parsear multiples puertos
          echo "$ports" | grep -oP '0\.0\.0\.0:(\d+)->(\d+)/(\w+)' \
            | while IFS= read -r mapping; do
                local ext_port proto
                ext_port=$(echo "$mapping" | grep -oP '0\.0\.0\.0:\K\d+')
                proto=$(echo "$mapping" | grep -oP '/\K\w+')
                printf "  %-8s %-20s %-25s %s\n" \
                  "$ext_port" "$svc" "$name" "$proto"
              done
        done
  done | sort -t' ' -k2 -n

  echo ""

  # Detectar conflictos
  local ports_list
  ports_list=$(
    for svc in $(svc_list); do
      local f
      f=$(svc_compose_file "$svc")
      [[ -z "$f" ]] && continue
      docker compose -f "$f" ps --format "{{.Ports}}" 2>/dev/null \
        | grep -oP '0\.0\.0\.0:\K\d+'
    done | sort -n
  )

  local dupes
  dupes=$(echo "$ports_list" | uniq -d)
  if [[ -n "$dupes" ]]; then
    echo -e "  \033[0;31m  CONFLICTOS detectados en puertos:\033[0m"
    echo "$dupes" | sed 's/^/    /'
    echo ""
  fi
}

# ── svc size — consumo de disco por servicio ───────────────────────────────
svc_size() {
  echo ""
  printf "  \033[1m%-20s %-12s %-12s %-12s %s\033[0m\n" \
    "SERVICIO" "IMAGENES" "VOLUMENES" "COMPOSE_DIR" "TOTAL"
  echo "  ───────────────────────────────────────────────────────────────────────"

  for svc in $(svc_list); do
    local compose_file
    compose_file=$(svc_compose_file "$svc")
    [[ -z "$compose_file" ]] && continue

    local svc_dir
    svc_dir=$(dirname "$compose_file")

    # Tamano del directorio del compose
    local dir_size
    dir_size=$(du -sh "$svc_dir" 2>/dev/null | cut -f1)

    # Tamano de imagenes
    local img_size="--"
    local images
    images=$(docker compose -f "$compose_file" images -q 2>/dev/null)
    if [[ -n "$images" ]]; then
      img_size=$(docker images --format "{{.Size}}" $images 2>/dev/null \
        | head -1)
    fi

    # Tamano de volumenes nombrados
    local vol_size="--"
    local vol_names
    vol_names=$(docker compose -f "$compose_file" config --volumes 2>/dev/null)
    if [[ -n "$vol_names" ]]; then
      local project
      project=$(basename "$svc_dir")
      local total_bytes=0
      while IFS= read -r vol; do
        [[ -z "$vol" ]] && continue
        local full_vol="${project}_${vol}"
        local vsize
        vsize=$(docker system df -v 2>/dev/null \
          | grep "$full_vol" | awk '{print $NF}' | head -1)
        [[ -n "$vsize" ]] && vol_size="$vsize"
      done <<< "$vol_names"
    fi

    printf "  %-20s %-12s %-12s %-12s\n" \
      "$svc" "$img_size" "$vol_size" "$dir_size"
  done

  echo ""
  echo -e "  \033[0;37m  Tip: 'docker system df' para ver espacio total de Docker\033[0m"
  echo ""
}

# ── svc net — mapa de redes Docker ─────────────────────────────────────────
svc_net() {
  echo ""
  echo -e "\033[1m  REDES DOCKER\033[0m"
  echo "  ───────────────────────────────────────────────────────────────"

  docker network ls --format "{{.Name}}" 2>/dev/null \
    | grep -v "^bridge$\|^host$\|^none$" \
    | while IFS= read -r net; do
        echo ""
        echo -e "  \033[0;34m  $net\033[0m"

        # Contenedores en esta red
        local containers
        containers=$(docker network inspect "$net" \
          --format '{{range .Containers}}{{.Name}} {{end}}' 2>/dev/null)

        if [[ -z "$containers" ]]; then
          echo "      (sin contenedores)"
        else
          for c in $containers; do
            local ip
            ip=$(docker inspect --format \
              "{{range .NetworkSettings.Networks}}{{if eq .NetworkID \"$(docker network inspect "$net" --format '{{.ID}}' 2>/dev/null)\"}}\
{{.IPAddress}}{{end}}{{end}}" "$c" 2>/dev/null)
            [[ -z "$ip" ]] && ip=$(docker inspect --format \
              "{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}" "$c" 2>/dev/null | head -1)
            printf "      %-25s %s\n" "$c" "$ip"
          done
        fi
      done

  echo ""
}

# ── svc env — ver/editar variables ─────────────────────────────────────────
svc_env() {
  local svc="$1"
  shift || true
  local compose_file
  compose_file=$(svc_compose_file "$svc")
  local svc_dir
  svc_dir=$(dirname "$compose_file")
  local env_file="$svc_dir/.env"

  case "${1:-}" in
    edit)
      local editor="${EDITOR:-nano}"
      if [[ -f "$env_file" ]]; then
        $editor "$env_file"
      else
        echo "  No existe .env para '$svc'. Creando..."
        touch "$env_file"
        $editor "$env_file"
      fi
      ;;
    *)
      echo ""
      echo -e "\033[0;34m  Variables de '$svc'\033[0m"
      echo ""

      # .env file
      if [[ -f "$env_file" ]]; then
        echo -e "  \033[0;37m  .env ($env_file):\033[0m"
        grep -v '^#\|^$' "$env_file" 2>/dev/null | sed 's/^/    /'
      else
        echo "    (sin archivo .env)"
      fi

      # Variables inline del compose
      echo ""
      echo -e "  \033[0;37m  Variables inline (del compose):\033[0m"
      docker compose -f "$compose_file" config 2>/dev/null \
        | grep -A50 "environment:" \
        | grep -E "^\s+-\s+|^\s+\w+=\w+" \
        | head -20 \
        | sed 's/^/    /'

      echo ""
      echo "  Para editar: svc env $svc edit"
      echo ""
      ;;
  esac
}

# ── svc create — scaffolding de servicio ───────────────────────────────────
svc_create() {
  local name="$1"

  if [[ -z "$name" ]]; then
    echo ""
    echo "  Uso: svc create <nombre>"
    echo ""
    return 1
  fi

  local svc_dir="$DOCKER_BASE/$name"

  if [[ -d "$svc_dir" ]]; then
    echo ""
    echo "  El directorio '$svc_dir' ya existe."
    echo ""
    return 1
  fi

  echo ""
  echo -e "\033[0;36m  Creando servicio '$name'...\033[0m"

  mkdir -p "$svc_dir"

  # docker-compose.yml template
  cat > "$svc_dir/docker-compose.yml" << 'TEMPLATE'
services:
  app:
    image: IMAGE:TAG
    container_name: SERVICE_NAME
    restart: unless-stopped
    ports:
      - "PORT:PORT"
    volumes:
      - ./data:/data
    env_file:
      - .env
    # networks:
    #   - proxy
    # healthcheck:
    #   test: ["CMD", "curl", "-f", "http://localhost:PORT/health"]
    #   interval: 30s
    #   timeout: 10s
    #   retries: 3

# networks:
#   proxy:
#     external: true
TEMPLATE

  # Reemplazar SERVICE_NAME
  sed -i "s/SERVICE_NAME/$name/g" "$svc_dir/docker-compose.yml"

  # .env vacio
  cat > "$svc_dir/.env" << EOF
# Variables de entorno para $name
# TZ=America/New_York
EOF

  # README
  cat > "$svc_dir/README.md" << EOF
# $name

## Descripcion

(Describir el servicio aqui)

## Puertos

- PORT: (descripcion)

## Volumenes

- \`./data\` -> datos persistentes

## Notas

- Creado: $(date +%Y-%m-%d)
EOF

  # Directorio de datos
  mkdir -p "$svc_dir/data"

  echo ""
  echo "  Estructura creada:"
  echo "    $svc_dir/"
  echo "    ├── docker-compose.yml"
  echo "    ├── .env"
  echo "    ├── README.md"
  echo "    └── data/"
  echo ""
  echo "  Siguiente paso: edita docker-compose.yml con la imagen real"
  echo "    nano $svc_dir/docker-compose.yml"
  echo ""
}

# ── svc watch — monitoreo continuo ─────────────────────────────────────────
svc_watch() {
  local interval="${1:-5}"

  echo -e "\033[0;36m  svc watch (Ctrl+C para salir, refresh: ${interval}s)\033[0m"
  echo ""

  while true; do
    clear
    echo -e "\033[0;36m  === svc watch === $(date '+%H:%M:%S') ===\033[0m"
    echo ""

    printf "  \033[1m%-20s %-10s %-10s %-10s %-12s %s\033[0m\n" \
      "SERVICIO" "ESTADO" "CPU" "MEM" "MEM_LIMIT" "UPTIME"
    echo "  ──────────────────────────────────────────────────────────────────────"

    for svc in $(svc_list); do
      local compose_file
      compose_file=$(svc_compose_file "$svc")
      [[ -z "$compose_file" ]] && continue

      local container_id
      container_id=$(docker compose -f "$compose_file" ps -q 2>/dev/null | head -1)

      if [[ -z "$container_id" ]]; then
        printf "  %-20s \033[0;31m%-10s\033[0m\n" "$svc" "detenido"
        continue
      fi

      # Stats (no-stream para una sola lectura)
      local stats_line
      stats_line=$(docker stats --no-stream --format \
        "{{.CPUPerc}}\t{{.MemUsage}}" "$container_id" 2>/dev/null)

      local cpu mem
      cpu=$(echo "$stats_line" | cut -f1)
      mem=$(echo "$stats_line" | cut -f2)

      # Uptime
      local started_at uptime_str="--"
      started_at=$(docker inspect --format='{{.State.StartedAt}}' "$container_id" 2>/dev/null)
      if [[ -n "$started_at" && "$started_at" != "0001-01-01"* ]]; then
        local start_epoch now_epoch diff
        start_epoch=$(date -d "$started_at" +%s 2>/dev/null || echo 0)
        now_epoch=$(date +%s)
        diff=$(( now_epoch - start_epoch ))
        if [[ $diff -lt 3600 ]]; then
          uptime_str="$(( diff / 60 ))m"
        elif [[ $diff -lt 86400 ]]; then
          uptime_str="$(( diff / 3600 ))h $(( (diff % 3600) / 60 ))m"
        else
          uptime_str="$(( diff / 86400 ))d $(( (diff % 86400) / 3600 ))h"
        fi
      fi

      printf "  %-20s \033[0;32m%-10s\033[0m %-10s %-22s %s\n" \
        "$svc" "activo" "${cpu:-N/A}" "${mem:-N/A}" "$uptime_str"
    done

    echo ""
    echo -e "  \033[0;37m  Refresh en ${interval}s... (Ctrl+C para salir)\033[0m"
    sleep "$interval"
  done
}
