# /docker/cli/lib/health.sh
# Dashboard de salud con healthcheck, uptime, y restart count

svc_health() {
  echo ""
  printf "  \033[1m%-20s %-12s %-14s %-10s %-8s %s\033[0m\n" \
    "SERVICIO" "ESTADO" "HEALTH" "UPTIME" "RESTART" "DETALLE"
  echo "  ─────────────────────────────────────────────────────────────────────────────────"

  for svc in $(svc_list); do
    local compose_file
    compose_file=$(svc_compose_file "$svc")
    [[ -z "$compose_file" ]] && continue

    local running total
    running=$(docker compose -f "$compose_file" ps -q 2>/dev/null | wc -l | tr -d ' ')
    total=$(docker compose -f "$compose_file" ps -a -q 2>/dev/null | wc -l | tr -d ' ')

    if [[ "$running" -gt 0 ]]; then
      # Obtener info del primer contenedor activo
      local container_id
      container_id=$(docker compose -f "$compose_file" ps -q 2>/dev/null | head -1)

      # Health status
      local health_status="--"
      if [[ -n "$container_id" ]]; then
        health_status=$(docker inspect --format='{{if .State.Health}}{{.State.Health.Status}}{{else}}--{{end}}' \
          "$container_id" 2>/dev/null || echo "--")
      fi

      # Colorear health
      local health_colored="$health_status"
      case "$health_status" in
        healthy)   health_colored="\033[0;32m$health_status\033[0m" ;;
        unhealthy) health_colored="\033[0;31m$health_status\033[0m" ;;
        starting)  health_colored="\033[1;33m$health_status\033[0m" ;;
      esac

      # Uptime
      local uptime_str="--"
      if [[ -n "$container_id" ]]; then
        local started_at
        started_at=$(docker inspect --format='{{.State.StartedAt}}' "$container_id" 2>/dev/null)
        if [[ -n "$started_at" && "$started_at" != "0001-01-01"* ]]; then
          local start_epoch now_epoch diff_seconds
          start_epoch=$(date -d "$started_at" +%s 2>/dev/null || echo 0)
          now_epoch=$(date +%s)
          diff_seconds=$(( now_epoch - start_epoch ))

          if [[ $diff_seconds -lt 3600 ]]; then
            uptime_str="$(( diff_seconds / 60 ))m"
          elif [[ $diff_seconds -lt 86400 ]]; then
            uptime_str="$(( diff_seconds / 3600 ))h"
          else
            uptime_str="$(( diff_seconds / 86400 ))d"
          fi
        fi
      fi

      # Restart count
      local restart_count="0"
      if [[ -n "$container_id" ]]; then
        restart_count=$(docker inspect --format='{{.RestartCount}}' "$container_id" 2>/dev/null || echo "0")
      fi

      local restart_colored="$restart_count"
      [[ "$restart_count" -gt 0 ]] && restart_colored="\033[1;33m${restart_count}\033[0m"
      [[ "$restart_count" -gt 5 ]] && restart_colored="\033[0;31m${restart_count}\033[0m"

      # Status detail
      local detail
      detail=$(docker compose -f "$compose_file" ps --format "{{.Status}}" 2>/dev/null \
        | head -1 | cut -c1-20)

      printf "  \033[0;32m●\033[0m %-20s \033[0;32m%-12s\033[0m %-14b %-10s %-8b %s\n" \
        "$svc" "$running/$total" "$health_colored" "$uptime_str" "$restart_colored" "$detail"
    else
      printf "  \033[0;31m○\033[0m %-20s \033[0;31m%-12s\033[0m\n" \
        "$svc" "detenido"
    fi
  done

  echo ""
}
