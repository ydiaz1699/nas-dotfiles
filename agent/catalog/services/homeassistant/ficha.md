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
needs_db: false
db_type: "postgresql opcional (externo; DataSQL usa 127.0.0.1:5432)"
volumes:
  - "./data:/config"
  - "/etc/localtime:/etc/localtime:ro"
  - "/run/dbus:/run/dbus:ro"
env_required:
  - HOMEASSISTANT_TOKEN
env_optional: []
healthcheck: '["CMD", "curl", "-f", "http://localhost:8123"]'
backup_critical: true
backup_paths:
  - "./data"
protected: true
docs_url: "docs/services/homeassistant-guide.md"
notes: "Usa network_mode: host (acceso directo a LAN para mDNS, descubrimiento IoT, USB y Bluetooth), stop_grace_period: 60s y DNS explícitos. Privileged: true es requerido por las integraciones de hardware; no agregar cap_drop/cap_add. Home Assistant usa SQLite por defecto en /config/home-assistant_v2.db y puede usar PostgreSQL opcionalmente mediante Recorder + db_url en su configuración persistente. La guía docs/services/homeassistant-datasql-guide.md prepara/verifica el backend, configura HA cuando se elige PostgreSQL y verifica db_url, pg_stat_activity y tablas. Para comandos `sh -c` en este NAS usar `NAS_CLI=bash svc exec homeassistant homeassistant sh -c ...`; el nombre interno Compose debe repetirse y no debe exponerse `-c` al parser Python. Para el caso NAS/DataSQL la URI usa 127.0.0.1:5432 por host networking; no usar datapostgres ni db_net desde HA. Completar el onboarding antes de editar configuration.yaml. Config organizada con !include en carpeta includes/. Integración ntfy para push notifications con imagen vía shell_command + curl, no ntfy.publish. TvOverlay configurado como rest_command. SERVER_IP y TZ se heredan del env_file global; HOMEASSISTANT_TOKEN es local para el widget de Homepage."
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

## Configuración operacional

- `network_mode: host` y `privileged: true` se mantienen para mDNS, descubrimiento
  IoT, USB, Bluetooth y dbus.
- El compose define `stop_grace_period: 60s`, DNS explícitos, healthcheck HTTP y
  límites de 2 CPU/2 GiB (reserva 0.5 CPU/512 MiB).
- El onboarding debe completarse antes de editar `configuration.yaml`.
- El Recorder usa SQLite por defecto en `home-assistant_v2.db`; PostgreSQL es opcional y requiere configurar `recorder.db_url` en HA.
- `SERVER_IP` y `TZ` vienen de `$dkco/.env`; `HOMEASSISTANT_TOKEN` permanece en el `.env` local para el widget de Homepage.

## Integraciones configuradas

- **ntfy** — integración oficial (texto) + shell_command (imágenes)
- **TvOverlay** — rest_command para notificaciones en Android TV
- **EMQX** — broker MQTT accesible desde HA por la red del host; no se agrega
  `network_mode: host` a `iot_net` ni se declara una red Docker en este compose.
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
