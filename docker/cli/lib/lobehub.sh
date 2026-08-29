#!/usr/bin/env bash
# Operaciones seguras y repetibles para LobeHub.
# Esta librería se carga desde svc.sh y no debe ejecutarse directamente.

_lobe_usage() {
  cat <<'EOF'
Uso: svc lobehub <acción> [--confirm]

Acciones de solo lectura:
  preflight       Validar archivos, secretos, compose, red y almacenamiento
  verify          Validar contenedores, HTTP, Redis, PostgreSQL y privilegios
  status          Resumen de contenedores sin configuración sensible
  providers       Diagnosticar avisos de proveedores/QStash/marketplace

Acciones con cambios:
  repair-storage --confirm   Corregir UID/permisos de data/rustfs sin borrar datos
  reconcile-db --confirm     Sincronizar rol, base y extensiones de LobeHub
  backup-db                  Crear dump lógico de lobehub_db

Las acciones mutantes requieren --confirm. Nunca imprimen valores de secretos.
EOF
}

_lobe_compose_args() {
  LOBE_COMPOSE_ARGS=()
  [[ -f "$BASE/.env" ]] && LOBE_COMPOSE_ARGS+=(--env-file "$BASE/.env")
  [[ -f "$BASE/lobehub/.env" ]] && LOBE_COMPOSE_ARGS+=(--env-file "$BASE/lobehub/.env")
}

_lobe_compose() {
  local compose_file="$BASE/lobehub/compose.yml"
  _lobe_compose_args
  docker compose "${LOBE_COMPOSE_ARGS[@]}" -f "$compose_file" "${@:1}"
}

_lobe_env_value() {
  local file="$1" key="$2"
  [[ -f "$file" ]] || return 1
  awk -F= -v wanted="$key" '$1 == wanted {print substr($0, index($0, "=") + 1); exit}' "$file"
}

_lobe_context_check() {
  local missing=0
  local global_env="$BASE/.env"
  local compose_file="$BASE/lobehub/compose.yml"
  local service_env="$BASE/lobehub/.env"
  local datasql_env="$BASE/datasql/.env"

  [[ -r "$global_env" ]] || missing=1
  [[ -r "$compose_file" ]] || missing=1
  [[ -r "$service_env" ]] || missing=1
  [[ -r "$datasql_env" ]] || missing=1
  command -v docker >/dev/null 2>&1 || missing=1
  docker info >/dev/null 2>&1 || missing=1
  return "$missing"
}

_lobe_result() {
  local label="$1" state="$2" detail="$3"
  case "$state" in
    pass) printf '  ✅ %-30s %s\n' "$label" "$detail" ;;
    warn) printf '  ⚠️  %-30s %s\n' "$label" "$detail" ;;
    fail) printf '  ❌ %-30s %s\n' "$label" "$detail" ;;
  esac
}

_lobe_confirm() {
  local action="$1"
  for arg in "$@"; do
    [[ "$arg" == "--confirm" ]] && return 0
  done
  printf 'La acción %s modifica el NAS. Repite con --confirm.\n' "$action" >&2
  return 1
}

_lobe_secret_bytes() {
  local value="$1"
  [[ -n "$value" ]] || { echo 0; return 0; }
  # validate=True rechaza caracteres/padding inválidos sin escribir el secreto
  # a disco ni imprimir los bytes decodificados.
  printf '%s' "$value" | python3 -c '
import base64
import binascii
import sys
try:
    decoded = base64.b64decode(sys.stdin.buffer.read(), validate=True)
except (binascii.Error, ValueError):
    print(0)
else:
    print(len(decoded))
'
}

