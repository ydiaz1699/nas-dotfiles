# /home/aadm/shell/lib/system.sh

# ── nas — dashboard rapido del NAS ────────────────────────────────────────
nas() {
  local RED='\033[0;31m' GRN='\033[0;32m' YLW='\033[1;33m'
  local BLU='\033[0;34m' CYN='\033[0;36m' GRY='\033[0;37m' NC='\033[0m'

  echo ""
  echo -e "${BLU}--- NAS ------------------------------------------------${NC}"

  # ── Sistema ──
  local uptime_str
  uptime_str=$(uptime -p 2>/dev/null | sed 's/up //')
  local load
  load=$(cut -d' ' -f1-3 /proc/loadavg)
  printf "  ${GRY}%-12s${NC} %s\n" "uptime" "$uptime_str"
  printf "  ${GRY}%-12s${NC} %s\n" "load" "$load"

  # ── Memoria ──
  local mem_total mem_used mem_pct
  mem_total=$(free -m | awk '/^Mem:/{print $2}')
  mem_used=$(free -m | awk '/^Mem:/{print $3}')
  mem_pct=$(( mem_used * 100 / mem_total ))
  local mem_color=$GRN
  [[ $mem_pct -ge 80 ]] && mem_color=$RED
  [[ $mem_pct -ge 60 && $mem_pct -lt 80 ]] && mem_color=$YLW
  printf "  ${GRY}%-12s${NC} ${mem_color}%s MB / %s MB (%s%%)${NC}\n" \
    "memoria" "$mem_used" "$mem_total" "$mem_pct"

  # ── Disco ──
  echo ""
  echo -e "  ${GRY}discos${NC}"
  df -h --output=target,used,size,pcent 2>/dev/null \
    | grep -v "^tmpfs\|^udev\|^/dev/loop\|^Filesystem\|^overlay" \
    | while read -r mount used size pct; do
        local n="${pct//%/}"
        local col=$GRN
        [[ $n -ge 90 ]] && col=$RED
        [[ $n -ge 75 && $n -lt 90 ]] && col=$YLW
        printf "    ${col}%-6s${NC}  %-20s  %s / %s\n" "$pct" "$mount" "$used" "$size"
      done

  # ── Red ──
  echo ""
  echo -e "  ${GRY}red${NC}"
  local iface ip_addr
  while IFS= read -r line; do
    iface=$(echo "$line" | awk '{print $1}' | tr -d ':')
    ip_addr=$(echo "$line" | awk '{print $2}')
    [[ "$iface" != "lo" ]] && printf "    %-12s %s\n" "$iface" "$ip_addr"
  done < <(ip -4 addr show 2>/dev/null \
    | awk '/^[0-9]+:/{iface=$2} /inet /{print iface, $2}' \
    | grep -v "^lo")

  # ── Docker ──
  echo ""
  echo -e "  ${GRY}docker${NC}"
  local running stopped
  running=$(docker ps -q 2>/dev/null | wc -l)
  stopped=$(docker ps -aq 2>/dev/null | wc -l)
  stopped=$(( stopped - running ))
  printf "    ${GRN}%-3s corriendo${NC}   ${RED}%s detenidos${NC}\n" \
    "$running" "$stopped"

  # ── Temperatura (si lm-sensors esta disponible) ──
  if command -v sensors >/dev/null 2>&1; then
    echo ""
    echo -e "  ${GRY}temperatura${NC}"
    sensors 2>/dev/null | grep -E "°C" | head -4 \
      | sed 's/^/    /'
  fi

  echo ""
  echo -e "${BLU}--------------------------------------------------------${NC}"
  echo ""
}

# ── disk — uso de disco rapido ─────────────────────────────────────────────
disk() {
  df -h --output=target,used,size,pcent 2>/dev/null \
    | grep -v "^tmpfs\|^udev\|^/dev/loop\|^Filesystem\|^overlay"
}

# ── netinfo — interfaces y puertos en uso ─────────────────────────────────
netinfo() {
  echo ""
  echo -e "\033[0;34mInterfaces:\033[0m"
  ip -4 addr show 2>/dev/null \
    | awk '/^[0-9]+:/{iface=$2} /inet /{printf "  %-12s %s\n", iface, $2}'
  echo ""
  echo -e "\033[0;34mPuertos en uso (TCP):\033[0m"
  ss -tulnp 2>/dev/null | grep LISTEN \
    | awk '{printf "  %-25s %s\n", $5, $7}' | sort
  echo ""
}

# ── logs — tail de journald o archivo ─────────────────────────────────────
# uso: logs           → ultimas 50 lineas (sin follow)
#      logs -f        → follow del journal
#      logs syslog    → /var/log/syslog (ultimas 50)
#      logs -f auth   → follow de /var/log/auth.log
logs() {
  local follow=false
  local target=""

  # Parsear flags
  while [[ $# -gt 0 ]]; do
    case "$1" in
      -f|--follow) follow=true; shift ;;
      *) target="$1"; shift ;;
    esac
  done

  if [[ -z "$target" ]]; then
    # Journal del sistema
    if $follow; then
      journalctl -n 50 -f 2>/dev/null || tail -f /var/log/syslog
    else
      journalctl -n 50 --no-pager 2>/dev/null || tail -50 /var/log/syslog
    fi
    return
  fi

  # Archivo de log especifico
  local logfile=""
  case "$target" in
    syslog) logfile="/var/log/syslog" ;;
    auth)   logfile="/var/log/auth.log" ;;
    kern)   logfile="/var/log/kern.log" ;;
    *)
      if [[ -f "/var/log/$target" ]]; then
        logfile="/var/log/$target"
      elif [[ -f "/var/log/$target.log" ]]; then
        logfile="/var/log/$target.log"
      else
        echo "  '$target' no reconocido"
        echo "  Opciones: syslog | auth | kern | (o usa: svc logs <servicio>)"
        return 1
      fi
      ;;
  esac

  if $follow; then
    tail -f "$logfile"
  else
    tail -50 "$logfile"
  fi
}
