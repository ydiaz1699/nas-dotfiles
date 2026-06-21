# /home/aadm/shell/lib/docker.sh
# Autocompletado de svc

# ── Comandos globales (no necesitan servicio) ──────────────────────────────
_SVC_GLOBAL_CMDS="lista health update-all menu port-map size net watch create --help -h"

# ── Comandos que requieren un servicio ─────────────────────────────────────
_SVC_SERVICE_CMDS="
up down start stop restart kill pause unpause
logs ps stats top exec run
pull build images rm config
cp events port volumes scale wait
update backup restore depends open env
"

_svc_services() {
  find /docker -mindepth 2 -maxdepth 2 \
    \( -name "docker-compose.yml" -o -name "docker-compose.yaml" \
       -o -name "compose.yml"     -o -name "compose.yaml" \) \
    2>/dev/null \
    | awk -F/ '{print $(NF-1)}' | sort -u
}

_svc_complete() {
  local cur="${COMP_WORDS[COMP_CWORD]}"
  local cmd="${COMP_WORDS[1]}"

  # svc <TAB> → todos los comandos
  if [[ $COMP_CWORD -eq 1 ]]; then
    COMPREPLY=($(compgen -W "$_SVC_GLOBAL_CMDS $_SVC_SERVICE_CMDS" -- "$cur"))
    return
  fi

  # svc <cmd_global> <TAB> → nada (no necesitan servicio)
  for gc in $_SVC_GLOBAL_CMDS; do
    if [[ "$cmd" == "$gc" ]]; then
      COMPREPLY=()
      return
    fi
  done

  # svc <cmd_servicio> <TAB> → lista servicios
  if [[ $COMP_CWORD -eq 2 ]]; then
    local svcs
    svcs=$(_svc_services)
    COMPREPLY=($(compgen -W "$svcs" -- "$cur"))
    return
  fi

  COMPREPLY=()
}

complete -F _svc_complete svc
