# Home Assistant — Guía Operativa

> **Puerto:** 8123  
> **Imagen:** ghcr.io/home-assistant/home-assistant:stable  
> **Red:** host (acceso directo al stack de red del NAS)  
> **Tipo:** Docker container (privileged)
> **Base de datos:** integración PostgreSQL opcional; la guía separada documenta DataSQL del NAS y otros backends confirmados

Esta guía incorpora la configuración real compartida en la [guía de Home Assistant del usuario](https://gist.github.com/ydiaz1699/ad4f9c92edd8669d720b8865c82a73ed), adaptada a las reglas actuales de `nas-dotfiles`: operaciones Docker mediante `svc`, credenciales leídas sin `source .env`, acceso LAN mediante `${SERVER_IP}` y publicación PostgreSQL limitada al loopback. La guía compartida mostraba `192.168.0.200` en algunos ejemplos; no se copia esa IP porque el NAS documentado usa `SERVER_IP` (`192.168.1.200` en la configuración actual).

---

## Índice

1. [Estructura de archivos](#estructura-de-archivos)
2. [Compose](#compose)
3. [Primer inicio y onboarding](#primer-inicio-y-onboarding)
4. [Integración opcional con PostgreSQL/DataSQL](#integración-opcional-con-postgresql-datasql)
5. [Verificación y operación diaria](#verificación-y-operación-diaria)
6. [Organización con includes](#organización-con-includes)
7. [secrets.yaml](#secretsyaml)
8. [Integración con ntfy (notificaciones push)](#integración-con-ntfy)
9. [Automatización: Cámara → snapshot → ntfy](#automatización-cámara--snapshot--ntfy)
10. [TvOverlay (notificaciones en TV)](#tvoverlay)
11. [Troubleshooting](#troubleshooting)

---

## Estructura de archivos

```
$dkco/homeassistant/
├── compose.yml
├── .env                            ← HOMEASSISTANT_TOKEN (para Homepage widget)
└── data/                           ← montado como /config dentro del contenedor
    ├── configuration.yaml          ← raíz, solo incluye módulos
    ├── secrets.yaml                ← secretos de Home Assistant (no subir a git)
    ├── automations.yaml            ← automatizaciones
    ├── scripts.yaml
    ├── scenes.yaml
    ├── core/                       ← ajustes base del sistema
    │   ├── homeassistant.yaml
    │   ├── recorder.yaml
    │   ├── http.yaml
    │   ├── zeroconf.yaml
    │   └── panel_custom.yaml
    ├── includes/                   ← integraciones
    │   ├── shell_commands.yaml     ← ntfy, utilidades
    │   ├── tvoverlay_commands.yaml ← TvOverlay (rest_command)
    │   └── notify.yaml             ← plataformas de notificación
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
    restart: on-failure:5
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

El onboarding de Home Assistant no depende de que el usuario haya elegido
PostgreSQL/DataSQL. Home Assistant puede levantarse directamente con Recorder y
SQLite, que es su backend predeterminado. Si se usará PostgreSQL, prepara
primero el backend y después sigue la guía separada para configurar `db_url` en
la configuración persistente de HA y verificar la conexión. Si no se usará
PostgreSQL, continúa con el onboarding sin crear una base externa.

Para el primer inicio, comprueba únicamente la configuración de HA y levanta el
servicio:

```bash
dk homeassistant
svc config homeassistant
svc up homeassistant
svc ps homeassistant
svc logs homeassistant
```

La configuración canónica usa `dns` explícitos, `stop_grace_period: 60s`,
`privileged: true`, el bind `./data:/config`, healthcheck HTTP y labels de
Homepage con `${SERVER_IP}`. `network_mode: host` hace innecesario declarar
`networks` y permite las integraciones de descubrimiento y hardware de HA.

---

## Integración opcional con PostgreSQL/DataSQL

La conexión de Home Assistant con PostgreSQL es opcional y está documentada por separado. Esta guía principal solo cubre la operación propia de Home Assistant, su compose, onboarding e integraciones de automatización.

Si quieres conectar el Recorder de Home Assistant a PostgreSQL, sigue la guía
completa. La creación de `homeassistant_db` y `ha_user` no conecta HA por sí
sola: cada consumidor tiene su propia configuración y Home Assistant usa
`recorder.db_url` en su configuración persistente. La guía documenta el camino
SQLite por defecto, la detección del backend actual, la configuración explícita
para PostgreSQL y la verificación de runtime.

[`docs/services/homeassistant-datasql-guide.md`](homeassistant-datasql-guide.md)

---

## Continuidad entre chats

La guía principal de Home Assistant conserva solo la operación del servicio. Si
estás ejecutando la integración PostgreSQL, el checkpoint canónico y sus pasos
están en [`_drafts/SESSION-HA-DATASQL.md`](../../_drafts/SESSION-HA-DATASQL.md), y la
guía que debes continuar es
[`homeassistant-datasql-guide.md`](homeassistant-datasql-guide.md).

No repitas una mutación ya confirmada (`CREATE ROLE`, `CREATE DATABASE`, cambio
de contraseña o edición del Recorder) solo porque cambies de chat. Pega la
última salida del NAS sin secretos y continúa desde la última postcondición
confirmada. La preparación del backend no demuestra que HA esté conectado: esa
conclusión requiere comprobar `db_url`, `pg_stat_activity` y las tablas del
Recorder.

---

## Verificación y operación diaria

Después de reiniciar HA y esperar aproximadamente 30 segundos:

```bash
svc ps homeassistant
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8123
svc logs homeassistant
```

El healthcheck HTTP confirma que la interfaz responde. No identifica el backend
del Recorder. Para distinguir SQLite de PostgreSQL y verificar una conexión real,
sigue las secciones de detección y verificación de
[`homeassistant-datasql-guide.md`](homeassistant-datasql-guide.md).

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

En vez de meter todos los ajustes en `configuration.yaml` (que se vuelve enorme), la configuración se separa en dos carpetas mediante `!include`:

- `core/` contiene los ajustes base del sistema: `homeassistant`, `recorder`, `http`, `zeroconf` y `panel_custom`.
- `includes/` contiene integraciones y acciones separadas: `shell_command`, `rest_command` y `notify`.

Los archivos `homeassistant.yaml`, `recorder.yaml`, `http.yaml` y `zeroconf.yaml` son **mapas YAML**: contienen pares `clave: valor` y no empiezan con guion. En cambio, `panel_custom.yaml` es una **lista YAML**: empieza con `-` porque esa integración espera una lista de paneles, aunque aquí solo se defina uno. No se debe igualar el formato entre estos archivos.

### configuration.yaml (raíz, solo includes)

```yaml
default_config:
homeassistant: !include core/homeassistant.yaml
frontend:
  themes: !include_dir_merge_named themes
automation: !include automations.yaml
script: !include scripts.yaml
scene: !include scenes.yaml
recorder: !include core/recorder.yaml
http: !include core/http.yaml
zeroconf: !include core/zeroconf.yaml
ssdp:
shell_command: !include includes/shell_commands.yaml
rest_command: !include includes/tvoverlay_commands.yaml
notify: !include includes/notify.yaml
panel_custom: !include core/panel_custom.yaml
```

`default_config:` y `ssdp:` son claves válidas sin contenido adicional. `configuration.yaml` ya no contiene directamente los valores de `homeassistant`, `recorder`, `http` ni `zeroconf`; solo conecta cada integración con su archivo de `core/` o `includes/`.

### Archivos de `core/`

Crear `$dkco/homeassistant/data/core/` y guardar estos archivos completos:

#### `core/homeassistant.yaml`

```yaml
name: Home
unit_system: metric
time_zone: America/La_Paz
allowlist_external_dirs:
  - "/config/www/snapshots"
```

#### `core/recorder.yaml`

```yaml
db_url: !secret recorder_db_url
purge_keep_days: 10
auto_purge: true
commit_interval: 1
```

El password no se escribe en este archivo. La referencia `!secret recorder_db_url` se resuelve desde `secrets.yaml`; consulta la sección [secrets.yaml](#secretsyaml).

#### `core/http.yaml`

```yaml
use_x_forwarded_for: true
trusted_proxies:
  - 192.168.1.0/24
  - 127.0.0.1
```

#### `core/zeroconf.yaml`

```yaml
default_interface: true
ipv6: false
```

#### `core/panel_custom.yaml`

```yaml
- name: panel_develop
  sidebar_title: Developer Tools
  sidebar_icon: mdi:hammer
  url_path: 'config/developer-tools'
  module_url: /api/hassio/app/entrypoint.js
  embed_iframe: true
  require_admin: true
```

> **Nota sobre `panel_custom` y Developer Tools:** `module_url: /api/hassio/app/entrypoint.js` es una ruta pensada para Home Assistant OS con Supervisor. En una instalación Docker Container pura, como la de esta guía, se esperaría que fallara. Sin embargo, **confirmado en producción:** el panel personalizado sí aparece y funciona correctamente en la barra lateral de este entorno Docker Container, por lo que se mantiene como válido para este setup específico. Si en algún momento deja de cargar al hacer clic, Developer Tools ya existe de forma nativa gracias a `default_config:` y queda disponible como respaldo.

### Crear archivos de integración en `includes/`

Desde el NAS (la ruta `$dkco/homeassistant/data/` es `/config` dentro de HA):

```bash
# Crear carpetas antes de crear archivos
mkdir -p $dkco/homeassistant/data/core
mkdir -p $dkco/homeassistant/data/includes
mkdir -p $dkco/homeassistant/data/www/snapshots

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
```

La secuencia es intencional: primero se crean las carpetas, después los archivos. Los permisos, si fueran necesarios, se aplican solo después de que existan los archivos.

### Configurar `configuration.yaml`

Escribir la configuración raíz completa —no añadir fragmentos a una versión antigua— para evitar duplicados:

```bash
cat > $dkco/homeassistant/data/configuration.yaml << 'EOF'
default_config:
homeassistant: !include core/homeassistant.yaml
frontend:
  themes: !include_dir_merge_named themes
automation: !include automations.yaml
script: !include scripts.yaml
scene: !include scenes.yaml
recorder: !include core/recorder.yaml
http: !include core/http.yaml
zeroconf: !include core/zeroconf.yaml
ssdp:
shell_command: !include includes/shell_commands.yaml
rest_command: !include includes/tvoverlay_commands.yaml
notify: !include includes/notify.yaml
panel_custom: !include core/panel_custom.yaml
EOF
```

> ⚠️ **IMPORTANTE:** Si ya tienes `shell_command:`, `rest_command:` o `notify:` definidos directamente en `configuration.yaml`, reemplaza el archivo por la versión completa anterior o borra esas secciones directas antes de usar los includes. No pueden coexistir las definiciones directas con sus respectivos `!include`.

### Aplicar cambios

```bash
# Reiniciar HA para que cargue los includes
svc restart homeassistant

# O desde HA: Herramientas para desarrolladores → YAML → Recargar todo
```

---

## secrets.yaml

El password de PostgreSQL usado por Recorder **ya no se escribe en texto plano dentro de `core/recorder.yaml`**. Ese archivo solo contiene `db_url: !secret recorder_db_url`; el valor real vive en `$dkco/homeassistant/data/secrets.yaml`, que Home Assistant carga como `/config/secrets.yaml`.

Crear o editar el archivo con el URI real del usuario dedicado:

```yaml
recorder_db_url: "postgresql://ha_user:TU_PASSWORD@127.0.0.1:5432/homeassistant_db"
```

Sustituir `TU_PASSWORD` por el password real de `ha_user`. `secrets.yaml` contiene credenciales y **nunca debe subirse a git ni compartirse**. Mantenerlo solo en el NAS y revisar que no se incluya accidentalmente en capturas, logs, commits o mensajes de soporte.

Si se pierde el password, resetearlo en PostgreSQL y después actualizar el mismo valor en `data/secrets.yaml`:

```bash
svc exec datasql postgres
```

Dentro de la sesión SQL de PostgreSQL:

```sql
ALTER ROLE ha_user WITH PASSWORD 'nueva_password';
```

Después, reemplazar el valor de `TU_PASSWORD` en `recorder_db_url` por `nueva_password` y validar la configuración antes de reiniciar HA:

```bash
svc config homeassistant
svc restart homeassistant
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

### `Cannot write /config/www/snapshots/alarma.jpg` o `allowlist_external_dirs`

La ruta autorizada para los snapshots de cámara es `/config/www/snapshots`, declarada en `core/homeassistant.yaml` y equivalente a `$dkco/homeassistant/data/www/snapshots` en el NAS. Es la misma ruta que usa la automatización cámara → ntfy porque permanece dentro de `/config`.

Si la carpeta no existe, crearla desde el NAS:

```bash
mkdir -p $dkco/homeassistant/data/www/snapshots
```

`/tmp` **nunca fue necesario para este caso de uso**. Si aparece `/tmp` en una configuración o en un diagnóstico antiguo, eliminarlo y cambiar el `filename` a `/config/www/snapshots/alarma.jpg`.


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

### `!include`, `!secret` o `!include_dir_merge_named` aparecen como `unknown tag`

Si un editor de archivos como Filebrowser, Cockpit u otro linter genérico marca líneas con `!include`, `!secret` o `!include_dir_merge_named` como `unknown tag`, o muestra un ícono de error, no es un error real de Home Assistant. Son etiquetas personalizadas que el linter YAML genérico del editor no reconoce. La validación real de esta configuración es siempre:

```bash
svc config homeassistant
```

### Error de ruta relativa al crear archivos con `cat`

Al crear archivos con un heredoc como `cat > archivo.yaml << 'EOF'` dentro del NAS, comprobar primero la carpeta actual con `pwd` o con la ruta mostrada en el prompt. Si ya estás dentro de `data/core/`, usa solo el nombre del archivo:

```bash
pwd
cat > homeassistant.yaml << 'EOF'
# contenido
EOF
```

No uses en ese caso `cat > data/core/homeassistant.yaml << 'EOF'`: intentaría crear una subcarpeta `data/core/` dentro de la carpeta en la que ya estás y puede fallar con `No existe el fichero o el directorio`. Si estás en `$dkco/homeassistant/`, entonces sí puedes usar la ruta completa `$dkco/homeassistant/data/core/homeassistant.yaml`.

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
