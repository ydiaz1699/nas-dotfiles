---
id: "usb-api"
name: "USB API"
description: "Mini API REST para listar y desmontar USBs desde web (Homepage widget)"
image: null
category: "sistema"
port_internal: 8091
port_default: 8091
protocol: "http"
native: true
needs_proxy: false
needs_db: false
db_type: ""
volumes: []
env_required:
  - USB_API_PORT
  - MOUNT_BASE
  - NTFY_URL
env_optional:
  - USB_API_BIND=0.0.0.0
healthcheck: "GET /health"
backup_critical: false
backup_paths: []
protected: false
docs_url: "docs/services/ntfy-guide.md"
notes: "Servicio NATIVO (systemd, NO Docker) porque necesita ejecutar umount en el host. Instalado por DebMenux scripts/services/usb-api.sh. El script Python está en /usr/local/lib/usb-api/server.py. Unit file en /etc/systemd/system/usb-api.service. Requiere acceso a MOUNT_BASE (/NAS/USB). Envía notificación a ntfy al desmontar. CORS habilitado para Homepage widgets."
networks: []
ports:
  http: 8091
resources:
  memory_limit: "32m"
aliases:
  - usb-api
  - usb
  - usb-manager
  - eject
---

# USB API

## Qué es

Mini servidor REST que expone endpoints para listar y desmontar dispositivos USB
montados en el NAS. Diseñado para ser consumido por Homepage (widget customapi)
y permitir al usuario expulsar USBs sin acceder a la terminal.

## Tipo de servicio

**Nativo (systemd)** — NO es un contenedor Docker.

Razón: necesita ejecutar `umount` directamente en el host. Un contenedor Docker
necesitaría `privileged: true` o acceso al socket Docker, ambos inseguros.

## Ubicación de archivos

```
/usr/local/lib/usb-api/server.py      ← Script Python (stdlib, sin pip)
/etc/systemd/system/usb-api.service   ← Unit file systemd
```

## Endpoints

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/usb/list` | Lista USBs montados (JSON) |
| POST | `/usb/unmount/:dev` | Desmonta USB de forma segura |
| GET | `/health` | Health check |

## Respuesta de /usb/list

```json
{
  "count": 2,
  "mount_base": "/NAS/USB",
  "devices": [
    {
      "device": "sdb1",
      "source": "/dev/sdb1",
      "mountpoint": "/NAS/USB/usb-sdb1",
      "fstype": "ntfs",
      "size": "500G",
      "used": "120G",
      "avail": "380G",
      "use_percent": "24%"
    }
  ]
}
```

## Gestión

```bash
# Estado
systemctl status usb-api

# Logs en tiempo real
journalctl -u usb-api -f

# Reiniciar
systemctl restart usb-api

# Deshabilitar
systemctl disable --now usb-api
```

## Seguridad

- Solo escucha en LAN (configurable via USB_API_BIND)
- Sin autenticación por ahora (LAN interna)
- Sanitiza nombres de dispositivos (solo [a-zA-Z0-9_-])
- Verifica que el mountpoint está bajo MOUNT_BASE antes de desmontar
- No puede desmontar rutas fuera de MOUNT_BASE

## Integración con Homepage

Widget customapi en services.yaml:
```yaml
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
