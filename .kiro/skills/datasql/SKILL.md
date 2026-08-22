---
name: datasql
description: >
  Procedimiento canónico para usar PostgreSQL y Redis compartidos de DataSQL
  al instalar servicios en el NAS. Activar antes de crear una base, un rol o
  configurar Redis para otra aplicación.
---

# Skill DataSQL

DataSQL es la infraestructura compartida del NAS. Antes de crear o configurar
una aplicación que necesite PostgreSQL o Redis, leer la guía completa:

```text
docs/services/datasql-guide.md
```

## Reglas obligatorias

1. Comprobar el stack con `svc health` y `svc ps datasql`. `svc health` es
   global; no acepta `datasql` como argumento.
2. Leer `POSTGRES_USER`, `POSTGRES_DB`, `POSTGRES_PASSWORD` y
   `REDIS_PASSWORD` desde `$dkco/datasql/.env`. No asumir `admin/appdb`, no
   ejecutar `source .env` y no pegar secretos en el repositorio o en el chat.
3. Ejecutar PostgreSQL mediante `svc exec datasql postgres ...` y pasar la
   contraseña administrativa explícitamente con `env PGPASSWORD="$PG_ADMIN_PASSWORD"`.
   El `env_file` del compose no exporta esas variables a la shell del usuario.
4. Crear el rol/usuario y la base en invocaciones separadas de `psql`:
   `CREATE ROLE/USER` primero y `CREATE DATABASE ... OWNER ...` después.
   Nunca combinar ambos comandos en una sola transacción o llamada `psql`.
5. Hacer el procedimiento idempotente: comprobar si el rol y la base existen;
   actualizar la contraseña del rol solo cuando corresponda y verificar el
   propietario de la base antes de cambiarlo.
6. Redis ya existe como `dataredis` en `db_net`. No crear otro Redis ni otra
   contraseña. Validar con `REDISCLI_AUTH="$REDIS_PASSWORD" redis-cli ping`, no
   con `-a` ni con una variable que no haya sido cargada explícitamente.
7. Las aplicaciones Docker usan `datapostgres` y `dataredis` como hosts, se
   conectan a la red externa `db_net`, no publican `5432`/`6379` y no declaran
   `depends_on` contra DataSQL cuando viven en otro compose. La única excepción
   es Home Assistant con `network_mode: host`: su Recorder usa PostgreSQL
   publicado exclusivamente como `127.0.0.1:5432:5432`, nunca una dirección LAN.
8. Después de usar credenciales en variables temporales, ejecutar `unset`.

## Contrato de configuración de una aplicación

- `DATABASE_HOST=datapostgres`
- `REDIS_HOST=dataredis`
- `networks: [db_net]` con `external: true`
- `env_file: [../.env, .env]`
- Usuario y base dedicados por aplicación; nunca reutilizar el administrador
- `REDIS_PASSWORD` exactamente igual al secreto de DataSQL

La guía es la fuente de verdad para los comandos completos, la secuencia,
backups, recuperación y variantes específicas. Esta skill solo contiene las
reglas de decisión que deben aplicarse antes de consultar o modificar un
servicio consumidor.
