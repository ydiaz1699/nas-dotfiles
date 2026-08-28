# docker/cli/lib/backup.sh
# Backup y restore de volumenes Docker con rotacion

BACKUP_DIR="${BACKUP_DIR:-/docker/backups}"
BACKUP_KEEP="${BACKUP_KEEP:-5}"  # Conservar ultimos N backups por servicio

svc_backup() {
  local svc="$1"
  local compose_file
  compose_file=$(svc_compose_file "$svc")
  local timestamp
  timestamp=$(date +%Y%m%d_%H%M%S)

  if [[ -z "$compose_file" ]]; then
    echo "  Servicio '$svc' no encontrado."
    return 1
  fi

  mkdir -p "$BACKUP_DIR"

  # ── Volumenes nombrados ──────────────────────────────────────────────────
  local volumes
  volumes=$(docker compose -f "$compose_file" config --volumes 2>/dev/null)

  # ── Bind mounts ──────────────────────────────────────────────────────────
  local bind_mounts
  bind_mounts=$(docker compose -f "$compose_file" config 2>/dev/null \
    | grep -A2 "volumes:" \
    | grep -oP '^\s+- \K/[^:]+' \
    | sort -u)

  if [[ -z "$volumes" && -z "$bind_mounts" ]]; then
    echo ""
    echo -e "  \033[1;33m'$svc' no tiene volumenes ni bind mounts\033[0m"
    echo ""
    return 0
  fi

  echo ""
  echo -e "\033[0;36m  Backup de '$svc' -> $BACKUP_DIR\033[0m"
  echo ""

  local ok=0 fail=0

  # ── Backup de volumenes nombrados ────────────────────────────────────────
  if [[ -n "$volumes" ]]; then
    local project
    project=$(basename "$(dirname "$compose_file")")

    while IFS= read -r vol; do
      [[ -z "$vol" ]] && continue

      local full_vol="${project}_${vol}"
      local out="${BACKUP_DIR}/${svc}_vol_${vol}_${timestamp}.tar.gz"

      printf "  %-40s" "vol: $full_vol"

      if docker volume inspect "$full_vol" &>/dev/null; then
        if docker run --rm \
            -v "${full_vol}:/data:ro" \
            -v "${BACKUP_DIR}:/backup" \
            alpine tar czf "/backup/$(basename "$out")" -C /data . 2>/dev/null; then
          local size
          size=$(du -sh "$out" 2>/dev/null | cut -f1)
          if _svc_backup_verify "$out"; then
            echo -e "\033[0;32m ok ($size) ✓\033[0m"
          else
            echo -e "\033[1;33m ok ($size) ⚠ verify failed\033[0m"
          fi
          ((ok++))
        else
          echo -e "\033[0;31m error al comprimir\033[0m"
          ((fail++))
        fi
      else
        # Intentar sin prefijo de proyecto
        if docker volume inspect "$vol" &>/dev/null; then
          if docker run --rm \
              -v "${vol}:/data:ro" \
              -v "${BACKUP_DIR}:/backup" \
              alpine tar czf "/backup/$(basename "$out")" -C /data . 2>/dev/null; then
            local size
            size=$(du -sh "$out" 2>/dev/null | cut -f1)
            if _svc_backup_verify "$out"; then
              echo -e "\033[0;32m ok ($size) ✓\033[0m"
            else
              echo -e "\033[1;33m ok ($size) ⚠ verify failed\033[0m"
            fi
            ((ok++))
          else
            echo -e "\033[0;31m error\033[0m"
            ((fail++))
          fi
        else
          echo -e "\033[1;33m volumen no existe\033[0m"
          ((fail++))
        fi
      fi
    done <<< "$volumes"
  fi

  # ── Backup de bind mounts ────────────────────────────────────────────────
  if [[ -n "$bind_mounts" ]]; then
    while IFS= read -r mount_path; do
      [[ -z "$mount_path" ]] && continue
      [[ ! -d "$mount_path" ]] && continue

      local mount_name
      mount_name=$(basename "$mount_path")
      local out="${BACKUP_DIR}/${svc}_bind_${mount_name}_${timestamp}.tar.gz"

      printf "  %-40s" "bind: $mount_path"

      if tar czf "$out" -C "$mount_path" . 2>/dev/null; then
        local size
        size=$(du -sh "$out" 2>/dev/null | cut -f1)
        if _svc_backup_verify "$out"; then
          echo -e "\033[0;32m ok ($size) ✓\033[0m"
        else
          echo -e "\033[1;33m ok ($size) ⚠ verify failed\033[0m"
        fi
        ((ok++))
      else
        echo -e "\033[0;31m error\033[0m"
        ((fail++))
      fi
    done <<< "$bind_mounts"
  fi

  # ── Rotacion: eliminar backups viejos ────────────────────────────────────
  _svc_backup_rotate "$svc"

  echo ""
  if [[ $fail -eq 0 ]]; then
    echo -e "  \033[0;32m  $ok archivos guardados en $BACKUP_DIR\033[0m"
  else
    echo -e "  \033[0;32m  $ok OK\033[0m  \033[0;31m  $fail con error\033[0m"
  fi
  echo ""
}

