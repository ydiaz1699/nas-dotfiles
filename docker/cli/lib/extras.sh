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
  done | sort -k1,1n

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


# ── svc doctor — chequeo general del NAS ───────────────────────────────────
svc_doctor() {
  echo ""
  echo -e "\033[1m  svc doctor — Chequeo general del NAS (8 puntos)\033[0m"
  echo "  ═══════════════════════════════════════════════════════════════"
  echo ""

  local issues=0
  local warnings=0

  # 1. Disco
  echo -e "\033[0;34m  [1/6] Disco\033[0m"
  while IFS= read -r line; do
    local pct
    pct=$(echo "$line" | awk '{print $5}' | tr -d '%')
    local mount
    mount=$(echo "$line" | awk '{print $6}')
    if [[ -n "$pct" && "$pct" =~ ^[0-9]+$ ]]; then
      if [[ $pct -ge 90 ]]; then
        echo -e "    \033[0;31m✗ CRÍTICO: $mount al ${pct}%\033[0m"
        ((issues++))
      elif [[ $pct -ge 75 ]]; then
        echo -e "    \033[1;33m⚠ ATENCIÓN: $mount al ${pct}%\033[0m"
        ((warnings++))
      fi
    fi
  done < <(df -h --type=ext4 --type=btrfs --type=xfs 2>/dev/null | tail -n+2)
  [[ $issues -eq 0 && $warnings -eq 0 ]] && echo "    ✓ Disco OK"
  echo ""

  # 2. Memoria
  echo -e "\033[0;34m  [2/6] Memoria\033[0m"
  local mem_pct
  mem_pct=$(free | awk '/^Mem:/{printf "%.0f", $3/$2*100}')
  if [[ $mem_pct -ge 90 ]]; then
    echo -e "    \033[0;31m✗ CRÍTICO: Memoria al ${mem_pct}%\033[0m"
    ((issues++))
  elif [[ $mem_pct -ge 80 ]]; then
    echo -e "    \033[1;33m⚠ Memoria al ${mem_pct}%\033[0m"
    ((warnings++))
  else
    echo "    ✓ Memoria al ${mem_pct}% (OK)"
  fi
  echo ""

  # 3. Servicios caídos
  echo -e "\033[0;34m  [3/6] Servicios Docker\033[0m"
  local total_svc=0
  local down_svc=0
  local restarting_svc=0
  for svc in $(svc_list 2>/dev/null); do
    ((total_svc++))
    local f
    f=$(svc_compose_file "$svc" 2>/dev/null)
    [[ -z "$f" ]] && continue
    local running
    running=$(docker compose -f "$f" ps -q 2>/dev/null | wc -l)
    if [[ $running -eq 0 ]]; then
      echo -e "    \033[0;31m✗ $svc: DETENIDO\033[0m"
      ((down_svc++))
      ((issues++))
    fi
  done
  # Contenedores reiniciando
  local restarting
  restarting=$(docker ps --filter "status=restarting" --format "{{.Names}}" 2>/dev/null)
  if [[ -n "$restarting" ]]; then
    while read -r name; do
      echo -e "    \033[1;33m⚠ $name: REINICIANDO (crash loop?)\033[0m"
      ((warnings++))
    done <<< "$restarting"
  fi
  [[ $down_svc -eq 0 && -z "$restarting" ]] && echo "    ✓ $total_svc servicios, todos activos"

  # Healthcheck HTTP genérico (para servicios sin healthcheck en compose)
  for svc in $(svc_list 2>/dev/null); do
    local f
    f=$(svc_compose_file "$svc" 2>/dev/null)
    [[ -z "$f" ]] && continue
    # Solo si está corriendo
    local running
    running=$(docker compose -f "$f" ps -q 2>/dev/null | wc -l)
    [[ $running -eq 0 ]] && continue
    # Solo si NO tiene healthcheck definido
    if grep -q "healthcheck:" "$f" 2>/dev/null; then
      continue
    fi
    # Detectar puerto expuesto
    local port
    port=$(grep -oP '"\K\d+(?=:\d+")' "$f" 2>/dev/null | head -1)
    [[ -z "$port" ]] && continue
    # Intentar curl
    if ! curl -sf --max-time 3 "http://localhost:${port}/" >/dev/null 2>&1; then
      echo -e "    \033[1;33m⚠ $svc (:$port) sin healthcheck y no responde HTTP\033[0m"
      ((warnings++))
    fi
  done
  echo ""

  # 4. Puertos reservados
  echo -e "\033[0;34m  [4/6] Puertos reservados\033[0m"
  local reserved_conflict=0
  for rp in 22 53 80 443; do
    if ss -tlnp 2>/dev/null | grep -q ":${rp} "; then
      # Verificar que sea un servicio esperado
      local proc
      proc=$(ss -tlnp 2>/dev/null | grep ":${rp} " | grep -oP 'users:\(\("\K[^"]+' | head -1)
      if [[ "$proc" != "sshd" && "$proc" != "systemd-resolve" && "$proc" != "traefik" && "$proc" != "nginx" && "$proc" != "pihole" ]]; then
        echo -e "    \033[1;33m⚠ Puerto $rp usado por: $proc (¿inesperado?)\033[0m"
        ((warnings++))
        ((reserved_conflict++))
      fi
    fi
  done
  [[ $reserved_conflict -eq 0 ]] && echo "    ✓ Puertos reservados libres/esperados"
  echo ""

  # 5. Contenedores con muchos restarts
  echo -e "\033[0;34m  [5/6] Restart count\033[0m"
  local high_restarts=0
  while read -r cid; do
    [[ -z "$cid" ]] && continue
    local name restarts
    name=$(docker inspect --format '{{.Name}}' "$cid" 2>/dev/null | tr -d '/')
    restarts=$(docker inspect --format '{{.RestartCount}}' "$cid" 2>/dev/null)
    if [[ -n "$restarts" && "$restarts" -gt 5 ]]; then
      echo -e "    \033[1;33m⚠ $name: $restarts restarts\033[0m"
      ((high_restarts++))
      ((warnings++))
    fi
  done < <(docker ps -q 2>/dev/null)
  [[ $high_restarts -eq 0 ]] && echo "    ✓ Sin contenedores con restarts excesivos"
  echo ""

  # 6. Docker disk usage
  echo -e "\033[0;34m  [6/6] Docker storage\033[0m"
  local docker_disk
  docker_disk=$(docker system df 2>/dev/null | tail -n+2)
  echo "$docker_disk" | sed 's/^/    /'
  # Verificar dangling images
  local dangling
  dangling=$(docker images -f "dangling=true" -q 2>/dev/null | wc -l)
  if [[ $dangling -gt 5 ]]; then
    echo -e "    \033[1;33m⚠ $dangling imágenes dangling (limpiar con: docker image prune)\033[0m"
    ((warnings++))
  fi
  echo ""

  # 7. Secretos sin rotar (PASSWORD/TOKEN con valor placeholder)
  echo -e "\033[0;34m  [7/8] Secretos\033[0m"
  local weak_secrets=0
  for svc_dir in "$BASE"/*/; do
    [[ -f "${svc_dir}.env" ]] || continue
    local svc_name
    svc_name=$(basename "$svc_dir")
    while IFS='=' read -r key value; do
      # Saltar comentarios y líneas vacías
      [[ -z "$key" || "$key" =~ ^[[:space:]]*# ]] && continue
      # Solo verificar variables que parecen secretos
      if [[ "$key" =~ (PASSWORD|SECRET|TOKEN|COOKIE|KEY) ]]; then
        # Detectar placeholders o valores débiles
        if [[ "$value" == "CAMBIAR" || "$value" == "changeme" || "$value" == "password" \
           || "$value" == "__pega_aqui__" || "$value" == "admin" || ${#value} -lt 8 ]]; then
          echo -e "    \033[1;33m⚠ $svc_name: $key tiene valor débil/placeholder\033[0m"
          ((weak_secrets++))
          ((warnings++))
        fi
      fi
    done < "${svc_dir}.env"
  done
  [[ $weak_secrets -eq 0 ]] && echo "    ✓ Sin secretos débiles detectados"
  echo ""

  # 8. Permisos de .env (deben ser 600)
  echo -e "\033[0;34m  [8/8] Permisos .env\033[0m"
  local bad_perms=0
  for svc_dir in "$BASE"/*/; do
    [[ -f "${svc_dir}.env" ]] || continue
    local svc_name
    svc_name=$(basename "$svc_dir")
    local perms
    perms=$(stat -c "%a" "${svc_dir}.env" 2>/dev/null)
    if [[ "$perms" != "600" ]]; then
      echo -e "    \033[1;33m⚠ $svc_name/.env tiene permisos $perms (debería ser 600)\033[0m"
      ((bad_perms++))
      ((warnings++))
    fi
  done
  [[ $bad_perms -eq 0 ]] && echo "    ✓ Todos los .env con permisos 600"
  echo ""

  # Resumen
  echo "  ═══════════════════════════════════════════════════════════════"
  if [[ $issues -gt 0 ]]; then
    echo -e "  \033[0;31m  RESULTADO: $issues error(es), $warnings advertencia(s)\033[0m"
  elif [[ $warnings -gt 0 ]]; then
    echo -e "  \033[1;33m  RESULTADO: 0 errores, $warnings advertencia(s)\033[0m"
  else
    echo -e "  \033[0;32m  RESULTADO: ✓ Todo en orden\033[0m"
  fi
  echo ""

  # Guardar historial (para tendencias)
  _svc_doctor_log "$issues" "$warnings"
}