_lobe_preflight() {
  local fail=0 warn=0
  local service_dir="$BASE/lobehub"
  local env_file="$service_dir/.env"
  local compose_file="$service_dir/compose.yml"
  local bucket_file="$service_dir/bucket.config.json"
  local rustfs_dir="$service_dir/data/rustfs"

  echo 'LobeHub preflight (solo lectura)'

  if _lobe_context_check; then
    _lobe_result context pass 'contexto host y archivos legibles'
  else
    _lobe_result context fail 'el helper no puede acceder al runtime real'
    fail=$((fail + 1))
  fi

  if [[ -f "$compose_file" ]]; then _lobe_result compose pass 'compose.yml existe'; else _lobe_result compose fail 'falta compose.yml'; fail=$((fail + 1)); fi
  if [[ -f "$env_file" ]]; then _lobe_result env pass '.env existe'; else _lobe_result env fail 'falta .env'; fail=$((fail + 1)); fi
  if [[ -f "$bucket_file" ]]; then _lobe_result bucket pass 'bucket.config.json existe'; else _lobe_result bucket fail 'falta bucket.config.json'; fail=$((fail + 1)); fi

  if [[ -f "$env_file" ]]; then
    local mode
    mode=$(stat -c '%a' "$env_file" 2>/dev/null || echo unknown)
    if [[ "$mode" == 600 ]]; then _lobe_result env_mode pass 'modo 600'; else _lobe_result env_mode fail "modo $mode; aplicar chmod 600"; fail=$((fail + 1)); fi

    local key_bytes
    key_bytes=$(_lobe_secret_bytes "$(_lobe_env_value "$env_file" KEY_VAULTS_SECRET)")
    if [[ "$key_bytes" == 16 || "$key_bytes" == 24 || "$key_bytes" == 32 ]]; then
      _lobe_result vault_key pass "$key_bytes bytes decodificados"
    else
      _lobe_result vault_key fail "formato inválido ($key_bytes bytes decodificados)"; fail=$((fail + 1))
    fi
    for key in LOBE_DB_PASSWORD REDIS_PASSWORD AUTH_SECRET JWKS_KEY RUSTFS_SECRET_KEY AUTH_ALLOWED_EMAILS; do
      if [[ -n "$(_lobe_env_value "$env_file" "$key")" && "$(_lobe_env_value "$env_file" "$key")" != '__pega_aqui__' ]]; then
        _lobe_result "env:$key" pass configured
      else
        _lobe_result "env:$key" fail missing
        fail=$((fail + 1))
      fi
    done
  fi

  if [[ -d "$rustfs_dir" ]]; then
    local owner mode
    owner=$(stat -c '%u:%g' "$rustfs_dir" 2>/dev/null || echo unknown)
    mode=$(stat -c '%a' "$rustfs_dir" 2>/dev/null || echo unknown)
    if [[ "$owner" == '10001:10001' ]]; then _lobe_result rustfs_owner pass "$owner"; else _lobe_result rustfs_owner fail "$owner; requiere 10001:10001"; fail=$((fail + 1)); fi
    if [[ "$mode" != unknown ]]; then _lobe_result rustfs_dir pass "modo $mode"; else _lobe_result rustfs_dir fail 'no se pudo leer modo'; fail=$((fail + 1)); fi
  else
    _lobe_result rustfs_dir fail 'falta data/rustfs'; fail=$((fail + 1))
  fi

  if [[ -f "$compose_file" ]]; then
    if grep -q -- '--secret-key' "$compose_file"; then _lobe_result rustfs_arg fail '--secret-key sigue en compose'; fail=$((fail + 1)); else _lobe_result rustfs_arg pass 'secreto no va en command'; fi
    if grep -q 'REDIS_URL:.*REDIS_PASSWORD' "$compose_file"; then _lobe_result redis_url pass 'URL incluye autenticación'; else _lobe_result redis_url fail 'REDIS_URL no incluye autenticación'; fail=$((fail + 1)); fi
    if grep -q 'env_file:' "$compose_file" && grep -q '      - ../.env' "$compose_file"; then _lobe_result env_file pass 'global y local'; else _lobe_result env_file fail 'env_file incompleto'; fail=$((fail + 1)); fi
    if _lobe_compose config --quiet >/dev/null 2>&1; then _lobe_result compose_resolved pass 'compose resoluble'; else _lobe_result compose_resolved fail 'compose config falló'; fail=$((fail + 1)); fi
  fi

  if docker network inspect db_net >/dev/null 2>&1; then _lobe_result db_net pass 'red externa existe'; else _lobe_result db_net fail 'falta db_net'; fail=$((fail + 1)); fi
  if [[ -f "$BASE/datasql/compose.yml" && -f "$BASE/datasql/.env" ]]; then _lobe_result datasql pass 'DataSQL preparado'; else _lobe_result datasql fail 'faltan archivos DataSQL'; fail=$((fail + 1)); fi

  printf '\nResultado: %d fallos, %d avisos\n' "$fail" "$warn"
  ((fail == 0))
}

