# shell/lib/completions.sh
# Completions adicionales

# ── instal — completa con paquetes disponibles ─────────────────────────────
_instal_complete() {
  local cur="${COMP_WORDS[COMP_CWORD]}"

  # Solo completar si el usuario ya escribio al menos 2 caracteres
  if [[ ${#cur} -lt 2 ]]; then
    COMPREPLY=()
    return
  fi

  # Usar apt-cache para buscar paquetes que empiecen con el texto actual
  COMPREPLY=($(apt-cache pkgnames "$cur" 2>/dev/null | head -20))
}

complete -F _instal_complete instal

# ── logs — completa con nombres de logs conocidos ──────────────────────────
_logs_complete() {
  local cur="${COMP_WORDS[COMP_CWORD]}"
  local prev="${COMP_WORDS[COMP_CWORD-1]}"

  # Flags
  if [[ "$cur" == -* ]]; then
    COMPREPLY=($(compgen -W "-f --follow" -- "$cur"))
    return
  fi

  # Logs conocidos + archivos en /var/log
  local known="syslog auth kern"
  local files=""
  if [[ -d /var/log ]]; then
    files=$(ls /var/log/*.log 2>/dev/null | xargs -I{} basename {} .log)
  fi

  COMPREPLY=($(compgen -W "$known $files" -- "$cur"))
}

complete -F _logs_complete logs

# ── nas — subcomandos si se extiende en el futuro ──────────────────────────
# Por ahora nas no tiene subcomandos, pero se puede agregar:
# _nas_complete() {
#   local cur="${COMP_WORDS[COMP_CWORD]}"
#   COMPREPLY=($(compgen -W "disk net docker temp" -- "$cur"))
# }
# complete -F _nas_complete nas
