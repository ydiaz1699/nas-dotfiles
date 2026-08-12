# shell/lib/nav.sh

# ── up() — subir N niveles ─────────────────────────────────────────────────
up() {
  local n=${1:-1}
  [[ "$n" =~ ^[0-9]+$ ]] || { echo "uso: up [numero]"; return 1; }
  local p=""
  for ((i=0; i<n; i++)); do p+="../"; done
  cd -- "$p" || return
}

# ── _nav() — funcion generica de navegacion ───────────────────────────────
_nav() {
  local base="$1"
  shift

  if [[ $# -eq 0 ]]; then
    cd -- "$base"
    return
  fi

  if [[ "$1" == ".." ]]; then
    up "$2"
    return
  fi

  local dir="$base/$1"

  if [[ -d "$dir" ]]; then
    shift
    cd -- "$dir" || return
    [[ $# -gt 0 ]] && "$@"
  else
    local cmd="$1"
    shift
    if command -v "$cmd" >/dev/null 2>&1; then
      (cd -- "$base" && "$cmd" "$@")
    else
      printf "  '%s' no es carpeta ni comando\n" "$cmd"
    fi
  fi
}

# ── _nav_complete() — autocompletado generico ─────────────────────────────
_nav_complete() {
  local base="$1"
  local cur="${COMP_WORDS[COMP_CWORD]}"
  local dirs=()
  for d in "$base"/*/; do
    [[ -d "$d" ]] && dirs+=("$(basename "$d")")
  done
  COMPREPLY=($(compgen -W "$(printf '%s\n' "${dirs[@]}")" -- "$cur"))
}

# ── _nav_fzf() — fuzzy generico ───────────────────────────────────────────
_nav_fzf() {
  local base="$1"
  local prompt="$2"

  if ! command -v fzf >/dev/null 2>&1; then
    printf "  fzf no instalado: apt install fzf\n"
    return 1
  fi

  local target
  target=$(find "$base" -type d \
    -maxdepth 4 \
    -not -path '*/\.*' \
    -not -path '*/node_modules/*' \
    -not -path '*/__pycache__/*' \
    -not -path '*/.git/*' \
    2>/dev/null | fzf \
      --prompt="$prompt " \
      --preview="ls -lah {}" \
      --preview-window=right:40%:wrap)

  [[ -n "$target" ]] && cd -- "$target"
}

# ── Navegación home del usuario (configurable via .config/user.conf) ───────
# NAV_CMD / NAV_VAR / NAV_HOME se definen en init.sh desde user.conf
# Defaults: adm / aadm / $HOME

# Crear la función dinámicamente con el nombre configurado
eval "${NAV_CMD:-adm}() { _nav \"\${${NAV_VAR:-adm}}\" \"\$@\"; }"
eval "${NAV_CMD:-adm}f() { _nav_fzf \"\${${NAV_VAR:-adm}}\" \"${NAV_CMD:-adm}>\"; }"

eval "_${NAV_CMD:-adm}_completions() { _nav_complete \"\${${NAV_VAR:-adm}}\"; }"
eval "complete -F _${NAV_CMD:-adm}_completions ${NAV_CMD:-adm}"

# ── dk — /docker ──────────────────────────────────────────────────────────
dk()  { _nav "$dkco" "$@"; }
dkf() { _nav_fzf "$dkco" "dk>"; }

_dk_completions() { _nav_complete "$dkco"; }
complete -F _dk_completions dk

# ── nasfk — /nas-dotfiles (código del framework) ──────────────────────────
nasfk()  { _nav "$NAS_DOTFILES" "$@"; }
nasfkf() { _nav_fzf "$NAS_DOTFILES" "nasfk>"; }
_nasfk_completions() { _nav_complete "$NAS_DOTFILES"; }
complete -F _nasfk_completions nasfk
