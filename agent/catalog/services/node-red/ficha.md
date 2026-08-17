---
id: "node-red"
name: "Node-RED"
description: "Plataforma visual de automatización de flujos IoT"
image: "nodered/node-red:latest"
category: "domótica"
port_internal: 1880
port_default: 1880
protocol: "http"
needs_proxy: false
needs_db: false
db_type: ""
volumes:
  - "./data:/data"
env_required: []
env_optional: []
healthcheck: '["CMD", "curl", "-f", "http://localhost:1880"]'
backup_critical: true
backup_paths:
  - "./data"
protected: false
docs_url: "docs/services/node-red-guide.md"
notes: "Conectado a iot_net para comunicación con EMQX (MQTT), ESPHome, y HA. NO usar cap_drop:[ALL] — Node-RED instala paquetes npm en runtime y necesita permisos flexibles. Los flujos se guardan en ./data/flows.json."
networks:
  - iot_net
ports:
  http: 1880
resources:
  memory_limit: "sin definir (medir con docker stats primero)"
aliases:
  - node-red
  - nodered
  - flujos
  - flows
---

# Node-RED

## Qué es

Plataforma visual de automatización basada en flujos (drag & drop).
Conecta EMQX (MQTT), Home Assistant, APIs, bases de datos, y más.

## Estructura

```
$dkco/node-red/
├── compose.yml
├── .env          ← vacío (solo hereda del global)
└── data/
    ├── flows.json        ← flujos (fuente de verdad)
    ├── flows_cred.json   ← credenciales de nodos (encriptadas)
    ├── settings.js       ← configuración del servidor
    └── node_modules/     ← paquetes npm instalados
```

## Redes

- `iot_net`: Comunicación con EMQX (mqtt://emqx:1883), ESPHome, HA

## docs_url

docs/services/node-red-guide.md
