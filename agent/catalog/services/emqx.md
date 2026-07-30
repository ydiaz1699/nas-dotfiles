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
  - EMQX_PORT_WS=7083
  - EMQX_PORT_WSS=7084
  - EMQX_PORT_DASHBOARD=18083
healthcheck: "emqx ping"
backup_critical: true
backup_paths:
  - "./data/data"
protected: false
docs_url: "https://docs.emqx.com/en/emqx/latest/"
notes: "Requiere ulimits nofile alto (1048576). Dashboard en puerto 18083 (solo localhost)."
networks:
  - iot_net
  - db_net
ports:
  mqtt: 1883
  mqtts: 8883
  ws: 7083
  wss: 7084
  dashboard: 18083
---

# EMQX

## Qué es

Broker MQTT distribuido de alto rendimiento para IoT/domótica. Soporta MQTT 5.0,
WebSocket, SSL/TLS, clustering y dashboard web para monitoreo de dispositivos.

## Estructura

```
/docker/emqx/
├── compose.yml
├── .env                    ← permisos 600
└── data/
    ├── data/
    └── log/
```

## Setup inicial

```bash
mkdir -p $dkco/emqx/data/{data,log}
docker network create iot_net    # si no existe
```

## compose.yml

```yaml
x-common-env: &common-env
  TZ: ${TZ}

x-common-ports: &common-ports
  - "${EMQX_PORT_MQTT}:1883"
  - "${EMQX_PORT_MQTTS}:8883"
  - "${EMQX_PORT_WS}:8083"
  - "${EMQX_PORT_WSS}:8084"
  - "127.0.0.1:${EMQX_PORT_DASHBOARD}:18083"

x-healthcheck-defaults: &healthcheck-defaults
  interval: 30s
  timeout: 10s
  retries: 5
  start_period: 40s

x-security-defaults: &security-defaults
  security_opt:
    - no-new-privileges:true
  ulimits:
    nofile:
      soft: 1048576
      hard: 1048576

x-logging-defaults: &logging-defaults
  driver: json-file
  options:
    max-size: "10m"
    max-file: "3"

x-resource-defaults: &resource-defaults
  deploy:
    resources:
      limits:
        memory: 1g
      reservations:
        memory: 256m

services:
  emqx:
    image: emqx/emqx:5.8.3
    container_name: emqx
    restart: unless-stopped
    <<: [*security-defaults, *resource-defaults]

    environment:
      <<: *common-env
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

    healthcheck:
      <<: *healthcheck-defaults
      test: ["CMD", "emqx", "ping"]

    logging: *logging-defaults

    volumes:
      - ./data/data:/opt/emqx/data
      - ./data/log:/opt/emqx/log

    ports: *common-ports

    networks:
      - iot_net
      - db_net

networks:
  iot_net:
    external: true
  db_net:
    external: true
```

## .env

```bash
TZ=America/La_Paz
EMQX_NODE_COOKIE=__pega_aqui__
EMQX_DASHBOARD_USER=admin
EMQX_DASHBOARD_PASSWORD=__pega_aqui__
EMQX_ALLOW_ANONYMOUS=false
EMQX_PORT_MQTT=1883
EMQX_PORT_MQTTS=8883
EMQX_PORT_WS=7083
EMQX_PORT_WSS=7084
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
- Dashboard solo accesible desde localhost (127.0.0.1:18083)

## Puertos

| Puerto | Protocolo | Descripción |
|--------|-----------|-------------|
| 1883   | MQTT      | MQTT sin TLS |
| 8883   | MQTTS     | MQTT con TLS |
| 7083   | WS        | WebSocket |
| 7084   | WSS       | WebSocket seguro |
| 18083  | HTTP      | Dashboard (solo localhost) |

## Redes

- `iot_net`: Red para dispositivos IoT (compartida con Node-RED, HA, etc.)
- `db_net`: Red para acceso a bases de datos (si se configura persistencia externa)

## Volúmenes y datos

- `./data/data/` — Base de datos interna, sesiones MQTT, reglas, usuarios
- `./data/log/` — Logs del broker

## Levantar

```bash
svc config emqx     # valida sintaxis (incluido merge de anchors)
svc up emqx
svc ps emqx          # healthy en ~40s
svc logs emqx
```

## Notas

- Requiere ulimits nofile alto (1048576) para manejar miles de conexiones MQTT
- El merge de anchors `<<: [*security-defaults, *resource-defaults]` funciona en
  YAML puro pero validar con `svc config emqx` por si Docker Compose es más estricto
- Pendiente: confirmar si el NAS corre Swarm (afecta si `deploy:` hace algo real)
- Pendiente: archivo `emqx.conf` montado en vez de env vars para config avanzada
- Pendiente: reverse proxy/TLS para exposición a internet