# ── svc diff — comparar compose en disco vs resuelto ───────────────────────
svc_diff() {
  local svc="$1"

  if [[ -z "$svc" ]]; then
    echo ""
    echo "  Uso: svc diff <servicio>"
    echo ""
    echo "  Compara el docker-compose.yml en disco contra la"
    echo "  configuración resuelta por 'docker compose config'."
    echo "  Detecta drift (variables no resueltas, overrides, etc.)"
    echo ""
    return 1
  fi

  local compose_file
  compose_file=$(svc_compose_file "$svc")

  if [[ -z "$compose_file" ]]; then
    echo ""
    echo "  Servicio '$svc' no encontrado."
    echo ""
    return 1
  fi

  echo ""
  echo -e "\033[0;34m  svc diff: $svc\033[0m"
  echo "  Archivo: $compose_file"
  echo "  ───────────────────────────────────────────────────────────"
  echo ""

  # Generar config resuelta
  local resolved
  resolved=$(docker compose -f "$compose_file" config 2>&1)

  if [[ $? -ne 0 ]]; then
    echo -e "  \033[0;31m  Error resolviendo config:\033[0m"
    echo "$resolved" | sed 's/^/    /'
    echo ""
    return 1
  fi

  # Comparar con diff
  local disk_content
  disk_content=$(cat "$compose_file")

  local diff_output
  diff_output=$(diff --color=always -u \
    <(echo "$disk_content") \
    <(echo "$resolved") \
    2>/dev/null)

  if [[ -z "$diff_output" ]]; then
    echo -e "  \033[0;32m  ✓ Sin diferencias — compose y config resuelto son idénticos\033[0m"
  else
    echo -e "  \033[1;33m  Diferencias encontradas:\033[0m"
    echo "  (izq = disco, der = resuelto por Docker)"
    echo ""
    echo "$diff_output" | sed 's/^/  /'
  fi

  # Variables sin resolver
  local unresolved
  unresolved=$(grep -oP '\$\{[^}]+\}' "$compose_file" 2>/dev/null | sort -u)
  if [[ -n "$unresolved" ]]; then
    echo ""
    echo -e "  \033[0;34m  Variables referenciadas:\033[0m"
    echo "$unresolved" | sed 's/^/    /'

    # Verificar cuáles no están definidas en .env
    local env_file
    env_file="$(dirname "$compose_file")/.env"
    if [[ -f "$env_file" ]]; then
      echo ""
      echo -e "  \033[0;34m  Estado en .env:\033[0m"
      echo "$unresolved" | while read -r var; do
        local varname
        varname=$(echo "$var" | tr -d '${}' | cut -d: -f1 | cut -d- -f1)
        if grep -q "^${varname}=" "$env_file" 2>/dev/null; then
          echo -e "    ✓ $varname (definida)"
        else
          echo -e "    \033[1;33m⚠ $varname (NO definida en .env)\033[0m"
        fi
      done
    fi
  fi

  echo ""
}



