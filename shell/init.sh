#!/usr/bin/env bash
# shell/init.sh — Loader único del shell framework
# Sourced por ~/.bashrc (tanto aadm como root)
#
# Requiere: export NAS_DOTFILES="$HOME/nas-dotfiles" en ~/.bashrc ANTES de este source

[[ -n "$_SHELL_INIT_LOADED" ]] && return
_SHELL_INIT_LOADED=1

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

# ── path_add disponible antes de los módulos ──────────────────────────────
path_add() {
  case ":$PATH:" in
    *":$1:"*) ;;
    *) PATH="$1:$PATH" ;;
  esac
}

export -f path_add

# ── PATH base ─────────────────────────────────────────────────────────────
path_add "$HOME/scripts"
path_add "$HOME/.cargo/bin"
export PATH

# ── Variables base ─────────────────────────────────────────────────────────
export aadm="$HOME"
export dkco=/docker
export DOCKER_BASE=/docker

# ── Alias de svc (evita symlink en /usr/local/bin) ─────────────────────────
alias svc="$NAS_DOTFILES/docker/cli/svc.sh"

# ── Alias del agente (ejecutable desde cualquier ruta) ─────────────────────
agent() {
  (cd "$NAS_DOTFILES" && python3 -m agent.nas_agent "$*")
}

# ── Cargar módulos en orden ────────────────────────────────────────────────
for _mod in \
  aliases \
  nav \
  docker \
  system \
  instal \
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
