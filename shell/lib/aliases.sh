# shell/lib/aliases.sh

# ── Navegacion ────────────────────────────────────────────────────────────
alias ..='cd ..'
alias ...='cd ../..'
alias ....='cd ../../..'
alias ~='cd ~'

# ── Listado (eza) ─────────────────────────────────────────────────────────
alias ls='eza'
alias ll='eza -lah'
alias la='eza -a'
alias lt='eza -lah --sort=modified'
alias lsd='eza -lD'

# ── Sistema ───────────────────────────────────────────────────────────────
alias cls='clear'
alias h='history'
alias ports='ss -tulnp'
reload() {
  _SHELL_RELOAD=1
  source ~/.bashrc
  echo "  ✓ bashrc recargado"
}
alias myip='curl -s https://ifconfig.me && echo'

# ── Docker ────────────────────────────────────────────────────────────────
alias dps='docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"'
alias dpa='docker ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"'
alias dim='docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"'
alias dnet='docker network ls'
alias dvol='docker volume ls'
alias dprune='docker system prune -f && docker volume prune -f'

# ── Archivos (TTY-safe: interactivo solo en terminal) ─────────────────────
# rm, cp, mv con -i solo si hay terminal interactiva
# En pipes/scripts se comportan normal sin preguntar
rm() {
  if [[ -t 0 && -t 1 ]]; then
    command rm -iv "$@"
  else
    command rm "$@"
  fi
}

cp() {
  if [[ -t 0 && -t 1 ]]; then
    command cp -iv "$@"
  else
    command cp "$@"
  fi
}

mv() {
  if [[ -t 0 && -t 1 ]]; then
    command mv -iv "$@"
  else
    command mv "$@"
  fi
}

alias mkdir='mkdir -pv'
alias df='df -h'
alias dus='du -sh'       # 'dus' para summary, 'du' queda libre para uso normal
alias free='free -h'

# ── Grep con color ────────────────────────────────────────────────────────
alias grep='grep --color=auto'
alias egrep='egrep --color=auto'
alias fgrep='fgrep --color=auto'

# ── Bat (batcat con estilo bonito) ────────────────────────────────────────
alias bat='batcat --style=header,grid --paging=never'

# ── Bat recursivo: ver el contenido de TODOS los archivos de una carpeta ──
# Uso:
#   batr                 → todos los archivos bajo el directorio actual
#   batr common          → todos los archivos bajo ./common
#   batr . yaml          → solo archivos *.yaml bajo el directorio actual
# PODA (no desciende) carpetas de build/caché/VCS pesadas: .esphome, .pioenvs,
# .piolibdeps, .git, node_modules, __pycache__, .cache, .venv — así no dispara
# la CPU en configs con miles de archivos generados (ej. ESPHome).
# Excluye secrets.yaml, .env y ocultos de la salida; FORCE=1 los incluye.
#
# Carpetas podadas configurables SIN tocar el código (export en ~/.bashrc):
#   BATR_PRUNE_EXTRA="dist out"   → AÑADE dist y out a la lista por defecto
#   BATR_PRUNE="target bin"       → REEMPLAZA la lista entera por esas
# (los nombres se separan por espacios; son nombres de carpeta, no rutas)
batr() {
  local dir="${1:-.}"
  local ext="${2:-}"
  # Lista por defecto de carpetas que NO se recorren (prune): evita el recorrido
  # costoso, no solo filtra la salida.
  local -a prune_names=(.esphome .pioenvs .piolibdeps .git node_modules
                        __pycache__ .cache .venv .mypy_cache .pytest_cache)
  # Override total con BATR_PRUNE, o añadir con BATR_PRUNE_EXTRA (word-split a propósito).
  if [ -n "${BATR_PRUNE:-}" ]; then
    prune_names=(${BATR_PRUNE})
  elif [ -n "${BATR_PRUNE_EXTRA:-}" ]; then
    prune_names+=(${BATR_PRUNE_EXTRA})
  fi
  local -a match=(-type f)
  [ -n "$ext" ] && match+=(-name "*.${ext}")
  if [ "${FORCE:-0}" != "1" ]; then
    match+=(! -name 'secrets.yaml' ! -name '.env' ! -name '.env.*' ! -path '*/.*')
  fi

  # Si no quedó ninguna carpeta a podar (BATR_PRUNE vacío), find sin la rama prune.
  if [ "${#prune_names[@]}" -eq 0 ]; then
    find "$dir" "${match[@]}" -exec batcat --style=header,grid --paging=never {} +
    return
  fi

  local -a prune=()
  local n
  for n in "${prune_names[@]}"; do
    prune+=(-name "$n" -o)
  done
  unset 'prune[${#prune[@]}-1]'   # quitar el -o sobrante del final

  # Estructura: \( <prune> \) -prune -o \( <match> -exec bat \)
  find "$dir" \( "${prune[@]}" \) -prune -o \
    \( "${match[@]}" -exec batcat --style=header,grid --paging=never {} + \)
}

# ── Nano con autoindent ───────────────────────────────────────────────────
alias nano='nano -i'