# ── svc clone — duplicar servicio existente ────────────────────────────────
svc_clone() {
  local origen="$1"
  local nuevo="$2"

  if [[ -z "$origen" || -z "$nuevo" ]]; then
    echo ""
    echo "  Uso: svc clone <servicio_origen> <servicio_nuevo>"
    echo ""
    echo "  Duplica un servicio existente como base para uno nuevo:"
    echo "    • Copia compose.yml con container_name y puertos actualizados"
    echo "    • Copia .env con secretos reemplazados por placeholders"
    echo "    • Crea estructura de carpetas (data/config)"
    echo "    • NO inicia el servicio (editar .env primero)"
    echo ""
    echo "  Ejemplo: svc clone ntfy ntfy-dev"
    echo ""
    return 1
  fi

  local origen_dir="${BASE}/${origen}"
  local nuevo_dir="${BASE}/${nuevo}"

  # Validar origen
  local compose_file
  compose_file=$(svc_compose_file "$origen")
  if [[ -z "$compose_file" ]]; then
    echo ""
    echo -e "  \033[0;31mServicio origen '$origen' no encontrado.\033[0m"
    echo ""
    return 1
  fi

  # Validar que nuevo no exista
  if [[ -d "$nuevo_dir" ]]; then
    echo ""
    echo -e "  \033[0;31mEl destino '$nuevo' ya existe en $BASE/\033[0m"
    echo ""
    return 1
  fi

  # Validar nombre
  if [[ ! "$nuevo" =~ ^[a-z0-9][a-z0-9._-]{0,63}$ ]]; then
    echo ""
    echo -e "  \033[0;31mNombre inválido: '$nuevo'\033[0m"
    echo "  Formato: [a-z0-9][a-z0-9._-]{0,63}"
    echo ""
    return 1
  fi

  echo ""
  echo -e "\033[0;36m  Clonando '$origen' → '$nuevo'\033[0m"
  echo ""

  # Crear directorio
  mkdir -p "$nuevo_dir"

  # Copiar compose.yml con reemplazos
  if [[ -f "${origen_dir}/compose.yml" ]]; then
    sed \
      -e "s/container_name: ${origen}/container_name: ${nuevo}/g" \
      -e "s/container_name: \"${origen}\"/container_name: \"${nuevo}\"/g" \
      "${origen_dir}/compose.yml" > "${nuevo_dir}/compose.yml"

    # Advertir sobre puertos que podrían conflictuar
    local ports
    ports=$(grep -oP '"\K\d+(?=:\d+")' "${nuevo_dir}/compose.yml" 2>/dev/null | head -5)
    if [[ -n "$ports" ]]; then
      echo -e "  \033[1;33m⚠ Puertos copiados (editar para evitar conflictos):\033[0m"
      echo "$ports" | sed 's/^/    /'
    fi
    echo "  ✓ compose.yml copiado (container_name actualizado)"
  fi

  # Copiar .env sanitizado (secretos → placeholder)
  if [[ -f "${origen_dir}/.env" ]]; then
    local secret_patterns="PASSWORD|SECRET|TOKEN|COOKIE|KEY|PASS"
    while IFS= read -r line; do
      if [[ "$line" =~ ^[[:space:]]*# ]] || [[ -z "$line" ]]; then
        echo "$line"
      elif [[ "$line" =~ ^([A-Z_]+)= ]]; then
        local key="${BASH_REMATCH[1]}"
        if [[ "$key" =~ ($secret_patterns) ]]; then
          echo "${key}=__CAMBIAR__"
        else
          echo "$line"
        fi
      else
        echo "$line"
      fi
    done < "${origen_dir}/.env" > "${nuevo_dir}/.env"
    chmod 600 "${nuevo_dir}/.env"
    echo "  ✓ .env copiado (secretos → __CAMBIAR__)"
  fi

  # Copiar estructura de carpetas de datos (vacías)
  if [[ -d "${origen_dir}/data" ]]; then
    # Replicar estructura sin contenido
    (cd "${origen_dir}" && find data -type d) | while read -r dir; do
      mkdir -p "${nuevo_dir}/${dir}"
    done
    echo "  ✓ Estructura data/ replicada (vacía)"
  fi

  if [[ -d "${origen_dir}/config" ]]; then
    # Config se copia con contenido (son plantillas)
    cp -r "${origen_dir}/config" "${nuevo_dir}/config"
    echo "  ✓ config/ copiado (con contenido)"
  fi

  echo ""
  echo -e "  \033[0;32m✅ Clonado exitosamente en $nuevo_dir\033[0m"
  echo ""
  echo "  Próximos pasos:"
  echo "    1. Editar .env: nano $nuevo_dir/.env"
  echo "    2. Editar compose.yml: cambiar puertos, redes, etc."
  echo "    3. Levantar: dk $nuevo && svc up $nuevo"
  echo ""
}

# ── svc cron — helper para agendar backups/updates via crontab ─────────────
svc_cron() {
  local action="$1"
  shift || true

  case "$action" in
    add)
      _svc_cron_add "$@"
      ;;
    list)
      _svc_cron_list
      ;;
    remove)
      _svc_cron_remove "$@"
      ;;
    ""|--help|-h)
      echo ""
      echo "  Uso: svc cron <acción> [opciones]"
      echo ""
      echo "  Acciones:"
      echo "    add <tipo> <horario> [servicio]   Agendar tarea"
      echo "    list                              Ver tareas agendadas"
      echo "    remove <n>                        Eliminar tarea por número"
      echo ""
      echo "  Tipos:"
      echo "    backup-all    Backup de todos los servicios"
      echo "    backup <svc>  Backup de un servicio específico"
      echo "    update-all    Actualizar todos los servicios"
      echo "    doctor        Chequeo general con log"
      echo ""
      echo "  Horarios (formato cron simplificado):"
      echo "    daily         Todos los días a las 03:00"
      echo "    weekly        Domingos a las 03:00"
      echo "    hourly        Cada hora"
      echo "    <cron expr>   Expresión cron completa (ej: '0 4 * * 1-5')"
      echo ""
      echo "  Ejemplos:"
      echo "    svc cron add backup-all daily"
      echo "    svc cron add backup datasql weekly"
      echo "    svc cron add update-all weekly"
      echo "    svc cron add doctor daily"
      echo "    svc cron list"
      echo "    svc cron remove 2"
      echo ""
      ;;
    *)
      echo "  Acción desconocida: $action (usa: add, list, remove)"
      return 1
      ;;
  esac
}

