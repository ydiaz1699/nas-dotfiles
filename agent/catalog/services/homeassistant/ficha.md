---
id: "homeassistant"
name: "Home Assistant"
description: "Plataforma de automatización del hogar con integraciones IoT"
image: "ghcr.io/home-assistant/home-assistant:stable"
category: "domótica"
port_internal: 8123
port_default: 8123
protocol: "http"
needs_proxy: false
needs_db: true
db_type: "postgresql (externo via 127.0.0.1:5432)"
volumes:
  - "./data:/config"
  - "/etc/localtime:/etc/localtime:ro"
  - "/run/dbus:/run/dbus:ro"
env_required:
  - HOMEASSISTANT_TOKEN
env_optional:
  - TZ=America/La_Paz
healthcheck: '["CMD", "curl", "-f", "http://localhost:8123"]'
backup_critical: true
backup_paths:
  - "./data"
protected: true
docs_url: "docs/services/homeassistant-guide.md"
notes: "Usa network_mode: host (acceso directo a LAN para mDNS, descubrimiento IoT, USB y Bluetooth). Privileged: true (USB, Bluetooth, dbus). El Recorder usa PostgreSQL externo en homeassistant_db mediante 127.0.0.1:5432; DataSQL debe estar saludable antes de iniciar HA. No usa db_net ni debe conectarse a datapostgres por DNS mientras conserve host networking. Config organizada con !include en carpeta includes/. Integración ntfy para push notifications con imagen (via shell_command, no ntfy.publish — este último no soporta attachments aún). TvOverlay configurado como rest_command."
networks: []
ports:
  http: 8123
resources:
  memory_limit: "2g"
  memory_reservation: "512m"
aliases:
  - homeassistant
  - home-assistant
  - ha
  - domótica
  - automatización
---

# Home Assistant

## Qué es

Plataforma de automatización del hogar. Controla cámaras, sensores, luces,
alarmas, y se integra con EMQX (MQTT), ESPHome, ntfy, TvOverlay.

## Estructura

```
$dkco/homeassistant/
├── compose.yml
├── .env                    ← HOMEASSISTANT_TOKEN (Homepage widget)
└── data/                   ← /config dentro del contenedor
    ├── configuration.yaml  ← con !includes
    ├── includes/
    │   ├── shell_commands.yaml
    │   ├── tvoverlay_commands.yaml
    │   └── notify.yaml
    └── www/snapshots/      ← imágenes de cámara
```

## Integraciones configuradas

- **ntfy** — integración oficial (texto) + shell_command (imágenes)
- **TvOverlay** — rest_command para notificaciones en Android TV
- **EMQX** — broker MQTT (via iot_net, accesible por network_mode:host)
- **ESPHome** — dispositivos ESP32/ESP8266

## Entidades clave

| Entidad | Tipo | Uso |
|---------|------|-----|
| `camera.camara_profile_000` | Cámara | Snapshot, stream |
| `binary_sensor.camara_cell_motion_detection` | Sensor | Trigger movimiento |
| `notify.nas_alerts` | ntfy | Notificaciones texto |
| `shell_command.ntfy_camara` | Shell | ntfy con imagen |
| `rest_command.tvoverlay_notify` | REST | Overlay en TV |

## docs_url

docs/services/homeassistant-guide.md
