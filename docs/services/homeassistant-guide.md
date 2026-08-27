# Home Assistant — Guía Operativa

> **Puerto:** 8123  
> **Imagen:** ghcr.io/home-assistant/home-assistant:stable  
> **Red:** host (acceso directo al stack de red del NAS)  
> **Tipo:** Docker container (privileged)
> **Base de datos:** `homeassistant_db` en PostgreSQL de DataSQL, mediante `127.0.0.1:5432`

Esta guía incorpora la configuración real compartida en la [guía de Home Assistant del usuario](https://gist.github.com/ydiaz1699/ad4f9c92edd8669d720b8865c82a73ed), adaptada a las reglas actuales de `nas-dotfiles`: operaciones Docker mediante `svc`, credenciales leídas sin `source .env`, acceso LAN mediante `${SERVER_IP}` y publicación PostgreSQL limitada al loopback. La guía compartida mostraba `192.168.0.200` en algunos ejemplos; no se copia esa IP porque el NAS documentado usa `SERVER_IP` (`192.168.1.200` en la configuración actual).

---

## Índice

1. [Estructura de archivos](#estructura-de-archivos)
2. [Compose](#compose)
3. [Primer inicio y onboarding](#primer-inicio-y-onboarding)
4. [Conectar Home Assistant a DataSQL](#conectar-home-assistant-a-datasql--procedimiento-completo)
5. [Verificación y operación diaria](#verificación-y-operación-diaria)
6. [Organización con includes](#organización-con-includes)
7. [Integración con ntfy (notificaciones push)](#integración-con-ntfy)
8. [Automatización: Cámara → snapshot → ntfy](#automatización-cámara--snapshot--ntfy)
9. [TvOverlay (notificaciones en TV)](#tvoverlay)
10. [Troubleshooting](#troubleshooting)

---

## Estructura de archivos

```
$dkco/homeassistant/
├── compose.yml
├── .env                            ← HOMEASSISTANT_TOKEN (para Homepage widget)
└── data/                           ← montado como /config dentro del contenedor
    ├── configuration.yaml          ← config principal (con !includes)
    ├── automations.yaml            ← automatizaciones
    ├── scripts.yaml
    ├── scenes.yaml
    ├── includes/                   ← configs separadas por tema
    │   ├── shell_commands.yaml     ← ntfy, utilidades
    │   ├── tvoverlay_commands.yaml ← TvOverlay (rest_command)
    │   └── notify.yaml            ← plataformas de notificación
    └── www/
        └── snapshots/              ← imágenes de cámara (temporales)
            └── alarma.jpg          ← se sobreescribe en cada detección
```

**Ruta del contenedor → Host:**
- `/config` dentro de HA = `$dkco/homeassistant/data/` en el NAS
- `/config/www/` = `$dkco/homeassistant/data/www/` = accesible como `http://IP:8123/local/`

---

## Compose

```yaml
# $dkco/homeassistant/compose.yml
services:
  homeassistant:
    image: ghcr.io/home-assistant/home-assistant:stable
    container_name: homeassistant
    restart: unless-stopped
    network_mode: host
    stop_grace_period: 60s
    dns:
      - 190.104.12.42
      - 200.73.96.146
      - 8.8.8.8
    privileged: true
    env_file:
      - ../.env
      - .env
    volumes:
      - ./data:/config
      - /etc/localtime:/etc/localtime:ro
      - /run/dbus:/run/dbus:ro
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8123"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 60s
    labels:
      - homepage.group=IoT
      - homepage.name=Home Assistant
      - homepage.icon=home-assistant
      - homepage.href=http://${SERVER_IP}:8123
      - homepage.description=Automatización del hogar
      - homepage.widget.type=homeassistant
      - homepage.widget.url=http://${SERVER_IP}:8123
      - homepage.widget.key=${HOMEASSISTANT_TOKEN}
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 512M
```

**Notas del compose:**
- `env_file: [../.env, .env]` — hereda SERVER_IP y TZ del global, secretos del local
- `network_mode: host` — HA accede directo a la LAN (necesario para mDNS, descubrimiento IoT)
- `privileged: true` — acceso a USB, Bluetooth, dbus (necesario para integraciones hardware)
- `dns` personalizado — evita depender de AdGuard para resolver (si AdGuard cae, HA sigue)
- La relación entre este DNS explícito, `systemd-resolved`, IPv6, Avahi y descubrimiento se documenta en [`docker-nas/references/networking.md`](../../docker-nas/references/networking.md); no asumir que `network_mode: host` hace que HA use automáticamente el stub del host
- `stop_grace_period: 60s` — tiempo para guardar estado al apagar
- Homepage labels — usa `${SERVER_IP}` (nunca IP hardcodeada)
- **NO** tiene `environment: TZ` — se hereda del `.env` global

---

## Primer inicio y onboarding

DataSQL debe estar disponible antes de iniciar Home Assistant. Como los Compose
son independientes, `depends_on` no puede ordenar esta dependencia.

Primero comprueba el stack, pero **no levantes HA desde esta sección**:

```bash
svc health
svc ps datasql
```

Continúa en la sección `Conectar Home Assistant a DataSQL — procedimiento
completo`. Su orden canónico es: comprobar DataSQL, crear y verificar
`homeassistant_db`/`ha_user`, iniciar HA, completar el onboarding, configurar el
Recorder y reiniciar para verificarlo. Así se evita iniciar HA con una base
inexistente o configurar el Recorder antes de que HA cree su configuración.

La configuración canónica usa `dns` explícitos, `stop_grace_period: 60s`,
`privileged: true`, el bind `./data:/config`, healthcheck HTTP y labels de
Homepage con `${SERVER_IP}`. `network_mode: host` hace innecesario declarar
`networks`; también explica por qué HA accede al Recorder mediante el loopback
del NAS y no mediante el hostname Docker `datapostgres`.

---

## Conectar Home Assistant a DataSQL — procedimiento completo

Esta sección une la información de Home Assistant y DataSQL en un único flujo.
No es necesario usar pgAdmin para crear la base ni el usuario: la ruta
principal es la terminal del NAS con `svc exec`.

### 1. Contexto de conexión

Home Assistant usa `network_mode: host`. Por eso:

- No pertenece a `db_net`.
- No puede usar `datapostgres` como hostname Docker.
- No debe usar la IP histórica `172.20.0.4`.
- Debe usar `127.0.0.1` y el puerto publicado realmente por DataSQL.

El catálogo actual usa `127.0.0.1:5432:5432` por defecto, pero el `.env` y el
compose instalados en el NAS son la autoridad. Comprueba el puerto antes de
escribir `db_url`:

```bash
dk datasql

HA_PG_PORT="$(awk -F= '$1=="AIPG_POSTGRES_HOST_PORT"{print $2}' "$dkco/datasql/.env")"
HA_PG_PORT="${HA_PG_PORT:-5432}"
printf 'Puerto PostgreSQL para Home Assistant: 127.0.0.1:%s\n' "$HA_PG_PORT"

if ! ss -ltn | grep -Eq "127\.0\.0\.1:${HA_PG_PORT}([[:space:]]|:)"; then
  printf 'No se detecta PostgreSQL escuchando en 127.0.0.1:%s.\n' "$HA_PG_PORT" >&2
  unset HA_PG_PORT
  exit 1
fi
```

Si el resultado es `5432`, el `db_url` usará `127.0.0.1:5432`. Si el NAS
mantiene una coexistencia histórica en `5433`, usa `127.0.0.1:5433`; no
sustituyas el valor por intuición.

### 2. Comprobar DataSQL

```bash
svc health
svc ps datasql
svc net
```

Continúa solo si `datapostgres` está `healthy` y `db_net` existe. No levantes
Home Assistant todavía si PostgreSQL no está saludable.

### 3. Cargar las credenciales administrativas

```bash
PG_ADMIN_PASSWORD="$(awk -F= '$1=="POSTGRES_PASSWORD"{print substr($0,index($0,"=")+1)}' "$dkco/datasql/.env")"
PG_ADMIN_USER="$(awk -F= '$1=="POSTGRES_USER"{print substr($0,index($0,"=")+1)}' "$dkco/datasql/.env")"
PG_ADMIN_DB="$(awk -F= '$1=="POSTGRES_DB"{print substr($0,index($0,"=")+1)}' "$dkco/datasql/.env")"

if [[ -z "$PG_ADMIN_PASSWORD" || -z "$PG_ADMIN_USER" || -z "$PG_ADMIN_DB" ]]; then
  printf 'Falta una variable administrativa en %s/.env.\n' "$dkco/datasql" >&2
  unset PG_ADMIN_PASSWORD PG_ADMIN_USER PG_ADMIN_DB HA_PG_PORT
  exit 1
fi
```

No ejecutes `source .env`, no uses `docker exec` y no pegues estas variables en
el chat.

### 4. Crear el rol dedicado de Home Assistant

Genera una contraseña hexadecimal en el terminal y consérvala localmente para
introducirla en `\password` y después en `data/secrets.yaml`:

```bash
openssl rand -hex 32
```

No pegues ese valor en el chat, en el repositorio ni en el historial. Si
`openssl` no está disponible, detente y usa el gestor de secretos habitual para
generar una contraseña hexadecimal equivalente.

El CLI `svc exec` del NAS puede interpretar opciones como `-U`, `-d` y `-c`
como opciones propias. Por eso se pasan `PGUSER` y `PGDATABASE` mediante
`env`, y las consultas se escriben dentro de `psql`:

```bash
svc exec datasql postgres \
  env PGPASSWORD="$PG_ADMIN_PASSWORD" \
      PGUSER="$PG_ADMIN_USER" \
      PGDATABASE="$PG_ADMIN_DB" \
  psql
```

Dentro de `psql` ejecuta:

```sql
CREATE ROLE ha_user LOGIN;
\password ha_user
```

Introduce dos veces la contraseña dedicada de Home Assistant. Después sal:

```text
\q
```

`\password` evita escribir la contraseña en el SQL o en el historial del
comando. Si `CREATE ROLE` responde que `ha_user` ya existe, no ejecutes
`\password` automáticamente: detente, conserva la contraseña que ya tengas y
consulta el estado antes de cambiarla.

### 5. Crear la base y comprobar que fue creada

`CREATE DATABASE` se ejecuta en una sesión separada porque no puede ejecutarse
dentro de una transacción:

```bash
svc exec datasql postgres \
  env PGPASSWORD="$PG_ADMIN_PASSWORD" \
      PGUSER="$PG_ADMIN_USER" \
      PGDATABASE="$PG_ADMIN_DB" \
  psql
```

Dentro de `psql` ejecuta:

```sql
CREATE DATABASE homeassistant_db OWNER ha_user;
```

La salida esperada es:

```text
CREATE DATABASE
```

Después verifica inmediatamente la base y su propietario, todavía dentro de
`psql`:

```sql
SELECT datname,
       pg_get_userbyid(datdba) AS owner
FROM pg_database
WHERE datname = 'homeassistant_db';
```

La salida debe mostrar `homeassistant_db` con propietario `ha_user`. Después
sal:

```text
\q
```

Si `CREATE DATABASE` responde que la base ya existe, no la recrees. Ejecuta
solo la consulta `SELECT` anterior y confirma que el propietario sea `ha_user`.
Si el propietario es diferente, detente antes de modificarlo.

### 6. Verificar el acceso con `ha_user`

Introduce temporalmente la contraseña dedicada:

```bash
read -r -s -p 'Contraseña de ha_user para verificar: ' HA_DB_PASSWORD
printf '\n'
```

Abre `psql` usando el rol y la base de Home Assistant:

```bash
svc exec datasql postgres \
  env PGPASSWORD="$HA_DB_PASSWORD" \
      PGUSER=ha_user \
      PGDATABASE=homeassistant_db \
  psql
```

Dentro ejecuta:

```sql
SELECT current_user, current_database();
```

El resultado esperado es:

```text
 current_user | current_database
--------------+------------------
 ha_user      | homeassistant_db
```

Después sal:

```text
\q
```

Si esta prueba falla, no configures todavía Home Assistant. El problema debe
resolverse primero en PostgreSQL, el rol, la contraseña o el propietario de la
base. Conserva `HA_DB_PASSWORD` solo hasta crear el secreto local de HA.

### 7. Iniciar Home Assistant y completar el onboarding

La primera ejecución debe crear la configuración inicial de HA antes de editar
el Recorder:

```bash
dk homeassistant
svc config homeassistant
svc up homeassistant
svc ps homeassistant
svc logs homeassistant
```

Abre `http://${SERVER_IP}:8123` y completa el onboarding. No edites
`configuration.yaml` antes de terminarlo.

### 8. Configurar el Recorder después del onboarding

Comprueba que exista el directorio antes de crear o proteger archivos:

```bash
dk homeassistant
mkdir -p data
touch data/secrets.yaml
chmod 600 data/secrets.yaml
```

Edita `data/secrets.yaml` y agrega el valor real localmente. Sustituye
`CONTRASEÑA_HEX` por la contraseña de `ha_user` y `PUERTO_HOST` por el valor
real de `HA_PG_PORT` (`5432` en la instalación final documentada):

```yaml
recorder_db_url: postgresql://ha_user:CONTRASEÑA_HEX@127.0.0.1:PUERTO_HOST/homeassistant_db
```

El formato hexadecimal evita caracteres que necesiten URL encoding. Si la
contraseña elegida contiene caracteres reservados (`@`, `:`, `/`, `#`, `%`),
debe codificarse antes de colocarla en la URI.

En `data/configuration.yaml`, agrega el bloque solo si no existe ya otra clave
`recorder:`:

```yaml
recorder:
  db_url: !secret recorder_db_url
  purge_keep_days: 10
  auto_purge: true
  commit_interval: 1
```

No dupliques `recorder:` si ya existe una configuración del Recorder. En ese
caso, modifica el bloque existente conservando una sola definición.

Después de guardar los archivos, elimina las contraseñas temporales y reinicia:

```bash
unset PG_ADMIN_PASSWORD PG_ADMIN_USER PG_ADMIN_DB HA_DB_PASSWORD HA_PG_PORT
svc restart homeassistant
svc ps homeassistant
svc logs homeassistant
```

El contenedor oficial de Home Assistant debe proporcionar el soporte necesario
para PostgreSQL. No instales paquetes dentro del contenedor sin que los logs
muestren explícitamente un error de driver; si aparece, detén el cambio y
registra el mensaje exacto.

### 9. Verificar la conexión desde Home Assistant

```bash
curl -s -o /dev/null -w '%{http_code}\n' "http://${SERVER_IP}:8123"
svc ps homeassistant
svc logs homeassistant
```

Cuando HA haya generado estados, consulta la base con la cuenta administrativa.
Como el CLI `svc exec` puede interpretar `-U`, `-d` y `-c`, esta verificación
usa variables de conexión y una sesión interactiva de `psql`:

```bash
PG_ADMIN_PASSWORD="$(awk -F= '$1=="POSTGRES_PASSWORD"{print substr($0,index($0,"=")+1); exit}' "$dkco/datasql/.env")"
PG_ADMIN_USER="$(awk -F= '$1=="POSTGRES_USER"{print substr($0,index($0,"=")+1); exit}' "$dkco/datasql/.env")"

svc exec datasql postgres \
  env PGPASSWORD="$PG_ADMIN_PASSWORD" \
      PGUSER="$PG_ADMIN_USER" \
      PGDATABASE=homeassistant_db \
  psql
```

Dentro de `psql` ejecuta:

```sql
SELECT COUNT(*) AS states_count FROM states;
```

Después sal:

```text
\q
```

Limpia las variables:

```bash
unset PG_ADMIN_PASSWORD PG_ADMIN_USER
```

Un resultado mayor que cero confirma que el Recorder está escribiendo estados.
El healthcheck HTTP por sí solo no confirma la conexión a PostgreSQL.

---

### Detalles técnicos del Recorder

Home Assistant conserva `network_mode: host` para mDNS, descubrimiento IoT,
USB y Bluetooth. Por eso no pertenece a `db_net` y debe usar el puerto loopback
real de DataSQL. Los consumidores Docker sí usan `datapostgres:5432` dentro de
`db_net`.

Los Compose son independientes: no uses `depends_on` para ordenar HA respecto a
DataSQL. El orden operativo es DataSQL saludable → base/rol dedicados →
onboarding de HA → Recorder → reinicio y verificación funcional.

---

## Verificación y operación diaria

Después de reiniciar HA y esperar aproximadamente 30 segundos:

```bash
svc ps homeassistant
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8123
svc logs homeassistant
```

El healthcheck HTTP confirma que la interfaz responde, pero no confirma por sí
solo la conexión del Recorder. La verificación funcional de PostgreSQL está en
la sección `9. Verificar la conexión desde Home Assistant`, donde se consulta
`states` usando `svc exec` con `PGUSER` y `PGDATABASE` para que el CLI no
interprete `-U`, `-d` o `-c` como opciones propias.

Las operaciones habituales son:

```bash
svc ps homeassistant
svc logs homeassistant
svc restart homeassistant
svc update homeassistant
svc stop homeassistant
```

El acceso LAN es `http://${SERVER_IP}:8123`; el acceso local para pruebas es
`http://127.0.0.1:8123`. Si HA reinicia en bucle y los logs no muestran el
motivo actual, deténlo con `svc stop homeassistant` y después consulta
`svc logs homeassistant` para aislar el arranque completo.

---

## Organización con includes

En vez de meter todo en `configuration.yaml` (que se vuelve enorme), usar `!include`:

### configuration.yaml (limpio)

```yaml
# Solo lo esencial + includes
homeassistant:
  name: Home
  unit_system: metric
  time_zone: America/La_Paz

# Includes organizados
shell_command: !include includes/shell_commands.yaml
rest_command: !include includes/tvoverlay_commands.yaml
notify: !include includes/notify.yaml

# Estos ya los genera HA automáticamente
automation: !include automations.yaml
script: !include scripts.yaml
scene: !include scenes.yaml
```

### Crear archivos includes

Desde el NAS (la ruta `$dkco/homeassistant/data/` es `/config` dentro de HA):

```bash
# Crear carpeta
mkdir -p $dkco/homeassistant/data/includes

# Crear shell_commands.yaml
cat > $dkco/homeassistant/data/includes/shell_commands.yaml << 'EOF'
# Shell Commands — ntfy + utilidades
ntfy_camara: >
  curl -s -H "Title: 🚨 Movimiento detectado"
  -H "Priority: 4"
  -H "Tags: warning,camera"
  -H "Filename: alarma.jpg"
  -T /config/www/snapshots/alarma.jpg
  http://192.168.1.200:8090/nas-alerts
EOF

# Crear tvoverlay_commands.yaml
cat > $dkco/homeassistant/data/includes/tvoverlay_commands.yaml << 'EOF'
tvoverlay_notify:
  url: "http://192.168.0.7:5001/notify"
  method: POST
  headers:
    Content-Type: "application/json"
  payload: >-
    {
      "id": "{{ id | default('') }}",
      "title": "{{ title | default('') }}",
      "message": "{{ message | default('') }}",
      "appTitle": "{{ appTitle | default('') }}",
      "smallIcon": "{{ smallIcon | default('mdi:bell') }}",
      "largeIcon": "{{ largeIcon | default('') }}",
      "color": "{{ color | default('#03A9F4') }}",
      "corner": "{{ corner | default('') }}",
      "duration": {{ duration | default(10) }},
      "image": "{{ image | default('') }}",
      "video": "{{ video | default('') }}"
    }

tvoverlay_notify_fixed:
  url: "http://192.168.1.50:5001/notify_fixed"
  method: POST
  headers:
    Content-Type: "application/json"
  payload: >-
    {
      "id": "{{ id | default('') }}",
      "visible": {{ visible | default(true) | lower }},
      "icon": "{{ icon | default('') }}",
      "message": "{{ message | default('') }}",
      "messageColor": "{{ messageColor | default('#FFFFFF') }}",
      "iconColor": "{{ iconColor | default('#FFFFFF') }}",
      "borderColor": "{{ borderColor | default('#FFFFFF') }}",
      "backgroundColor": "{{ backgroundColor | default('#66000000') }}",
      "shape": "{{ shape | default('rounded') }}",
      "expiration": "{{ expiration | default('') }}"
    }

tvoverlay_set_overlay:
  url: "http://192.168.1.50:5001/set/overlay"
  method: POST
  headers:
    Content-Type: "application/json"
  payload: >-
    {
      "overlayVisibility": {{ overlayVisibility | default(0) }},
      "clockOverlayVisibility": {{ clockOverlayVisibility | default(0) }},
      "hotCorner": "{{ hotCorner | default('') }}"
    }

tvoverlay_set_notifications:
  url: "http://192.168.1.50:5001/set/notifications"
  method: POST
  headers:
    Content-Type: "application/json"
  payload: >-
    {
      "displayNotifications": {{ displayNotifications | default(true) | lower }},
      "displayFixedNotifications": {{ displayFixedNotifications | default(true) | lower }},
      "notificationLayoutName": "{{ notificationLayoutName | default('Default') }}",
      "notificationDuration": {{ notificationDuration | default(7) }},
      "fixedNotificationsVisibility": {{ fixedNotificationsVisibility | default(-1) }}
    }

tvoverlay_set_settings:
  url: "http://192.168.1.50:5001/set/settings"
  method: POST
  headers:
    Content-Type: "application/json"
  payload: >-
    {
      "deviceName": "{{ deviceName | default('') }}",
      "remotePort": "{{ remotePort | default('') }}",
      "displayDebug": {{ displayDebug | default(false) | lower }},
      "pixelShift": {{ pixelShift | default(false) | lower }}
    }

tvoverlay_set_mqtt:
  url: "http://192.168.1.50:5001/set/mqtt"
  method: POST
  headers:
    Content-Type: "application/json"
  payload: >-
    {
      "displayMqttStatusChange": {{ displayMqttStatusChange | default(false) | lower }},
      "mqttConfig": {
        "broker": "{{ broker }}",
        "port": {{ port | default(1883) }},
        "user": "{{ user | default('') }}",
        "password": "{{ password | default('') }}"
      }
    }

tvoverlay_get_status:
  url: "http://192.168.1.50:5001/get"
  method: GET

tvoverlay_restart:
  url: "http://192.168.1.50:5001/set/restart_service"
  method: POST
EOF

# Crear notify.yaml
cat > $dkco/homeassistant/data/includes/notify.yaml << 'EOF'
- name: tvoverlay_sala
  platform: rest
  method: POST_JSON
  resource: http://192.168.1.50:5001/notify
  verify_ssl: false
  title_param_name: title
  data:
    id: "{{ data.id | default('') }}"
    appTitle: "{{ data.appTitle | default('') }}"
    color: "{{ data.color | default('#03A9F4') }}"
    image: "{{ data.image | default(null) }}"
    video: "{{ data.video | default(null) }}"
    smallIcon: "{{ data.smallIcon | default('mdi:home-assistant') }}"
    largeIcon: "{{ data.largeIcon | default(null) }}"
    corner: "{{ data.corner | default(null) }}"
    duration: "{{ data.duration | default(7) }}"
EOF

# Crear carpeta de snapshots
mkdir -p $dkco/homeassistant/data/www/snapshots
```

### Agregar includes a configuration.yaml

```bash
# Agregar al final de configuration.yaml (si no están ya)
cat >> $dkco/homeassistant/data/configuration.yaml << 'EOF'

# ================================================================
# Includes organizados (ver carpeta includes/)
# ================================================================
shell_command: !include includes/shell_commands.yaml
rest_command: !include includes/tvoverlay_commands.yaml
notify: !include includes/notify.yaml
EOF
```

> ⚠️ **IMPORTANTE:** Si ya tienes `shell_command:`, `rest_command:` o `notify:` 
> definidos directamente en `configuration.yaml`, **borrar esas secciones** antes
> de agregar los includes. No pueden coexistir ambos.

### Aplicar cambios

```bash
# Reiniciar HA para que cargue los includes
svc restart homeassistant

# O desde HA: Herramientas para desarrolladores → YAML → Recargar todo
```

---

## Integración con ntfy

### Paso 1: Instalar integración oficial ntfy en HA

1. **Settings → Devices & Services → Add Integration → ntfy**
2. Service URL: `http://192.168.1.200:8090`
3. Sin autenticación (dejar vacío — auth abierto en LAN)
4. Verify SSL: desactivar
5. Add Topic → escribir: `nas-alerts`

Esto crea la entidad `notify.nas_alerts` para notificaciones de texto.

### Paso 2: Notificaciones con imagen (shell_command)

La integración oficial de ntfy en HA **aún no soporta adjuntar imágenes** (feature
request pendiente). Para enviar imágenes se usa `shell_command` + `curl -T`:

El archivo `includes/shell_commands.yaml` ya contiene `ntfy_camara` que hace esto.

### Probar desde terminal del NAS

```bash
# 1. Capturar snapshot via API de HA (requiere Long-Lived Access Token)
curl -s -o /tmp/camara-test.jpg \
  -H "Authorization: Bearer TU_TOKEN_HA_LARGO" \
  "http://192.168.1.200:8123/api/camera_proxy/camera.camara_profile_000"

# 2. Enviar a ntfy
curl -H "Title: 🧪 Test cámara" \
     -H "Priority: 4" \
     -H "Tags: camera" \
     -H "Filename: camara-test.jpg" \
     -T /tmp/camara-test.jpg \
     http://192.168.1.200:8090/nas-alerts

# 3. Limpiar
rm /tmp/camara-test.jpg
```

### Probar desde HA (Herramientas para desarrolladores → Acciones)

**Primero** capturar snapshot:
```yaml
action: camera.snapshot
target:
  entity_id: camera.camara_profile_000
data:
  filename: "/config/www/snapshots/alarma.jpg"
```

**Después** enviar (esperar 2 segundos):
```yaml
action: shell_command.ntfy_camara
```

---

## Automatización: Cámara → snapshot → ntfy

### Automatización completa (crear en Settings → Automations)

```yaml
alias: "Movimiento cámara → ntfy con imagen"
description: "Captura snapshot y envía push al celular al detectar movimiento"
mode: single
trigger:
  - platform: state
    entity_id: binary_sensor.camara_cell_motion_detection
    to: "on"
    for:
      seconds: 5
action:
  - action: camera.snapshot
    target:
      entity_id: camera.camara_profile_000
    data:
      filename: "/config/www/snapshots/alarma.jpg"
  - delay:
      seconds: 2
  - action: shell_command.ntfy_camara
```

### Cómo funciona

```
Cámara detecta movimiento (5s filtro)
    │
    ├─→ camera.snapshot → guarda /config/www/snapshots/alarma.jpg
    │
    ├─→ delay 2s (esperar escritura)
    │
    └─→ shell_command.ntfy_camara → curl envía imagen a ntfy → celular
```

### Notificación sin imagen (solo texto, más simple)

```yaml
alias: "Movimiento cámara → ntfy texto"
trigger:
  - platform: state
    entity_id: binary_sensor.camara_cell_motion_detection
    to: "on"
    for:
      seconds: 5
action:
  - action: ntfy.publish
    target:
      entity_id: notify.nas_alerts
    data:
      title: "🚨 Movimiento detectado"
      message: "Cámara detectó movimiento"
      priority: 4
      tags: "warning,camera"
```

> **Nota:** `priority` en `ntfy.publish` de HA usa **números**: 1=min, 2=low, 3=default, 4=high, 5=urgent.
> En curl/bash se usa texto ("high"), pero en HA se usa número.

---

## TvOverlay

TvOverlay envía notificaciones overlay a una Android TV/Fire TV.

### Entidades disponibles

| Acción | Uso |
|--------|-----|
| `rest_command.tvoverlay_notify` | Notificación emergente (texto, imagen, video) |
| `rest_command.tvoverlay_notify_fixed` | Icono fijo en esquina |
| `rest_command.tvoverlay_set_overlay` | Fondo oscuro, reloj |
| `rest_command.tvoverlay_set_notifications` | Config general |
| `rest_command.tvoverlay_set_mqtt` | Configurar MQTT remoto |
| `rest_command.tvoverlay_restart` | Reiniciar servicio |
| `notify.tvoverlay_sala` | Notificación rápida (sintaxis corta) |

### Ejemplo: enviar a TV cuando la cámara detecta

```yaml
action:
  - action: rest_command.tvoverlay_notify
    data:
      title: "🚨 Movimiento"
      message: "Cámara detectó movimiento"
      smallIcon: "mdi:cctv"
      color: "#FF0000"
      duration: 15
```

### IPs de dispositivos TvOverlay

| Dispositivo | IP | Puerto |
|-------------|-----|--------|
| TV principal | 192.168.0.7 | 5001 |
| TV secundaria | 192.168.1.50 | 5001 |

---

## Troubleshooting

### DataSQL no arranca con `Address already in use`

Si el error completo es `failed to set up container networking: Address already
in use`, no cambies primero el puerto de pgAdmin o PostgreSQL: en este entorno
la causa fue una IP estática (`ipv4_address`) ocupada en la red compartida
`db_net`. `svc restart datasql` tampoco recrea esa red ni cambia las IPs.

Mantener `db_net`, retirar las IPs estáticas del Compose y aplicar la versión
canónica de DataSQL con asignación dinámica. El procedimiento completo de
instalación, diagnóstico y migración está en
[`docs/services/datasql-guide.md`](datasql-guide.md) y en el
[troubleshooting general](../troubleshooting.md). Después de corregir DataSQL,
seguir este orden:

```bash
svc config datasql
svc down datasql
svc up datasql
svc ps datasql
# continuar solo cuando datapostgres y dataredis estén healthy
svc up homeassistant
svc ps homeassistant
```

No ejecutar `docker network prune` ni cambiar el Recorder a un PostgreSQL
expuesto en la LAN. HA debe conservar `network_mode: host` y usar
`127.0.0.1:5432`.

### `svc snapshot` no existe en el CLI Python

Si `svc snapshot datasql` muestra `No such command 'snapshot'`, usar mientras
se actualiza el NAS:

```bash
NAS_CLI=bash svc snapshot datasql
```

Después de actualizar el checkout con `nasfk` + `gpl`, Python registra
`snapshot` pero delega al mismo Bash. Para rollback, el fallback explícito es:

```bash
NAS_CLI=bash svc rollback datasql
```

### `connection refused` del Recorder con `localhost`

Si PostgreSQL está escuchando en `127.0.0.1:5432` pero el Recorder falla con
`localhost`, cambiar el `db_url` a `127.0.0.1`. En este entorno el cliente puede
intentar IPv6 primero; `localhost` no es equivalente a la publicación loopback
IPv4 usada por DataSQL.

### `psql` pide contraseña o `source .env` rompe la shell

No ejecutar `source $dkco/datasql/.env`: los secretos pueden contener caracteres
especiales. Tampoco usar el ejemplo `admin/appdb` de la guía compartida. Leer las
variables necesarias con `grep` y pasarlas como `env PGPASSWORD=...` dentro de
`svc exec datasql postgres`, siguiendo la receta de DataSQL.

### Aviso de reverse proxy

Un mensaje como `A request from a reverse proxy was received` puede aparecer si
un proxy de la red llega directamente a HA. No impide el funcionamiento inicial;
si se va a usar proxy, declarar después sus rangos autorizados en
`trusted_proxies` y validar la configuración antes de reiniciar.

### Home Assistant reinicia en bucle y no aparecen logs nuevos

Aislar el arranque con los comandos del NAS, sin usar Docker directamente:

```bash
svc stop homeassistant
svc logs homeassistant
```

Revisar primero `configuration.yaml`, la URL del Recorder, la disponibilidad de
DataSQL y los permisos del bind `./data:/config`.

### `curl: cannot open '/config/www/snapshots/alarma.jpg'`

La carpeta no existe. Crear desde el NAS:
```bash
mkdir -p $dkco/homeassistant/data/www/snapshots
```

### `Cannot write /tmp/alarma.jpg, allowlist_external_dirs`

HA no tiene permiso para escribir en `/tmp/`. Usar `/config/www/snapshots/` en vez de `/tmp/`.

### `extra keys not allowed @ data['image']` en ntfy.publish

La integración oficial de ntfy en HA **no soporta imágenes adjuntas** (aún).
Usar `shell_command` + `curl -T` para enviar imágenes.

### `extra keys not allowed @ data['priority']` / `expected int`

`priority` en `ntfy.publish` debe ser **número** (no texto):
- 1=min, 2=low, 3=default, 4=high, 5=urgent

### Shell commands no aparecen después de crear el archivo

Recargar: **Herramientas para desarrolladores → YAML → Recargar Shell Commands**
O reiniciar HA: `svc restart homeassistant`

### `!include` da error de duplicado

No pueden coexistir `shell_command:` definido directamente en `configuration.yaml`
Y también como `!include`. Borrar la definición directa y dejar solo el include.

### Snapshot se ejecuta pero shell_command falla

El snapshot tarda en escribirse. Asegurar `delay: { seconds: 2 }` entre ambas acciones.

---

## Entidades clave de este setup

| Entidad | Tipo | Uso |
|---------|------|-----|
| `camera.camara_profile_000` | Cámara | Snapshot, stream |
| `binary_sensor.camara_cell_motion_detection` | Sensor | Trigger de movimiento |
| `notify.nas_alerts` | Notificación | ntfy (solo texto) |
| `shell_command.ntfy_camara` | Shell | ntfy con imagen |
| `rest_command.tvoverlay_notify` | REST | Overlay en TV |
| `notify.tvoverlay_sala` | Notificación | TV (sintaxis corta) |
