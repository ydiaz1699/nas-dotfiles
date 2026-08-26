---
name: datasql
description: >
  Procedimiento canónico para usar el stack ParadeDB PostgreSQL y Redis
  compartidos al instalar servicios en el NAS. Activar antes de crear una
  base, un rol o configurar Redis para otra aplicación.
---

# Skill `datasql`

El stack operativo único es `datasql` y vive en `$dkco/datasql`. Su guía
completa es:

```text
docs/services/aipostgres-guide.md
```

La guía de instalación y operación del stack es
`docs/services/aipostgres-guide.md`. La guía para consumidores y creación de
bases/roles es `docs/services/datasql-guide.md`.

## Estado final obligatorio

- PostgreSQL: ParadeDB 17 en `datapostgres`, base administrativa `aipostgres`,
  usuario administrativo `aiadmin`.
- pgAdmin: 9.17 en `datapgadmin`, accesible desde la LAN en `5050`.
- Redis: 7 en `dataredis`, accesible únicamente como `dataredis:6379` dentro
  de `db_net`.
- PostgreSQL: `127.0.0.1:5432:5432` solo para Home Assistant con
  `network_mode: host`; los contenedores usan `datapostgres:5432`.
- La instalación limpia puede haber eliminado el DataSQL anterior sin backup,
  si el usuario lo solicitó. No asumir que existen bases antiguas.

No usar nombres temporales (`aipgadmin`, `airedis`), puertos `5433`/`5051`,
`postgres:16-alpine`, ni el hostname Docker `postgres` para consumidores.

## Reglas obligatorias

1. Comprobar el stack con `svc health` y `svc ps datasql`. `svc health` es
   global; no acepta `datasql` como argumento.
2. Leer `POSTGRES_USER`, `POSTGRES_DB`, `POSTGRES_PASSWORD` y
   `REDIS_PASSWORD` desde `$dkco/datasql/.env`. No asumir `admin/appdb`, no
   ejecutar `source .env` y no pegar secretos en el repositorio o en el chat.
3. Ejecutar PostgreSQL mediante `svc exec datasql postgres ...` y pasar la
   contraseña administrativa explícitamente con `env PGPASSWORD="$PG_ADMIN_PASSWORD"`.
4. Crear el rol/usuario y la base en invocaciones separadas de `psql`:
   `CREATE ROLE/USER` primero y `CREATE DATABASE ... OWNER ...` después.
   Nunca combinar ambos comandos en una transacción o llamada `psql`.
5. Hacer el procedimiento idempotente cuando la aplicación ya exista:
   comprobar si el rol y la base existen, verificar el propietario y no
   cambiar una contraseña sin confirmar la configuración efectiva del servicio.
6. Redis ya existe como `dataredis` en `db_net`. No crear otro Redis ni otra
   contraseña. Validar con `REDISCLI_AUTH="$REDIS_PASSWORD" redis-cli ping`, no
   con `-a` ni con una variable que no haya sido cargada explícitamente.
7. Las aplicaciones Docker usan `datapostgres` y `dataredis` como hosts, se
   conectan a la red externa `db_net`, no publican `5432`/`6379` y no declaran
   `depends_on` contra DataSQL cuando viven en otro compose. Home Assistant es
   la excepción host-network y usa `127.0.0.1:5432`.
8. Después de usar credenciales en variables temporales, ejecutar `unset`.
9. `db_net` no demuestra uso de una base: confirmar la conexión en compose,
   configuración y runtime. El inventario confirmado es Flowise →
   `flowise_db` + `dataredis`, Home Assistant → `homeassistant_db` por loopback,
   y `n8n_db` existente con su configuración aún pendiente de auditar.
10. No reutilizar el usuario administrativo para una aplicación. Cada
    consumidor debe tener su propio rol, base y contraseña.
11. PostgreSQL ParadeDB ofrece `vector`, `pg_search` y `pg_cron`; habilitar
    `CREATE EXTENSION` únicamente en las bases que realmente las necesiten.
    Preparar el clúster no obliga a instalar LobeHub, Hermes ni el agente.
12. RustFS no pertenece a este compose. Instalarlo como servicio S3 separado
    solo cuando exista un consumidor real de objetos.

## Contrato de configuración de una aplicación

- `DATABASE_HOST=datapostgres`
- `DATABASE_PORT=5432`
- `REDIS_HOST=dataredis`
- `REDIS_PORT=6379`
- `networks: [db_net]` con `external: true`
- `env_file: [../.env, .env]`
- Usuario y base dedicados por aplicación
- La contraseña de Redis es la misma de `$dkco/datasql/.env`, leída sin
  mostrarla y pasada con el mecanismo de autenticación de la imagen

La guía es la fuente de verdad para instalación, renombrado, permisos,
recreación, recuperación y verificación. Esta skill solo contiene las reglas
de decisión para un consumidor.
