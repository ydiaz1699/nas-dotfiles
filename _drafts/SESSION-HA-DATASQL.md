# Continuidad activa: conectar Home Assistant con DataSQL

> Archivo de checkpoint para retomar la guía entre chats. No contiene secretos.

## Estado

- **Estado:** PAUSADO_ESPERANDO_USUARIO
- **Guía canónica:** `docs/services/homeassistant-guide.md`
- **Objetivo:** conectar Home Assistant (`network_mode: host`) con la base PostgreSQL `homeassistant_db` del único stack `datasql`.
- **Última actualización:** 2026-08-25
- **Paso actual:** 6 — verificar propietario y login de `ha_user`

## Evidencia confirmada en el NAS

- `AIPG_POSTGRES_HOST_PORT` resolvió a `5432`.
- PostgreSQL escucha en `127.0.0.1:5432`.
- `datapostgres` está `healthy`.
- `dataredis` está `healthy`.
- Existe `db_net`.
- Las variables administrativas `PG_ADMIN_PASSWORD`, `PG_ADMIN_USER` y `PG_ADMIN_DB` se cargaron correctamente en la sesión actual.
- `CREATE ROLE ha_user LOGIN;` terminó correctamente con salida `CREATE ROLE`.
- La contraseña de `ha_user` se estableció mediante `\\password ha_user`.
- `CREATE DATABASE homeassistant_db OWNER ha_user;` terminó correctamente con salida `CREATE DATABASE`.
- La verificación con `-U`, `-d` y `-c` falló antes de ejecutar PostgreSQL porque el parser de `svc exec` interpretó `-U` como opción propia.
- El usuario intentó ejecutar `SELECT` directamente en Bash; falló porque SQL debe ejecutarse dentro de una sesión interactiva de `psql`. Ese fallo no modificó nada.

## Próxima acción única: verificar propietario

No repetir `CREATE ROLE` ni `CREATE DATABASE`.

Ejecutar:

```bash
svc exec datasql postgres \
  env PGPASSWORD="$PG_ADMIN_PASSWORD" \
      PGUSER="$PG_ADMIN_USER" \
      PGDATABASE="$PG_ADMIN_DB" \
  psql
```

Dentro de `psql`, ejecutar solamente:

```sql
SELECT datname,
       pg_get_userbyid(datdba) AS owner
FROM pg_database
WHERE datname = 'homeassistant_db';
```

Esperado: `homeassistant_db` con propietario `ha_user`. Después ejecutar:

```text
\\q
```

## Siguiente paso después de confirmar el propietario

Verificar el login con la contraseña dedicada, sin usar `-U`, `-d` ni `-c`:

```bash
read -r -s -p 'Contraseña de ha_user para verificar: ' HA_DB_PASSWORD
printf '\n'

svc exec datasql postgres \
  env PGPASSWORD="$HA_DB_PASSWORD" \
      PGUSER=ha_user \
      PGDATABASE=homeassistant_db \
  psql
```

Dentro de `psql`:

```sql
SELECT current_user, current_database();
```

Esperado: `ha_user | homeassistant_db`. Después ejecutar `\\q` y conservar
`HA_DB_PASSWORD` solamente hasta crear el secreto de Home Assistant.

## Reglas de continuidad

1. No repetir el preflight salvo que el usuario reporte un cambio o un error.
2. No saltar al Recorder ni iniciar HA hasta confirmar propietario y login de `ha_user`.
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
