# OpenWA — guía operativa del gateway de WhatsApp

> Servicio nuevo en el NAS: `$dkco/openwa`.
>
> OpenWA es un gateway **self-hosted y no oficial** de WhatsApp: expone una API
> REST + WebSocket y un dashboard para conectar uno o varios números de WhatsApp
> desde tus propios workflows (n8n, scripts, etc.).
>
> Esta guía es autocontenida. Los comandos leen secretos desde `.env` sin hacer
> `source .env` ni imprimir contraseñas, y respetan el orden real de ejecución:
> **directorios → archivos → permisos → levantar**.

## Aviso importante antes de empezar

- Es un gateway **NO oficial**. WhatsApp puede **banear** el número. Usa un
  número **dedicado**, nunca tu personal.
- Respeta los rate limits: pocos mensajes por minuto, nada de envíos masivos a
  desconocidos.
- El estado de esta guía y su ficha es **pendiente de verificación en runtime**:
  la configuración está preparada, pero debe comprobarse en el NAS antes de
  tratarla como desplegada.

## Resumen del resultado final

| Componente | Contenedor | Acceso correcto |
|---|---|---|
| OpenWA (API + dashboard + Swagger) | `openwa` | `http://${SERVER_IP}:2785` desde la LAN; `http://openwa:2785` desde `db_net` |

- **Imagen:** `ghcr.io/rmyndharis/openwa:0.23.5` (verificada accesible en GHCR).
- **Base de datos:** SQLite local en `./data/openwa.sqlite` (autocontenido).
- **Motor:** `baileys` por defecto. ⚠️ `whatsapp-web.js` tiene ROTO el envío de
  imágenes/media con la versión actual de WhatsApp Web (verificado en runtime);
  ver §14.
- **Red:** `db_net` externa (la misma que n8n), para integración interna.
- **Autenticación:** cabecera `X-API-Key` con el valor de `API_MASTER_KEY`.

### Fuentes verificadas

