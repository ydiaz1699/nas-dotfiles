# Continuidad activa: conectar Home Assistant con DataSQL

> Archivo de checkpoint para retomar la guía entre chats. No contiene secretos.

## Estado

- **Estado:** PAUSADO_ESPERANDO_USUARIO
- **Guía canónica:** `docs/services/homeassistant-datasql-guide.md`
- **Guía principal relacionada:** `docs/services/homeassistant-guide.md`
- **Objetivo:** conectar opcionalmente Home Assistant (`network_mode: host`) con una base PostgreSQL dedicada; PostgreSQL/DataSQL puede existir previamente o ser una decisión posterior del usuario.
- **Última actualización:** 2026-08-25
- **Paso actual:** 7 — levantar Home Assistant y completar el onboarding, si el usuario eligió y confirmó un backend PostgreSQL

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

## Próxima acción única: levantar Home Assistant

La base, el propietario y el login de `ha_user` ya están confirmados. No repetir
la creación de PostgreSQL ni el preflight.

Si el onboarding todavía no está completado, ejecutar:

```bash
dk homeassistant
svc config homeassistant
svc up homeassistant
svc ps homeassistant
svc logs homeassistant
```

Después abrir `http://${SERVER_IP}:8123` y completar el onboarding. No editar
`configuration.yaml` ni configurar el Recorder hasta terminarlo.

Si el onboarding ya estaba completado, no crear otra configuración: verificar
con `svc ps homeassistant` y continuar con el paso 8 de la guía, que crea
`data/secrets.yaml` y configura el Recorder.

## Reglas de continuidad

1. No repetir el preflight salvo que el usuario reporte un cambio o un error.
2. No saltar al Recorder hasta confirmar propietario y login de `ha_user`, y no editar la configuración de HA antes de completar el onboarding.
3. El `svc exec` de este NAS puede interpretar `-U`, `-d` y `-c` como opciones propias; usar `PGUSER`, `PGDATABASE` y sesiones interactivas de `psql`.
4. No ejecutar SQL en Bash.
5. Después de cada mutación o verificación confirmada, actualizar este checkpoint con el paso, salida esperada y próxima acción.
6. Si el usuario hace una pregunta lateral, responderla brevemente y volver explícitamente al paso actual; no iniciar otro flujo.
7. No pedir ni guardar contraseñas reales en este archivo.

## Pasos posteriores

- **7:** iniciar Home Assistant y completar onboarding, si todavía no está completado.
- **8:** crear/proteger `data/secrets.yaml` y configurar una única sección `recorder:`.
- **9:** reiniciar HA y revisar logs.
- **10:** consultar `states` y confirmar `states_count > 0`.
