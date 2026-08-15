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

### Windows / Linux (Chrome PWA)

1. Abrir `http://192.168.1.200:8090` en Chrome/Edge
2. Cuando pregunte "Permitir notificaciones" → **Permitir**
3. Suscribirse a topics deseados en la web UI
4. (Opcional) Menú Chrome → "Instalar ntfy" → se queda como app en taskbar

Las notificaciones aparecen como toast de Windows incluso con el browser cerrado
(siempre que Chrome tenga permiso de background).

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

### Caso: Alarma → Cámara → ntfy → PC/Celular

Cuando la alarma suena, HA captura snapshot de la cámara y lo envía como push
notification con imagen adjunta.

```yaml
# automation.yaml
- alias: "Alarma → ntfy con snapshot"
  trigger:
    - platform: state
      entity_id: alarm_control_panel.alarma
      to: "triggered"
  action:
    - service: camera.snapshot
      target:
        entity_id: camera.puerta_principal
      data:
        filename: "/config/www/snapshots/alarma_{{ now().strftime('%Y%m%d_%H%M%S') }}.jpg"
    - delay: { seconds: 2 }
    - service: shell_command.ntfy_alarma

# configuration.yaml
shell_command:
  ntfy_alarma: >
    curl -H "Title: 🚨 Alarma activada"
    -H "Priority: urgent"
    -H "Tags: rotating_light"
    -H "Actions: view, Ver cámara, http://192.168.1.200:8123/lovelace/camaras"
    -H "Filename: alarma.jpg"
    -T /config/www/snapshots/alarma_$(date +%Y%m%d_%H%M%S).jpg
    http://192.168.1.200:8090/alarma
```

### Integración alternativa (custom component)

Repo: `hbrennhaeuser/homeassistant_integration_ntfy`

```yaml
# configuration.yaml
notify:
  - platform: ntfy
    name: ntfy_nas
    url: http://192.168.1.200:8090
    topic: alarma
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
