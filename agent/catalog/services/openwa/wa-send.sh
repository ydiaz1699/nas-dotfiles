#!/usr/bin/env bash
# wa-send — enviar un mensaje de WhatsApp por la API de OpenWA desde la terminal.
#
# Despliegue en el NAS: copiar a $dkco/openwa/wa-send.sh y dar permiso de
# ejecución. Uso:
#
#   ./wa-send.sh <sesion> <numero> <mensaje...>
#   ./wa-send.sh prueba 34600111222 "Hola desde el NAS"
#
#   <sesion>  = el NAME de la sesión (no el UUID; el script resuelve el id solo)
#   <numero>  = número internacional SIN '+', sin espacios ni guiones
#               (se le añade @c.us automáticamente si no trae sufijo)
#   <mensaje> = el resto de argumentos se unen como el texto
#
# Notas:
# - Lee API_MASTER_KEY desde $dkco/openwa/.env SIN imprimirla y hace unset al
#   terminar. No usa `source .env`.
# - La API de OpenWA usa el id (UUID) de la sesión en las URLs, no el name;
#   por eso el script traduce name -> id con GET /api/sessions.
# - Requiere que la sesión esté 'ready' y con el motor activo.

set -euo pipefail

OPENWA_URL="${OPENWA_URL:-http://127.0.0.1:2785}"
ENV_FILE="${OPENWA_ENV_FILE:-${dkco:-/docker}/openwa/.env}"

die() { printf 'wa-send: %s\n' "$1" >&2; exit 1; }

# --- Argumentos ---
[[ $# -ge 3 ]] || die "uso: wa-send <sesion> <numero> <mensaje...>"
SESSION_NAME="$1"; shift
NUMBER="$1"; shift
TEXT="$*"

# chatId: si el número no trae sufijo @..., asumir contacto individual @c.us
case "$NUMBER" in
  *@*) CHAT_ID="$NUMBER" ;;
  *)   CHAT_ID="${NUMBER}@c.us" ;;
esac

# --- Dependencias ---
command -v curl   >/dev/null 2>&1 || die "falta 'curl'"
command -v python3 >/dev/null 2>&1 || die "falta 'python3'"
[[ -f "$ENV_FILE" ]] || die "no existe el .env: $ENV_FILE"

# --- Leer la API key sin imprimirla ---
API_KEY="$(grep '^API_MASTER_KEY=' "$ENV_FILE" | cut -d= -f2-)"
[[ -n "$API_KEY" ]] || die "API_MASTER_KEY vacía en $ENV_FILE"

cleanup() { unset API_KEY SID; }
trap cleanup EXIT

# --- Resolver el id (UUID) a partir del name ---
SID="$(curl -fsS "$OPENWA_URL/api/sessions" -H "X-API-Key: $API_KEY" \
  | python3 -c "import sys,json
name='$SESSION_NAME'
data=json.load(sys.stdin)
m=[s for s in data if s.get('name')==name]
if not m: sys.exit(3)
print(m[0]['id'])" )" || die "no encontré una sesión con name='$SESSION_NAME'"

# --- Enviar el mensaje ---
RESP="$(curl -fsS -X POST "$OPENWA_URL/api/sessions/$SID/messages/send-text" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  --data "$(python3 -c "import json,sys; print(json.dumps({'chatId': sys.argv[1], 'text': sys.argv[2]}))" "$CHAT_ID" "$TEXT")" )" \
  || die "el envío falló (¿sesión '$SESSION_NAME' activa y 'ready'?)"

printf '%s\n' "$RESP"
