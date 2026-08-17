---
id: "ntfy"
name: "ntfy"
description: "Servidor de notificaciones push HTTP pub-sub self-hosted"
image: "binwiederhier/ntfy:latest"
category: "sistema"
port_internal: 80
port_default: 8090
protocol: "http"
needs_proxy: false
needs_db: false
db_type: ""
volumes:
  - "./config:/etc/ntfy"
  - "./data/cache:/var/cache/ntfy"
  - "./data/lib:/var/lib/ntfy"
  - "./data/attachments:/var/cache/ntfy/attachments"
env_required:
  - SERVER_IP
env_optional:
  - NTFY_AUTH_DEFAULT_ACCESS=read-write
healthcheck: '["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://localhost:80/v1/health"]'
backup_critical: false
backup_paths:
  - "./data/lib"
  - "./config"
protected: false
docs_url: "docs/services/ntfy-guide.md"
notes: "Stateless cache — los mensajes se guardan 24h y luego se purgan. Los attachments (imágenes de cámaras) expiran en 24h. Auth por defecto abierto (LAN only). Para exponer a internet: cambiar auth-default-access a deny-all y crear usuarios con ntfy user add."
networks:
  - homepage_net
ports:
  http: 8090
resources:
  memory_limit: "256m"
  memory_reservation: "64m"
aliases:
  - ntfy
  - notificaciones
  - push
  - alertas
---

# ntfy

## Qué es

Servidor de notificaciones push basado en HTTP pub-sub. Permite enviar alertas
desde cualquier script (curl) y recibirlas en Android (app ntfy), Windows (browser
PWA), Linux (curl/websocket), e iOS (limitado).

## Estructura

```
$dkco/ntfy/
├── compose.yml
├── .env                    ← SERVER_IP, TZ (solo globales, sin secretos)
├── config/
│   └── server.yml          ← configuración del servidor
└── data/
    ├── cache/              ← cache.db (mensajes temporales)
    ├── lib/                ← BD de usuarios/ACL (si auth habilitada)
    └── attachments/        ← imágenes adjuntas (alarma/cámaras)
```

## Topics configurados

| Topic | Quién envía | Prioridad | Ejemplo |
|-------|-------------|-----------|---------|
| `usb` | usb-automount.sh | default/high | "USB sdb1 montado" |
| `docker` | svc / agent daemon | high | "emqx DOWN" |
| `backups` | cron / svc backup | default | "Backup PostgreSQL OK: 2.3GB" |
| `system` | SMART / SSH / cron | urgent | "Disco predice fallo" |
| `alarma` | Home Assistant | urgent | "🚨 Movimiento en puerta" + snapshot |
| `nas-alerts` | catch-all | varies | Cualquier alerta general |

## Redes

- `homepage_net`: Para que Homepage pueda consultar stats via API interna

## Enviar notificación (ejemplos)

```bash
# Básica
curl -d "Hola mundo" http://192.168.1.200:8090/nas-alerts

# Con título + prioridad + tags
curl -H "Title: 🔌 USB Montado" -H "Priority: default" -H "Tags: usb" \
     -d "sdb1 (ntfs) → /NAS/USB/usb-sdb1" http://192.168.1.200:8090/usb

# Con imagen adjunta (alarma + cámara)
curl -H "Title: 🚨 Alarma" -H "Priority: urgent" -H "Tags: rotating_light" \
     -H "Filename: alarma.jpg" -T /path/to/snapshot.jpg http://192.168.1.200:8090/alarma
```

## Clientes

- **Android:** App "ntfy" (F-Droid / Play Store) → agregar servidor → http://IP:8090
- **Windows:** Chrome/Edge → abrir http://IP:8090/TOPIC → permitir notificaciones → instalar PWA
- **CLI:** `curl -s http://IP:8090/TOPIC/json` (SSE stream)

## docs_url

docs/services/ntfy-guide.md
