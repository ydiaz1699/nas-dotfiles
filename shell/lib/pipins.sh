# shell/lib/pipins.sh
# pipins — Instalador de paquetes pip (equivalente a instal para Python)
#
# Uso:
#   pipins docker rich typer       # instala los 3
#   pipins -u rich                 # upgrade (--upgrade)
#   pipins                         # sin args → muestra uso
#
# Features:
#   - Detecta si ya está instalado (skip)
#   - Log en logs/pip_packages.txt
#   - Soporta --upgrade / -u
#   - Funciona con pip3 o pip

# ── _pip_cmd — detecta pip3 o pip ─────────────────────────────────────────
_pip_cmd() {
  if command -v pip3 >/dev/null 2>&1; then
    echo "pip3"
  elif command -v pip >/dev/null 2>&1; then
    echo "pip"
  else
    echo ""
  fi
}

pipins() {
  if [[ $# -eq 0 ]]; then
    echo ""
    echo "  pipins — Instalador de paquetes Python (pip)"
    echo ""
    echo "  Uso: pipins paquete1 [paquete2 ...]"
    echo "       pipins -u paquete      (upgrade)"
    echo ""
    echo "  Ejemplos:"
    echo "    pipins rich typer InquirerPy"
    echo "    pipins docker pyyaml"
    echo "    pipins -u rich            (actualizar)"
    echo ""
    return 1
  fi

  local pip_cmd
  pip_cmd=$(_pip_cmd)

  if [[ -z "$pip_cmd" ]]; then
    echo "  ✗ pip no encontrado. Instalar: instal python3-pip" >&2
    return 1
  fi

  local pkgs_to_install=()
  local skipped=()
  local upgrade=false
  local pkg

  # Parsear argumentos
  for pkg in "$@"; do
    case "$pkg" in
      -u|--upgrade) upgrade=true; continue ;;
    esac

    # Verificar si ya está instalado
    if $pip_cmd show "$pkg" >/dev/null 2>&1 && ! $upgrade; then
      local ver
      ver=$($pip_cmd show "$pkg" 2>/dev/null | grep "^Version:" | cut -d' ' -f2)
      echo "  Ya instalado: $pkg ($ver)"
      skipped+=("$pkg")
    else
      pkgs_to_install+=("$pkg")
    fi
  done

  # Nada que instalar
  if [[ ${#pkgs_to_install[@]} -eq 0 ]]; then
    echo "  Nada que instalar."
    return 0
  fi

  # Instalar
  local flags=()
  $upgrade && flags+=(--upgrade)

  echo ""
  echo "  Instalando: ${pkgs_to_install[*]}"
  echo ""

  $pip_cmd install "${flags[@]}" "${pkgs_to_install[@]}"
  local exit_code=$?

  # Log
  if [[ $exit_code -eq 0 ]]; then
    local logdir="${NAS_DOTFILES:-/nas-dotfiles}/logs"
    mkdir -p "$logdir"
    for pkg in "${pkgs_to_install[@]}"; do
      if $pip_cmd show "$pkg" >/dev/null 2>&1; then
        local ver
        ver=$($pip_cmd show "$pkg" 2>/dev/null | grep "^Version:" | cut -d' ' -f2)
        local action="install"
        $upgrade && action="upgrade"
        # Evitar duplicados
        if ! grep -qF "pip $action $pkg" "$logdir/pip_packages.txt" 2>/dev/null; then
          echo "pip $action $pkg==$ver" >> "$logdir/pip_packages.txt"
        fi
      fi
    done
  fi

  # Resumen
  echo ""
  [[ ${#pkgs_to_install[@]} -gt 0 && $exit_code -eq 0 ]] && echo "  ✓ Instalados: ${pkgs_to_install[*]}"
  [[ ${#skipped[@]}         -gt 0 ]] && echo "  ─ Ya tenías:  ${skipped[*]}"
  [[ $exit_code -ne 0 ]]             && echo "  ✗ Error al instalar" >&2

  return $exit_code
}