# ── Rotacion de backups ────────────────────────────────────────────────────
_svc_backup_rotate() {
  local svc="$1"
  local keep="${BACKUP_KEEP:-5}"

  # Contar backups de este servicio
  local count
  count=$(ls -1 "$BACKUP_DIR/${svc}_"*.tar.gz 2>/dev/null | wc -l)

  if [[ $count -gt $keep ]]; then
    local to_delete=$(( count - keep ))
    echo ""
    echo -e "  \033[0;37m  Rotacion: eliminando $to_delete backup(s) antiguo(s)\033[0m"
    ls -1t "$BACKUP_DIR/${svc}_"*.tar.gz | tail -n "$to_delete" | xargs rm -f
  fi
}

# ── Restore ────────────────────────────────────────────────────────────────
svc_restore() {
  local svc="$1"
  local archive="$2"

  # Si no se especifico archivo, mostrar disponibles
  if [[ -z "$archive" ]]; then
    echo ""
    echo -e "\033[0;34m  Backups disponibles para '$svc':\033[0m"
    echo ""

    local backups
    backups=$(ls -1t "$BACKUP_DIR/${svc}_"*.tar.gz 2>/dev/null)

    if [[ -z "$backups" ]]; then
      echo "  No hay backups para '$svc'"
      echo ""
      return 1
    fi

    local i=1
    while IFS= read -r f; do
      local size
      size=$(du -sh "$f" 2>/dev/null | cut -f1)
      local date_str
      date_str=$(stat -c %y "$f" 2>/dev/null | cut -d. -f1)
      printf "    %2d) %-50s %6s  %s\n" "$i" "$(basename "$f")" "$size" "$date_str"
      ((i++))
    done <<< "$backups"

    echo ""
    echo "  Uso: svc restore $svc <archivo.tar.gz>"
    echo ""

    # Selector interactivo si fzf esta disponible
    if command -v fzf &>/dev/null; then
      local selected
      selected=$(echo "$backups" | fzf --prompt="  Seleccionar backup > " --preview="du -sh {}")
      if [[ -n "$selected" ]]; then
        archive="$selected"
      else
        return 0
      fi
    else
      return 0
    fi
  fi

  # Validar archivo
  if [[ ! -f "$archive" && -f "$BACKUP_DIR/$archive" ]]; then
    archive="$BACKUP_DIR/$archive"
  fi

  if [[ ! -f "$archive" ]]; then
    echo "  Archivo no encontrado: $archive"
    return 1
  fi

  echo ""
  echo -e "\033[1;33m  ATENCION: Esto sobreescribira datos existentes.\033[0m"
  echo "  Archivo: $(basename "$archive")"
  echo "  Servicio: $svc"
  echo ""
  read -rp "  Continuar? [y/N] " confirm

  if [[ ! "$confirm" =~ ^[yY]$ ]]; then
    echo "  Cancelado."
    return 0
  fi

  # Determinar si es volumen o bind mount por el nombre
  local fname
  fname=$(basename "$archive")

  if [[ "$fname" == *"_vol_"* ]]; then
    # Extraer nombre del volumen
    local vol_name
    vol_name=$(echo "$fname" | sed "s/^${svc}_vol_//" | sed 's/_[0-9]\{8\}_[0-9]\{6\}\.tar\.gz$//')
    local project
    project=$(basename "$(dirname "$(svc_compose_file "$svc")")")
    local full_vol="${project}_${vol_name}"

    echo "  Restaurando volumen: $full_vol"

    # Detener servicio primero
    local compose_file
    compose_file=$(svc_compose_file "$svc")
    docker compose -f "$compose_file" stop 2>/dev/null

    # Restaurar
    docker run --rm \
      -v "${full_vol}:/data" \
      -v "$(dirname "$archive"):/backup:ro" \
      alpine sh -c "rm -rf /data/* && tar xzf /backup/$(basename "$archive") -C /data"

    echo -e "\033[0;32m  Volumen restaurado.\033[0m"
    echo ""
    read -rp "  Levantar $svc? [Y/n] " start_confirm
    if [[ ! "$start_confirm" =~ ^[nN]$ ]]; then
      docker compose -f "$compose_file" up -d
    fi

  elif [[ "$fname" == *"_bind_"* ]]; then
    # Extraer nombre del bind mount
    local mount_name
    mount_name=$(echo "$fname" | sed "s/^${svc}_bind_//" | sed 's/_[0-9]\{8\}_[0-9]\{6\}\.tar\.gz$//')

    echo "  Restaurando bind mount (nombre: $mount_name)"
    echo "  Necesitas especificar el path destino:"
    read -rp "  Path: " dest_path

    if [[ -z "$dest_path" || ! -d "$dest_path" ]]; then
      echo "  Path invalido."
      return 1
    fi

    tar xzf "$archive" -C "$dest_path"
    echo -e "\033[0;32m  Bind mount restaurado en $dest_path\033[0m"
  else
    echo "  No se pudo determinar el tipo de backup."
    echo "  Intenta extraer manualmente: tar xzf $archive -C /destino/"
    return 1
  fi

  echo ""
}



