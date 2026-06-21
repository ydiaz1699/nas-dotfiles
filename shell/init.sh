#!/usr/bin/env bash
# /home/aadm/shell/init.sh
# Loader unico — sourced por aadm y root

[[ -n "$SHELL_INIT_LOADED" ]] && return
export SHELL_INIT_LOADED=1

SHELL_DIR="/home/aadm/shell"

# ── path_add disponible antes de los modulos ──────────────────────────────
path_add() {
  case ":$PATH:" in
    *":$1:"*) ;;
    *) PATH="$1:$PATH" ;;
  esac
}

export -f path_add

# ── PATH base ─────────────────────────────────────────────────────────────
path_add "/home/aadm/scripts"
path_add "/home/aadm/.cargo/bin"
path_add "/docker/cli"
export PATH

# ── Variables base ─────────────────────────────────────────────────────────
export aadm=/home/aadm
export dkco=/docker

# ── Cargar modulos en orden ────────────────────────────────────────────────
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
    echo "  ⚠  shell: modulo '$_mod' no encontrado en $SHELL_DIR/lib/" >&2
  fi
done
unset _mod _f
