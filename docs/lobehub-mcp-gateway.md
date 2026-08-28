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

```bash
set -e
: "${NAS_DOTFILES:?Define NAS_DOTFILES apuntando al checkout}"
: "${dkco:?Define dkco apuntando a la raíz de datos Docker}"
: "${aadm:?Define aadm apuntando al home del usuario del NAS}"

# (1) Crear el grupo dedicado antes de crear el socket o arrancar contenedores.
if ! getent group nas-mcp >/dev/null; then
  sudo groupadd --system nas-mcp
fi
MCP_SOCKET_GID="$(getent group nas-mcp | cut -d: -f3)"
export MCP_SOCKET_GID

# (2) Carpetas antes de archivos.
sudo install -d -m 0750 /etc/nas
sudo install -d -o "$(id -u)" -g "$(id -g)" -m 0750 /var/lib/nas/lobehub-mcp

# (3) Copiar la unidad y su configuración no secreta.
sudo install -m 0644 "$NAS_DOTFILES/systemd/lobehub-mcp-helper.service" \
  /etc/systemd/system/lobehub-mcp-helper.service
sudo install -m 0640 "$NAS_DOTFILES/systemd/lobehub-mcp-helper.env.example" \
  /etc/nas/lobehub-mcp-helper.env
sudo sed -i "s/^MCP_SOCKET_GID=.*/MCP_SOCKET_GID=$MCP_SOCKET_GID/" \
  /etc/nas/lobehub-mcp-helper.env

# (4) La configuración anterior no contiene secretos. El audit log se crea
# con modo 600 al primer uso por el proceso helper.
sudo systemctl daemon-reload
```

Si el checkout o el runtime no usan las rutas estándar, editar
`/etc/nas/lobehub-mcp-helper.env` antes de arrancar y conservar:

```env
MCP_MODE=helper
NAS_DOTFILES=<ruta-del-checkout>
DOCKER_BASE=<ruta-de-datos-docker>
MCP_HELPER_SOCKET=/run/nas/lobehub-mcp.sock
MCP_SOCKET_GID=<gid-del-grupo-nas-mcp>
MCP_AUDIT_LOG=/var/lib/nas/lobehub-mcp/audit.jsonl
```

El archivo no contiene el token MCP. El helper solo necesita leer los
manifests y ejecutar las cuatro comprobaciones fijas.

### 2. Preparar el compose y el token del sidecar

Si `$dkco/lobehub/` ya existe, tomar un snapshot antes de reemplazar el
compose. No copiar secretos al catálogo:

```bash
svc snapshot lobehub

# (1) La carpeta y el almacenamiento ya deben existir antes de copiar archivos.
mkdir -p "$dkco/lobehub/data/rustfs"

# (2) Copiar únicamente el compose canónico y completar el path runtime.
cp "$NAS_DOTFILES/agent/catalog/services/lobehub/compose.yml" \
  "$dkco/lobehub/compose.yml"
sed -i 's|file: ../../_common.yml|file: ../_common.yml|g' \
  "$dkco/lobehub/compose.yml"

# El .env existente se conserva. Si no existe, crear una copia del ejemplo.
if [[ ! -f "$dkco/lobehub/.env" ]]; then
  cp "$NAS_DOTFILES/agent/catalog/services/lobehub/.env.example" \
    "$dkco/lobehub/.env"
fi

# (3) Esta sección es autocontenida: no depende de que la sección 1 se haya
# ejecutado en la misma shell. El GID lo obtiene Debian automáticamente.
if ! getent group nas-mcp >/dev/null; then
  sudo groupadd --system nas-mcp
fi
MCP_SOCKET_GID="$(getent group nas-mcp | cut -d: -f3)"
[[ "$MCP_SOCKET_GID" =~ ^[0-9]+$ ]] || {
  printf 'No se pudo obtener el GID del grupo nas-mcp.\n' >&2
  exit 1
}

# Generar un token solo si falta o todavía es el placeholder. Si ya existe un
# token válido, conservarlo para no romper una configuración de LobeHub activa.
MCP_TOKEN=""
if ! grep -q '^LOBEHUB_MCP_TOKEN=' "$dkco/lobehub/.env" || \
   grep -Eq '^LOBEHUB_MCP_TOKEN=(|__pega_aqui__)$' "$dkco/lobehub/.env"; then
  MCP_TOKEN="$(openssl rand -hex 32)"
fi
export MCP_TOKEN MCP_SOCKET_GID

python3 - "$dkco/lobehub/.env" <<'PY'
import os
import sys
from pathlib import Path

path = Path(sys.argv[1])
updates = {
    "NAS_DOTFILES": "/nas-dotfiles",
    "MCP_HELPER_SOCKET": "/run/nas/lobehub-mcp.sock",
    "MCP_SOCKET_GID": os.environ["MCP_SOCKET_GID"],
}
if os.environ["MCP_TOKEN"]:
    updates["LOBEHUB_MCP_TOKEN"] = os.environ["MCP_TOKEN"]

lines = path.read_text(encoding="utf-8").splitlines()
found = set()
output = []
for line in lines:
    key = line.split("=", 1)[0] if "=" in line else ""
    if key in updates:
        output.append(f"{key}={updates[key]}")
        found.add(key)
    else:
        output.append(line)
for key, value in updates.items():
    if key not in found:
        output.append(f"{key}={value}")
path.write_text("\n".join(output) + "\n", encoding="utf-8")
PY
unset MCP_TOKEN MCP_SOCKET_GID
chmod 600 "$dkco/lobehub/.env"
```

