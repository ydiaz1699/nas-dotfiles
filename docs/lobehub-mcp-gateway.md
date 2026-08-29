# Gateway MCP read-only: LobeHub ↔ nas-dotfiles

> **Estado:** implementación inicial. Expone solo consultas seguras; no expone
> el agente Strands, el Docker socket, SQL, rutas arbitrarias ni comandos `svc`
> enviados por el cliente.

## Qué se construyó

La integración tiene dos procesos separados:

```text
LobeHub (lobe_storage)
    │  HTTP MCP interno + Bearer token
    ▼
lobehub-mcp (sidecar, sin puerto publicado)
    │  Unix socket montado; protocolo de una línea
    ▼
lobehub-mcp-helper (host, usuario aadm)
    │  allowlist fija + argumentos constantes
    ▼
svc lobehub {preflight,verify,status,providers}
```

El sidecar no tiene Docker socket y no puede ejecutar `svc`. El helper host es
el único proceso que puede invocar el CLI, y rechaza cualquier operación que no
esté en la allowlist. `capabilities` lee los manifests versionados y valida, sin importar código del
checkout, que cada operación publicada tenga source, dispatch y guard
read-only conectados.

## Resultado verificado en el NAS

La prueba runtime realizada el **28 de agosto de 2026** confirmó la ruta completa
sin exponer el token:

```text
sin_token_status=401
manifest_status=200
manifest_content_type=application/json; charset=utf-8
tools_count=5
```

El `401` de la primera prueba es intencional: se hizo un POST MCP sin `Bearer` y
confirma que DNS, red, ruta y autenticación están alcanzables. El `200` de
`tools/list` autenticado confirma el manifest funcional y las cinco tools
esperadas. Un `GET /mcp` en un navegador no sustituye estas pruebas: el endpoint
es interno, espera POST JSON-RPC y puede responder `405` a GET por diseño.

En la misma sesión, `svc lobehub verify` terminó con **Resultado: 0 fallos**.
LobeHub y `lobehub-mcp` estaban healthy; RustFS estaba healthy, `rustfs-init`
había terminado correctamente, Redis respondió `PONG`, PostgreSQL mostró
`vector`/`pg_search` y el rol `lobehub_user` cumplió mínimo privilegio. El aviso
`QSTASH_TOKEN not set` es opcional y no invalida la integración.

Herramientas publicadas:

| Tool MCP | Operación interna | Cambia datos |
|---|---|:---:|
| `lobehub_preflight` | `svc lobehub preflight` | No |
| `lobehub_verify` | `svc lobehub verify` | No |
| `lobehub_status` | `svc lobehub status` | No |
| `lobehub_providers` | `svc lobehub providers` | No |
| `capabilities` | índice de capabilities filtrado | No |

Ninguna tool acepta argumentos. El gateway rechaza rutas, comandos, SQL,
flags y parámetros adicionales. `backup-db`, `repair-storage` y
`reconcile-db` no se publican; una futura mutación requerirá una superficie
separada con preparación, autorización humana y auditoría propia.

## Requisitos

- LobeHub y `lobehub-mcp` en la red Docker interna `lobe_storage`.
- `db_net`, DataSQL y el runtime LobeHub preparados según
  [`docs/services/lobehub-guide.md`](services/lobehub-guide.md).
- Un checkout accesible como `$NAS_DOTFILES` y el runtime Docker en `$dkco`.
- El usuario del helper (`$aadm`) con permiso para ejecutar las consultas
  read-only del Docker CLI; no se añade el socket al sidecar.

Antes de tocar el runtime, consultar la guía del servicio y el entorno Docker:

```bash
nasfk
bat docs/services/lobehub-guide.md
bat docs/docker-entorno.md
svc health
svc ps datasql
```

## Instalación en el NAS

La secuencia respeta: **carpetas → archivos → permisos → levantar**.
Los comandos siguientes generan el token localmente y no lo imprimen ni lo
piden en el chat.

### 1. Preparar el helper host

El bloque siguiente es autocontenido: usa las variables que el entorno del NAS
ya exporta y, si faltan, intenta recuperarlas desde un login shell. No hay que
rellenar manualmente `NAS_DOTFILES`, `DOCKER_BASE`, `MCP_SOCKET_GID` ni ninguna
ruta. Si una variable no está configurada, se detiene antes de copiar archivos.