_lobe_sql_admin() {
  local sql="$1"
  local pg_password="$2" pg_user="$3" pg_db="$4"
  # La contraseña viaja por stdin y se convierte en PGPASSWORD dentro del
  # contenedor; nunca aparece en argv/ps del host.
  printf '%s\n%s\n' "$pg_password" "$sql" | docker exec -i \
    -e "PGUSER=$pg_user" -e "PGDATABASE=$pg_db" datapostgres \
    sh -c 'IFS= read -r pg_password || exit 1; export PGPASSWORD="$pg_password"; exec psql -X -v ON_ERROR_STOP=1 -At'
}

_lobe_redis_ping() {
  local redis_password="$1"
  # Igual que PostgreSQL: el secreto entra por stdin y no por REDISCLI_AUTH
  # en la línea de comandos del proceso del host.
  printf '%s\n' "$redis_password" | docker exec -i dataredis \
    sh -c 'IFS= read -r REDISCLI_AUTH || exit 1; export REDISCLI_AUTH; exec redis-cli PING'
}

_lobe_pg_dump() {
  local pg_password="$1" pg_user="$2" pg_db="$3"
  printf '%s\n' "$pg_password" | docker exec -i \
    -e "PGUSER=$pg_user" -e "PGDATABASE=$pg_db" datapostgres \
    sh -c 'IFS= read -r pg_password || exit 1; export PGPASSWORD="$pg_password"; exec pg_dump --format=plain --no-owner --no-privileges'
}

_lobe_verify() {
  local fail=0
  local env_file="$BASE/lobehub/.env"
  local data_env="$BASE/datasql/.env"
  local server_ip="${SERVER_IP:-$(_lobe_env_value "$BASE/.env" SERVER_IP)}"
  echo 'LobeHub verify (solo lectura)'

  if _lobe_context_check; then _lobe_result context pass 'contexto host y archivos legibles'; else _lobe_result context fail 'el helper no puede acceder al runtime real'; fail=$((fail + 1)); fi
  if _lobe_compose ps --status running --services 2>/dev/null | grep -qx lobehub; then _lobe_result container pass 'lobehub activo'; else _lobe_result container fail 'lobehub no está activo'; fail=$((fail + 1)); fi
  if _lobe_compose ps --status running --services 2>/dev/null | grep -qx rustfs; then _lobe_result rustfs pass 'RustFS activo'; else _lobe_result rustfs fail 'RustFS no está activo'; fail=$((fail + 1)); fi
  if _lobe_compose ps --status exited --services 2>/dev/null | grep -qx rustfs-init; then _lobe_result rustfs_init pass 'init terminó'; else _lobe_result rustfs_init warn 'init no aparece como exited'; fi

  if [[ -n "$server_ip" ]] && curl -fsS -o /dev/null "http://${server_ip}:3210" 2>/dev/null; then _lobe_result http pass 'HTTP 3210 responde'; else _lobe_result http fail 'HTTP 3210 no responde'; fail=$((fail + 1)); fi
  if [[ -n "$server_ip" ]] && curl -fsS -o /dev/null "http://${server_ip}:9000/health" 2>/dev/null; then _lobe_result s3 pass 'RustFS health responde'; else _lobe_result s3 fail 'RustFS health no responde'; fail=$((fail + 1)); fi

  local redis_password redis_result
  redis_password=$(_lobe_env_value "$data_env" REDIS_PASSWORD)
  if [[ -n "$redis_password" ]]; then
    redis_result=$(_lobe_redis_ping "$redis_password" 2>/dev/null || true)
    if [[ "$redis_result" == PONG ]]; then _lobe_result redis pass PONG; else _lobe_result redis fail 'autenticación o respuesta falló'; fail=$((fail + 1)); fi
  else
    _lobe_result redis fail 'no se encontró REDIS_PASSWORD de DataSQL'; fail=$((fail + 1))
  fi
  unset redis_password redis_result

  local pg_password pg_user ext_count role_flags
  pg_password=$(_lobe_env_value "$data_env" POSTGRES_PASSWORD)
  pg_user=$(_lobe_env_value "$data_env" POSTGRES_USER)
  if [[ -n "$pg_password" && -n "$pg_user" ]]; then
    ext_count=$(_lobe_sql_admin "SELECT count(*) FROM pg_extension WHERE extname IN ('vector','pg_search');" "$pg_password" "$pg_user" lobehub_db 2>/dev/null || echo 0)
    if [[ "$ext_count" == 2 ]]; then _lobe_result extensions pass 'vector y pg_search'; else _lobe_result extensions fail "se encontraron $ext_count de 2"; fail=$((fail + 1)); fi
    role_flags=$(_lobe_sql_admin "SELECT CASE WHEN rolcanlogin THEN 't' ELSE 'f' END || '|' || CASE WHEN rolsuper THEN 't' ELSE 'f' END || '|' || CASE WHEN rolcreaterole THEN 't' ELSE 'f' END || '|' || CASE WHEN rolcreatedb THEN 't' ELSE 'f' END || '|' || CASE WHEN rolreplication THEN 't' ELSE 'f' END || '|' || CASE WHEN rolbypassrls THEN 't' ELSE 'f' END FROM pg_roles WHERE rolname='lobehub_user';" "$pg_password" "$pg_user" lobehub_db 2>/dev/null || true)
    if [[ "$role_flags" == 't|f|f|f|f|f' ]]; then _lobe_result role pass 'lobehub_user login sin privilegios elevados'; else _lobe_result role fail 'atributos no cumplen mínimo privilegio'; fail=$((fail + 1)); fi
  else
    _lobe_result postgres fail 'faltan credenciales administrativas'; fail=$((fail + 1))
  fi
  unset pg_password pg_user ext_count role_flags

  local logs provider_count qstash_count marketplace_count
  logs=$(_lobe_compose logs --no-color --tail=300 lobehub 2>/dev/null || true)
  if grep -q 'database migration pass' <<< "$logs"; then _lobe_result migration pass 'migración completada'; else _lobe_result migration warn 'no se encontró confirmación reciente'; fi
  provider_count=$(grep -Ec 'InvalidProviderAPIKey|invalid.*provider.*key' <<< "$logs" || true)
  qstash_count=$(grep -Ec 'QSTASH_TOKEN not set|QStash token is required' <<< "$logs" || true)
  marketplace_count=$(grep -Ec 'Missing bearer token|Failed to fetch (skill|mcp) list' <<< "$logs" || true)
  if [[ "$provider_count" == 0 ]]; then _lobe_result providers pass 'sin claves inválidas recientes'; else _lobe_result providers warn "$provider_count avisos de proveedores"; fi
  if [[ "$qstash_count" == 0 ]]; then _lobe_result qstash pass 'sin avisos QStash'; else _lobe_result qstash warn 'QStASH_TOKEN opcional no configurado'; fi
  if [[ "$marketplace_count" == 0 ]]; then _lobe_result marketplace pass 'sin avisos marketplace'; else _lobe_result marketplace warn 'marketplace requiere bearer token/sesión'; fi

  printf '\nResultado: %d fallos\n' "$fail"
  ((fail == 0))
}

