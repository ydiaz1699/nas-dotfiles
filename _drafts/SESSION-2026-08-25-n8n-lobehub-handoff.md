# Handoff de sesión — n8n reparado, DataSQL migrado y siguiente LobeHub

## Estado: COMPLETADO para la reparación funcional; PAUSADO para hardening/version pin
## Fecha: 2026-08-25
## Propósito

Dar continuidad a otro chat sin repetir la migración de DataSQL, la creación de
roles ni la validación de n8n. Este checkpoint registra solo evidencia segura y
no contiene secretos reales.

## Completado

- DataSQL es el stack operativo único: `datapostgres`, `datapgadmin`, `dataredis`
  y `db_net`.
- n8n estaba detenido para evitar un bucle de reinicios causado por la base.
- `n8n_user` fue creado con login.
- La contraseña de `DB_PASSWORD` del `.env` local de n8n permitió login como
  `n8n_user` contra `aipostgres`.
- `n8n_db` fue creada en una sesión PostgreSQL separada con owner `n8n_user`.
- Login dedicado verificado: `current_user=n8n_user`,
  `current_database=n8n_db`.
- n8n arrancó y completó sus migraciones.
- Runtime observado: `n8nio/n8n:latest` → n8n `2.23.4`.
- `svc health` mostró `0` reinicios observados.
- `/healthz` respondió `HTTP 200`.
- Se creó un snapshot con `svc snapshot n8n` antes del hardening propuesto.

## Runtime observado antes del hardening

```yaml
image: n8nio/n8n:latest
container_name: n8n
env_file: .env
port: "5678:5678"
volume: "./data:/home/node/.n8n"
network: db_net
network_address: ipv4_address fija observada en el compose
healthcheck: ausente
variables:
  - TZ
  - N8N_SECURE_COOKIE
  - DB_TYPE
  - DB_POSTGRESDB_HOST
  - DB_POSTGRESDB_PORT
  - DB_POSTGRESDB_DATABASE
  - DB_POSTGRESDB_USER
  - DB_POSTGRESDB_PASSWORD
  - N8N_ENCRYPTION_KEY
  - WEBHOOK_URL
  - N8N_PROXY_HOPS
local_env_keys:
  - DB_PASSWORD
  - N8N_ENCRYPTION_KEY
```

## Realimentación reusable

- `\password n8n_user` es un prompt interactivo de `psql`; una variable Bash
  no se conecta automáticamente a ese prompt.
- Para secretos existentes, leer la clave local con `awk`, consumirla mediante
  `PGPASSWORD`/otra variable temporal y ejecutar `unset`; no imprimirla con
  `grep | cut`, `echo` o `cat .env`.
- Crear primero el rol y después la base en sesiones separadas.
- Una base existente no demuestra que la aplicación la use: comprobar compose,
  variables efectivas, login y logs/runtime.
- Conservar la sesión `root` cuando `svc` necesite leer `$dkco/.env`; desde
  `aadm` se observó `permission denied` en el `.env` global.
- `latest` es mutable. La versión observada es `2.23.4`; la release estable
  oficial consultada es `2.36.7` y la beta/pre-release es `2.37.3`. No usar la
  beta y no afirmar que `2.36.7` está desplegada sin evidencia.
- `svc config` valida la configuración; `svc up` inicia y `svc update` descarga
  la imagen y recrea el servicio. Para cambiar la etiqueta, hacer backup y usar
  `svc update` después de validar.
- El error `Failed to connect to ACP` pertenece a Kiro Web y no al NAS; no se
  debe mezclar con el diagnóstico de n8n.

## Hardening pendiente

1. Desde root: `dk n8n`.
2. Confirmar snapshot y crear `svc backup n8n` antes de modificar datos/config.
3. Aplicar el compose objetivo de `docs/services/n8n-guide.md` o del catálogo:
   `extends`, `env_file: [../.env, .env]`, `n8nio/n8n:2.36.7`, healthcheck,
   `${SERVER_IP}`, sin `TZ` inline, sin `ipv4_address` y sin
   `N8N_PROXY_HOPS` mientras no haya proxy.
4. Ejecutar `svc config n8n >/dev/null`.
5. Ejecutar `svc update n8n`.
6. Verificar `svc ps`, `svc health`, logs, `/healthz`, editor y reinicios.
7. Si falla, no borrar `data`; usar snapshot/rollback y registrar la causa.

## LobeHub — siguiente trabajo

Antes de crear cualquier archivo, leer:

- `docs/docker-entorno.md`
- `.kiro/skills/datasql/SKILL.md`
- `docs/services/datasql-guide.md`
- `docs/services/n8n-guide.md` solo como referencia de la migración realizada

Confirmar en la documentación oficial de la versión de LobeHub elegida:
imagen/tag, variables, PostgreSQL, Redis, persistencia, puerto, healthcheck,
recursos y si requiere S3/RustFS.

Crear un rol/base dedicados para LobeHub solo después de confirmar los nombres
reales; no reutilizar `n8n_user`, `n8n_db`, `aiadmin` ni `aipostgres`. Usar
`datapostgres:5432` y, si aplica, `dataredis:6379` por `db_net`. No publicar
PostgreSQL/Redis y no usar `depends_on` contra DataSQL. RustFS queda fuera del
compose de DataSQL y solo se instala si LobeHub lo necesita realmente.

## No repetir

- No volver a ejecutar `CREATE ROLE n8n_user` sin consultar su existencia.
- No volver a ejecutar `CREATE DATABASE n8n_db`.
- No regenerar `N8N_ENCRYPTION_KEY`.
- No cambiar contraseñas existentes a ciegas.
- No pedir ni guardar el `.env` real.
- No afirmar que el hardening o `2.36.7` fueron aplicados sin salida posterior.

## Fuente canónica

- Procedimiento completo: `docs/services/n8n-guide.md`
- Ficha/compose objetivo: `agent/catalog/services/n8n/`
- DataSQL: `docs/services/datasql-guide.md`
- Reglas de secretos: `.kiro/skills/nas-runtime-secrets/SKILL.md`
- Contexto comprimido del agente: `docker-nas/references/nas-context.md`