_svc_cron_add() {
  local tipo="$1"
  local horario="$2"
  local servicio="$3"

  if [[ -z "$tipo" || -z "$horario" ]]; then
    echo "  Uso: svc cron add <tipo> <horario> [servicio]"
    return 1
  fi

  # Resolver horario simplificado
  local cron_expr
  case "$horario" in
    daily)   cron_expr="0 3 * * *" ;;
    weekly)  cron_expr="0 3 * * 0" ;;
    hourly)  cron_expr="0 * * * *" ;;
    *)       cron_expr="$horario" ;;
  esac

  # Construir comando
  local svc_cmd
  local cli_path="${NAS_DOTFILES:-/nas-dotfiles}/docker/cli/svc.sh"
  local env_prefix="DOCKER_BASE=${BASE} NAS_DOTFILES=${NAS_DOTFILES:-/nas-dotfiles}"

  case "$tipo" in
    backup-all)
      svc_cmd="${env_prefix} bash ${cli_path} backup-all -y"
      ;;
    backup)
      if [[ -z "$servicio" ]]; then
        echo "  'backup' requiere servicio: svc cron add backup <servicio> <horario>"
        return 1
      fi
      svc_cmd="${env_prefix} bash ${cli_path} backup ${servicio}"
      ;;
    update-all)
      svc_cmd="${env_prefix} bash ${cli_path} update-all -y"
      ;;
    doctor)
      svc_cmd="${env_prefix} bash ${cli_path} doctor >> /var/log/svc-doctor.log 2>&1"
      ;;
    *)
      echo "  Tipo desconocido: $tipo"
      return 1
      ;;
  esac

  # Agregar al crontab
  local cron_line="${cron_expr} ${svc_cmd} # svc-cron:${tipo}"
  (crontab -l 2>/dev/null; echo "$cron_line") | crontab -

  echo ""
  echo -e "  \033[0;32m✅ Tarea agendada:\033[0m"
  echo "     Tipo: $tipo"
  echo "     Horario: $cron_expr ($horario)"
  echo "     Comando: $svc_cmd"
  echo ""
  echo "  Ver todas: svc cron list"
  echo ""
}