```bash
set -euo pipefail

# Recuperar las rutas del entorno NAS sin pedirlas ni escribirlas a mano.
if [[ -z "${NAS_DOTFILES:-}" || -z "${dkco:-}" || -z "${aadm:-}" ]]; then
  IFS=$'\x1f' read -r detected_nas detected_docker detected_home < <(
    bash -lc 'printf "%s\037%s\037%s" "${NAS_DOTFILES:-}" "${dkco:-}" "${aadm:-}"' \
      2>/dev/null || true
  ) || true
  NAS_DOTFILES="${NAS_DOTFILES:-${detected_nas:-}}"
  dkco="${dkco:-${detected_docker:-}}"
  aadm="${aadm:-${detected_home:-}}"
fi

: "${NAS_DOTFILES:?No se encontró NAS_DOTFILES; carga el entorno con nasfk}"
: "${dkco:?No se encontró dkco; carga el entorno con dk}"
: "${aadm:?No se encontró aadm; carga el entorno con adm}"
DOCKER_BASE="${DOCKER_BASE:-$dkco}"
export NAS_DOTFILES DOCKER_BASE

# Validar antes de crear o reemplazar cualquier archivo.
test -f "$NAS_DOTFILES/systemd/lobehub-mcp-helper.service"
test -f "$NAS_DOTFILES/systemd/lobehub-mcp-helper.env.example"
test -f "$NAS_DOTFILES/agent/lobehub_mcp.py"
test -d "$dkco"
test -d "$aadm"

# Crear el grupo dedicado antes de crear el socket o arrancar contenedores.
if ! getent group nas-mcp >/dev/null; then
  sudo groupadd --system nas-mcp
fi
MCP_SOCKET_GID="$(getent group nas-mcp | cut -d: -f3)"
[[ "$MCP_SOCKET_GID" =~ ^[0-9]+$ ]] || {
  printf 'No se pudo obtener un GID numérico para nas-mcp.\n' >&2
  exit 1
}

# Crear carpetas antes de instalar archivos. El helper corre como aadm,
# incluso si este bloque se pega desde una sesión root.
AADM_UID="$(id -u "$(basename "$aadm")")"
AADM_GID="$(id -g "$(basename "$aadm")")"
sudo install -d -m 0750 /etc/nas
sudo install -d -o "$AADM_UID" -g "$AADM_GID" -m 0750 \
  /var/lib/nas/lobehub-mcp

# Copiar la unidad y su configuración no secreta.
sudo install -m 0644 "$NAS_DOTFILES/systemd/lobehub-mcp-helper.service" \
  /etc/systemd/system/lobehub-mcp-helper.service
sudo install -m 0640 "$NAS_DOTFILES/systemd/lobehub-mcp-helper.env.example" \
  /etc/nas/lobehub-mcp-helper.env
sudo sed -i \
  -e "s|^NAS_DOTFILES=.*|NAS_DOTFILES=$NAS_DOTFILES|" \
  -e "s|^DOCKER_BASE=.*|DOCKER_BASE=$DOCKER_BASE|" \
  -e "s|^MCP_SOCKET_GID=.*|MCP_SOCKET_GID=$MCP_SOCKET_GID|" \
  /etc/nas/lobehub-mcp-helper.env
# El helper corre como aadm y necesita leer solo los .env compartidos para
# interpolar Compose y comprobar Redis/PostgreSQL. No hacerlos públicos: el
# grupo dedicado nas-mcp es el único grupo adicional del helper.
for shared_env in "$DOCKER_BASE/.env" "$DOCKER_BASE/datasql/.env"; do
  test -f "$shared_env" || {
    printf 'Falta el archivo requerido: %s\n' "$shared_env" >&2
    exit 1
  }
  sudo chgrp nas-mcp "$shared_env"
  sudo chmod 640 "$shared_env"
  sudo -u aadm test -r "$shared_env" || {
    printf 'aadm no puede leer %s; no arrancar el helper.\n' "$shared_env" >&2
    exit 1
  }
done

sudo systemctl daemon-reload
```

El bloque escribe automáticamente en `/etc/nas/lobehub-mcp-helper.env`:
`NAS_DOTFILES` detectado, `DOCKER_BASE` heredado de `dkco`, el socket fijo del
helper, el GID real del grupo `nas-mcp` y el audit log. También concede al grupo
privado `nas-mcp` lectura sobre el `.env` global y el `.env` de DataSQL, porque el
helper se ejecuta como `aadm`; conserva el `.env` de LobeHub en `0600` propiedad
de `aadm`. No se imprimen valores. El helper no recibe el token MCP; solo lee
manifests y ejecuta las cuatro comprobaciones fijas.

### 2. Preparar el compose, el token y comprobar el resultado

