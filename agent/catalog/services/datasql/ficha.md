---
id: "datasql"
name: "ParadeDB PostgreSQL (datasql)"
description: "Stack final de ParadeDB PostgreSQL 17 con pgvector, pg_search y pg_cron, pgAdmin 9.17 y Redis 7"
aliases:
  - datasql
  - datapostgres
  - datapgadmin
  - dataredis
  - aipostgres
  - ai-postgres
  - postgres-ia
  - postgres
  - pgadmin
  - redis
  - paradedb
  - pgvector
  - pg_search
  - vector-db
  - semantic-search
image: "paradedb/paradedb:0.25.4-pg17"
category: "base-datos"
port_internal: 5432
port_default: 5432
protocol: "tcp"
needs_proxy: false
needs_db: false
db_type: "postgres"
services:
  postgres:
    image: "paradedb/paradedb:0.25.4-pg17"
    container_name: "datapostgres"
    port_internal: 5432
    port_default: 5432
    exposure: "loopback"
    healthcheck: '["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]'
    volumes:
      - "./data/postgres/pgdata:/var/lib/postgresql/data/pgdata"
      - "./data/postgres/backups:/backups"
    resources:
      memory_limit: "1536M"
      memory_reservation: "256M"
      cpus_limit: "1.5"
      cpus_reservation: "0.25"
  pgadmin:
    image: "dpage/pgadmin4:9.17"
    container_name: "datapgadmin"
    port_internal: 80
    port_default: 5050
    exposure: "lan"
    healthcheck: null
    volumes:
      - "./data/pgadmin:/var/lib/pgadmin"
    resources:
      memory_limit: "512M"
      memory_reservation: "128M"
      cpus_limit: "1"
      cpus_reservation: "0.25"
  redis:
    image: "redis:7-alpine"
    container_name: "dataredis"
    port_internal: 6379
    port_default: null
    exposure: "internal"
    healthcheck: '["CMD", "redis-cli", "-a", "${REDIS_PASSWORD}", "ping"]'
    volumes:
      - "./data/redis:/data"
    resources:
      memory_limit: "256M"
      memory_reservation: "64M"
      cpus_limit: "0.5"
      cpus_reservation: "0.1"
env_required:
  - POSTGRES_DB
  - POSTGRES_USER
  - POSTGRES_PASSWORD
  - PGADMIN_EMAIL
  - PGADMIN_PASSWORD
  - REDIS_PASSWORD
env_optional:
  - AIPG_POSTGRES_HOST_PORT=5432
  - AIPGADMIN_PORT=5050
backup_critical: true
backup_paths:
  - "./data/postgres/backups"
  - "./data/postgres/pgdata"
  - "./data/pgadmin"
  - "./data/redis"
protected: false
docs_url: "docs/services/datasql-guide.md"
install_docs_url: "docs/services/aipostgres-guide.md"
notes: "Servicio operativo final en $dkco/datasql. ParadeDB usa datapostgres y publica PostgreSQL solo en 127.0.0.1:5432 para Home Assistant host-network; los consumidores Docker usan datapostgres:5432 en db_net. pgAdmin usa datapgadmin y se expone como dashboard LAN en :5050, excepción documentada. Redis usa dataredis:6379 solo en db_net y no publica ports. La base administrativa de PostgreSQL se llama aipostgres y el usuario es aiadmin. El compose precarga pg_search y pg_cron, configura cron.database_name con POSTGRES_DB, hereda SERVER_IP/TZ desde ../.env y no fija ipv4_address. datasql-guide.md documenta consumidores y creación de bases/roles; aipostgres-guide.md documenta instalación y operación del stack."
networks:
  - db_net
ports:
  postgres_loopback: 5432
  pgadmin: 5050
security_extra:
  postgres: {}
  pgadmin:
    note: "Dashboard LAN aprobado en :5050; no heredar security_opt/cap_drop porque pgAdmin usa sudo internamente."
  redis:
    security_opt: ["no-new-privileges:true"]
    cap_drop: ["ALL"]
    cap_add: ["CHOWN", "DAC_OVERRIDE", "SETUID", "SETGID"]
---

## Referencia del agente

La ficha debe apuntar a `docs/services/datasql-guide.md` para el uso por consumidores. La instalación y operación del stack están en `docs/services/aipostgres-guide.md`.