_svc_cron_list() {
  echo ""
  echo -e "\033[0;34m  ━━━ Tareas svc agendadas en crontab ━━━\033[0m"
  echo ""

  local found=0
  local i=1
  while IFS= read -r line; do
    if [[ "$line" == *"# svc-cron:"* ]]; then
      local tipo
      tipo=$(echo "$line" | grep -oP '# svc-cron:\K\S+')
      local schedule
      schedule=$(echo "$line" | awk '{print $1,$2,$3,$4,$5}')
      printf "    %2d) [%s] %s\n" "$i" "$schedule" "$tipo"
      ((found++))
      ((i++))
    fi
  done < <(crontab -l 2>/dev/null)

  if [[ $found -eq 0 ]]; then
    echo "    (ninguna tarea agendada)"
    echo ""
    echo "    Agendar: svc cron add backup-all daily"
  fi
  echo ""
}

_svc_cron_remove() {
  local num="$1"

  if [[ -z "$num" ]]; then
    echo "  Uso: svc cron remove <número>"
    echo "  (ver números con: svc cron list)"
    return 1
  fi

  # Obtener línea N de las que tienen svc-cron
  local target_line
  local i=0
  while IFS= read -r line; do
    if [[ "$line" == *"# svc-cron:"* ]]; then
      ((i++))
      if [[ $i -eq $num ]]; then
        target_line="$line"
        break
      fi
    fi
  done < <(crontab -l 2>/dev/null)

  if [[ -z "$target_line" ]]; then
    echo "  No se encontró tarea #$num"
    return 1
  fi

  # Escapar para grep -v
  local escaped
  escaped=$(printf '%s\n' "$target_line" | sed 's/[[\.*^$()+?{|]/\\&/g')
  crontab -l 2>/dev/null | grep -vF "$target_line" | crontab -

  echo ""
  echo -e "  \033[0;32m✅ Tarea #$num eliminada\033[0m"
  echo ""
}



