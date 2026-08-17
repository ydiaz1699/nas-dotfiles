---
id: "emqx"
name: "EMQX"
description: "Broker MQTT distribuido y de alto rendimiento para IoT"
image: "emqx/emqx:5.8.3"
category: "domótica"
port_internal: 1883
port_default: 1883
protocol: "mqtt"
needs_proxy: false
needs_db: false
db_type: ""
volumes:
  - "./data/data:/opt/emqx/data"
  - "./data/log:/opt/emqx/log"
env_required:
  - EMQX_NODE_COOKIE
  - EMQX_DASHBOARD_USER
  - EMQX_DASHBOARD_PASSWORD
env_optional:
  - EMQX_ALLOW_ANONYMOUS=false
  - EMQX_PORT_MQTT=1883
  - EMQX_PORT_MQTTS=8883
  - EMQX_PORT_WS=8083
  - EMQX_PORT_WSS=8084
  - EMQX_PORT_DASHBOARD=18083
healthcheck: '["CMD", "emqx", "ctl", "status"]'
backup_critical: true
backup_paths:
  - "./data/data"
protected: false
docs_url: "docs/services/emqx-guide.md"
notes: "Requiere ulimits nofile alto (1048576). Dashboard en puerto 18083, expuesto en LAN (no restringido a localhost pese a la regla general de _compose_base.md); ver justificación en README del servicio. Usa env_file: [../.env, .env] para heredar SERVER_IP y TZ del .env global."
networks:
  - iot_net
ports:
  mqtt: 1883
  mqtts: 8883
  ws: 8083
  wss: 8084
  dashboard: 18083
resources:
  memory_limit: "1g"
  memory_reservation: "256m"
security_extra:
  ulimits:
    nofile:
      soft: 1048576
      hard: 1048576
---

# EMQX

## Qué es

Broker MQTT distribuido de alto rendimiento para IoT/domótica. Soporta MQTT 5.0,
WebSocket, SSL/TLS, clustering y dashboard web para monitoreo de dispositivos.

## Estructura

```
/docker/emqx/
├── compose.yml
├── .env                    ← secretos del servicio (permisos 600)
└── data/
    ├── data/               ← BD interna, sesiones, reglas, usuarios
    └── log/                ← logs del broker
```

Hereda variables globales de `$dkco/.env` (SERVER_IP, TZ) via:
```yaml
env_file:
  - ../.env      # global
  - .env         # secretos locales (sobreescribe si hay conflicto)
```

## Setup inicial

```bash
mkdir -p $dkco/emqx/data/{data,log}
docker network create iot_net    # si no existe
```

## Variables de entorno específicas

```yaml
environment:
  EMQX_NODE__NAME: "emqx@emqx.iot_net"
  EMQX_NODE__COOKIE: "${EMQX_NODE_COOKIE}"
  EMQX_NODE__ROLE: core
  EMQX_CLUSTER__DISCOVERY_STRATEGY: manual
  EMQX_DASHBOARD__DEFAULT_USERNAME: "${EMQX_DASHBOARD_USER}"
  EMQX_DASHBOARD__DEFAULT_PASSWORD: "${EMQX_DASHBOARD_PASSWORD}"
  EMQX_ALLOW_ANONYMOUS: "${EMQX_ALLOW_ANONYMOUS:-false}"
  EMQX_LOG__CONSOLE_HANDLER__LEVEL: warning
  EMQX_MQTT__SESSION_EXPIRY_INTERVAL: 1h
  EMQX_MQTT__MAX_TOPIC_LEVELS: 7
```

## Puertos

| Puerto | Protocolo | Descripción |
|--------|-----------|-------------|
| 1883   | MQTT      | MQTT sin TLS |
| 8883   | MQTTS     | MQTT con TLS |
| 8083   | WS        | WebSocket MQTT |
| 8084   | WSS       | WebSocket seguro MQTT |
| 18083  | HTTP      | Dashboard (expuesto en LAN) |

## Redes

- `iot_net`: Compartida con Node-RED, Home Assistant, ESPHome

> Nota: `db_net` se eliminó por mínimo privilegio. Reconectar cuando se implemente
> persistencia externa (PostgreSQL como backend de EMQX).

## .env

```bash
TZ=America/La_Paz
EMQX_NODE_COOKIE=__pega_aqui__
EMQX_DASHBOARD_USER=admin
EMQX_DASHBOARD_PASSWORD=__pega_aqui__
EMQX_ALLOW_ANONYMOUS=false
EMQX_PORT_MQTT=1883
EMQX_PORT_MQTTS=8883
EMQX_PORT_WS=8083
EMQX_PORT_WSS=8084
EMQX_PORT_DASHBOARD=18083
```

### Generar secretos

```bash
COOKIE=$(openssl rand -hex 32)
PASS=$(openssl rand -base64 18 | tr -d '/+=')
sed -i \
  -e "0,/__pega_aqui__/s//${COOKIE}/" \
  -e "0,/__pega_aqui__/s//${PASS}/" \
  "$dkco/emqx/.env"
chmod 600 "$dkco/emqx/.env"
```

## Configuración importante

- `EMQX_NODE_COOKIE`: Token secreto para clustering (hex 64 chars)
- `EMQX_DASHBOARD_PASSWORD`: Password del panel admin
- `EMQX_ALLOW_ANONYMOUS`: SIEMPRE false en producción
- Dashboard expuesto en LAN (sin bind a localhost) para acceso frecuente
  desde otros equipos en la red local

## Notas

- Requiere ulimits nofile alto (1048576) para manejar miles de conexiones MQTT
- Dashboard NO está restringido a localhost (excepción documentada a la regla
  general de _compose_base.md) porque se accede frecuentemente desde la LAN
- Pendiente: confirmar si el NAS corre Swarm (afecta si `deploy:` hace algo real)
- Pendiente: archivo `emqx.conf` montado en vez de env vars para config avanzada
- Pendiente: reverse proxy/TLS para exposición a internet