_lobe_status() {
  echo 'LobeHub status'
  _lobe_compose ps
}

_lobe_providers() {
  local logs
  logs=$(_lobe_compose logs --no-color --tail=300 lobehub 2>/dev/null || true)
  echo 'LobeHub provider diagnostics (sin mostrar logs completos)'
  if grep -Eq 'InvalidProviderAPIKey|invalid.*provider.*key' <<< "$logs"; then
    _lobe_result providers warn 'hay claves OpenAI/DeepSeek u otro proveedor inválidas; corregir desde la UI'
  else
    _lobe_result providers pass 'no se detectaron claves inválidas recientes'
  fi
  if grep -Eq 'QSTASH_TOKEN not set|QStash token is required' <<< "$logs"; then
    _lobe_result qstash warn 'QStash es opcional; configurar solo para workflows programados'
  else
    _lobe_result qstash pass 'sin aviso QStash'
  fi
  if grep -Eq 'Missing bearer token|Failed to fetch (skill|mcp) list' <<< "$logs"; then
    _lobe_result marketplace warn 'marketplace requiere sesión/token; no bloquea el servidor'
  else
    _lobe_result marketplace pass 'sin aviso marketplace'
  fi
}

_lobe_restore_running() {
  local service="$1"
  _lobe_compose start "$service" >/dev/null 2>&1 || return 1
  _lobe_compose ps --status running --services 2>/dev/null | grep -qx "$service"
}

