# Home Assistant — Guía Operativa

> **Puerto:** 8123  
> **Imagen:** ghcr.io/home-assistant/home-assistant:stable  
> **Red:** host (acceso directo al stack de red del NAS)  
> **Tipo:** Docker container (privileged)

---

## Índice

1. [Estructura de archivos](#estructura-de-archivos)
2. [Compose](#compose)
3. [Organización con includes](#organización-con-includes)
4. [Integración con ntfy (notificaciones push)](#integración-con-ntfy)
5. [Automatización: Cámara → snapshot → ntfy](#automatización-cámara--snapshot--ntfy)
6. [TvOverlay (notificaciones en TV)](#tvoverlay)
7. [Troubleshooting](#troubleshooting)

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
