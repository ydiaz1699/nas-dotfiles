---
id: "datasql"
name: "Datasql"
description: "Servicio auto-catalogado desde compose existente"
image: "postgres:16-alpine"
category: "base-datos"
port_internal: 5432
port_default: 5432
protocol: "http"
needs_proxy: false
needs_db: false
volumes:
  - "./data/postgres/pgdata:/var/lib/postgresql/data/pgdata"
  - "./data/postgres/backups:/backups"
env_required:
  - POSTGRES_DB
  - POSTGRES_USER
  - POSTGRES_PASSWORD
  - PGDATA
  - TZ
healthcheck: "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"
backup_critical: true
backup_paths:
  - "./data"
protected: false
docs_url: "docs/services/datasql-guide.md"
notes: "Ficha generada automáticamente — revisar y completar"
---

# Datasql

## Qué es

(Completar manualmente — descripción del servicio)

## Configuración detectada

- Imagen: `postgres:16-alpine`
- Puerto: 5432:5432
- Volúmenes: 2 mount(s)
- Variables: 6 definidas

## Notas

- Ficha generada automáticamente por nas-agent
- Revisar y completar la descripción y notas de seguridad