_lobe_repair_storage() {
  _lobe_confirm repair-storage "$@" || return 1
  local dir="$BASE/lobehub/data/rustfs"
  [[ -d "$dir" ]] || { echo "Falta $dir" >&2; return 1; }
  if declare -F svc_snapshot >/dev/null 2>&1; then svc_snapshot lobehub || return 1; fi

  local lobehub_running=0 rustfs_running=0 stop_status=0 mutation_status=0
  if _lobe_compose ps --status running --services 2>/dev/null | grep -qx lobehub; then
    lobehub_running=1
  fi
  if _lobe_compose ps --status running --services 2>/dev/null | grep -qx rustfs; then
    rustfs_running=1
  fi

  # Evitar que RustFS escriba mientras se corrige el propietario del bind mount.
  _lobe_compose stop lobehub rustfs >/dev/null 2>&1 || stop_status=$?
  if (( stop_status != 0 )); then
    # El stop puede haber sido parcial; restaurar y verificar cada contenedor
    # que estaba activo antes de tocar el almacenamiento.
    local restore_status=0
    if (( lobehub_running )); then _lobe_restore_running lobehub || restore_status=1; fi
    if (( rustfs_running )); then _lobe_restore_running rustfs || restore_status=1; fi
    if (( restore_status != 0 )); then
      echo 'No se pudo detener completamente ni restaurar el estado previo de LobeHub/RustFS.' >&2
      return 1
    fi
    echo 'No se pudo detener completamente LobeHub/RustFS; no se cambiaron permisos.' >&2
    return "$stop_status"
  fi

  chown -R 10001:10001 "$dir" || mutation_status=1
  chmod -R u+rwX,go-rX "$dir" || mutation_status=1

  # Dejar el runtime como estaba antes y comprobarlo: el comando no debe
  # convertir una reparación de permisos en una parada permanente.
  if (( lobehub_running )); then _lobe_restore_running lobehub || mutation_status=1; fi
  if (( rustfs_running )); then _lobe_restore_running rustfs || mutation_status=1; fi

  if (( mutation_status != 0 )); then
    echo 'Falló la corrección o la restauración del estado de LobeHub/RustFS.' >&2
    return "$mutation_status"
  fi
  _lobe_result storage pass 'UID 10001 y permisos corregidos; datos conservados'
}

_lobe_reconcile_db() {
  _lobe_confirm reconcile-db "$@" || return 1
  local env_file="$BASE/lobehub/.env" data_env="$BASE/datasql/.env"
  local pg_password pg_user pg_admin_db app_password
  pg_password=$(_lobe_env_value "$data_env" POSTGRES_PASSWORD)
  pg_user=$(_lobe_env_value "$data_env" POSTGRES_USER)
  pg_admin_db=$(_lobe_env_value "$data_env" POSTGRES_DB)
  app_password=$(_lobe_env_value "$env_file" LOBE_DB_PASSWORD)
  if [[ -z "$pg_password" || -z "$pg_user" || -z "$pg_admin_db" ||
        -z "$app_password" || "$app_password" == '__pega_aqui__' ]]; then
    echo 'Faltan credenciales locales; no se modifica PostgreSQL.' >&2
    return 1
  fi
  [[ "$app_password" =~ ^[0-9a-fA-F]+$ ]] || { echo 'LOBE_DB_PASSWORD debe ser hexadecimal.' >&2; return 1; }

  local role_exists
  role_exists=$(_lobe_sql_admin "SELECT 1 FROM pg_roles WHERE rolname='lobehub_user';" "$pg_password" "$pg_user" "$pg_admin_db" 2>/dev/null || true)
  if [[ "$role_exists" == 1 ]]; then
    _lobe_sql_admin "ALTER ROLE lobehub_user LOGIN PASSWORD '$app_password'; ALTER ROLE lobehub_user NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS;" "$pg_password" "$pg_user" "$pg_admin_db" >/dev/null
  else
    _lobe_sql_admin "CREATE ROLE lobehub_user LOGIN PASSWORD '$app_password'; ALTER ROLE lobehub_user NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS;" "$pg_password" "$pg_user" "$pg_admin_db" >/dev/null
  fi

  local db_exists db_owner
  db_exists=$(_lobe_sql_admin "SELECT 1 FROM pg_database WHERE datname='lobehub_db';" "$pg_password" "$pg_user" "$pg_admin_db" 2>/dev/null || true)
  if [[ "$db_exists" != 1 ]]; then
    _lobe_sql_admin 'CREATE DATABASE lobehub_db OWNER lobehub_user;' "$pg_password" "$pg_user" "$pg_admin_db" >/dev/null
  else
    db_owner=$(_lobe_sql_admin "SELECT pg_get_userbyid(datdba) FROM pg_database WHERE datname='lobehub_db';" "$pg_password" "$pg_user" "$pg_admin_db" 2>/dev/null || true)
    if [[ "$db_owner" != 'lobehub_user' ]]; then
      _lobe_sql_admin 'ALTER DATABASE lobehub_db OWNER TO lobehub_user;' "$pg_password" "$pg_user" "$pg_admin_db" >/dev/null
    fi
  fi

  _lobe_sql_admin "CREATE EXTENSION IF NOT EXISTS vector; CREATE EXTENSION IF NOT EXISTS pg_search;" "$pg_password" "$pg_user" lobehub_db >/dev/null
  _lobe_result database pass 'rol/base/extensiones reconciliados; secretos no impresos'
  unset pg_password pg_user pg_admin_db app_password db_exists db_owner role_exists
}

