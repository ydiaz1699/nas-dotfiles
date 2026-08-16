# ntfy — Guía Operativa Completa

> **Puerto:** 8090  
> **Imagen:** binwiederhier/ntfy:latest  
> **Red:** homepage_net  
> **Instalado por:** DebMenux (`scripts/services/ntfy.sh`)  
> **Tipo:** Docker container

---

## Índice

1. [Qué es ntfy](#qué-es-ntfy)
2. [Instalación](#instalación)
3. [Configuración del servidor](#configuración-del-servidor)
4. [Topics](#topics)
5. [Clientes — cómo recibir notificaciones](#clientes)
6. [Enviar notificaciones](#enviar-notificaciones)
7. [Integración con usb-automount](#integración-con-usb-automount)
8. [Integración con svc (Docker CLI)](#integración-con-svc)
9. [Integración con Home Assistant (alarma + cámara)](#integración-con-home-assistant)
10. [Integración con Homepage](#integración-con-homepage)
11. [Autenticación (opcional)](#autenticación)
12. [Backup y recuperación](#backup-y-recuperación)
13. [Troubleshooting](#troubleshooting)
14. [USB API (companion service)](#usb-api)

---

## Qué es ntfy

ntfy (pronunciado "notify") es un servidor HTTP pub-sub minimalista para enviar
notificaciones push. Funciona 100% en LAN sin depender de internet.

**Casos de uso en el NAS:**
- Recibir alertas de USB montados/desmontados en el celular
- Saber si un servicio Docker se cayó
- Confirmar que backups se completaron
- Alarma inteligente: recibir snapshot de cámara cuando hay movimiento

**Clientes soportados:**
- Android (app ntfy en F-Droid/Play Store)
- Windows/Linux (Chrome/Edge/Firefox como PWA)
- CLI (curl, websocket)
- Home Assistant (integración nativa)

---

## Instalación

La instalación es gestionada por DebMenux. Si necesitas instalar manualmente:

```bash
# 1. Crear directorios
mkdir -p $dkco/ntfy/{config,data/cache,data/lib,data/attachments}

# 2. Crear config/server.yml (ver sección siguiente)

# 3. Crear .env
cat > $dkco/ntfy/.env <<'EOF'
TZ=America/La_Paz
SERVER_IP=192.168.1.200
EOF
chmod 600 $dkco/ntfy/.env

# 4. Crear red (si no existe)
docker network create homepage_net 2>/dev/null || true

# 5. Copiar compose.yml del catálogo o del instalador DebMenux

# 6. Levantar
svc up ntfy
```

---

## Primer uso (configuración inicial)

Después de instalar ntfy (via `debmenu install ntfy` o manualmente), verificar que funciona:

```bash
# 1. Verificar que responde
curl http://192.168.1.200:8090/v1/health
# Debe devolver: {"healthy":true}

# 2. Enviar mensaje de prueba
curl -H "Title: 🎉 ntfy funciona" -H "Tags: tada" \
     -d "Primer mensaje desde el NAS" http://192.168.1.200:8090/nas-alerts
```

### Suscribirse a topics en la Web UI

1. Abrir `http://192.168.1.200:8090` en el navegador
2. Clic en **"+ Suscribirse al tópico"** (menú izquierdo)
3. Escribir el nombre del topic y confirmar
4. Repetir para cada topic que quieras monitorear:

| Topic | Para qué |
|-------|----------|
| `nas-alerts` | Alertas generales |
| `usb` | Montaje/desmontaje USBs |
| `docker` | Servicios Docker caídos/actualizados |
| `system` | Alertas de disco, SSH, temperatura |
| `backups` | Backups completados o fallidos |

> **Nota:** Los topics se crean automáticamente al suscribirse o al enviar
> el primer mensaje. No necesitan configuración previa en el servidor.

### Aviso "Notificaciones no soportadas" en la Web UI

Si ves un banner amarillo que dice _"Las notificaciones solo se admiten a través de HTTPS"_:

- **Es normal** — es una limitación del browser (Web Push API requiere HTTPS)
- La web UI **sigue funcionando** para ver mensajes en tiempo real (sin pop-up)
- Para recibir push reales: usar la **app Android** (funciona con HTTP) o
  configurar Chrome con el flag de seguridad (ver sección [Clientes → PC](#windows--linux-notificaciones-push-en-pc))

### Configurar NTFY_URL global en el sistema

Para que todos los scripts (`usb-automount`, `svc`, crons) puedan enviar notificaciones:

```bash
# Agregar a /etc/environment (persiste entre reboots)
echo 'NTFY_URL=http://192.168.1.200:8090' >> /etc/environment

# Aplicar en la sesión actual
export NTFY_URL=http://192.168.1.200:8090
```

---

## Configuración del servidor

Archivo: `$dkco/ntfy/config/server.yml`

```yaml
# URL base (para links en notificaciones)
base-url: "http://192.168.1.200:8090"

# Puerto interno del contenedor
listen-http: ":80"

# Cache de mensajes
cache-file: "/var/cache/ntfy/cache.db"
cache-duration: "24h"

# Attachments (imágenes de cámaras, archivos)
attachment-cache-dir: "/var/cache/ntfy/attachments"
attachment-total-size-limit: "1G"
attachment-file-size-limit: "10M"
attachment-expiry-duration: "24h"

# Auth: abierto en LAN (cambiar si se expone a internet)
auth-default-access: "read-write"

# No hay reverse proxy por delante
behind-proxy: false

# Keepalive WebSocket
keepalive-interval: "45s"

# Rate limiting (anti-spam)
visitor-subscription-limit: 30
visitor-request-limit-burst: 60
visitor-request-limit-replenish: "5s"
visitor-attachment-total-size-limit: "100M"
```

### Parámetros importantes

| Parámetro | Default | Descripción |
|-----------|---------|-------------|
| `cache-duration` | 24h | Cuánto tiempo se guardan mensajes (recibir offline) |
| `attachment-file-size-limit` | 10M | Tamaño máximo por adjunto |
| `attachment-total-size-limit` | 1G | Espacio total para adjuntos |
| `auth-default-access` | read-write | Acceso sin auth (LAN segura) |
| `keepalive-interval` | 45s | Ping WebSocket para mantener conexión |

---

## Topics

Los topics son canales de notificaciones. Se crean automáticamente al enviar
el primer mensaje. No necesitan configuración previa.

| Topic | Quién envía | Prioridad típica | Uso |
|-------|-------------|-------------------|-----|
| `usb` | usb-automount.sh | default/high | Mount/unmount/unsafe disconnect |
| `docker` | svc, agent daemon | high | Servicio caído, actualización |
| `backups` | cron, svc backup | default | Backup completado/fallido |
| `system` | SMART, SSH, cron | urgent | Fallo de disco, login SSH |
| `alarma` | Home Assistant | urgent | Movimiento + snapshot cámara |
| `nas-alerts` | catch-all | varies | Cualquier alerta general |

### Suscribirse a un topic

```bash
# En la app Android/browser: agregar topic por nombre
# Via CLI (stream JSON):
curl -s http://192.168.1.200:8090/usb/json

# Via CLI (stream SSE):
curl -s http://192.168.1.200:8090/usb/sse
```

---

## Clientes

### Android (recomendado)

1. Instalar app **ntfy** desde F-Droid o Play Store
2. Abrir app → Settings → "Add default server"
3. URL: `http://192.168.1.200:8090`
4. Suscribirse a topics: `nas-alerts`, `usb`, `docker`, `alarma`

> **Nota:** En LAN funciona sin internet. Si quieres recibir notificaciones
> fuera de casa, necesitas exponer ntfy vía reverse proxy + auth.

### Windows / Linux (notificaciones push en PC)

> **Problema:** Las notificaciones del browser (Web Push API) solo funcionan con HTTPS.
> En LAN con HTTP puro, Chrome/Edge/Firefox bloquean las notificaciones push.
> Abajo las soluciones, de más fácil a más robusta.

#### Método 1: Chrome/Edge con flag de seguridad (rápido, recomendado)

Crear un acceso directo especial que trata la URL HTTP del NAS como segura:

**Windows:**

1. Crear acceso directo en el escritorio con este destino:
```
"C:\Program Files\Google\Chrome\Application\chrome.exe" --unsafely-treat-insecure-origin-as-secure=http://192.168.1.200:8090
```

2. Abrir `http://192.168.1.200:8090` desde ese Chrome especial
3. Cuando pida permiso de notificaciones → **Permitir**
4. Suscribirse a topics: `nas-alerts`, `usb`, `docker`, `system`
5. (Opcional) Menú Chrome → "Instalar ntfy" → queda como app en la taskbar

> **Nota:** El flag solo aplica a ESE acceso directo. El Chrome normal sigue sin cambios.

Para **Edge** es igual cambiando la ruta al ejecutable:
```
"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" --unsafely-treat-insecure-origin-as-secure=http://192.168.1.200:8090
```

**Linux:**

```bash
# Chrome
google-chrome --unsafely-treat-insecure-origin-as-secure=http://192.168.1.200:8090 http://192.168.1.200:8090

# Chromium
chromium --unsafely-treat-insecure-origin-as-secure=http://192.168.1.200:8090 http://192.168.1.200:8090
```

Para hacerlo permanente, crear un `.desktop` con esa línea en `Exec=`.

#### Método 2: ntfy CLI en background (Linux)

Instalar el binario de ntfy y suscribirse desde terminal. Las notificaciones
aparecen como popups de escritorio (usa `notify-send` internamente):

```bash
# Descargar binario
curl -Lo /usr/local/bin/ntfy \
    https://github.com/binwiederhier/ntfy/releases/latest/download/ntfy_linux_amd64
chmod +x /usr/local/bin/ntfy

# Suscribirse (corre en foreground, muestra notificaciones de escritorio)
ntfy subscribe http://192.168.1.200:8090/nas-alerts

# Suscribirse a múltiples topics en background
ntfy subscribe http://192.168.1.200:8090/nas-alerts &
ntfy subscribe http://192.168.1.200:8090/usb &
ntfy subscribe http://192.168.1.200:8090/docker &
```

Para que arranque al login, agregar al autostart o crear un servicio systemd de usuario.

#### Método 3: HTTPS con reverse proxy (solución definitiva)

Si tienes o planeas instalar un reverse proxy (Nginx Proxy Manager, Caddy, Traefik),
configurar un subdominio con certificado SSL:

```
https://ntfy.tudominio.local → http://ntfy:80 (contenedor Docker)
```

Con certificado válido (Let's Encrypt o autofirmado importado en el browser), las
notificaciones push funcionan nativamente sin flags ni hacks.

#### Resumen de métodos para PC

| Método | OS | Esfuerzo | Notificaciones reales | Sin internet |
|--------|-----|----------|----------------------|--------------|
| Chrome + flag `--unsafely-treat...` | Win/Linux | Bajo (1 acceso directo) | ✅ Push nativo | ✅ |
| ntfy CLI subscribe | Linux | Medio (binario) | ✅ notify-send | ✅ |
| HTTPS reverse proxy | Cualquiera | Alto (una vez) | ✅ Push nativo | ✅ |
| Web UI sin flag (solo ver) | Cualquiera | Ninguno | ❌ Sin push | ✅ |

> **Recomendación:** Empezar con el flag de Chrome (Método 1). Si en el futuro
> instalas Nginx Proxy Manager, migrar a HTTPS (Método 3) y quitar el flag.

### CLI (scripting)

```bash
# Escuchar en tiempo real
curl -s http://192.168.1.200:8090/nas-alerts/json | while read -r line; do
    echo "$line" | jq -r '.title + ": " + .message'
done
```

---

## Enviar notificaciones

### Básica (curl)

```bash
curl -d "Mensaje simple" http://192.168.1.200:8090/nas-alerts
```

### Con título, prioridad y tags

```bash
curl -H "Title: 🔌 USB Montado" \
     -H "Priority: default" \
     -H "Tags: usb,mount" \
     -d "sdb1 (ntfs) → /NAS/USB/usb-sdb1" \
     http://192.168.1.200:8090/usb
```

### Con imagen adjunta (alarma)

```bash
curl -H "Title: 🚨 Alarma activada" \
     -H "Priority: urgent" \
     -H "Tags: rotating_light,camera" \
     -H "Filename: alarma.jpg" \
     -T /path/to/snapshot.jpg \
     http://192.168.1.200:8090/alarma
```

### Con botón de acción

```bash
curl -H "Title: 🔔 Servicio caído" \
     -H "Priority: high" \
     -H "Actions: view, Ver Dashboard, http://192.168.1.200:3000" \
     -d "emqx no responde al healthcheck" \
     http://192.168.1.200:8090/docker
```

### Desde scripts bash (función ntfy_send)

```bash
source /docker/cli/lib/notifications.sh
ntfy_send "docker" "⚠️ emqx DOWN" "No responde desde las 14:30" "high" "warning,whale"
```

### Prioridades disponibles

| Prioridad | Efecto en Android | Efecto en browser |
|-----------|-------------------|-------------------|
| `min` | Sin sonido, sin vibrar | Sin popup |
| `low` | Sonido suave | Popup silencioso |
| `default` | Sonido normal | Popup normal |
| `high` | Sonido fuerte + vibrar | Popup persistente |
| `urgent` | Alarma continua hasta abrir | Popup + sonido repetido |

---

## Integración con usb-automount

El script `usb-automount.sh` (instalado por DebMenux) usa ntfy automáticamente:

- **USB montado:** `ntfy_send "usb" "🔌 USB Montado" "sdb1 (ntfs) → /NAS/USB/usb-sdb1"`
- **USB desmontado:** `ntfy_send "usb" "⏏️ USB Desmontado" "sdb1 desconectado"`
- **Desconexión insegura:** `ntfy_send "usb" "⚠️ Desconexión Insegura" "..." "high"`

Requiere `ENABLE_NOTIFICATIONS="true"` en `/etc/usb-automount.conf`.

---

## Integración con svc

El CLI `svc` puede usar ntfy via la librería `docker/cli/lib/notifications.sh`:

```bash
# Después de svc update-all:
ntfy_update_complete "$count" "emqx, filebrowser, ntfy"

# En svc health (servicio caído):
ntfy_service_down "emqx"

# En svc backup:
ntfy_backup_complete "datasql" "2.3GB"
```

---

## Integración con Home Assistant

### Método recomendado: Integración oficial nativa

Desde 2025, ntfy tiene **integración oficial** en Home Assistant (no necesita HACS
ni custom components). Se configura desde la UI.

**Configuración:**

1. Settings → Devices & Services → Add Integration → **ntfy**
2. Service URL: `http://192.168.1.200:8090`
3. Sin autenticación (LAN con auth abierto)
4. Add Topic → escribir `nas-alerts` (o el topic que uses)

Esto crea una entidad `notify.nas_alerts` que puedes usar en automatizaciones.

### Caso real: Cámara detecta movimiento → snapshot → push al celular

Entidades de tu setup:
- `binary_sensor.camara_cell_motion_detection` — sensor de movimiento
- `camera.camara_profile_000` — cámara IP

```yaml
# automations.yaml
- alias: "Movimiento cámara → ntfy con snapshot"
  trigger:
    - platform: state
      entity_id: binary_sensor.camara_cell_motion_detection
      to: "on"
      for:
        seconds: 5    # filtro anti-falsos-positivos
  action:
    # 1. Capturar snapshot (nombre fijo, se sobreescribe cada vez)
    - action: camera.snapshot
      target:
        entity_id: camera.camara_profile_000
      data:
        filename: "/config/www/snapshots/alarma.jpg"

    # 2. Esperar a que se escriba el archivo
    - delay:
        seconds: 2

    # 3. Enviar notificación con la imagen
    - action: ntfy.publish
      target:
        entity_id: notify.nas_alerts
      data:
        title: "🚨 Movimiento detectado"
        message: "Cámara detectó movimiento"
        priority: high
        tags: "warning,camera"
        image: "/config/www/snapshots/alarma.jpg"
```

> **Nota:** Se usa `ntfy.publish` (acción oficial) en vez de `notify.send_message`
> para acceder a todas las features de ntfy (priority, tags, image, actions).

### Alternativa: shell_command (sin integración oficial)

Si prefieres no instalar la integración (o tu versión de HA no la tiene):

```yaml
# configuration.yaml
shell_command:
  ntfy_camara: >
    curl -s -H "Title: 🚨 Movimiento detectado"
    -H "Priority: high"
    -H "Tags: warning,camera"
    -H "Filename: alarma.jpg"
    -T /config/www/snapshots/alarma.jpg
    http://192.168.1.200:8090/nas-alerts
```

```yaml
# automations.yaml
- alias: "Movimiento cámara → ntfy (shell_command)"
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

> **⚠️ NUNCA usar `$(date...)` en el filename del shell_command** — se ejecuta
> en un momento diferente al snapshot y el archivo no coincide. Usar nombre fijo.

### Prueba rápida desde terminal (sin HA)

Para verificar que el flujo cámara → ntfy funciona end-to-end:

```bash
# 1. Capturar snapshot via API de HA (requiere Long-Lived Access Token)
curl -s -o /tmp/camara-test.jpg \
  -H "Authorization: Bearer TU_TOKEN_HA_LARGO" \
  "http://192.168.1.200:8123/api/camera_proxy/camera.camara_profile_000"

# 2. Enviar a ntfy con imagen
curl -H "Title: 🧪 Test cámara en vivo" \
     -H "Priority: high" \
     -H "Tags: camera,test_tube" \
     -H "Filename: camara-test.jpg" \
     -T /tmp/camara-test.jpg \
     http://192.168.1.200:8090/nas-alerts

# 3. Limpiar
rm /tmp/camara-test.jpg
```

> **Nota:** El `access_token` del entity state (el que aparece en `entity_picture`)
> es solo para el proxy del frontend. Para la API necesitas un **Long-Lived Access Token**:
> HA → Tu perfil → scroll abajo → "Long-Lived Access Tokens" → Crear.

---

### Automatización en HA (sin terminal, 100% dentro de Home Assistant)

La automatización se configura una vez y se ejecuta sola cada vez que la cámara
detecta movimiento. No necesitas tocar la terminal.

#### Paso 1: Instalar integración ntfy en HA

1. Settings → Devices & Services → **Add Integration** → buscar **ntfy**
2. Service URL: `http://192.168.1.200:8090`
3. Sin autenticación (dejar vacío)
4. Verify SSL: desactivar (es HTTP local)
5. Add Topic → escribir: `nas-alerts`

Esto crea la entidad `notify.nas_alerts`.

#### Paso 2: Crear la automatización

Settings → Automations & Scenes → **Create Automation** → Editar en YAML:

```yaml
alias: "Movimiento cámara → ntfy con snapshot"
description: "Captura imagen y envía push notification al detectar movimiento"
mode: single
trigger:
  - platform: state
    entity_id: binary_sensor.camara_cell_motion_detection
    to: "on"
    for:
      seconds: 5
action:
  # Capturar snapshot
  - action: camera.snapshot
    target:
      entity_id: camera.camara_profile_000
    data:
      filename: "/config/www/snapshots/alarma.jpg"

  # Esperar a que se escriba el archivo
  - delay:
      seconds: 2

  # Enviar notificación con imagen
  - action: ntfy.publish
    target:
      entity_id: notify.nas_alerts
    data:
      title: "🚨 Movimiento detectado"
      message: "Cámara detectó movimiento"
      priority: high
      tags: "warning,camera"
      image: "/config/www/snapshots/alarma.jpg"
```

#### Paso 3: Verificar que funciona

1. Guardar la automatización
2. Pasar frente a la cámara (esperar 5 segundos del filtro)
3. Debería llegar al celular: título "🚨 Movimiento detectado" + imagen de la cámara

#### Paso 4 (opcional): Más automatizaciones útiles

```yaml
# Notificar cuando un servicio Docker se cae (si HA monitorea uptime)
- alias: "Servicio Docker caído → ntfy"
  trigger:
    - platform: state
      entity_id: binary_sensor.emqx_running  # (si tienes sensor de Docker)
      to: "off"
      for:
        seconds: 30
  action:
    - action: ntfy.publish
      target:
        entity_id: notify.nas_alerts
      data:
        title: "⚠️ Servicio Docker caído"
        message: "EMQX no responde desde hace 30s"
        priority: high
        tags: "warning,whale"
```

```yaml
# Notificación diaria de estado del NAS
- alias: "Reporte diario NAS → ntfy"
  trigger:
    - platform: time
      at: "09:00:00"
  action:
    - action: ntfy.publish
      target:
        entity_id: notify.nas_alerts
      data:
        title: "📊 NAS Status"
        message: "Servicios: OK | Disco: {{ states('sensor.disk_use_percent') }}%"
        priority: low
        tags: "chart_with_upwards_trend"
```

---

## Integración con Homepage

En `$dkco/homepage/config/services.yaml`:

```yaml
- Sistema:
    - ntfy:
        icon: ntfy
        href: http://192.168.1.200:8090
        description: Notificaciones push del NAS
        widget:
          type: customapi
          url: http://ntfy:80/v1/stats
          mappings:
            - field: messages
              label: Mensajes
            - field: topics
              label: Topics

    - USB Manager:
        icon: usb
        href: http://192.168.1.200:8091
        description: Dispositivos USB conectados
        widget:
          type: customapi
          url: http://192.168.1.200:8091/usb/list
          mappings:
            - field: count
              label: USBs montados
```

---

## Autenticación

Por defecto ntfy está abierto (LAN). Si se expone a internet:

```bash
# Cambiar auth en server.yml:
# auth-default-access: "deny-all"

# Crear usuario admin
docker exec -it ntfy ntfy user add --role=admin admin

# Crear token para scripts
docker exec -it ntfy ntfy token add admin

# Usar token en scripts:
export NTFY_TOKEN="tk_xxxxxxxxx"
ntfy_send "docker" "Test" "Con auth"
```

---

## Backup y recuperación

### Qué respaldar

- `$dkco/ntfy/config/server.yml` — configuración
- `$dkco/ntfy/data/lib/` — base de datos de usuarios/ACL (si auth habilitada)

### Qué NO respaldar

- `$dkco/ntfy/data/cache/` — mensajes temporales (se purgan en 24h)
- `$dkco/ntfy/data/attachments/` — adjuntos temporales (expiran en 24h)

### Recuperación

```bash
# 1. Crear directorios
mkdir -p $dkco/ntfy/{config,data/cache,data/lib,data/attachments}

# 2. Restaurar config
cp backup/server.yml $dkco/ntfy/config/

# 3. Restaurar DB de usuarios (si existía)
cp backup/user.db $dkco/ntfy/data/lib/

# 4. Levantar
svc up ntfy
```

---

## Troubleshooting

### ntfy no arranca

```bash
# Ver logs
svc logs ntfy

# Verificar config YAML válido
docker run --rm -v $dkco/ntfy/config:/etc/ntfy binwiederhier/ntfy:latest serve --dry-run
```

### No recibo notificaciones en Android

1. Verificar que la app tiene el servidor correcto: `http://IP:8090` (no https)
2. Verificar que el topic coincide (case sensitive)
3. Probar enviar desde CLI: `curl -d "test" http://IP:8090/TOPIC`
4. Verificar que el celular está en la misma LAN
5. Android: verificar que ntfy no está en "battery optimization"

### No recibo notificaciones en Windows

1. Chrome → Settings → Privacy → Notifications → ntfy debe estar en "Allow"
2. Verificar que Chrome puede correr en background (Settings → System)
3. Probar con pestaña abierta primero

### curl funciona pero la app no recibe

- El celular puede estar en otra subnet/VLAN
- Verificar firewall: `sudo iptables -L -n | grep 8090`
- Verificar que el contenedor está healthy: `svc health ntfy`

### Homepage widget no muestra datos

- Verificar que ntfy está en `homepage_net`: `docker network inspect homepage_net`
- La URL del widget debe usar el nombre del contenedor: `http://ntfy:80/v1/stats`

### USB no notifica al montar/desmontar

1. Verificar que las notificaciones están habilitadas:
```bash
grep -E "ENABLE_NOTIFICATIONS|NTFY_URL" /etc/usb-automount.conf
# Debe mostrar:
#   ENABLE_NOTIFICATIONS="true"
#   NTFY_URL="http://192.168.1.200:8090"
```

2. Si falta alguna, agregar:
```bash
sed -i 's/ENABLE_NOTIFICATIONS="false"/ENABLE_NOTIFICATIONS="true"/' /etc/usb-automount.conf
grep -q "^NTFY_URL" /etc/usb-automount.conf || echo 'NTFY_URL="http://192.168.1.200:8090"' >> /etc/usb-automount.conf
```

3. Verificar que el script tiene la versión con ntfy (no la vieja con notify-send):
```bash
grep -c "ntfy_send\|ntfy_usb" /usr/local/bin/usb-automount.sh
# Debe devolver > 0. Si devuelve 0, actualizar:
cp /debmenux/templates/usb-automount/usb-automount.sh /usr/local/bin/usb-automount.sh
chmod +x /usr/local/bin/usb-automount.sh
```

4. Verificar que estás suscrito al topic **`usb`** en la app (no solo `nas-alerts`)

### Mountpoint huérfano (carpeta usb-* que no se borra)

**Síntoma:** En File Browser (o `ls /NAS/USB/`) aparece una carpeta `usb-sdb1`
pero no hay USB conectado. `rmdir` da "Dispositivo o recurso ocupado".

**Causa:** El USB se desconectó sin desmontar (tirón físico). El kernel mantiene
un "mount fantasma" aunque el dispositivo ya no existe.

**Diagnóstico:**
```bash
# ¿Está marcado como montado? (sí = mount fantasma)
mountpoint /NAS/USB/usb-sdb1

# ¿El dispositivo existe? (no = ya se desconectó)
lsblk | grep sdb

# ¿La carpeta está vacía?
ls /NAS/USB/usb-sdb1/
```

Si `mountpoint` dice "es un punto de montaje" pero `lsblk` no muestra el dispositivo:

**Solución:**
```bash
# Desmontar lazy (libera el mount fantasma) + borrar carpeta
umount -l /NAS/USB/usb-sdb1 && rmdir /NAS/USB/usb-sdb1

# Verificar
ls /NAS/USB/
```

**Prevención:**
- El timer `usb-automount-cleanup.timer` limpia huérfanos cada hora automáticamente
- Verificar que está activo: `systemctl status usb-automount-cleanup.timer`
- Si no está activo: `systemctl enable --now usb-automount-cleanup.timer`
- Siempre que sea posible, **desmontar antes de desconectar**:
  - Desde terminal: `usb-automount.sh --status` → `curl -X POST http://IP:8091/usb/unmount/sdb1`
  - Desde File Browser: no tocar, usar usb-api
  - Desde el celular: enviar POST al endpoint de usb-api

> **Nota:** El cleanup timer solo borra carpetas que NO están marcadas como mountpoint
> Y están vacías. Los mounts fantasma necesitan `umount -l` manual (o reboot).

---

## USB API

### Qué es

Servicio companion (NO Docker, systemd nativo) que expone una API REST para
listar y desmontar USBs desde el browser (Homepage widget con botón ⏏️).

### Puerto y endpoints

- Puerto: **8091**
- `GET /usb/list` → JSON con dispositivos montados
- `POST /usb/unmount/sdb1` → Desmonta sdb1 de forma segura + notifica via ntfy
- `GET /health` → Health check

### Gestión

```bash
systemctl status usb-api
systemctl restart usb-api
journalctl -u usb-api -f
```

### Por qué no es Docker

Necesita ejecutar `umount` en el host real. Un contenedor Docker necesitaría
`privileged: true` (inseguro) o montar el socket Docker (complejo). La solución
más limpia es un servicio systemd nativo (~50 líneas Python, sin dependencias pip).

### Archivos

```
/usr/local/lib/usb-api/server.py        ← Servidor Python (stdlib http.server)
/etc/systemd/system/usb-api.service     ← Unit file
```

### Seguridad

- Solo escucha en LAN (configurable)
- Sanitiza nombres de dispositivos
- Solo desmonta paths bajo MOUNT_BASE (/NAS/USB)
- No requiere auth (LAN interna de confianza)