El `.env` debe tener también `NAS_DOTFILES`,
`MCP_HELPER_SOCKET=/run/nas/lobehub-mcp.sock` y el GID numérico de `nas-mcp` en
`MCP_SOCKET_GID`. No usar `docker compose config` para mostrar el archivo
resuelto: puede interpolar secretos.

### 3. Levantar en orden

Primero arrancar el helper y verificar que el socket exista; después levantar
el stack mediante `svc`:

```bash
sudo systemctl enable --now lobehub-mcp-helper

test -S /run/nas/lobehub-mcp.sock
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

En el cuadro de importación, usar una configuración equivalente a esta, sin
cometer el token en Git:

```json
{
  "mcpServers": {
    "nas-dotfiles": {
      "url": "http://lobehub-mcp:8790/mcp",
      "type": "http",
      "headers": {
        "Authorization": "Bearer <LOBEHUB_MCP_TOKEN>"
      }
    }
  }
}
```

En la interfaz, si el formulario ofrece **Auth type: API Key**, elegirlo y
pegar el valor del token local sin el prefijo `Bearer`; LobeHub construye el
header. Si se usan headers avanzados, enviar exactamente
`Authorization: Bearer <token>`. Nunca poner `AUTH_SECRET`, `JWKS_KEY`,
`LOBE_DB_PASSWORD` ni `REDIS_PASSWORD` en este campo.

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

### Fallos frecuentes

| Síntoma | Revisión segura |
|---|---|
| `Connection refused` al probar MCP | `svc ps lobehub`, `svc logs lobehub --tail=100`, y comprobar que `lobehub-mcp` esté healthy. |
| `helper_unavailable` | `sudo systemctl status lobehub-mcp-helper` y `test -S /run/nas/lobehub-mcp.sock`; no crear el socket a mano. |
| `401 Unauthorized` | Regenerar/leer el token solo localmente, actualizar el valor de LobeHub y no compartirlo. |
| `Origin no permitido` | Añadir el origin exacto a `MCP_ALLOWED_ORIGINS`, recrear el sidecar con `svc recreate lobehub`; no usar `*`. |
| Faltan tools en el preview | Revisar `svc capabilities --service lobehub`; el gateway falla cerrado si faltan source, dispatch o guard. |
| El sidecar no inicia | `svc logs lobehub --tail=100`; comprobar que el helper ya exista y que `$NAS_DOTFILES` sea accesible para el build. |
| Se solicita una mutación | Es comportamiento esperado: no está publicada. Usar el flujo local documentado y confirmación humana, nunca ampliar esta allowlist desde LobeHub. |

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
