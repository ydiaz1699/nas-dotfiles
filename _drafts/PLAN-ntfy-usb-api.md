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
