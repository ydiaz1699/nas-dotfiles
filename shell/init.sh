#!/usr/bin/env bash
# shell/init.sh — Loader único del shell framework
# Sourced por ~/.bashrc (tanto usuario como root)
#
# Requiere: export NAS_DOTFILES="$HOME/nas-dotfiles" en ~/.bashrc ANTES de este source

[[ -n "$_SHELL_INIT_LOADED" && -z "$_SHELL_RELOAD" ]] && return
_SHELL_INIT_LOADED=1
unset _SHELL_RELOAD

# ── Validar NAS_DOTFILES ──────────────────────────────────────────────────
if [[ -z "$NAS_DOTFILES" ]]; then
  echo "  ⚠  NAS_DOTFILES no definida. Agrega a ~/.bashrc:" >&2
  echo '     export NAS_DOTFILES="$HOME/nas-dotfiles"' >&2
  return 1
fi

if [[ ! -d "$NAS_DOTFILES/shell" ]]; then
  echo "  ⚠  $NAS_DOTFILES/shell no existe. Verifica NAS_DOTFILES." >&2
  return 1
fi

SHELL_DIR="$NAS_DOTFILES/shell"

# ── Cargar configuración del usuario ──────────────────────────────────────
# Generada por setup.py o install.sh en la primera instalación
_NAS_USER_CONF="$NAS_DOTFILES/.config/user.conf"
if [[ -f "$_NAS_USER_CONF" ]]; then
  # shellcheck disable=SC1090
  source "$_NAS_USER_CONF"
fi

# Valores por defecto si no hay config (compatibilidad)
: "${NAV_HOME:=$HOME}"
: "${NAV_VAR:=adm}"
: "${NAV_CMD:=adm}"

# ── path_add disponible antes de los módulos ──────────────────────────────
path_add() {
  case ":$PATH:" in
    *":$1:"*) ;;
    *) PATH="$1:$PATH" ;;
  esac
}

export -f path_add

# ── PATH base ─────────────────────────────────────────────────────────────
path_add "$NAS_DOTFILES/shell/scripts"
path_add "$HOME/.cargo/bin"
export PATH

# ── Variables base ─────────────────────────────────────────────────────────
# Variable de navegación del usuario (configurable)
export "$NAV_VAR=$NAV_HOME"
export dkco=/docker
export DOCKER_BASE="${DOCKER_BASE:-/docker}"

# ── Cargar .env global de Docker (SERVER_IP, TZ, etc.) ────────────────────
# Permite que Docker Compose interpole ${VAR} sin warnings
if [[ -f "$DOCKER_BASE/.env" ]]; then
  set -a
  source "$DOCKER_BASE/.env"
  set +a
fi

# ── CLI svc: dual bash/python ──────────────────────────────────────────────
# NAS_CLI=python → usa Python CLI (Rich + InquirerPy)
# NAS_CLI=bash   → usa Bash CLI (sin dependencias, default)
svc() {
    if [[ "${NAS_CLI:-bash}" == "python" ]]; then
        (cd "$NAS_DOTFILES" && python3 -m svc_py "$@")
    else
        "$NAS_DOTFILES/docker/cli/svc.sh" "$@"
    fi
}

# ── Alias del agente (ejecutable desde cualquier ruta) ─────────────────────
agent() {
  (cd "$NAS_DOTFILES" && python3 -m agent.nas_agent "$@")
}

# ── Cargar módulos en orden ────────────────────────────────────────────────
for _mod in \
  aliases \
  nav \
  docker \
  system \
  instal \
  pipins \
  git \
  completions \
  prompt
do
  _f="$SHELL_DIR/lib/${_mod}.sh"
  if [[ -f "$_f" ]]; then
    # shellcheck disable=SC1090
    source "$_f"
  else
    echo "  ⚠  shell: módulo '$_mod' no encontrado en $SHELL_DIR/lib/" >&2
  fi
done
unset _mod _f
