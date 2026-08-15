# PLAN: ntfy + USB API + Homepage — lado nas-dotfiles

> **Estado:** PENDIENTE — implementar en próxima sesión
> **Fecha:** 2026-08-14
> **Plan completo:** ver también `/debmenux/_drafts/PLAN-ntfy-usb-api.md`

---

## Qué hacer en este repo (nas-dotfiles)

### Archivos a crear

| Archivo | Descripción |
|---------|-------------|
| `agent/catalog/services/ntfy/ficha.md` | Metadatos del servicio ntfy |
| `agent/catalog/services/ntfy/compose.yml` | Compose final (post-fix) |
| `agent/catalog/services/ntfy/.env.example` | Variables (sin secretos reales) |
| `agent/catalog/services/usb-api/ficha.md` | Metadatos de la API USB |
| `docs/services/ntfy-guide.md` | Guía operativa completa (topics, auth, clientes, troubleshooting) |
| `docker/cli/lib/notifications.sh` | Función `ntfy_send()` para uso en scripts svc |
| `agent/plugins/notification_plugin.py` | Plugin del agente que envía alertas via ntfy |

### Archivos a actualizar

| Archivo | Cambio |
|---------|--------|
| `docker-nas/SKILL.md` | Agregar ntfy a tabla de guías + tabla de herramientas |
| `$dkco/homepage/config/services.yaml` | Widgets de ntfy + USB Manager |

---

## Función ntfy_send() para nas-dotfiles

Va en `docker/cli/lib/notifications.sh` — sourced por svc y otros scripts:

```bash
#!/bin/bash
# Enviar notificación via ntfy (servidor local)
ntfy_send() {
    local topic="${1:-nas-alerts}"
    local title="${2:-}"
    local message="${3:-}"
    local priority="${4:-default}"
    local tags="${5:-}"

    local ntfy_url="${NTFY_URL:-http://localhost:8090}"

    local -a headers=()
    [[ -n "$title" ]] && headers+=(-H "Title: $title")
    [[ -n "$priority" ]] && headers+=(-H "Priority: $priority")
    [[ -n "$tags" ]] && headers+=(-H "Tags: $tags")

    curl -s "${headers[@]}" -d "$message" "${ntfy_url}/${topic}" 2>/dev/null || true
}
```

### Dónde usarla en nas-dotfiles:

```bash
# En svc update-all (cuando termina):
ntfy_send "docker" "🆙 Actualización completada" "$updated_count servicios actualizados"

# En svc health (cuando detecta servicio caído):
ntfy_send "docker" "⚠️ Servicio caído" "$service_name DOWN desde $(date)" "high" "warning"

# En backup cron:
ntfy_send "backups" "✅ Backup completado" "PostgreSQL: ${size}MB" "default" "floppy_disk"
```

---

## Plugin del agente: notification_plugin.py

```python
"""Plugin de notificaciones via ntfy para el agente NAS."""

import subprocess
from agent.plugins.base import BasePlugin

class NotificationPlugin(BasePlugin):
    name = "notification"
    
    def ntfy_send(self, topic="nas-alerts", title="", message="", priority="default", tags=""):
        """Enviar notificación via ntfy."""
        ntfy_url = self.config.get("ntfy_url", "http://localhost:8090")
        cmd = ["curl", "-s"]
        if title:
            cmd += ["-H", f"Title: {title}"]
        if priority:
            cmd += ["-H", f"Priority: {priority}"]
        if tags:
            cmd += ["-H", f"Tags: {tags}"]
        cmd += ["-d", message, f"{ntfy_url}/{topic}"]
        subprocess.run(cmd, capture_output=True, timeout=5)
    
    def on_service_down(self, service_name):
        """Hook: servicio detectado como caído."""
        self.ntfy_send("docker", f"⚠️ {service_name} DOWN", 
                      f"El servicio {service_name} no responde", "high", "warning")
    
    def on_backup_complete(self, service_name, size_mb):
        """Hook: backup completado."""
        self.ntfy_send("backups", f"✅ Backup {service_name}", 
                      f"Completado: {size_mb}MB", "default", "floppy_disk")
```

---

## usb-api: decisión de implementación

**Recomendado: systemd service nativo** (NO Docker) porque necesita ejecutar `umount` en el host.

Archivos a crear en DebMenux (templates) y copiar al sistema:
- `/usr/local/bin/usb-api.py` — servidor Python (Flask/http.server)
- `/etc/systemd/system/usb-api.service` — unit file

El catálogo en nas-dotfiles solo documenta la ficha (como servicio del sistema, no Docker).

---

## Homepage: widgets a agregar

En `$dkco/homepage/config/services.yaml`:

```yaml
- Sistema:
    - ntfy:
        icon: ntfy
        href: http://192.168.1.200:8090
        description: Notificaciones push del NAS
    - USB Manager:
        icon: usb
        href: http://192.168.1.200:8091
        description: Gestión de USB conectados
```

---

## Dependencias entre tareas

```
1. ntfy compose (DebMenux instala, nas-dotfiles documenta)
   ↓
2. lib/notifications.sh (ambos repos)
   ↓
3. Actualizar usb-automount.sh → usa ntfy_send (DebMenux)
   ↓
4. usb-api (DebMenux instala, nas-dotfiles documenta)
   ↓
5. Homepage widgets (nas-dotfiles, $dkco/homepage/)
   ↓
6. Agente plugin + daemon hooks (nas-dotfiles)
   ↓
7. SKILL.md + guía (nas-dotfiles)
```

---