Este bloque respeta el orden **snapshot opcional → carpetas → archivos →
permisos → comprobaciones**. El token existente se conserva; solo se genera uno
nuevo si falta o es `__pega_aqui__`. No usa heredoc ni Python multilínea, no
imprime el token y no lo pasa como argumento de ningún proceso.

```bash
set -euo pipefail
: "${NAS_DOTFILES:?Ejecuta primero la sección 1 o carga el entorno NAS}"
: "${dkco:?Ejecuta primero la sección 1 o carga el entorno NAS}"

SERVICE_DIR="$dkco/lobehub"
ENV_FILE="$SERVICE_DIR/.env"

# El helper y la operación normal del NAS usan aadm. No usar id -u/id -g sin
# nombre: si este bloque se pega desde root, eso dejaría la configuración como
# root:root y aadm no podría ejecutar svc ni leer el .env.
AADM_USER="aadm"
getent passwd "$AADM_USER" >/dev/null || {
  printf 'No existe el usuario %s; no continuar.\n' "$AADM_USER" >&2
  exit 1
}
AADM_UID="$(id -u "$AADM_USER")"
AADM_GID="$(id -g "$AADM_USER")"

# Una ejecución anterior como root puede haber dejado el directorio de
# configuración no escribible para aadm. Normalizar SOLO la carpeta de
# configuración y sus archivos; no tocar data/rustfs ni sus UID 10001.
if [[ -d "$SERVICE_DIR" ]]; then
  sudo chown "$AADM_UID:$AADM_GID" "$SERVICE_DIR"
  sudo chmod 0750 "$SERVICE_DIR"
  for config_file in compose.yml .env bucket.config.json; do
    if [[ -e "$SERVICE_DIR/$config_file" ]]; then
      sudo chown "$AADM_UID:$AADM_GID" "$SERVICE_DIR/$config_file"
    fi
  done
  [[ ! -e "$ENV_FILE" ]] || sudo chmod 600 "$ENV_FILE"
  [[ ! -e "$SERVICE_DIR/compose.yml" ]] || sudo chmod 644 "$SERVICE_DIR/compose.yml"
  [[ ! -e "$SERVICE_DIR/bucket.config.json" ]] || sudo chmod 644 "$SERVICE_DIR/bucket.config.json"
else
  sudo install -d -o "$AADM_UID" -g "$AADM_GID" -m 0750 "$SERVICE_DIR"
fi

# svc snapshot necesita leer la configuración y escribir el destino de
# snapshots. Esto no contiene secretos nuevos y evita que una ejecución desde
# root deje el destino inaccesible para aadm.
sudo install -d -o "$AADM_UID" -g "$AADM_GID" -m 0750 \
  "$dkco/backups/.snapshots"

# Snapshot solo si ya existe un compose que pueda reemplazarse.
if [[ -f "$SERVICE_DIR/compose.yml" ]]; then
  svc snapshot lobehub
fi

# Crear carpetas antes de copiar archivos. La carpeta de datos queda fuera de
# la normalización de configuración; después se aplicará UID 10001 a RustFS.
mkdir -p "$SERVICE_DIR/data/rustfs"

# Instalar el compose canónico sin usar el alias interactivo cp del NAS.
# install reemplaza deliberadamente el compose, porque es la fuente canónica.
install -o "$AADM_UID" -g "$AADM_GID" -m 0644 \
  "$NAS_DOTFILES/agent/catalog/services/lobehub/compose.yml" \
  "$SERVICE_DIR/compose.yml"
sed -i 's|file: ../../_common.yml|file: ../_common.yml|g' \
  "$SERVICE_DIR/compose.yml"

# El .env existente se conserva; si no existe, se crea desde el ejemplo.
if [[ ! -f "$ENV_FILE" ]]; then
  install -o "$AADM_UID" -g "$AADM_GID" -m 0600 \
    "$NAS_DOTFILES/agent/catalog/services/lobehub/.env.example" \
    "$ENV_FILE"
fi

# Obtener el GID real y leer el token solo en memoria local.
MCP_SOCKET_GID="$(getent group nas-mcp | cut -d: -f3)"
[[ "$MCP_SOCKET_GID" =~ ^[0-9]+$ ]] || {
  printf 'GID inválido para nas-mcp.\n' >&2
  exit 1
}
MCP_TOKEN="$(awk -F= \
  '$1=="LOBEHUB_MCP_TOKEN"{print substr($0,index($0,"=")+1); exit}' \
  "$ENV_FILE")"
if [[ -z "$MCP_TOKEN" || "$MCP_TOKEN" == "__pega_aqui__" ]]; then
  MCP_TOKEN="$(openssl rand -hex 32)"
fi
[[ "$MCP_TOKEN" =~ ^[[:xdigit:]]{64}$ ]] || {
  printf 'El token MCP no tiene el formato esperado.\n' >&2
  exit 1
}

# El token se guarda en un temporal 0600, no en el entorno ni en argv de awk.
umask 077
tmp_env="$(mktemp "$SERVICE_DIR/.env.mcp.XXXXXX")"
tmp_token="$(mktemp "$SERVICE_DIR/.token.mcp.XXXXXX")"
cleanup_mcp_files() {
  rm -f "$tmp_env" "$tmp_token"
  unset MCP_TOKEN MCP_SOCKET_GID
}
trap cleanup_mcp_files EXIT
printf '%s\n' "$MCP_TOKEN" > "$tmp_token"
chmod 600 "$tmp_token"

awk -v token_file="$tmp_token" -v gid="$MCP_SOCKET_GID" \
    -v repo="$NAS_DOTFILES" '
BEGIN {
  if ((getline token < token_file) <= 0) {
    print "No se pudo leer el token temporal" > "/dev/stderr"
    exit 1
  }
}
{
  key=$0
  sub(/=.*/, "", key)
  if (key == "NAS_DOTFILES") {
    print "NAS_DOTFILES=" repo
    seen_repo=1
  } else if (key == "MCP_HELPER_SOCKET") {
    print "MCP_HELPER_SOCKET=/run/nas/lobehub-mcp.sock"
    seen_socket=1
  } else if (key == "MCP_SOCKET_GID") {
    print "MCP_SOCKET_GID=" gid
    seen_gid=1
  } else if (key == "LOBEHUB_MCP_TOKEN") {
    print "LOBEHUB_MCP_TOKEN=" token
    seen_token=1
  } else {
    print
  }
}
END {
  if (!seen_repo) print "NAS_DOTFILES=" repo
  if (!seen_socket) print "MCP_HELPER_SOCKET=/run/nas/lobehub-mcp.sock"
  if (!seen_gid) print "MCP_SOCKET_GID=" gid
  if (!seen_token) print "LOBEHUB_MCP_TOKEN=" token
}' "$ENV_FILE" > "$tmp_env"
chmod 600 "$tmp_env"
mv -f "$tmp_env" "$ENV_FILE"
# Si el bloque se ejecutó desde root, el temporal nació como root; el .env
# debe quedar siempre administrable por aadm y seguir protegido con 0600.
sudo chown "$AADM_UID:$AADM_GID" "$ENV_FILE"
chmod 600 "$ENV_FILE"
rm -f "$tmp_token"
trap - EXIT
unset MCP_TOKEN MCP_SOCKET_GID tmp_env tmp_token
```

