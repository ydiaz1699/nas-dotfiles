# Continuidad activa: conectar Home Assistant con DataSQL

> Archivo de checkpoint para retomar la guía entre chats. No contiene secretos.

## Estado

- **Estado:** CONEXIÓN_POSTGRESQL_CONFIRMADA
- **Guía canónica:** `docs/services/homeassistant-datasql-guide.md`
- **Guía principal relacionada:** `docs/services/homeassistant-guide.md`
- **Objetivo:** conectar Home Assistant (`network_mode: host`) con una base PostgreSQL dedicada; PostgreSQL/DataSQL puede existir previamente o ser una decisión posterior del usuario.
- **Última actualización:** 2026-08-25
- **Paso actual:** 11 — conexión y escritura del Recorder verificadas

## Evidencia confirmada en el NAS

- `AIPG_POSTGRES_HOST_PORT` resolvió a `5432`.
- PostgreSQL escucha en `127.0.0.1:5432`.
- `datapostgres` está `healthy`.
- `dataredis` está `healthy`.
- Existe `db_net`.
- Las variables administrativas `PG_ADMIN_PASSWORD`, `PG_ADMIN_USER` y `PG_ADMIN_DB` se cargaron correctamente en la sesión actual.
- `CREATE ROLE ha_user LOGIN;` terminó correctamente con salida `CREATE ROLE`.
- La contraseña de `ha_user` se estableció mediante `\\password ha_user`.
- La consulta en `psql` confirmó `homeassistant_db` con propietario `ha_user`.
- La consulta `SELECT current_user, current_database();` confirmó el login como `ha_user` en `homeassistant_db`.
- La verificación con `-U`, `-d` y `-c` falló antes de ejecutar PostgreSQL porque el parser de `svc exec` interpretó `-U` como opción propia.
- El usuario intentó ejecutar `SELECT` directamente en Bash; falló porque SQL debe ejecutarse dentro de una sesión interactiva de `psql`. Ese fallo no modificó nada.

La verificación más reciente mostró tres errores de procedimiento, sin modificar PostgreSQL ni Home Assistant:

- `svc exec homeassistant sh -c ...` falló porque el CLI Python interpretó `-c`; la forma correcta para este NAS es `NAS_CLI=bash svc exec homeassistant homeassistant sh -c ...`.
- `\connect homeassistant_db` seguido de una consulta pegada produjo `invalid integer value "AS" for connection option "port"`; las comprobaciones de tablas deben abrir una segunda sesión con `PGDATABASE=homeassistant_db`, sin usar `\connect`.
- Los comandos Bash (`read`, `printf` y `svc exec`) se pegaron dentro del prompt `aipostgres=#`; la guía ahora exige salir con `\q` y confirmar el prompt `root@Nas ... #` antes de continuar.

## Evidencia adicional confirmada en la verificación final

- `datapostgres` está `Up (healthy)` y publica `127.0.0.1:5432->5432/tcp`.
- `ss` confirma que `127.0.0.1:5432` está escuchando.
- `ha_user` existe con `rolcanlogin = t`.
- `homeassistant_db` existe y su propietario es `ha_user`.
- La prueba de credenciales confirmó `current_user = ha_user` y `current_database = homeassistant_db`.
- `pg_stat_activity` mostró a `ha_user` conectado a `homeassistant_db` desde `172.20.0.1`.
- Existen las tablas `states` y `events`.
- `SELECT COUNT(*) FROM states` devolvió `76`.
- `svc health` mostró `homeassistant` como `healthy`.
- Los logs de HA contienen `psycopg2` y operaciones del Recorder sobre PostgreSQL.
- El usuario intentó ejecutar `read`, `printf` y `svc exec` mientras seguía en el prompt `aipostgres=#`; PostgreSQL rechazó esas entradas como SQL y no se modificó nada.


La preparación externa de PostgreSQL y la conexión funcional de Home Assistant terminaron. El rol, la base, el propietario, el login, la conexión activa y las tablas del Recorder están confirmados. `states_count = 76` confirma que HA ya está escribiendo estados en PostgreSQL.

La guía debe conservar una separación visual obligatoria entre los dos intérpretes:

- `root@Nas ... #` → Bash: aquí se ejecutan `read`, `printf`, `svc exec`, `unset` y otros comandos de terminal.
- `aipostgres=#` o `homeassistant_db=>` → `psql`: aquí se ejecuta SQL y comandos internos como `\q`.
- Antes de pasar de `psql` a Bash, ejecutar `\q` y esperar el prompt `root@Nas ... #`.
- Nunca pegar comandos Bash dentro de `psql`.

La existencia de `homeassistant_db` por sí sola no conecta HA, pero en este caso la conexión ya quedó demostrada por `pg_stat_activity`, las tablas `states`/`events` y `states_count = 76`.

## Reglas de continuidad

1. No repetir el preflight salvo que el usuario reporte un cambio o un error.
2. No repetir `CREATE ROLE`, `CREATE DATABASE` ni el cambio de contraseña después de confirmar sus postcondiciones.
3. El `svc exec` de este NAS puede interpretar `-U`, `-d` y `-c` como opciones propias. Para comandos HA con `sh -c`, usar `NAS_CLI=bash svc exec homeassistant homeassistant sh -c ...`; incluir siempre el nombre interno Compose.
4. No ejecutar SQL en Bash ni comandos Bash dentro de `psql`. Antes de ejecutar `read`, `printf`, `svc exec` o `unset` después de una sesión SQL, salir con `\q` y confirmar el prompt `root@Nas ... #`.
5. Para consultar tablas de `homeassistant_db`, abrir una segunda sesión con `PGDATABASE=homeassistant_db`; no usar `\connect` con consultas pegadas en la misma entrada.
6. La configuración de PostgreSQL del consumidor es independiente: en HA se realiza con `recorder.db_url`, no modificando el compose.
7. Después de cada mutación o verificación confirmada, actualizar este checkpoint con el paso, salida esperada y próxima acción.
8. No pedir ni guardar contraseñas reales en este archivo.

## Pasos posteriores

- **8:** completado; Home Assistant está levantado y saludable.
- **9:** completado; el backend observado es PostgreSQL mediante `psycopg2` y la configuración de HA.
- **10:** completado; `recorder.db_url` apunta a `homeassistant_db` mediante el secreto local.
- **11:** completado; conexión activa de `ha_user`, tablas `states`/`events` y `states_count = 76` confirmados.
- **Documentación:** reforzar siempre el límite `psql` → Bash con `\q` y el prompt esperado antes de continuar.
