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
# Excluye secrets.yaml, .env y archivos ocultos para no volcar credenciales;
# usa FORCE=1 para incluirlos (FORCE=1 batr).
batr() {
  local dir="${1:-.}"
  local ext="${2:-}"
  local -a find_args=("$dir" -type f)
  if [ -n "$ext" ]; then
    find_args+=(-name "*.${ext}")
  fi
  if [ "${FORCE:-0}" != "1" ]; then
    find_args+=(! -name 'secrets.yaml' ! -name '.env' ! -name '.env.*' ! -path '*/.*')
  fi
  find "${find_args[@]}" -exec batcat --style=header,grid --paging=never {} +
}

# ── Nano con autoindent ───────────────────────────────────────────────────
alias nano='nano -i'
