---
id: "flowise"
name: "Flowise"
description: "Constructor visual de agentes y flujos LLM conectado a PostgreSQL de DataSQL"
aliases:
  - flowise
  - ai
  - agentes
  - llm
  - langchain
image: "flowiseai/flowise:latest"
category: "desarrollo"
port_internal: 3000
port_default: 8100
protocol: "http"
needs_proxy: false
needs_db: true
db_type: "postgres"
volumes:
  - "./data:/home/node/.flowise"
env_required:
  - SERVER_IP
  - FLOWISE_DB_NAME
  - FLOWISE_DB_USER
  - FLOWISE_DB_PASSWORD
  - FLOWISE_SECRETKEY_OVERWRITE
env_optional:
  - DATABASE_SSL=false
  - DISABLE_FLOWISE_TELEMETRY=true
healthcheck: '["CMD", "curl", "-f", "http://localhost:3000/api/v1/ping"]'
backup_critical: true
backup_paths:
  - "./data"
protected: false
docs_url: "docs/services/flowise-guide.md"
notes: "Flowise usa PostgreSQL dedicado en DataSQL mediante db_net y el hostname datapostgres; no usa depends_on contra otro compose. El dashboard se expone en LAN en :8100 para esta prueba y debe protegerse antes de exponerlo fuera de la LAN. La ruta relativa ./data del compose siempre corresponde a $dkco/flowise/data y debe pertenecer al uid 1000 del contenedor. El backup requiere tanto los datos de Flowise como un pg_dump de flowise_db. La memoria de 1G es provisional hasta medir con svc stats."
networks:
  - db_net
ports:
  http: 8100
resources:
  memory_limit: "1g"
  memory_reservation: "256m"
security_extra:
  cap_drop:
    - ALL
---

# Flowise

## Qué es

Flowise es una interfaz visual para construir chatflows y agentes basados en
modelos y componentes de LangChain. En este NAS se prueba como servicio separado
y usa una base PostgreSQL dedicada dentro de DataSQL.

## Estructura

```
$dkco/flowise/
├── compose.yml
├── .env                    ← secretos y credenciales de flowise_db, permisos 600
└── data/                   ← /home/node/.flowise dentro del contenedor
    ├── logs/
    └── storage/
```

## Conexión con DataSQL

- Red: `db_net` externa.
- Host: `datapostgres`.
- Puerto: `5432` interno.
- Base: `flowise_db`.
- Usuario: `flowise_user`.
- No se crea otro PostgreSQL y no se publica `5432` al host.

## Exposición

El panel se publica temporalmente en `http://${SERVER_IP}:8100` para la prueba.
Es una excepción documentada de exposición LAN; no debe tratarse como una
publicación segura para Internet. Antes de exponerlo fuera de la LAN se necesita
reverse proxy, autenticación y revisar la configuración de seguridad de Flowise.