_lobe_backup_db() {
  local env_file="$BASE/lobehub/.env"
  local app_password output temporary timestamp suffix
  app_password=$(_lobe_env_value "$env_file" LOBE_DB_PASSWORD)
  [[ -n "$app_password" && "$app_password" != '__pega_aqui__' ]] || { echo 'Falta LOBE_DB_PASSWORD.' >&2; return 1; }

  local backup_dir="$BASE/datasql/data/postgres/backups"
  mkdir -p "$backup_dir"
  timestamp=$(date +%Y%m%d_%H%M%S)
  # umask 077 + mktemp evita exposición durante la escritura y colisiones en
  # ejecuciones simultáneas o dentro del mismo segundo.
  local previous_umask
  previous_umask=$(umask)
  umask 077
  temporary=$(mktemp "$backup_dir/.lobehub_db_${timestamp}.XXXXXX") || {
    umask "$previous_umask"
    unset app_password output temporary timestamp suffix previous_umask backup_dir env_file
    echo 'No se pudo crear el archivo temporal del dump.' >&2
    return 1
  }
  umask "$previous_umask"

  suffix="${temporary##*.}"
  output="$backup_dir/lobehub_db_${timestamp}_${suffix}.sql"
  if ! _lobe_pg_dump "$app_password" lobehub_user lobehub_db > "$temporary"; then
    rm -f -- "$temporary"
    unset app_password output temporary timestamp suffix previous_umask backup_dir env_file
    echo 'Falló el dump; se eliminó el archivo temporal.' >&2
    return 1
  fi
  if [[ ! -s "$temporary" || -e "$output" ]]; then
    rm -f -- "$temporary"
    unset app_password output temporary timestamp suffix previous_umask backup_dir env_file
    echo 'El dump está vacío o el destino ya existe.' >&2
    return 1
  fi
  # Publicar mediante hard-link: la creación del destino es atómica y falla si
  # otra ejecución ya lo creó; nunca se sobrescribe un dump existente.
  if ! chmod 600 "$temporary" || ! ln -- "$temporary" "$output"; then
    rm -f -- "$temporary"
    unset app_password output temporary timestamp suffix previous_umask backup_dir env_file
    echo 'No se pudo proteger o publicar el dump sin sobrescribir otro.' >&2
    return 1
  fi
  if ! rm -f -- "$temporary"; then
    unset app_password output temporary timestamp suffix previous_umask backup_dir env_file
    echo "Dump publicado, pero no se pudo retirar el temporal: $output" >&2
    return 1
  fi
  printf 'Dump lógico creado: %s\n' "$output"
  unset app_password output temporary timestamp suffix previous_umask backup_dir env_file
}

svc_lobehub() {
  local action="${1:-help}"
  shift || true
  case "$action" in
    help|-h|--help) _lobe_usage ;;
    preflight) _lobe_preflight "$@" ;;
    verify) _lobe_verify "$@" ;;
    status) _lobe_status "$@" ;;
    providers|diagnose) _lobe_providers "$@" ;;
    repair-storage) _lobe_repair_storage "$@" ;;
    reconcile-db) _lobe_reconcile_db "$@" ;;
    backup-db) _lobe_backup_db "$@" ;;
    *) echo "Acción LobeHub desconocida: $action" >&2; _lobe_usage >&2; return 2 ;;
  esac
}
