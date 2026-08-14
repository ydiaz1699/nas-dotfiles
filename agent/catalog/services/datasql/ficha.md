---
id: "datasql"
name: "DataSQL"
description: "Stack de bases de datos: PostgreSQL 16, pgAdmin 4 y Redis 7 para persistencia de servicios del NAS"
aliases:
  - postgres
  - pgadmin
  - redis
  - db
  - database
image: "postgres:16-alpine"
category: "base-datos"
protocol: "tcp"
needs_proxy: false
needs_db: false
db_type: ""
services:
  postgres:
    image: "postgres:16-alpine"
    container_name: "datapostgres"
    port_internal: 5432
    port_default: null
    exposure: "internal"
    healthcheck: '["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]'
    volumes:
      - "./data/postgres/pgdata:/var/lib/postgresql/data/pgdata"
      - "./data/postgres/backups:/backups"
    resources:
      memory_limit: "2G"
      memory_reservation: "512M"
      cpus_limit: "2"
      cpus_reservation: "0.5"
  pgadmin:
    image: "dpage/pgadmin4:latest"
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
  - TZ
env_optional: []
backup_critical: true
backup_paths:
  - "./data/postgres/backups"
  - "./data/pgadmin"
  - "./data/redis"
protected: false
docs_url: "docs/services/datasql-guide.md"
notes: "PostgreSQL y Redis NO exponen puertos al host — acceso solo via db_net. pgAdmin expuesto en LAN (:5050). PGDATA es variable fija interna (no requiere .env). Usa env_file para .env local."
networks:
  - db_net
security_extra:
  all_services:
    security_opt: ["no-new-privileges:true"]
    cap_drop: ["ALL"]
    cap_add: ["CHOWN", "DAC_OVERRIDE", "SETUID", "SETGID"]
---

# DataSQL

## Qué es

Stack de bases de datos del NAS: PostgreSQL 16 (DB relacional principal),
pgAdmin 4 (administración web) y Redis 7 (caché/colas). Todos los servicios
del homelab que necesiten persistencia se conectan a este stack via `db_net`.

## Estructura

```
/docker/datasql/
├── compose.yml
├── .env                    ← secretos (permisos 600)
└── data/
    ├── postgres/
    │   ├── pgdata/         ← datos PostgreSQL
    │   └── backups/        ← dumps pg_dump
    ├── pgadmin/            ← configuración pgAdmin
    └── redis/              ← AOF persistence
```

## Servicios

| Servicio   | Imagen              | Puerto host | Red     | Acceso   |
|-----------|---------------------|-------------|---------|----------|
| postgres  | postgres:16-alpine  | —           | db_net  | internal |
| pgadmin   | dpage/pgadmin4      | 5050        | db_net  | LAN      |
| redis     | redis:7-alpine      | —           | db_net  | internal |

## Variables de entorno

### Requeridas (.env)

```bash
POSTGRES_DB=homelab
POSTGRES_USER=nasadmin
POSTGRES_PASSWORD=__pega_aqui__
PGADMIN_EMAIL=admin@local.lan
PGADMIN_PASSWORD=__pega_aqui__
REDIS_PASSWORD=__pega_aqui__
TZ=America/La_Paz
```

### Fijas (en compose, NO requieren .env)

- `PGDATA=/var/lib/postgresql/data/pgdata`
- `POSTGRES_INITDB_ARGS="--auth-host=scram-sha-256 --auth-local=scram-sha-256"`
- `PGADMIN_CONFIG_SERVER_MODE=True`

## Redes

- `db_net` (external: true): Red compartida por todos los servicios que necesitan DB

## Seguridad

- PostgreSQL y Redis **nunca** exponen puertos al host
- Todos los contenedores: `no-new-privileges`, `cap_drop: ALL`, caps mínimas
- Resource limits configurados por servicio
- scram-sha-256 para autenticación PostgreSQL

## Notas

- pgAdmin accesible desde LAN en :5050 (documentado como excepción)
- Redis usa `--appendonly yes` + `--requirepass`
- Backups: `pg_dump` via crontab a `./data/postgres/backups/`
- Guía completa de operación: `docs/services/datasql-guide.md`