# ── svc backup-all — Backup de todos los servicios en secuencia ────────────
svc_backup_all() {
  local auto_yes=false

  # Parsear flags
  for arg in "$@"; do
    case "$arg" in
      -y|--yes) auto_yes=true ;;
    esac
  done

  local services
  services=$(svc_list)
  local count
  count=$(echo "$services" | wc -l | tr -d ' ')

  echo ""
  echo -e "\033[0;36m  ━━━ svc backup-all: Backup de $count servicios ━━━\033[0m"
  echo ""

  # Mostrar servicios a respaldar
  for svc in $services; do
    echo "    • $svc"
  done
  echo ""

  # Confirmación
  if ! $auto_yes; then
    read -rp "  ¿Iniciar backup de todos? [y/N] " confirm
    if [[ ! "$confirm" =~ ^[yY]$ ]]; then
      echo "  Cancelado."
      return 0
    fi
  fi

  echo ""

  local ok=0 fail=0 skip=0
  local start_time
  start_time=$(date +%s)
  local results=()

  for svc in $services; do
    local compose_file
    compose_file=$(svc_compose_file "$svc")

    if [[ -z "$compose_file" ]]; then
      results+=("⚠️  $svc: sin compose file")
      ((skip++))
      continue
    fi

    # Verificar si tiene volúmenes
    local volumes
    volumes=$(docker compose -f "$compose_file" config --volumes 2>/dev/null)
    local bind_mounts
    bind_mounts=$(docker compose -f "$compose_file" config 2>/dev/null \
      | grep -A2 "volumes:" \
      | grep -oP '^\s+- \K/[^:]+' \
      | sort -u)

    if [[ -z "$volumes" && -z "$bind_mounts" ]]; then
      results+=("⏭️  $svc: sin volúmenes (skip)")
      ((skip++))
      continue
    fi

    echo -e "\033[1;33m  ┌─ $svc\033[0m"
    if svc_backup "$svc" 2>/dev/null; then
      # Verificar último backup creado
      local last_backup
      last_backup=$(ls -1t "$BACKUP_DIR/${svc}_"*.tar.gz 2>/dev/null | head -1)
      if [[ -n "$last_backup" ]] && _svc_backup_verify "$last_backup"; then
        local size
        size=$(du -sh "$last_backup" 2>/dev/null | cut -f1)
        results+=("✅ $svc: OK ($size)")
        ((ok++))
      else
        results+=("⚠️  $svc: backup creado pero verificación falló")
        ((ok++))
      fi
    else
      results+=("🔴 $svc: ERROR")
      ((fail++))
    fi
    echo -e "  └─ done"
    echo ""
  done

  local end_time
  end_time=$(date +%s)
  local elapsed=$(( end_time - start_time ))

  # Resumen final
  echo ""
  echo "  ━━━ Resumen backup-all ━━━"
  echo ""
  for r in "${results[@]}"; do
    echo "    $r"
  done
  echo ""
  echo -e "  \033[0;32m✅ $ok OK\033[0m | \033[0;31m🔴 $fail errores\033[0m | ⏭️  $skip saltados"
  echo "  ⏱️  Tiempo total: ${elapsed}s"
  echo "  📂 Destino: $BACKUP_DIR"
  echo ""

  # Notificar via ntfy si está disponible
  if [[ $ok -gt 0 ]] && command -v curl &>/dev/null && [[ -n "${NTFY_URL:-}" ]]; then
    local notify_msg="${ok} servicios respaldados"
    [[ $fail -gt 0 ]] && notify_msg="${notify_msg}, ${fail} con error"
    if [[ -f "${NAS_DOTFILES:-/nas-dotfiles}/docker/cli/lib/notifications.sh" ]]; then
      source "${NAS_DOTFILES:-/nas-dotfiles}/docker/cli/lib/notifications.sh" 2>/dev/null
      ntfy_send "backups" "📦 backup-all completado" "$notify_msg (${elapsed}s)" "default" "package"
    fi
  fi
}

