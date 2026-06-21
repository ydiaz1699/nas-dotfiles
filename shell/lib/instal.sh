# /home/aadm/shell/lib/instal.sh

# ── _apt_cmd — detecta apt-fast o fallback a apt-get ──────────────────────
_apt_cmd() {
  if command -v apt-fast >/dev/null 2>&1; then
    echo "apt-fast"
  else
    echo "apt-get"
  fi
}

# ── _apt_cache_stale — true si el cache de apt tiene mas de N horas ───────
_apt_cache_stale() {
  local max_hours="${1:-6}"
  local stamp="/var/cache/apt/pkgcache.bin"

  if [[ ! -f "$stamp" ]]; then
    return 0  # no existe = stale
  fi

  local now file_time age_hours
  now=$(date +%s)
  file_time=$(stat -c %Y "$stamp" 2>/dev/null || echo 0)
  age_hours=$(( (now - file_time) / 3600 ))

  [[ $age_hours -ge $max_hours ]]
}

instal() {
  if [[ $# -eq 0 ]]; then
    echo "Uso: instal paquete1 [paquete2 ...]" >&2
    return 1
  fi

  local pkgs_to_install=()
  local skipped=()
  local not_found=()
  local pkg
  local auto_yes=false

  # Clasificar cada paquete
  for pkg in "$@"; do
    case "$pkg" in
      -y|--yes) auto_yes=true; continue ;;
    esac

    local status
    status=$(dpkg-query -W -f='${Status}' "$pkg" 2>/dev/null)

    if [[ "$status" == "install ok installed" ]]; then
      echo "  Ya instalado: $pkg"
      skipped+=("$pkg")
    elif ! apt-cache show "$pkg" >/dev/null 2>&1; then
      echo "  No encontrado: $pkg" >&2
      not_found+=("$pkg")
    else
      pkgs_to_install+=("$pkg")
    fi
  done

  # Nada valido que instalar
  if [[ ${#pkgs_to_install[@]} -eq 0 ]]; then
    echo "Nada que instalar."
    return 0
  fi

  # Actualizar cache si esta viejo (>6 horas)
  if _apt_cache_stale 6; then
    echo "  Actualizando cache de apt..."
    local acmd
    acmd=$(_apt_cmd)
    [[ $EUID -ne 0 ]] && acmd="sudo $acmd"
    $acmd update -qq
  fi

  # Instalar
  local apt_cmd
  apt_cmd=$(_apt_cmd)
  [[ $EUID -ne 0 ]] && apt_cmd="sudo $apt_cmd"

  $apt_cmd install -y "${pkgs_to_install[@]}"
  local exit_code=$?

  # Log: verificar cuales quedaron realmente instalados
  if [[ $exit_code -eq 0 ]]; then
    local logdir="${aadm:-$HOME}/instal"
    mkdir -p "$logdir"
    for pkg in "${pkgs_to_install[@]}"; do
      if dpkg-query -W -f='${Status}' "$pkg" 2>/dev/null | grep -q "install ok installed"; then
        # Evitar duplicados en el log
        if ! grep -qF "install -y $pkg" "$logdir/manual.txt" 2>/dev/null; then
          echo "$(_apt_cmd) install -y $pkg" >> "$logdir/manual.txt"
        fi
      fi
    done
  fi

  # Resumen final
  echo ""
  [[ ${#pkgs_to_install[@]} -gt 0 ]] && echo "  Instalados:  ${pkgs_to_install[*]}"
  [[ ${#skipped[@]}         -gt 0 ]] && echo "  Ya tenias:   ${skipped[*]}"
  [[ ${#not_found[@]}       -gt 0 ]] && echo "  No existe:   ${not_found[*]}"

  return $exit_code
}
