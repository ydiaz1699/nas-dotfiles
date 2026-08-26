---
id: "aipostgres"
name: "PostgreSQL IA"
description: "Stack sucesor de DataSQL: PostgreSQL 17 con pgvector/pg_search, pgAdmin 4 y Redis 7"
aliases:
  - aipostgres
  - ai-postgres
  - postgres-ia
  - paradedb
  - pgvector
  - pg_search
  - vector-db
  - semantic-search
  - pgadmin-ia
  - redis-ia
image: "paradedb/paradedb:0.25.4-pg17"
category: "base-datos"
port_internal: 5432
port_default: 5433
protocol: "tcp"
needs_proxy: false
needs_db: false
db_type: "postgres"
services:
  postgres:
    image: "paradedb/paradedb:0.25.4-pg17"
    container_name: "aipostgres"
    port_internal: 5432
    port_default: 5433
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
    image: "dpage/pgadmin4:latest"
    container_name: "aipgadmin"
    port_internal: 80
    port_default: 5051
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
    container_name: "airedis"
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
  - AIPG_POSTGRES_HOST_PORT=5433
  - AIPGADMIN_PORT=5051
backup_critical: true
backup_paths:
  - "./data/postgres/backups"
  - "./data/postgres/pgdata"
  - "./data/pgadmin"
  - "./data/redis"
protected: false
docs_url: "docs/services/aipostgres-guide.md"
notes: "Stack completo sucesor de DataSQL: postgres es aipostgres, pgAdmin es aipgadmin y Redis es airedis. Durante la coexistencia PostgreSQL se publica solo en 127.0.0.1:5433 para preparar la migración de Home Assistant, pgAdmin en LAN :5051 y Redis permanece interno. Los consumidores Docker deben usar aipostgres:5432 y airedis:6379. La imagen ParadeDB 0.25.4-pg17 incluye pgvector y pg_search; pg_search se carga mediante shared_preload_libraries. El REDIS_PASSWORD de airedis se genera nuevo y no se copia desde DataSQL; solo consumidores aún conectados a dataredis conservan la credencial antigua. No incluye RustFS: RustFS es un servicio S3 independiente y solo se instala cuando existe LobeHub u otro consumidor de objetos. En el catálogo extends.file es ../../_common.yml; el compose desplegado usa ../_common.yml."
networks:
  - db_net
ports:
  postgres_loopback: 5433
  pgadmin: 5051
security_extra:
  postgres: {}
  pgadmin: {}
  redis:
    security_opt: ["no-new-privileges:true"]
    cap_drop: ["ALL"]
    cap_add: ["CHOWN", "DAC_OVERRIDE", "SETUID", "SETGID"]
---

# PostgreSQL IA

La guía operativa completa está en `docs/services/aipostgres-guide.md`. Esta ficha contiene los metadatos del stack sucesor de DataSQL para el catálogo del agente; no reemplaza la guía de migración.