Comprobar el resultado sin mostrar el token ni interpolar secretos:

```bash
ENV_FILE="$dkco/lobehub/.env"
HELPER_ENV=/etc/nas/lobehub-mcp-helper.env
EXPECTED_GID="$(getent group nas-mcp | cut -d: -f3)"

# Estas tres líneas no son secretas y deben mostrar los valores configurados.
grep -E '^(NAS_DOTFILES|MCP_HELPER_SOCKET|MCP_SOCKET_GID)=' "$ENV_FILE"

# Estas comprobaciones solo imprimen estados, nunca el token. Se usan `if`
# explícitos para que un fallo no cierre una shell root que tenga `set -e`.
if grep -q '^LOBEHUB_MCP_TOKEN=[^[:space:]]' "$ENV_FILE" && \
   ! grep -q '^LOBEHUB_MCP_TOKEN=__pega_aqui__$' "$ENV_FILE"; then
  echo 'Token MCP configurado'
else
  echo 'FALTA configurar el token MCP' >&2
fi

if [[ "$(stat -c '%a' "$ENV_FILE")" == 600 ]]; then
  echo '.env protegido (0600)'
else
  echo 'ERROR: .env no tiene modo 600' >&2
fi

ENV_GID="$(awk -F= '$1=="MCP_SOCKET_GID"{print $2; exit}' "$ENV_FILE")"
HELPER_GID="$(awk -F= '$1=="MCP_SOCKET_GID"{print $2; exit}' "$HELPER_ENV")"
if [[ "$ENV_GID" == "$EXPECTED_GID" && "$HELPER_GID" == "$EXPECTED_GID" ]]; then
  echo 'GID del socket coincide en runtime y helper'
else
  echo 'ERROR: GID del socket no coincide' >&2
fi
```

No usar `docker compose config` para mostrar el archivo resuelto: puede
interpolar secretos.

### 3. Levantar en orden