# ── Verificación post-backup (tar -tzf) ───────────────────────────────────
_svc_backup_verify() {
  local archive="$1"

  if [[ ! -f "$archive" ]]; then
    return 1
  fi

  # Verificar integridad del tar.gz (listar contenido sin extraer)
  if tar -tzf "$archive" >/dev/null 2>&1; then
    return 0
  else
    echo -e "    \033[0;31m⚠ Backup corrupto: $(basename "$archive")\033[0m"
    return 1
  fi
}

# ── svc logs-grep — buscar en logs de todos los servicios ──────────────────
svc_logs_grep() {
  local pattern="$1"

  if [[ -z "$pattern" ]]; then
    echo ""
    echo "  Uso: svc logs-grep <patrón>"
    echo ""
    echo "  Busca texto en los logs de todos los servicios Docker."
    echo "  Muestra las últimas 100 líneas que coinciden."
    echo ""
    echo "  Ejemplos:"
    echo "    svc logs-grep error"
    echo "    svc logs-grep 'connection refused'"
    echo "    svc logs-grep OOM"
    echo ""
    return 1
  fi

  echo ""
  echo -e "\033[0;34m  ━━━ svc logs-grep: buscando '$pattern' ━━━\033[0m"
  echo ""

  local found=0

  for svc in $(svc_list); do
    local f
    f=$(svc_compose_file "$svc")
    [[ -z "$f" ]] && continue

    # Solo buscar en servicios que están corriendo
    if ! docker compose -f "$f" ps -q 2>/dev/null | grep -q .; then
      continue
    fi

    local matches
    matches=$(docker compose -f "$f" logs --tail=500 2>/dev/null | grep -i "$pattern" 2>/dev/null | tail -5)

    if [[ -n "$matches" ]]; then
      local match_count
      match_count=$(docker compose -f "$f" logs --tail=500 2>/dev/null | grep -ic "$pattern" 2>/dev/null || echo "0")
      echo -e "  \033[1;33m── $svc ($match_count coincidencias) ──\033[0m"
      echo "$matches" | sed 's/^/    /'
      echo ""
      ((found++))
    fi
  done

  if [[ $found -eq 0 ]]; then
    echo "  No se encontró '$pattern' en los logs de ningún servicio."
  else
    echo -e "  ━━━ $found servicio(s) con coincidencias ━━━"
  fi
  echo ""
}