# ── Doctor history — guardar resultado para tendencias ─────────────────────
DOCTOR_LOG="${DOCKER_BASE:-/docker}/backups/doctor-history.log"

_svc_doctor_log() {
  local issues="$1"
  local warnings="$2"
  local timestamp
  timestamp=$(date -Iseconds)
  local mem_pct
  mem_pct=$(free | awk '/^Mem:/{printf "%.0f", $3/$2*100}' 2>/dev/null || echo "0")
  local disk_pct
  disk_pct=$(df / 2>/dev/null | awk 'NR==2{print $5}' | tr -d '%')
  local containers
  containers=$(docker ps -q 2>/dev/null | wc -l)

  mkdir -p "$(dirname "$DOCTOR_LOG")"

  # Formato: timestamp | issues | warnings | mem% | disk% | containers
  echo "${timestamp}|${issues}|${warnings}|${mem_pct}|${disk_pct:-0}|${containers}" >> "$DOCTOR_LOG"
}

# ── svc doctor-history — ver tendencia de las últimas corridas ─────────────
svc_doctor_history() {
  local lines="${1:-20}"

  if [[ ! -f "$DOCTOR_LOG" ]]; then
    echo ""
    echo "  Sin historial de doctor. Ejecutar 'svc doctor' al menos una vez."
    echo ""
    return 0
  fi

  echo ""
  echo -e "\033[0;34m  ━━━ Historial de svc doctor (últimas $lines corridas) ━━━\033[0m"
  echo ""
  printf "  %-22s %7s %7s %5s %5s %6s\n" "FECHA" "ERRORES" "WARNS" "MEM%" "DISK%" "CONT."
  echo "  ──────────────────────────────────────────────────────────────────"

  tail -n "$lines" "$DOCTOR_LOG" | while IFS='|' read -r ts issues warns mem disk conts; do
    local date_short
    date_short=$(echo "$ts" | cut -d'T' -f1,2 | sed 's/T/ /' | cut -c1-16)

    # Colorear según severidad
    local issue_color="\033[0;32m"
    [[ $issues -gt 0 ]] && issue_color="\033[0;31m"
    local warn_color="\033[0;32m"
    [[ $warns -gt 0 ]] && warn_color="\033[1;33m"
    local mem_color=""
    [[ ${mem:-0} -ge 80 ]] && mem_color="\033[1;33m"
    [[ ${mem:-0} -ge 90 ]] && mem_color="\033[0;31m"

    printf "  %-22s ${issue_color}%7s\033[0m ${warn_color}%7s\033[0m ${mem_color}%5s\033[0m %5s %6s\n" \
      "$date_short" "$issues" "$warns" "${mem}%" "${disk}%" "$conts"
  done

  echo ""
  echo "  Ubicación: $DOCTOR_LOG"
  echo "  Tip: agendar con 'svc cron add doctor daily'"
  echo ""
}



