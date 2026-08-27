# Continuidad activa: conectar Home Assistant con DataSQL

> Archivo de checkpoint para retomar la guía entre chats. No contiene secretos.

## Estado

- **Estado:** PAUSADO_ESPERANDO_USUARIO
- **Guía canónica:** `docs/services/homeassistant-datasql-guide.md`
- **Guía principal relacionada:** `docs/services/homeassistant-guide.md`
- **Objetivo:** conectar opcionalmente Home Assistant (`network_mode: host`) con una base PostgreSQL dedicada; PostgreSQL/DataSQL puede existir previamente o ser una decisión posterior del usuario.
- **Última actualización:** 2026-08-25
- **Paso actual:** 8 — preparación PostgreSQL terminada; Home Assistant no fue modificado

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

## Resultado actual

La preparación externa de PostgreSQL terminó. El rol, la base, el propietario y el login están confirmados. Home Assistant aún no tiene evidencia versionada de conexión a PostgreSQL.

**Siguiente decisión del usuario:**

- Si acepta SQLite: levantar HA; no hace falta configurar PostgreSQL.
- Si quiere PostgreSQL: levantar/completar onboarding y seguir la guía desde el paso de detección/configuración de `recorder.db_url`.

La existencia de `homeassistant_db` no conecta HA por sí sola.

## Reglas de continuidad

1. No repetir el preflight salvo que el usuario reporte un cambio o un error.
2. No repetir `CREATE ROLE`, `CREATE DATABASE` ni el cambio de contraseña después de confirmar sus postcondiciones.
3. El `svc exec` de este NAS puede interpretar `-U`, `-d` y `-c` como opciones propias; usar `PGUSER`, `PGDATABASE` y sesiones interactivas de `psql`.
4. No ejecutar SQL en Bash.
5. La configuración de PostgreSQL del consumidor es independiente: en HA se realiza con `recorder.db_url`, no modificando el compose.
6. Después de cada mutación o verificación confirmada, actualizar este checkpoint con el paso, salida esperada y próxima acción.
7. No pedir ni guardar contraseñas reales en este archivo.

## Pasos posteriores

- **8:** si se acepta SQLite, levantar HA y completar onboarding sin configurar PostgreSQL.
- **9:** detectar el backend actual sin modificarlo.
- **10:** si se elige PostgreSQL, configurar `secrets.yaml` y una única sección `recorder:`.
- **11:** verificar configuración, conexión activa y tablas del Recorder.