## Notas técnicas

- ntfy usa puerto 8090 (no 80 para evitar conflicto con otros servicios)
- usb-api usa puerto 8091
- ntfy se conecta a `homepage_net` para que Homepage lo vea
- usb-api corre nativo (systemd) — NO en Docker (necesita umount real)
- `ntfy_send()` tiene fallback silencioso (`|| true`) — si ntfy no corre, no rompe nada
- Topics separados por contexto: usb, docker, backups, system, nas-alerts
- Prioridades: default (info), high (warning), urgent (critical)



---

## Caso de uso adicional: Alarma → Cámara → ntfy → PC/Celular

### Problema
Cuando la alarma suena, Home Assistant envía la imagen de la cámara a la TV.
Pero si el usuario está en la PC (no viendo la TV), no se entera.

### Solución
Home Assistant captura snapshot de la cámara y lo envía via ntfy con imagen adjunta.
ntfy lo muestra como push notification en Windows (browser) y Android (app) simultáneamente.

### Flujo

```
Sensor (ESPHome/Zigbee) → detecta movimiento
    ↓
Home Assistant → Automation triggered
    ↓
    1. camera.snapshot → /config/www/snapshots/alarma_FECHA.jpg
    2. curl con -T (attach file) → ntfy:8090/alarma
    ↓
ntfy (NAS :8090)
    ├── 📱 Android: push con imagen de la cámara
    └── 🖥️ Windows: browser push con imagen (Chrome/Edge PWA)
```

### ntfy: cómo enviar imagen adjunta

```bash
# Opción A: archivo local (snapshot guardado en disco)
curl -H "Title: 🚨 Alarma activada" \
     -H "Priority: urgent" \
     -H "Tags: rotating_light,camera" \
     -H "Filename: alarma.jpg" \
     -H "Actions: view, Ver cámara en vivo, http://192.168.1.200:8123/lovelace/camaras" \
     -T /config/www/snapshots/alarma.jpg \
     http://192.168.1.200:8090/alarma

# Opción B: URL externa (cámara expone endpoint de snapshot)
curl -H "Title: 🚨 Alarma activada" \
     -H "Priority: urgent" \
     -H "Attach: http://192.168.1.XXX/api/camera_proxy/camera.puerta" \
     -d "Movimiento detectado en puerta principal" \
     http://192.168.1.200:8090/alarma
```

### Home Assistant: automation YAML

```yaml
automation:
  - alias: "Alarma → Notificar con cámara via ntfy"
    trigger:
      - platform: state
        entity_id: alarm_control_panel.alarma
        to: "triggered"
    action:
      # 1. Capturar snapshot
      - service: camera.snapshot
        target:
          entity_id: camera.puerta_principal
        data:
          filename: "/config/www/snapshots/alarma_{{ now().strftime('%Y%m%d_%H%M%S') }}.jpg"
      # 2. Esperar a que se guarde
      - delay:
          seconds: 2
      # 3. Enviar a ntfy con imagen
      - service: shell_command.ntfy_alarma

shell_command:
  ntfy_alarma: >
    curl -H "Title: 🚨 Alarma activada"
    -H "Priority: urgent"
    -H "Tags: rotating_light"
    -H "Actions: view, Ver cámara en vivo, http://192.168.1.200:8123/lovelace/camaras"
    -H "Filename: alarma.jpg"
    -T /config/www/snapshots/alarma_$(date +%Y%m%d_%H%M%S).jpg
    http://192.168.1.200:8090/alarma
```

### Alternativa: integración ntfy para Home Assistant (custom component)

Repo: https://github.com/hbrennhaeuser/homeassistant_integration_ntfy
Soporta: auth, tags, imágenes adjuntas, resize/compress, action buttons.

```yaml
# En configuration.yaml:
notify:
  - platform: ntfy
    name: ntfy_nas
    url: http://192.168.1.200:8090
    topic: alarma

# En automation:
- service: notify.ntfy_nas
  data:
    title: "🚨 Alarma activada"
    message: "Movimiento en puerta principal"
    data:
      priority: urgent
      tags: rotating_light
      image: /config/www/snapshots/alarma.jpg
      actions:
        - action: view
          label: Ver cámara
          url: http://192.168.1.200:8123/lovelace/camaras
```

### Recibir en Windows (sin app nativa)

ntfy en Windows funciona via:
1. **Browser (pestaña abierta):** `http://192.168.1.200:8090/alarma` → "Allow notifications"
2. **PWA (mejor):** Chrome → menú ⋮ → "Instalar aplicación" → queda como app en taskbar
3. La notificación aparece como toast de Windows con la imagen adjunta

### Topic dedicado para alarmas

Agregar a la tabla de topics del plan:

| Topic | Quién envía | Prioridad | Ejemplo |
|-------|-------------|-----------|---------|
| `alarma` | Home Assistant | urgent | "🚨 Alarma: movimiento en puerta" + snapshot cámara |

### Opera Smart Home (bonus, no prioritario)

Opera GX Smart Home Extension conecta el browser al MQTT (EMQX).
Caso de uso complementario (NO para notificaciones):
- Home Assistant detecta Opera GX activo → "usuario está en PC"
- Automation: si alarma + usuario en PC → enviar a ntfy (no a TV)
- Automation: si alarma + usuario NO en PC → enviar a TV
- Requiere: Opera GX instalado + extensión + EMQX como broker

Esto es un bonus para DESPUÉS de tener ntfy funcionando.
Prioridad: implementar ntfy primero, Opera Smart Home después.