# ══════════════════════════════════════════════════════════════════════════════
# svc snapshot / svc rollback — Config liviana (compose+.env) antes de cambios
# ══════════════════════════════════════════════════════════════════════════════
# A diferencia de backup (volúmenes pesados), snapshot guarda SOLO la config:
#   compose.yml + .env → un tar.gz pequeño para revertir rápido
# Útil antes de editar compose, actualizar imagen, o cambiar variables.

SNAPSHOT_DIR="${SNAPSHOT_DIR:-/docker/backups/.snapshots}"

svc_snapshot() {
  local svc="$1"
  local compose_file
  compose_file=$(svc_compose_file "$svc")

  if [[ -z "$compose_file" ]]; then
    echo "  Servicio '$svc' no encontrado."
    return 1
  fi

  local svc_dir
  svc_dir=$(dirname "$compose_file")
  local timestamp
  timestamp=$(date +%Y%m%d_%H%M%S)

  # El snapshot puede contener .env; protegerlo durante la creación y dejar
  # también el archivo final con modo 600 aunque la umask del usuario sea laxa.
  local previous_umask
  previous_umask=$(umask)
  umask 077
  mkdir -p "$SNAPSHOT_DIR" || {
    umask "$previous_umask"
    echo "  No se pudo crear el directorio de snapshots."
    return 1
  }

  local out="${SNAPSHOT_DIR}/${svc}_${timestamp}.tar.gz"

  # Archivos a guardar: compose + .env + cualquier .yml en raíz
  local files_to_snap=()
  for f in "$svc_dir"/compose.yml "$svc_dir"/compose.yaml "$svc_dir"/docker-compose.yml \
           "$svc_dir"/.env "$svc_dir"/*.yml "$svc_dir"/*.yaml; do
    [[ -f "$f" ]] && files_to_snap+=("$f")
  done

  if [[ ${#files_to_snap[@]} -eq 0 ]]; then
    umask "$previous_umask"
    echo "  No hay archivos de config para '$svc'."
    return 1
  fi

  # Crear snapshot relativo al directorio del servicio.
  if ! tar czf "$out" -C "$svc_dir" \
      $(for f in "${files_to_snap[@]}"; do basename "$f"; done | sort -u) 2>/dev/null; then
    umask "$previous_umask"
    rm -f -- "$out"
    echo "  No se pudo crear el snapshot de '$svc'."
    return 1
  fi
  if ! chmod 600 "$out"; then
    umask "$previous_umask"
    rm -f -- "$out"
    echo "  No se pudieron proteger los permisos del snapshot."
    return 1
  fi
  umask "$previous_umask"

  local size
  size=$(du -sh "$out" 2>/dev/null | cut -f1)

  echo ""
  echo -e "  \033[0;32m📸 Snapshot de '$svc' guardado ($size)\033[0m"
  echo "     ${out}"
  echo ""

  # Rotación: conservar últimos 10 snapshots por servicio
  local count
  count=$(ls -1 "$SNAPSHOT_DIR/${svc}_"*.tar.gz 2>/dev/null | wc -l)
  if [[ $count -gt 10 ]]; then
    local to_delete=$(( count - 10 ))
    ls -1t "$SNAPSHOT_DIR/${svc}_"*.tar.gz | tail -n "$to_delete" | xargs rm -f
    echo -e "  \033[0;37m  Rotación: eliminados $to_delete snapshot(s) antiguos\033[0m"
  fi
}

svc_rollback() {
  local svc="$1"
  local compose_file
  compose_file=$(svc_compose_file "$svc")

  if [[ -z "$compose_file" ]]; then
    echo "  Servicio '$svc' no encontrado."
    return 1
  fi

  local svc_dir
  svc_dir=$(dirname "$compose_file")

  # Listar snapshots disponibles
  local snapshots
  snapshots=$(ls -1t "$SNAPSHOT_DIR/${svc}_"*.tar.gz 2>/dev/null)

  if [[ -z "$snapshots" ]]; then
    echo ""
    echo "  No hay snapshots para '$svc'."
    echo "  Crea uno con: svc snapshot $svc"
    echo ""
    return 1
  fi

  echo ""
  echo -e "\033[0;34m  Snapshots disponibles para '$svc':\033[0m"
  echo ""

  local i=1
  while IFS= read -r f; do
    local size
    size=$(du -sh "$f" 2>/dev/null | cut -f1)
    local date_str
    date_str=$(stat -c %y "$f" 2>/dev/null | cut -d. -f1)
    printf "    %2d) %-45s %5s  %s\n" "$i" "$(basename "$f")" "$size" "$date_str"
    ((i++))
  done <<< "$snapshots"
  echo ""

  local selected=""

  # Selector interactivo si fzf está disponible
  if command -v fzf &>/dev/null; then
    selected=$(echo "$snapshots" | fzf --prompt="  Seleccionar snapshot > " \
      --preview="tar -tzf {}" --height=15)
  else
    read -rp "  Número (o path): " choice
    if [[ "$choice" =~ ^[0-9]+$ ]]; then
      selected=$(echo "$snapshots" | sed -n "${choice}p")
    else
      selected="$choice"
    fi
  fi

  if [[ -z "$selected" ]]; then
    echo "  Cancelado."
    return 0
  fi

  if [[ ! -f "$selected" ]]; then
    echo "  Archivo no encontrado: $selected"
    return 1
  fi

  echo ""
  echo -e "\033[1;33m  ⚠️  Esto SOBREESCRIBIRÁ la config actual de '$svc'.\033[0m"
  echo "     Snapshot: $(basename "$selected")"
  echo "     Destino:  $svc_dir/"
  echo ""

  # Mostrar qué contiene el snapshot
  echo "  Contenido del snapshot:"
  tar -tzf "$selected" 2>/dev/null | sed 's/^/    /'
  echo ""

  read -rp "  ¿Restaurar? [y/N] " confirm
  if [[ ! "$confirm" =~ ^[yY]$ ]]; then
    echo "  Cancelado."
    return 0
  fi

  # Guardar un snapshot de seguridad antes del rollback
  echo ""
  echo -e "  \033[0;37m  Guardando snapshot de seguridad antes del rollback...\033[0m"
  svc_snapshot "$svc" 2>/dev/null

  # Restaurar
  tar xzf "$selected" -C "$svc_dir"

  echo ""
  echo -e "  \033[0;32m✅ Config restaurada a: $(basename "$selected")\033[0m"
  echo ""

  read -rp "  ¿Recrear contenedor con la config restaurada? [Y/n] " recreate_confirm
  if [[ ! "$recreate_confirm" =~ ^[nN]$ ]]; then
    echo ""
    docker compose -f "$compose_file" up -d --force-recreate
    echo ""
    echo -e "  \033[0;32m  Servicio recreado con config anterior.\033[0m"
  fi
  echo ""
}
