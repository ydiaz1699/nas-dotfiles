# /home/aadm/shell/lib/aliases.sh

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
alias reload='source ~/.bashrc && echo "  ✓ bashrc recargado"'
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

# ── Nano con autoindent ───────────────────────────────────────────────────
alias nano='nano -i'
