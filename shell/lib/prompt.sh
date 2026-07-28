# shell/lib/prompt.sh
#
# Prompt resultante (ejemplo):
#   root@Nas /docker/cli 4↑ 71% #
#   aadm@Nas ~/shell (main*) 0↑ 71% $
#
# 4↑  = contenedores docker corriendo (cached 5s)
# 71% = uso del disco raiz (cached 5s)
# (main*) = rama git + dirty flag

# ── Cache con TTL para evitar latencia ─────────────────────────────────────
# Docker count: se refresca cada 5 segundos como maximo
_prompt_cache_docker() {
  local now=$SECONDS
  if (( now - ${_PROMPT_DK_TS:-0} >= 5 )); then
    _PROMPT_DK_N=$(docker ps -q 2>/dev/null | wc -l | tr -d ' ')
    _PROMPT_DK_TS=$now
  fi
}

# Disk usage: se refresca cada 10 segundos
_prompt_cache_disk() {
  local now=$SECONDS
  if (( now - ${_PROMPT_DISK_TS:-0} >= 10 )); then
    _PROMPT_DISK_PCT=$(df / --output=pcent 2>/dev/null | tail -1 | tr -d ' %')
    _PROMPT_DISK_TS=$now
  fi
}

# ── Git branch + dirty ────────────────────────────────────────────────────
_prompt_git() {
  local branch
  branch=$(git symbolic-ref --short HEAD 2>/dev/null || git rev-parse --short HEAD 2>/dev/null)
  [[ -z "$branch" ]] && return

  local dirty=""
  if ! git diff --quiet 2>/dev/null || ! git diff --cached --quiet 2>/dev/null; then
    dirty="*"
  fi

  echo -n " \033[0;35m(${branch}${dirty})\033[0m"
}

# ── _build_prompt() — se llama en PROMPT_COMMAND ─────────────────────────
_build_prompt() {
  local exit_code=$?

  # Refrescar caches
  _prompt_cache_docker
  _prompt_cache_disk

  local docker_info="${_PROMPT_DK_N:-0}"
  local disk_pct="${_PROMPT_DISK_PCT:-0}"

  # color docker
  local dc_color='\033[0;32m'
  [[ "$docker_info" -eq 0 ]] && dc_color='\033[0;37m'

  # color disco
  local dk_color='\033[0;32m'
  [[ "$disk_pct" -ge 90 ]] && dk_color='\033[0;31m'
  [[ "$disk_pct" -ge 75 && "$disk_pct" -lt 90 ]] && dk_color='\033[1;33m'

  # color del simbolo final segun exit code
  local sym_color='\033[0;32m'
  [[ $exit_code -ne 0 ]] && sym_color='\033[0;31m'

  # simbolo segun usuario
  local sym='$'
  [[ "$EUID" -eq 0 ]] && sym='#'

  # color del nombre de usuario
  local user_color='\033[0;34m'
  [[ "$EUID" -eq 0 ]] && user_color='\033[0;31m'

  # git info (solo si estamos en un repo)
  local git_info=""
  git_info=$(_prompt_git)

  PS1="\[${user_color}\]\u\[\033[0m\]@\[\033[0;36m\]\h\[\033[0m\] \[\033[1m\]\w\[\033[0m\]"
  PS1+="${git_info}"
  PS1+=" \[${dc_color}\]${docker_info}↑\[\033[0m\]"
  PS1+=" \[${dk_color}\]${disk_pct}%\[\033[0m\]"
  PS1+=" \[${sym_color}\]${sym}\[\033[0m\] "
}

PROMPT_COMMAND='_build_prompt'