# ── svc lock/unlock — proteger servicios contra stop/down accidental ───────
LOCK_FILE="${DOCKER_BASE:-/docker}/.locks"

svc_lock() {
  local svc="$1"

  if [[ -z "$svc" ]]; then
    echo ""
    echo "  Uso: svc lock <servicio>"
    echo ""
    echo "  Marca un servicio como protegido. Las acciones destructivas"
    echo "  (stop, down, kill, restore) requieren doble confirmación."
    echo ""
    echo "  Servicios protegidos actualmente:"
    _svc_lock_list
    echo ""
    return 0
  fi

  # Verificar que el servicio existe
  local f
  f=$(svc_compose_file "$svc")
  if [[ -z "$f" ]]; then
    echo "  Servicio '$svc' no encontrado."
    return 1
  fi

  # Agregar al archivo de locks (si no está ya)
  touch "$LOCK_FILE"
  if grep -qx "$svc" "$LOCK_FILE" 2>/dev/null; then
    echo ""
    echo -e "  \033[1;33m⚠ '$svc' ya está protegido.\033[0m"
    echo ""
  else
    echo "$svc" >> "$LOCK_FILE"
    echo ""
    echo -e "  \033[0;32m🔒 '$svc' protegido.\033[0m"
    echo "  Acciones stop/down/kill/restore requerirán doble confirmación."
    echo "  Desproteger con: svc unlock $svc"
    echo ""
  fi
}

svc_unlock() {
  local svc="$1"

  if [[ -z "$svc" ]]; then
    echo ""
    echo "  Uso: svc unlock <servicio>"
    echo ""
    echo "  Servicios protegidos actualmente:"
    _svc_lock_list
    echo ""
    return 0
  fi

  if [[ ! -f "$LOCK_FILE" ]] || ! grep -qx "$svc" "$LOCK_FILE" 2>/dev/null; then
    echo ""
    echo "  '$svc' no está protegido."
    echo ""
    return 0
  fi

  # Quitar del archivo
  local tmp
  tmp=$(mktemp)
  grep -vx "$svc" "$LOCK_FILE" > "$tmp"
  mv "$tmp" "$LOCK_FILE"

  echo ""
  echo -e "  \033[0;32m🔓 '$svc' desprotegido.\033[0m"
  echo ""
}

_svc_lock_list() {
  if [[ ! -f "$LOCK_FILE" ]] || [[ ! -s "$LOCK_FILE" ]]; then
    echo "    (ninguno)"
    return
  fi
  while read -r svc; do
    [[ -n "$svc" ]] && echo "    🔒 $svc"
  done < "$LOCK_FILE"
}

# Guard: verificar si un servicio está protegido antes de acción destructiva
# Retorna 0 si se puede continuar, 1 si se cancela
_svc_lock_guard() {
  local svc="$1"
  local action="$2"

  if [[ ! -f "$LOCK_FILE" ]]; then
    return 0
  fi

  if ! grep -qx "$svc" "$LOCK_FILE" 2>/dev/null; then
    return 0
  fi

  # Servicio protegido — pedir doble confirmación
  echo ""
  echo -e "  \033[0;31m⚠️  ATENCIÓN: '$svc' está PROTEGIDO (🔒)\033[0m"
  echo ""
  echo "  Estás a punto de ejecutar: svc $action $svc"
  echo "  Esta acción puede causar downtime o pérdida de datos."
  echo ""
  read -rp "  Escribir el nombre del servicio para confirmar: " confirm_name

  if [[ "$confirm_name" != "$svc" ]]; then
    echo ""
    echo -e "  \033[0;32m  Cancelado. (nombre no coincide)\033[0m"
    echo ""
    return 1
  fi

  echo ""
  echo -e "  \033[1;33m  Confirmado — procediendo con $action...\033[0m"
  echo ""
  return 0
}