Los datos se verificaron contra la **documentación oficial**
(https://docs.open-wa.org, v0.23.5) y el repositorio real `rmyndharis/OpenWA`:

- Doc oficial — modelo de API keys (`API_MASTER_KEY` verbatim, formato
  `owa_k1_...`, el pepper invalida hashes), flujo de sesión con `qr_ready`.
- `openapi.json` — endpoints y `securityScheme` (`X-API-Key`, `in: header`).
- `docker-compose.dev.yml` — puerto `2785`, red `openwa-network`, hardening.
- `Dockerfile` — imagen con root FS de solo lectura, tmpfs, caps mínimas.
- `.env.minimal` — variables de la configuración SQLite single-tenant.
- `docs/22-n8n-integration.md` — nodo oficial de n8n.
- **Runtime confirmado en el NAS:** la API usa el `id` (UUID) en las URLs, no el
  `name`; el envío de texto funciona (`messageId` con sufijo `_out`).

## Redes y exposición

- OpenWA se conecta a la red externa `db_net`, donde ya vive n8n.
- Se publica en la LAN en `2785:2785` para abrir el dashboard y para que el
  navegador escanee el QR.
- n8n **no** debe llamar a `localhost:2785`: dentro de un contenedor,
  `localhost` es el propio contenedor. Debe usar `http://openwa:2785` (nombre de
  contenedor dentro de `db_net`).
- No usar `depends_on` contra n8n ni contra ningún otro compose externo.

## Excepción de seguridad (Chromium)

El motor `whatsapp-web.js` lanza Chromium/Puppeteer. Por eso este servicio **no**
lleva `cap_drop: [ALL]` a secas como los servicios simples del NAS. Se replica la
postura de hardening de la imagen oficial:

- `read_only: true` — root FS de solo lectura.
- `tmpfs: [/tmp]` — Chromium escribe su config/cache aquí.
- `pids_limit: 2048` — guarda contra fork-bomb (Chromium es multiproceso).
- `cap_drop: [ALL]` + `cap_add: [CHOWN, DAC_OVERRIDE, FOWNER, SETGID, SETUID]`.
- `no-new-privileges: true` — heredado de `_common.yml`.

No cambies esto por `cap_drop: [ALL]` sin `cap_add`: el contenedor no arrancará.

---

## 1. Preflight

```bash
svc health
svc net
svc port-map
nas
disk
```

Continúa solo si:

- La red `db_net` existe (la usa n8n).
- El puerto `2785` está libre en `svc port-map`.
- Hay RAM disponible (OpenWA con whatsapp-web.js puede usar 300-500 MB por
  sesión; el límite del compose es 2 GB).

---

## 2. Crear directorios

```bash
mkdir -p "$dkco/openwa/data"
```

Árbol esperado tras la instalación (las subcarpetas de `data/` las crea el
contenedor en el primer arranque: `sessions/`, `media/`, `plugins/` y
`openwa.sqlite`):

```text
$dkco/openwa/
├── compose.yml
├── .env
└── data/                 ← sesiones de WhatsApp, DB SQLite, media, plugins
```

---

## 3. Copiar compose y crear el `.env`

```bash
cp "$NAS_DOTFILES/agent/catalog/services/openwa/compose.yml" \
  "$dkco/openwa/compose.yml"
cp "$NAS_DOTFILES/agent/catalog/services/openwa/.env.example" \
  "$dkco/openwa/.env"
sed -i \
  's#file: ../../_common.yml#file: ../_common.yml#g' \
  "$dkco/openwa/compose.yml"
```

Genera la clave maestra de la API sin imprimirla ni copiarla a Git:

```bash
dk openwa

ENV_FILE="$dkco/openwa/.env"
(
  umask 077
  API_KEY=$(openssl rand -hex 32)
  sed -i "s/^API_MASTER_KEY=.*/API_MASTER_KEY=$API_KEY/" "$ENV_FILE"
  unset API_KEY
)
unset ENV_FILE
```

No pongas `SERVER_IP` ni `TZ` en este archivo: se heredan del `.env` global
mediante `env_file: [../.env, .env]`.

### Elegir el motor

Por defecto **`baileys`** (más ligero, sin Chromium). ⚠️ **No uses
`whatsapp-web.js` si vas a enviar imágenes:** tiene roto el envío de media con la
versión actual de WhatsApp Web (ver §14). Para pinearlo explícitamente en
`$dkco/openwa/.env`:

```text
ENGINE_TYPE=baileys
```

Cambiar de motor **obliga a re-escanear el QR** (cada motor guarda su sesión por
separado en `data/`).

---

## 4. Aplicar permisos

Después de crear directorios y archivos:

```bash
chmod 600 "$dkco/openwa/.env"
```

El contenedor arregla la propiedad de `./data` en cada arranque (su entrypoint
corre como root y luego baja al usuario `openwa` con `gosu`), así que no hace
falta un `chown` manual del bind mount.

---

## 5. Validar antes de levantar

```bash
dk openwa
svc config openwa
```

La salida debe mostrar:

- `ghcr.io/rmyndharis/openwa:0.23.5`.
- `container_name: openwa`.
- `db_net` externa.
- Puerto `2785:2785`.
- `read_only: true`, `tmpfs` con `/tmp`, `cap_add` con las cinco capabilities.
- `env_file` global y local.
- `API_MASTER_KEY` interpolada (no vacía).

No levantes si aparece `cap_drop: [ALL]` sin `cap_add`, si falta el puerto, o si
`API_MASTER_KEY` quedó vacía.

---

## 6. Levantar y verificar

```bash
svc pull openwa
svc up openwa
svc ps openwa
svc logs openwa
```

`Ctrl-C` termina la vista de logs, no detiene el contenedor. Después:

```bash
svc health
svc port-map
```

Condiciones de aceptación:

- `openwa` está `Up (healthy)` (el healthcheck consulta
  `/api/health/ready`; `start_period` es 40s, dale un momento).
- `svc port-map` muestra `2785`.
- No hay reinicios repetidos.

Comprobación de la API desde el host (lee la clave del `.env`, no la imprime):

```bash
API_KEY="$(grep '^API_MASTER_KEY=' "$dkco/openwa/.env" | cut -d= -f2-)"
curl -s -H "X-API-Key: $API_KEY" http://127.0.0.1:2785/api/sessions
unset API_KEY
```

Debe responder JSON (una lista de sesiones, probablemente vacía al inicio).

---

## 7. API keys — cómo funcionan (LEER antes de conectar)

> Fuente: documentación oficial `docs.open-wa.org` (v0.23.5) y
> `docs/04-security-design.md` del repo. Esta sección resume el modelo real de
> claves para evitar el error de "Invalid API key".

OpenWA maneja **dos tipos de clave**, y conviene no confundirlos:

| Tipo | De dónde sale | Formato | Uso |
|---|---|---|---|
| **Seed key** (`API_MASTER_KEY`) | La variable de tu `.env`, tomada **verbatim** (tal cual) | Lo que tú pongas | Clave de bootstrap/administración |
| **Key normal** | La crea OpenWA (primer arranque o desde el dashboard) y la guarda hasheada en `main.sqlite` | `owa_k1_<64 hex>` | Uso diario en API/dashboard/n8n |

Reglas oficiales que hay que respetar:

- El header **siempre** es `X-API-Key` (nunca en la URL ni como query param).
- En el **primer arranque** OpenWA imprime en el log una key nueva
  (`🔑 API Key (newly created)`). Esa key vive en `main.sqlite`.
- **`API_KEY_PEPPER` es sensible:** rotarlo o añadirlo **invalida el hash de
  TODAS las keys ya existentes** (doc oficial). Si defines el pepper *después*
  de que ya se sembró una key, esa key deja de validar → "Invalid API key".

### 7.1 Si aparece "Invalid API key" tras activar `API_KEY_PEPPER`

Es el caso más común. Causa: la key se sembró antes del pepper. Solución limpia
(re-sembrar las keys; NO borra sesiones de WhatsApp, que viven en `openwa.sqlite`
y `sessions/`):

```bash
dk openwa
svc stop openwa

# Backup de la DB de auth por si acaso
cp "$dkco/openwa/data/main.sqlite" "$dkco/openwa/data/main.sqlite.bak"

# Borrar SOLO la DB de auth (se recrea con el pepper ya activo)
rm -f "$dkco/openwa/data/main.sqlite"

# Poner una API_MASTER_KEY nueva y limpia (no reutilizar la del log)
ENV_FILE="$dkco/openwa/.env"
( umask 077; sed -i "s/^API_MASTER_KEY=.*/API_MASTER_KEY=$(openssl rand -hex 32)/" "$ENV_FILE" )
unset ENV_FILE
chmod 600 "$dkco/openwa/.env"

svc up openwa
svc logs openwa      # copia la key nueva del bloque "🔑 API Key (newly created)"
```

Verifica cuál valida:

```bash
API_KEY="$(grep '^API_MASTER_KEY=' "$dkco/openwa/.env" | cut -d= -f2-)"
curl -s -o /dev/null -w "HTTP %{http_code}\n" -H "X-API-Key: $API_KEY" http://127.0.0.1:2785/api/sessions
unset API_KEY
```

`HTTP 200` → usa esa `API_MASTER_KEY` en el campo "Clave API" del dashboard. Si
da `401`, usa la key `newly created` que salió en el log.

---

## 8. Conectar un número de WhatsApp

Hay dos métodos oficiales: **QR** (recomendado) y **pairing-code** (por número).

> ⚠️ **CRÍTICO — la API usa el `id` (UUID) de la sesión en las URLs, NO el
> `name`.** Confirmado en runtime: usar el name da
> `Validation failed (uuid is expected)`. El `name` solo se usa al **crear** la
> sesión (`POST /api/sessions`); a partir de ahí, todas las rutas
> `/api/sessions/{sessionId}/...` esperan el UUID que devuelve esa creación (o
> el campo `id` de `GET /api/sessions`).

Patrón recomendado: resolver el UUID a una variable a partir del `name`:

```bash
API_KEY="$(grep '^API_MASTER_KEY=' "$dkco/openwa/.env" | cut -d= -f2-)"
SID="$(curl -s http://127.0.0.1:2785/api/sessions -H "X-API-Key: $API_KEY" \
  | python3 -c "import sys,json; print(next(s['id'] for s in json.load(sys.stdin) if s['name']=='prueba'))")"
echo "$SID"   # p.ej. 3db78128-6aa9-4355-85c2-91235dc512ed
```

### 8.1 Por el dashboard (recomendado)

1. Abre `http://${SERVER_IP}:2785` y entra con la API key (sección 7).
2. Crea una sesión, arráncala y **escanea el QR** con el número dedicado
   (WhatsApp → Dispositivos vinculados → Vincular dispositivo).

### 8.2 Por API — flujo oficial con estado `qr_ready`

El estado correcto a esperar es **`qr_ready`** (no `ready` todavía). Fuente:
`docs/examples/session-phone-number-pairing.md`. Se crea con el `name`, luego se
opera con `$SID` (UUID).

```bash
API_KEY="$(grep '^API_MASTER_KEY=' "$dkco/openwa/.env" | cut -d= -f2-)"

# 1. Crear sesión (requiere "name"); DEVUELVE el id — guárdalo
curl -s -X POST http://127.0.0.1:2785/api/sessions \
  -H "Content-Type: application/json" -H "X-API-Key: $API_KEY" \
  -d '{"name":"prueba"}'

# 2. Resolver el UUID a $SID (ver patrón arriba)
SID="$(curl -s http://127.0.0.1:2785/api/sessions -H "X-API-Key: $API_KEY" \
  | python3 -c "import sys,json; print(next(s['id'] for s in json.load(sys.stdin) if s['name']=='prueba'))")"

# 3. Arrancar la sesión (por UUID)
curl -s -X POST "http://127.0.0.1:2785/api/sessions/$SID/start" -H "X-API-Key: $API_KEY"

# 4. Esperar hasta status == qr_ready (y engineLoaded == true)
curl -s "http://127.0.0.1:2785/api/sessions/$SID" -H "X-API-Key: $API_KEY"

# 5. Obtener el QR
curl -s "http://127.0.0.1:2785/api/sessions/$SID/qr" -H "X-API-Key: $API_KEY"

unset API_KEY SID
```

### 8.3 Alternativa: pairing-code (vincular por número, sin QR)

Solo cuando `status` sea `qr_ready` (usa `$SID`, no el name):

```bash
curl -s -X POST "http://127.0.0.1:2785/api/sessions/$SID/pairing-code" \
  -H "Content-Type: application/json" -H "X-API-Key: $API_KEY" \
  -d '{"phoneNumber":"34600111222"}'
```

Devuelve un código de 8 caracteres. En el teléfono: WhatsApp → Ajustes →
Dispositivos vinculados → **Vincular con número de teléfono** → introducir el
código. `phoneNumber` = dígitos en formato internacional, sin `+`, espacios ni
guiones.

> ⚠️ **whatsapp-web.js:** pedir pairing-code para un número que YA tiene una
> sesión vinculada puede hacer que WhatsApp **desvincule** ese dispositivo. Si
> una sesión de ese número debe seguir viva, vincula la nueva por QR. (Baileys
> no se ve afectado.)

Cuando el número queda vinculado, `status` pasa a `ready`.

### 8.4 Enviar un mensaje (por API)

`chatId` = número internacional sin `+`, sufijo `@c.us` (individual) o `@g.us`
(grupo). `SendTextMessageDto` requiere `chatId` y `text`. Usa `$SID`:

```bash
API_KEY="$(grep '^API_MASTER_KEY=' "$dkco/openwa/.env" | cut -d= -f2-)"
SID="$(curl -s http://127.0.0.1:2785/api/sessions -H "X-API-Key: $API_KEY" \
  | python3 -c "import sys,json; print(next(s['id'] for s in json.load(sys.stdin) if s['name']=='prueba'))")"

curl -s -X POST "http://127.0.0.1:2785/api/sessions/$SID/messages/send-text" \
  -H "Content-Type: application/json" -H "X-API-Key: $API_KEY" \
  -d '{"chatId":"34600111222@c.us","text":"Hola desde OpenWA"}'

unset API_KEY SID
```

Respuesta OK: `{"messageId":"...","timestamp":...}`. Un `messageId` con sufijo
`_out` confirma que el mensaje salió.

> La sesión debe estar activa. Si sale `Session ... is not active` o
> `Session is not started`, arráncala con `POST /api/sessions/$SID/start`.

### 8.5 Envío rápido con `wa-send.sh`

Para no repetir el `curl` ni resolver el UUID a mano, el servicio incluye un
script que hace todo (resuelve name→id, lee la key sin imprimirla, `unset` al
final). Se despliega junto al servicio:

```bash
# Instalación (una vez), tras crear la carpeta del servicio:
cp "$NAS_DOTFILES/agent/catalog/services/openwa/wa-send.sh" "$dkco/openwa/wa-send.sh"
chmod 700 "$dkco/openwa/wa-send.sh"
```

Uso:

```bash
dk openwa
./wa-send.sh prueba 34600111222 "Hola desde el NAS"
#            ^sesión  ^número      ^mensaje
```

- Añade `@c.us` automáticamente si el número no trae sufijo (respeta `@g.us` /
  `@lid` si los pones).
- Variables opcionales: `OPENWA_URL` (default `http://127.0.0.1:2785`) y
  `OPENWA_ENV_FILE` (default `$dkco/openwa/.env`).

---

## 9. Integración con n8n (nodo oficial)

OpenWA publica un **nodo de comunidad oficial** para n8n, así que no hay que
armar los webhooks a mano (fuente: `docs/22-n8n-integration.md` del repo).

### 9.1 Instalar el nodo en n8n

1. En n8n: **Settings → Community Nodes → Install**.
2. Paquete: `@rmyndharis/n8n-nodes-openwa`.
3. Acepta el aviso e instala. Reinicia n8n si te lo pide (`svc restart n8n`).

### 9.2 Credenciales del nodo

| Campo | Valor |
|---|---|
| Server URL | `http://openwa:2785` (sin `/api`, sin barra final) |
| API Key | el valor de `API_MASTER_KEY` de `$dkco/openwa/.env` |

`http://openwa:2785` funciona porque n8n y OpenWA comparten `db_net`. No uses
`localhost` ni `${SERVER_IP}` desde el nodo.

### 9.2.1 ⚠️ REQUISITO: permitir el host de n8n en el guard anti-SSRF

**Sin este paso, el Trigger de n8n falla** con
`400 Bad Request: Destination address is not allowed`.

OpenWA valida la URL de destino del webhook **al registrarlo** (no solo al
entregar) y, con la protección SSRF activa por defecto, **rechaza direcciones
privadas/internas**. n8n construye la URL del webhook desde su
`WEBHOOK_URL` (en este NAS: `http://${SERVER_IP}:5678`), que es una IP privada
de la LAN → OpenWA la bloquea. Fuente oficial:
`docs/06-api-specification.md` (validación de webhooks en registro;
`WEBHOOK_SSRF_PROTECT` / `SSRF_ALLOWED_HOSTS`).

Solución: el compose del catálogo incluye `SSRF_ALLOWED_HOSTS: ${SERVER_IP}`
en el `environment:`. Debe estar presente antes de usar el Trigger:

```bash
grep -n "SSRF_ALLOWED_HOSTS" "$dkco/openwa/compose.yml"
# Si falta, añadirlo al environment: y recrear
svc config openwa      # verificar SSRF_ALLOWED_HOSTS: 192.168.1.200 interpolado
svc recreate openwa
```

> Alternativa (más "pura" pero con efectos colaterales): cambiar el
> `WEBHOOK_URL` de n8n a `http://n8n:5678` para que el webhook use la red interna
> Docker. No se eligió porque `WEBHOOK_URL` afecta a TODOS los webhooks de n8n
> (incluidos los que se llaman desde fuera de la LAN).

### 9.3 Nodos disponibles

- **OpenWA** — ejecuta acciones: enviar texto/imagen/documento/ubicación,
  comprobar si un número existe, gestionar webhooks, etc.
- **OpenWA Trigger** — arranca workflows con eventos de WhatsApp
  (`message.received`, `session.status`, `session.disconnected`, etc.). Crea y
  borra el webhook en OpenWA automáticamente al activar/desactivar el workflow.

### 9.4 Nota sobre el Trigger

Cuando uses el nodo Trigger, **activa el workflow** y deja que registre la URL
de producción del webhook. La URL de test de n8n solo recibe un evento y luego
deja de escuchar. Para deduplicar reintentos, añade un paso keyed en
`idempotencyKey` (viene en el body y en la cabecera `X-OpenWA-Idempotency-Key`).

El campo **"Session Name or ID"** de los nodos es un desplegable que lista tus
sesiones y usa el **UUID** internamente: eliges el name y el nodo pone el id
correcto. Esto evita el error `uuid is expected` — con el nodo NO hay que
resolver el UUID a mano (a diferencia de las llamadas curl de la §8). El campo
del texto en `Message → Send Text` se llama **Message** (no "Text").

### 9.5 ⚠️ Gotcha del scope del paquete (importante)

El paquete oficial es **con scope**: `@rmyndharis/n8n-nodes-openwa`. Los tipos de
nodo internos son `@rmyndharis/n8n-nodes-openwa.openWa` y
`@rmyndharis/n8n-nodes-openwa.openWaTrigger`.

Si un workflow JSON trae el tipo SIN el scope (`n8n-nodes-openwa.*`), al
importarlo n8n intenta instalar un **segundo paquete** con ese nombre y quedan
DOS paquetes duplicados en conflicto (síntomas: al editar un nodo pide
"instalar" aunque ya esté instalado, y el workflow da `Bad request`). Solución:
Settings → Community Nodes → desinstalar el duplicado sin scope y dejar solo
`@rmyndharis/n8n-nodes-openwa`; usar JSON con el tipo correcto (con scope).

### 9.6 Workflows de ejemplo (JSON para importar)

En el catálogo hay flujos listos para importar, con los tipos de nodo correctos:

```text
agent/catalog/services/openwa/n8n-flows/
├── README.md          ← instrucciones de import y ajustes
├── auto-reply.json    ← recibe → si contiene "hola" → responde
└── echo-simple.json   ← recibe cualquier mensaje → responde con eco
```

Importar: n8n → menú **⋮** → **Import from File / Clipboard**. Tras importar,
en cada nodo OpenWA seleccionar la credencial **OpenWA API** y elegir la sesión
en el desplegable (los placeholders `REEMPLAZA_ID_CREDENCIAL` y el UUID se
sustituyen así). Ver el README de la carpeta para el detalle.

---

## 10. Registrar en el arranque escalonado

OpenWA no depende de DataSQL (usa SQLite), pero comparte `db_net` y encaja bien
junto a n8n. Añádelo a `$dkco/scripts/layers.conf` en la **Capa 2**
(consumidores independientes), después de n8n:

```text
# Capa 2 — Consumidores de DataSQL (Compose independiente)
homeassistant
n8n
openwa
flowise
lobehub
```

> Con `BOOT_ORDER_REQUIRE_ALL=1` (default), un compose presente en `$dkco` que
> falte en `layers.conf` **hace fallar el arranque**. Al eliminar el servicio,
> quita también su línea.

Para dejarlo fuera del boot temporalmente sin borrarlo: `svc no-boot openwa`
(revertir con `svc boot-enable openwa`).

---

## 11. Generar documentación en cascada

```bash
svc catalog-sync openwa
```

---

## 12. Operación y mantenimiento

### Estado y diagnóstico

```bash
svc health
svc ps openwa
svc stats openwa
svc logs openwa
svc port-map
```

### Operaciones normales

```bash
svc restart openwa
svc recreate openwa            # recrear sin pull (cambió la config)
svc update openwa              # pull + recrear (actualizar imagen)
```

Al actualizar la imagen, cambia el tag pineado en `compose.yml`
(`ghcr.io/rmyndharis/openwa:<nueva>`) en vez de usar `latest`, y verifica que
las sesiones existentes reconecten tras el cambio.

### Backup

Los datos críticos (sesiones de WhatsApp, DB SQLite, media, plugins) viven en
`./data`. Es `backup_critical`:

```bash
svc backup openwa
```

Restaurar una sesión sobre una imagen de Chromium más nueva puede invalidar el
IndexedDB; si actualizas un major del navegador y algo falla, restaura `./data`
desde el backup.

---

## 13. Errores comunes

| Síntoma | Causa | Solución |
|---|---|---|
| El contenedor no arranca, Chromium crashea | Se aplicó `cap_drop: [ALL]` sin `cap_add`, o se quitó `read_only`/`tmpfs` | Restaurar el bloque de hardening del compose del catálogo |
| `401 Unauthorized` en la API | Falta o no coincide la cabecera `X-API-Key` | Enviar `X-API-Key: <API_MASTER_KEY>` |
| n8n no alcanza OpenWA | Se usó `localhost` o `${SERVER_IP}` en el nodo | Usar `http://openwa:2785` (ambos en `db_net`) |
| Trigger n8n: `Bad request — Destination address is not allowed` | El guard anti-SSRF de OpenWA rechaza el webhook a la IP privada de n8n | Añadir `SSRF_ALLOWED_HOSTS: ${SERVER_IP}` al `environment:` del compose y `svc recreate openwa` (ver §9.2.1) |
| Trigger no llega y probabas escribiendo tú | `message.received` solo se dispara con mensajes de OTROS | Probar desde OTRO número; `fromMe:false` en el payload |
| Activaste el filtro y no llegan mensajes de grupo | Filtro `isGroup=false` descarta grupos | Vaciar Filters (recibe todo) o ajustar la condición |
| El Trigger de n8n recibe un evento y calla | Se registró la URL de test, no la de producción | Activar el workflow y usar la URL de producción |
| Healthcheck en `starting` mucho tiempo | Primer arranque de Chromium es lento | Esperar el `start_period` (40s) y revisar `svc logs openwa` |
| `Validation failed (uuid is expected)` | Se usó el `name` de la sesión en la URL | Usar el `id` (UUID) — ver §8, resolver name→id con `GET /api/sessions` |
| `Session '<x>' is not active` / `is not started` | El motor de la sesión no está corriendo | `POST /api/sessions/$SID/start` y esperar unos segundos |
| El QR no aparece | La sesión no se arrancó | `POST /api/sessions/$SID/start` (por UUID) y luego `GET .../qr` |
| Dashboard se ve **en blanco** por HTTP | CSP fuerza `https://` en los assets | `CSP_UPGRADE_INSECURE_REQUESTS=false` (ya en el compose) |
| Peticiones del navegador bloqueadas (CORS) | Falta el origen permitido | `CORS_ORIGINS=http://${SERVER_IP}:2785` (ya en el compose) |
| Aviso `API_KEY_PEPPER is not set` | Las keys se guardan con SHA-256 plano | Definir `API_KEY_PEPPER` y re-emitir las keys |
| Tras poner/cambiar `API_KEY_PEPPER`, las keys dan 401/Invalid | El pepper cambia el hash de todas las keys | Re-sembrar: borrar `data/main.sqlite` (backup antes) y recrear — ver §7.1 |
| `Invalid API key` en el dashboard | La key se sembró antes del pepper | Re-sembrar la DB de auth (§7.1) o usar la key `newly created` del log |
| Aparece una API key en los logs del primer arranque | OpenWA crea una key inicial en la DB y la imprime | Revocarla desde el dashboard; usar tu `API_MASTER_KEY` |
| `chatId` con `@lid` no envía bien | El `@lid` es un id de privacidad, no el número | Iniciar envíos con `<numero>@c.us` (número internacional sin `+`) |
| `send-image` da 500 `Data passed to getter must include an id property` | Bug de media en `whatsapp-web.js` con la versión actual de WA Web | Cambiar a `ENGINE_TYPE=baileys` y re-escanear QR (§14) |
| Enviar imagen a tu PROPIO número (self-chat) falla | whatsapp-web.js/baileys no resuelven bien el self-chat para media | Enviar a un número destino DISTINTO del vinculado |
| `send-image` por URL da `Destination address is not allowed` | El SSRF guard bloquea el fetch de la imagen externa | Usar `base64`/binario, o ampliar `SSRF_ALLOWED_HOSTS` con el host de la imagen |
| `svc logs openwa` se queda colgado / imprime cientos de líneas | Hace follow y OpenWA loguea ~200 rutas al arrancar | `docker logs --tail 300 openwa 2>&1 \| grep -iE "ready\|error\|qr" \| tail -20` |

---

## 14. Envío de imágenes / cámaras de Home Assistant

Verificado en runtime. Para enviar imágenes (p.ej. una cámara de HA a WhatsApp):

1. **Motor `baileys` obligatorio.** `whatsapp-web.js` falla al enviar media con
   la versión actual de WhatsApp Web (error `Data passed to getter must include
   an id property`). El texto funciona en ambos; solo el media falla en wweb.js.
   Cambiar el motor obliga a re-escanear el QR.
2. **Fuente de la imagen:** usar **binario** o **base64**, NO una URL externa —
   el guard SSRF bloquea el fetch de URLs externas (`Destination address is not
   allowed`) salvo que se añada ese host a `SSRF_ALLOWED_HOSTS`.
3. **Destino:** enviar a un número **distinto** del vinculado. Enviarte media a
   tu propio número (self-chat) falla.

Prueba directa por API (base64, a un número real distinto del vinculado):

```bash
API_KEY="$(grep '^API_MASTER_KEY=' "$dkco/openwa/.env" | cut -d= -f2-)"
SID="<UUID_de_la_sesion>"
B64="iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
curl -s -X POST "http://127.0.0.1:2785/api/sessions/$SID/messages/send-image" \
  -H "Content-Type: application/json" -H "X-API-Key: $API_KEY" \
  -d "{\"chatId\":\"<NUMERO_REAL>@c.us\",\"base64\":\"$B64\",\"mimetype\":\"image/png\",\"caption\":\"prueba\"}"
echo ""
unset API_KEY SID B64
```

Respuesta OK: `{"messageId":"...","timestamp":...}` (con baileys, sin sufijo
`_lid`) y la imagen llega al número.

### Flujo n8n "pide cámara" (WhatsApp → foto de HA)

Flujo de ejemplo en `agent/catalog/services/openwa/n8n-flows/pide-camara.json`:

```
[On message received] → [IF: ¿"camara"?] → [HA: Camera Proxy screenshot] → [OpenWA: Send Image]
```

- **HA: Camera Proxy** (nodo `Home Assistant`, operación *Get the camera
  screenshot*) devuelve la imagen como binario en la propiedad `data`.
  Credencial: URL `http://${SERVER_IP}:8123` + token de larga duración de HA.
- **OpenWA: Send Image**: `Image Source = Binary Data`, `Binary Property = data`.
  - **Chat Name or ID:** para recibir la foto en un número fijo, poner
    `<TU_NUMERO>@c.us` (no el `@lid` del remitente, y no el número vinculado).
  - **Vaciar** `Quoted Message ID` y `Mentions` (los valores de ejemplo rompen
    el envío).
- Al importar el JSON, seleccionar a mano las credenciales OpenWA y HA, y la
  sesión; el nodo no las vincula solo.

---

## docs_url

Ficha del catálogo: `agent/catalog/services/openwa/ficha.md`