Primero arrancar el helper y verificar que el socket exista; después validar
la configuración y levantar el stack mediante `svc`:

```bash
sudo systemctl enable --now lobehub-mcp-helper
systemctl is-active --quiet lobehub-mcp-helper \
  && echo 'Helper MCP activo'
test -S /run/nas/lobehub-mcp.sock \
  && echo 'Socket MCP creado correctamente'

svc config lobehub >/dev/null
svc up lobehub
svc ps lobehub
```

El sidecar `lobehub-mcp` no tiene `ports:` y solo pertenece a `lobe_storage`.
LobeHub lo alcanza por el nombre interno `lobehub-mcp`; ningún puerto MCP se
publica en la LAN. El build usa `$NAS_DOTFILES/agent` como contexto mínimo y
`mcp/Dockerfile`; el `.dockerignore` excluye el resto del checkout y no necesita
credenciales de registro.

## Configurar LobeHub Web

LobeHub documenta la configuración de un MCP personalizado desde **Settings →
Skills → Skill Store → Custom → Add custom skill**, o desde las Skills de un
agente. También permite importar JSON y probar la conexión antes de instalarlo.
Consulta la guía oficial: [Custom MCP en LobeHub](https://lobehub.com/docs/usage/community/custom-mcp).

### Procedimiento UI verificado

1. En LobeHub, abrir **Settings → Skills → Skill Store → Custom → Add custom
   skill** (o las Skills del agente) y seleccionar importar JSON.
2. Importar únicamente la URL y el tipo, sin insertar secretos en el JSON:
   `http://lobehub-mcp:8790/mcp` y conexión `http`/**Streamable HTTP**.
3. En los campos de autenticación de la interfaz elegir **Auth type: API Key**
   y pegar el valor local de `LOBEHUB_MCP_TOKEN` **sin** el prefijo `Bearer`.
4. Ejecutar **Test connection** y comprobar las cinco tools de esta guía.
5. Instalar/habilitar `nas-dotfiles` en el agente que lo usará. Instalar el MCP
   no lo habilita automáticamente para todos los agentes.

El navegador del usuario no debe resolver `lobehub-mcp`: LobeHub hace la petición
como backend dentro de Docker, en `lobe_storage`. No cambiar el endpoint por
`http://${SERVER_IP}:8790/mcp`, no publicar `8790` y no abrirlo directamente en
el navegador.

En el cuadro de importación, usa inicialmente solo la URL y el tipo de conexión;
configura la autenticación después en los campos de la interfaz:

```json
{
  "mcpServers": {
    "nas-dotfiles": {
      "url": "http://lobehub-mcp:8790/mcp",
      "type": "http"
    }
  }
}
```

### Alternativa: configuración manual en LobeHub

Si la importación JSON no muestra los campos de autenticación o falla con
`Error POSTing to endpoint`, configura el MCP manualmente en la misma pantalla.
Esta alternativa es equivalente y fue la ruta verificada en la interfaz:

```text
MCP name:        nas-dotfiles
Connection type: Streamable HTTP
Endpoint URL:    http://lobehub-mcp:8790/mcp
Auth type:       API Key
API Key:         <valor local de LOBEHUB_MCP_TOKEN, sin Bearer>
```

No escribas `Bearer` en el campo **API Key**: LobeHub lo añade al header
`Authorization`. No agregues headers manuales en el primer intento y no uses
`type: "stdio"`; este gateway es HTTP interno. Después:

1. Pulsa **Test connection**.
2. Comprueba que aparecen exactamente `lobehub_preflight`, `lobehub_verify`,
   `lobehub_status`, `lobehub_providers` y `capabilities`.
3. Pulsa **Install** o **Save**.
4. Abre la configuración del agente que lo usará, entra en **Skills**, busca
   `nas-dotfiles`, activa el interruptor y guarda. La instalación no habilita el
   MCP automáticamente para todos los agentes.

Si se configura desde el agente en lugar del Skill Store, usa **Agent settings
→ Skills → Add custom skill** y repite los mismos campos. Los nombres pueden
variar ligeramente según la versión de LobeHub, pero no cambian el endpoint, el
tipo de conexión ni el modo de autenticación.

La configuración final debe usar **Streamable HTTP**, el endpoint
`http://lobehub-mcp:8790/mcp` y **Auth type: API Key**. Pegar el valor local
del token sin el prefijo `Bearer`; LobeHub construye el header. Esta forma es
preferible al header JSON manual porque evita que el importador convierta o
pierda la autenticación. Si se usan headers avanzados, enviar exactamente
`Authorization: Bearer <token>`. Nunca poner `AUTH_SECRET`, `JWKS_KEY`,
`LOBE_DB_PASSWORD` ni `REDIS_PASSWORD` en este campo.

Para obtener el token cuando estés listo para pegarlo en LobeHub, ejecuta este
comando **solo en la terminal local del NAS**. Imprime un secreto
intencionadamente; no copies su salida al chat, a un issue, a un log ni al
repositorio:

```bash
awk -F= '$1=="LOBEHUB_MCP_TOKEN"{print substr($0,index($0,"=")+1); exit}' \
  "$dkco/lobehub/.env"
```

Después de **Test connection**, deben aparecer exactamente las cinco tools de
la tabla. Finalmente habilitar `nas-dotfiles` en la configuración del agente de
LobeHub; instalar un MCP no lo habilita automáticamente para todos los agentes.

El endpoint usa HTTP interno deliberadamente. No usar `http://${SERVER_IP}:...`
ni agregar `ports:` al servicio `lobehub-mcp`. Si se conecta desde un cliente
fuera de `lobe_storage`, detenerse: la primera versión no está diseñada para
exponer el gateway a la LAN.

## Seguridad y límites

- El token MCP es independiente de todos los secretos de LobeHub y DataSQL.
- El sidecar corre read-only, con `cap_drop: [ALL]`, `no-new-privileges`, sin
  Docker socket y sin bind mounts de `.env`.
- El helper recibe solo `{"operation":"..."}` y rechaza claves adicionales,
  argumentos, SQL, comandos y rutas.
- HTTP exige `Authorization: Bearer ...`; un `Origin` presente solo se acepta
  si está incluido en `MCP_ALLOWED_ORIGINS`. Sin `Origin` se admite la llamada
  server-to-server de LobeHub.
- Se limita el tamaño de solicitudes/respuestas y hay timeout individual por
  operación. Los errores no devuelven stderr, logs ni valores de entorno.
- El audit log guarda timestamp, tool, resultado y duración; no guarda
  argumentos ni contenido de logs. Revisarlo con permisos administrativos, no
  publicarlo.
- La implementación no reutiliza `nas_agent.py` ni `ALL_TOOLS`, porque el agente
  conversacional tiene tools de escritura, memoria, búsquedas y acceso más
  amplio que el necesario para esta frontera.

El transporte Streamable HTTP de MCP requiere JSON-RPC y recomienda validar
`Origin` y autenticar las conexiones; esta implementación sigue esas
restricciones y responde JSON directamente para requests normales. Referencias:
[transporte MCP](https://modelcontextprotocol.io/specification/2025-03-26/basic/transports)
y [SDK Python oficial](https://github.com/modelcontextprotocol/python-sdk).
Contenido externo reescrito y resumido para esta guía.

## Compatibilidad con el CLI `svc`

El NAS tiene dos entradas para `svc` y sus sintaxis no son intercambiables:

- Bash: `NAS_CLI=bash` (predeterminada salvo que el entorno la cambie).
- Python/Typer: `NAS_CLI=python`.

Para ejecutar comandos dentro del compose de LobeHub, usa estas formas:

```bash
# CLI Bash: el proyecto es lobehub y el servicio interno se indica después.
NAS_CLI=bash svc exec lobehub lobehub-mcp python -c 'print("ok")'
NAS_CLI=bash svc exec lobehub /bin/node -e 'console.log("ok")'

# CLI Python/Typer: `--` separa las opciones de svc del comando interno.
NAS_CLI=python svc exec lobehub -- lobehub-mcp python -c 'print("ok")'
NAS_CLI=python svc exec lobehub -- /bin/node -e 'console.log("ok")'
```

Reglas para cualquier diagnóstico paste-safe:

- En Python, `--` es obligatorio antes de argumentos del comando que empiecen
  por `-`; de lo contrario `-c`, `-e`, `-U`, `-d`, `-v` o `-T` pueden producir
  `No such option` en el parser de Typer.
- En Python, el primer argumento después de `svc exec` selecciona el compose.
  Si el servicio interno difiere, va después de `--`: `lobehub` es el compose y
  `lobehub-mcp` el servicio.
- En Bash no usar esta variante con `--`; Bash hace passthrough directo a
  Compose y usa `NAS_CLI=bash svc exec lobehub lobehub-mcp ...`.
- No usar la forma antigua `svc exec lobehub lobehub-mcp -- python -c ...`:
  mezcla el orden del Bash CLI con el separador del CLI Python y puede producir
  `No such option` o enviar argumentos al servicio equivocado.
- `-T` no es una opción registrada por el CLI Python; no usarlo.
- `Endpoint:`, `Auth type:` y `API Key:` son campos de la interfaz de LobeHub,
  nunca comandos para pegar en Bash.
- Si el diagnóstico lee `$dkco/.env`, ejecutarlo como root o después de `dk`
  con un usuario que tenga permisos; desde `~` puede aparecer
  `open /docker/.env: permission denied`.

Las respuestas de `lobehub_status`, `lobehub_verify` y `lobehub_preflight` incluyen
un bloque no sensible `execution_context`. En una instalación correcta debe
mostrar `executor: host-helper`, `framework: nas-dotfiles`, `entrypoint: available`
y `docker_base: configured`. Si aparece `local-process`, el sidecar no está
usando el helper del host; si aparece `host-helper` junto a `context` en estado
`fail`, el helper sí alcanzó el NAS pero su usuario no tiene acceso al runtime.

El detalle de `context` identifica ahora cada prerrequisito sin mostrar rutas,
valores ni secretos. Una salida típica tiene este formato:

```text
context: global_env=ok;compose=ok;common=ok;lobehub_env=ok;datasql_env=ok;docker_cli=ok;docker_access=ok
compose_resolved: compose resoluble
```

Si alguno aparece como `missing` o `denied`, ese es el contexto que debe
corregirse. `compose_resolved` además clasifica el error sin copiar stderr:
`permission_denied`, `missing_compose_dependency`,
`missing_environment_variable`, `invalid_compose` o `docker_unavailable`.

Comandos MCP paste-safe usando el CLI Python/Typer activo:

```bash
# Red/DNS: 401 es el resultado esperado porque no hay Bearer.
NAS_CLI=python svc exec lobehub -- /bin/node -e '
fetch("http://lobehub-mcp:8790/mcp", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream"
  },
  body: JSON.stringify({
    jsonrpc: "2.0",
    id: 1,
    method: "initialize",
    params: {
      protocolVersion: "2025-03-26",
      capabilities: {},
      clientInfo: { name: "nas-diagnostic", version: "1.0" }
    }
  })
}).then(async response => {
  console.log("sin_token_status=" + response.status)
  console.log("sin_token_content_type=" + (response.headers.get("content-type") || ""))
  console.log("sin_token_body=" + (await response.text()).slice(0, 160))
}).catch(error => console.log("sin_token_network_error=" + error.name + ":" + error.message))
'

# Manifest autenticado: el token ya está dentro del sidecar; no se imprime.
NAS_CLI=python svc exec lobehub -- lobehub-mcp python -c '
import os,json,urllib.request
body=json.dumps({"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}).encode()
request=urllib.request.Request(
  "http://127.0.0.1:8790/mcp", data=body, method="POST",
  headers={
    "Authorization":"Bearer "+os.environ["MCP_SERVICE_TOKEN"],
    "Content-Type":"application/json",
    "Accept":"application/json, text/event-stream"
  })
with urllib.request.urlopen(request, timeout=5) as response:
  result=json.loads(response.read().decode())
  print("manifest_status="+str(response.status))
  print("manifest_content_type="+response.headers.get("content-type",""))
  print("tools_count="+str(len(result.get("result",{}).get("tools",[]))))
'
```

No añadir `-T`, no repetir `lobehub` como servicio interno y no pegar las
etiquetas `Endpoint:`, `Auth type:` o `API Key:` en Bash.

## Validación y troubleshooting

### Comprobación funcional

```bash
svc lobehub preflight
svc lobehub status
svc lobehub verify
svc lobehub providers
svc capabilities --service lobehub
```

Desde la interfaz, `capabilities` debe indicar `mutations_exposed: false` y las
operaciones publicadas deben estar conectadas. No se debe esperar que el MCP
cree bases, haga backups, arregle permisos o detenga servicios.

### Fallos frecuentes y causa real

| Síntoma observado | Causa | Corrección segura |
|---|---|---|
| Todas las comprobaciones fallan desde LobeHub, pero `svc lobehub verify` funciona manualmente como root | El MCP sí llega al helper, pero `aadm` no puede leer `$dkco/.env`/`$dkco/datasql/.env`, acceder a Docker o está consultando otro checkout/proyecto Compose | Ejecutar `lobehub_preflight` y comprobar que `execution_context.executor` sea `host-helper`; corregir grupo `nas-mcp`, lectura restringida de los `.env`, rutas configuradas y reiniciar el helper. No hacer los secretos world-readable. |
| No se puede abrir `http://lobehub-mcp:8790/mcp` en el navegador | `lobehub-mcp` es un hostname Docker interno y `/mcp` no es una página GET | Validar con POST JSON-RPC desde `svc exec`; `GET /mcp` puede devolver `405` por diseño. |
| `sin_token_status=401` | La prueba omitió deliberadamente `Authorization` | Es el resultado esperado; confirma que el endpoint está protegido. Continuar con `tools/list` autenticado. |
| `No such option: -T`, `-e`, `-c`, `-U` o `-d` | Se está usando el CLI Python/Typer y sus opciones están recibiendo flags del comando interno | Usar `NAS_CLI=python svc exec lobehub -- ...`; `--` separa Typer del comando. `-T` no es compatible con este CLI. |
| El comando funciona con Bash pero no con Python | `NAS_CLI` selecciona dos implementaciones con sintaxis distinta | Fijar `NAS_CLI=bash` o `NAS_CLI=python` en cada bloque; no mezclar ejemplos. |
| `open /docker/.env: permission denied` | Se ejecutó `svc` desde `~` con un usuario que no puede resolver el `.env` global | Entrar con `dk lobehub` o usar el contexto administrativo autorizado; no relajar permisos globales para ocultarlo. |
| `csl: orden no encontrada`, `Endpoint: orden no encontrada`, `Auth: orden no encontrada` | Se pegó texto de la UI como si fueran comandos Bash, o el bloque quedó truncado | Separar los campos UI de los bloques de terminal y pegar bloques completos; no ejecutar `Endpoint:`, `Auth type:` ni `API Key:`. |
| La sesión SSH se cierra durante un diagnóstico | `set -e`/`exit` se ejecutó en la shell interactiva root, a veces después de un `grep` que devolvió 1 | Usar subshells o `if/else`; no pegar `exit` en la shell principal. |
| `svc lobehub verify` marca fallo de rol | El usuario de aplicación aún no está reconciliado con la contraseña de `.env` o tiene atributos elevados | Ejecutar el procedimiento local `svc lobehub reconcile-db --confirm`, volver a verificar y no compartir contraseñas. |
| Aparece “migración PostgreSQL” aunque no se instaló otro PostgreSQL | LobeHub ejecuta sus migraciones contra la base dedicada `lobehub_db` dentro del PostgreSQL existente de DataSQL (`datapostgres`) | Es normal; reutilizar DataSQL, mantener `lobehub_user` dedicado y no crear un segundo contenedor PostgreSQL. |
| `Connection refused` al probar MCP | El sidecar no está healthy o no está en la red privada | Ejecutar `svc ps lobehub` y revisar solo las últimas líneas con `svc logs lobehub -n 100`; comprobar que `lobehub-mcp` esté healthy. |
| El sidecar no inicia | Falta el helper/socket o `$NAS_DOTFILES` no es accesible durante el build | Revisar `svc logs lobehub -n 100`, el servicio systemd y la ruta configurada; no publicar el socket ni el Docker socket. |
| `helper_unavailable` | El servicio systemd no está activo o falta el socket | `sudo systemctl status lobehub-mcp-helper` y `test -S /run/nas/lobehub-mcp.sock`; no crear el socket a mano. |
| `Origin no permitido` | El origen no está en `MCP_ALLOWED_ORIGINS` | Añadir el origin exacto, recrear con `svc recreate lobehub` y no usar `*`. |
| Faltan tools en el preview | Falta una conexión source/dispatch/guard en los manifests | Revisar `svc capabilities --service lobehub`; el gateway debe fallar cerrado. |
| Se solicita una mutación | La tool no está publicada por diseño | Usar el flujo local con confirmación humana; nunca ampliar esta allowlist desde LobeHub. |

Para revisar el audit log sin exponer secretos:

```bash
sudo journalctl -u lobehub-mcp-helper --since '1 hour ago' --no-pager
sudo stat /var/lib/nas/lobehub-mcp/audit.jsonl
```

Si hay que retirar la integración, deshabilitar primero el agente/Skill en
LobeHub, luego detener el stack con `svc stop lobehub` y finalmente:

```bash
sudo systemctl disable --now lobehub-mcp-helper
```

## Archivos de esta integración

- `agent/lobehub_mcp.py`: protocolo MCP, allowlist, sanitización, helper y
  transporte HTTP/stdio.
- `agent/mcp/Dockerfile`: imagen mínima del sidecar sin socket Docker.
- `systemd/lobehub-mcp-helper.service`: helper host restringido.
- `systemd/lobehub-mcp-helper.env.example`: configuración no secreta del helper.
- `agent/catalog/services/lobehub/compose.yml`: sidecar interno sin puerto LAN.
- `agent/catalog/services/lobehub/.env.example`: variables del token y socket.
