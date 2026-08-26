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
4. [Recorder con PostgreSQL y arranque coordinado](#recorder-con-postgresql-y-arranque-coordinado)
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
son independientes, `depends_on` no puede ordenar esta dependencia. Verificar
primero el stack con:

```bash
svc ps datasql
```

`datapostgres` y `dataredis` deben estar `healthy`; `datapgadmin` debe estar
`Up` (la imagen canónica no define healthcheck para pgAdmin). Después validar y
levantar Home Assistant:

```bash
dk homeassistant
svc config homeassistant
svc up homeassistant
```

Esperar aproximadamente 60 segundos y revisar el estado y los logs con la
interfaz `svc`:

```bash
svc ps homeassistant
svc logs homeassistant
```

Acceder desde la LAN mediante `http://${SERVER_IP}:8123` y completar el
onboarding de Home Assistant (cuenta, nombre y ubicación). No editar
`configuration.yaml` antes de completar ese proceso. Si existe un reverse proxy,
es posible ver un aviso indicando que se recibió una petición desde un proxy no
confiable; el servicio puede seguir funcionando y se puede documentar después
la red del proxy en `trusted_proxies`.

La configuración canónica usa `dns` explícitos, `stop_grace_period: 60s`,
`privileged: true`, el bind `./data:/config`, healthcheck HTTP y labels de
Homepage con `${SERVER_IP}`. `network_mode: host` hace innecesario declarar
`networks`; también explica por qué HA accede al Recorder mediante el loopback
del NAS y no mediante el hostname Docker `datapostgres`.

---

## Recorder con PostgreSQL y arranque coordinado

Home Assistant conserva `network_mode: host` para mDNS, descubrimiento IoT,
USB y Bluetooth. Por eso no pertenece a `db_net` y no puede usar
`datapostgres` como hostname Docker. Su Recorder debe conectar al endpoint local
de PostgreSQL:

```yaml
recorder:
  db_url: postgresql://ha_user:CONTRASEÑA@127.0.0.1:5432/homeassistant_db
  purge_keep_days: 10
  auto_purge: true
  commit_interval: 1
```

La contraseña real no debe copiarse a esta guía ni al repositorio. La base `homeassistant_db` y el usuario `ha_user` deben crearse previamente con la receta de la sección 5 de `docs/services/datasql-guide.md`, usando credenciales dedicadas. Esa misma guía cubre la instalación y recuperación del stack. Lee `POSTGRES_USER`, `POSTGRES_DB` y `POSTGRES_PASSWORD` reales de
`$dkco/datasql/.env` sin ejecutar `source`. Como PostgreSQL usa
`scram-sha-256`, pasar `PGPASSWORD` explícitamente dentro de
`svc exec datasql postgres`, tal como indica `docs/services/datasql-guide.md`.

DataSQL conserva PostgreSQL en `db_net` con IP dinámica, pero publica su puerto
**solo en loopback**:

```yaml
ports:
  - "127.0.0.1:5432:5432"
```

No cambiarlo a `0.0.0.0:5432:5432` ni a `${SERVER_IP}:5432:5432`: Home Assistant
solo necesita acceso desde el propio NAS. Usar `127.0.0.1` explícitamente en
`db_url`, nunca `localhost`: la resolución de `localhost` puede intentar IPv6 y
producir `connection refused` aunque `127.0.0.1:5432` esté escuchando. Los
consumidores Docker conectados a `db_net` usan `datapostgres:5432` directamente.

Los Compose están separados, así que `depends_on` no puede ordenar HA respecto
a DataSQL. El arranque correcto es:

```bash
svc up datasql
svc ps datasql
# continuar cuando datapostgres y dataredis estén healthy
svc up homeassistant
svc ps homeassistant
```

`restart: unless-stopped` permite que HA vuelva a intentar después de un
reinicio de DataSQL, pero no sustituye esta precondición inicial. El healthcheck
HTTP de HA confirma la interfaz web, no la salud del Recorder.

---

## Verificación y operación diaria

Después de reiniciar HA y esperar aproximadamente 30 segundos:

```bash
svc ps homeassistant
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8123
svc logs homeassistant
```

Para confirmar que el Recorder está escribiendo datos, esperar a que HA haya
generado estados y consultar la base usando las credenciales administrativas de
DataSQL. No usar `docker exec` directo ni `source $dkco/datasql/.env`:

```bash
PG_ADMIN_USER=$(grep '^POSTGRES_USER=' "$dkco/datasql/.env" | cut -d= -f2-)
PG_ADMIN_DB=$(grep '^POSTGRES_DB=' "$dkco/datasql/.env" | cut -d= -f2-)
PG_ADMIN_PASSWORD=$(grep '^POSTGRES_PASSWORD=' "$dkco/datasql/.env" | cut -d= -f2-)

svc exec datasql postgres \
  env PGPASSWORD="$PG_ADMIN_PASSWORD" \
  psql -U "$PG_ADMIN_USER" -d homeassistant_db \
  -c "SELECT COUNT(*) FROM states;"

unset PG_ADMIN_USER PG_ADMIN_DB PG_ADMIN_PASSWORD
```

El resultado esperado es un conteo mayor que cero después de que HA haya
registrado estados. Las operaciones habituales son:

```bash
svc ps homeassistant
svc logs homeassistant
svc restart homeassistant
svc update homeassistant
svc stop homeassistant
```

El acceso LAN es `http://${SERVER_IP}:8123`; el acceso local para pruebas es
`http://127.0.0.1:8123`. Si HA reinicia en bucle y los logs no muestran el
motivo actual, detenerlo con `svc stop homeassistant` y después consultar
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
