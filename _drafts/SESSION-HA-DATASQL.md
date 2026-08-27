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

La preparación externa de PostgreSQL terminó. El rol, la base, el propietario y el login están confirmados. Esta guía no indica levantar, reiniciar ni configurar Home Assistant; no existe una siguiente acción de HA en este checkpoint.

## Reglas de continuidad

1. No repetir el preflight salvo que el usuario reporte un cambio o un error.
2. No repetir `CREATE ROLE`, `CREATE DATABASE` ni el cambio de contraseña después de confirmar sus postcondiciones.
3. El `svc exec` de este NAS puede interpretar `-U`, `-d` y `-c` como opciones propias; usar `PGUSER`, `PGDATABASE` y sesiones interactivas de `psql`.
4. No ejecutar SQL en Bash.
5. Esta guía no modifica ningún archivo, secreto, contenedor o proceso de Home Assistant.
6. Después de cada mutación o verificación confirmada, actualizar este checkpoint con el paso, salida esperada y próxima acción de PostgreSQL.
7. No pedir ni guardar contraseñas reales en este archivo.

## Pasos posteriores

No hay pasos posteriores de Home Assistant en esta guía. El backend PostgreSQL queda preparado para el procedimiento que el usuario decida aplicar posteriormente.
