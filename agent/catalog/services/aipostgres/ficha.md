---
id: "aipostgres"
name: "PostgreSQL IA"
description: "Clúster PostgreSQL 17 separado basado en ParadeDB, preparado para búsqueda vectorial y full-text con pgvector y pg_search"
aliases:
  - aipostgres
  - ai-postgres
  - postgres-ia
  - paradedb
  - pgvector
  - pg_search
  - vector-db
  - semantic-search
image: "paradedb/paradedb:0.25.4-pg17"
category: "base-datos"
port_internal: 5432
port_default: null
protocol: "tcp"
needs_proxy: false
needs_db: false
db_type: "postgres"
services:
  aipostgres:
    image: "paradedb/paradedb:0.25.4-pg17"
    container_name: "aipostgres"
    port_internal: 5432
    port_default: null
    exposure: "internal"
    healthcheck: '["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]'
    volumes:
      - "./data:/var/lib/postgresql/data"
    resources:
      memory_limit: "1536M"
      memory_reservation: "256M"
      cpus_limit: "1.5"
      cpus_reservation: "0.25"
env_required:
  - POSTGRES_DB
  - POSTGRES_USER
  - POSTGRES_PASSWORD
env_optional: []
backup_critical: true
backup_paths:
  - "./data"
protected: false
docs_url: "docs/services/aipostgres-guide.md"
notes: "Servicio interno separado de DataSQL. Usa db_net externa y no publica 5432 al host. La imagen ParadeDB 0.25.4-pg17 incluye pgvector y pg_search; el compose carga pg_search mediante shared_preload_libraries. No crear todavía lobehub_db ni nas_agent_db: cada consumidor futuro debe tener una base y un rol dedicados. La primera instalación omite cap_drop: ALL hasta validar compatibilidad de la imagen. En el catálogo extends.file es ../../_common.yml; el compose desplegado usa ../_common.yml."
networks:
  - db_net
ports: {}
security_extra: {}
---

# PostgreSQL IA

La guía operativa completa está en `docs/services/aipostgres-guide.md`. Esta ficha contiene solo metadatos para que el agente encuentre el servicio, resuelva sus aliases y conozca sus límites de exposición.
