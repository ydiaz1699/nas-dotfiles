---
id: "flowise"
name: "Flowise"
description: "Flowise en modo queue con PostgreSQL y Redis de DataSQL, un main y un worker"
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
  - REDIS_PASSWORD
  - FLOWISE_USERNAME
  - FLOWISE_PASSWORD
  - FLOWISE_SECRETKEY_OVERWRITE
  - JWT_AUTH_TOKEN_SECRET
  - JWT_REFRESH_TOKEN_SECRET
  - JWT_ISSUER
  - JWT_AUDIENCE
  - JWT_TOKEN_EXPIRY_IN_MINUTES
  - JWT_REFRESH_TOKEN_EXPIRY_IN_MINUTES
  - EXPRESS_SESSION_SECRET
  - TOKEN_HASH_SECRET
env_optional:
  - DATABASE_SSL=false
  - DISABLE_FLOWISE_TELEMETRY=true
  - WORKER_CONCURRENCY=5
  - TRUST_PROXY=false
  - SECURE_COOKIES=false
  - NUMBER_OF_PROXIES=0
healthcheck: '["CMD", "curl", "-f", "http://localhost:3000/api/v1/ping"]'
backup_critical: true
backup_paths:
  - "./data"
  - "$dkco/datasql/data/postgres/backups/flowise_db_*.sql"
protected: true
docs_url: "docs/services/flowise-guide.md"
notes: "Flowise usa MODE=queue con PostgreSQL dedicado flowise_db en datapostgres y Redis dataredis mediante la red externa db_net. Main y worker comparten FLOWISE_SECRETKEY_OVERWRITE, el bind ./data y la configuración de queue. El main usa flowiseai/flowise:latest y el worker la imagen oficial separada flowiseai/flowise-worker:latest; el worker inicia healthcheck.js y pnpm run start-worker, valida /healthz en el puerto interno 5566 y no publica ese puerto. Main y worker tienen límites de 1g y reserva de 256m. No se usa depends_on contra DataSQL. El dashboard se publica en LAN en :8100 durante esta fase; no debe exponerse a Internet sin reverse proxy y HTTPS. svc no implementa scale todavía y flowise-worker conserva container_name fijo. El backup requiere los datos de Flowise y un dump de flowise_db. La etiqueta latest es mutable: verificar la versión real antes de fijarla o actualizarla."
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

Flowise es una interfaz visual para construir chatflows y agentes basados en
modelos y componentes de LangChain. En este NAS se ejecuta en modo `queue`: el
main atiende la API y el worker procesa ejecuciones mediante Redis.

La guía operativa única es `docs/services/flowise-guide.md`. Esta ficha solo
contiene metadatos para el catálogo y apunta a esa guía; no duplica su
procedimiento.

## Arquitectura resumida

- PostgreSQL dedicado `flowise_db` en `datapostgres`.
- Redis compartido `dataredis`, con `QUEUE_NAME=flowise-queue`.
- Red externa `db_net`.
- Main publicado temporalmente en `${SERVER_IP}:8100`.
- Main usa `flowiseai/flowise:latest`; worker usa `flowiseai/flowise-worker:latest` y arranca el healthcheck auxiliar antes de `pnpm run start-worker`.
- Worker interno con healthcheck en `5566/healthz`.
- Bind mount `./data:/home/node/.flowise` compartido por main y worker.
- No se publican `5432`, `6379` ni `5566` al host.
