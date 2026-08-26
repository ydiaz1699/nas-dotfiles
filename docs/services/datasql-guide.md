# `datasql` — referencia operativa del clúster ParadeDB

> **Fuente canónica:** la instalación, el renombrado inicial, los puertos y la
> verificación están documentados en [`aipostgres-guide.md`](aipostgres-guide.md).
> Esta página conserva el nombre `datasql` porque es el servicio que se opera
> con `svc` y el punto de entrada que deben leer las aplicaciones consumidoras.
>
> **No uses recetas antiguas** con `postgres:16-alpine`, `homelab`, `nasadmin`,
> `aipgadmin`, `airedis`, `5433`, `5051` o el hostname `postgres`. El estado
> vigente usa ParadeDB y los nombres `datapostgres`, `datapgadmin` y `dataredis`.

## Estado vigente

| Componente | Imagen | Contenedor | Acceso |
|---|---|---|---|
| PostgreSQL | `paradedb/paradedb:0.25.4-pg17` | `datapostgres` | `127.0.0.1:5432` desde el host; `datapostgres:5432` en `db_net` |
| pgAdmin | `dpage/pgadmin4:9.17` | `datapgadmin` | `${SERVER_IP}:5050` desde la LAN |
| Redis | `redis:7-alpine` | `dataredis` | `dataredis:6379` solo en `db_net` |

La base administrativa es `aipostgres` y el usuario administrativo es
`aiadmin`. Redis no publica `6379`. PostgreSQL solo publica el loopback del
NAS para Home Assistant con `network_mode: host`; no está expuesto a la LAN.

El compose y el `.env.example` canónicos son:

```text
$NAS_DOTFILES/agent/catalog/services/datasql/compose.yml
$NAS_DOTFILES/agent/catalog/services/datasql/.env.example
```

La guía completa contiene la migración destructiva desde `$dkco/aipostgres`,
la recreación con los nombres finales y el procedimiento de primera
instalación:

```bash
# Leer antes de operar el servicio:
# docs/services/aipostgres-guide.md
svc health
svc ps datasql
```

## Reglas para aplicaciones consumidoras

Antes de crear una base, un rol PostgreSQL o configurar Redis:

1. Leer la guía específica de la aplicación y la guía canónica de ParadeDB.
2. Comprobar `svc health`, `svc ps datasql` y `svc net`.
3. Leer las variables reales desde `$dkco/datasql/.env`, sin `source .env` y
   sin pegar secretos en la salida.
4. Crear el rol primero y la base después, en llamadas separadas de `psql`.
5. Verificar el propietario de la base y la conexión con el usuario dedicado.
6. Usar `datapostgres:5432` y `dataredis:6379` desde contenedores en `db_net`.
7. Usar `127.0.0.1:5432` solo desde servicios host-network como Home Assistant.
8. Limpiar variables temporales con `unset`.

`db_net` permite comunicación, pero no prueba que una aplicación use la base.
Confirmar siempre el compose, la configuración efectiva y el runtime.

### Lectura segura de credenciales

```bash
PG_ADMIN_USER=$(grep '^POSTGRES_USER=' "$dkco/datasql/.env" | cut -d= -f2-)
PG_ADMIN_DB=$(grep '^POSTGRES_DB=' "$dkco/datasql/.env" | cut -d= -f2-)
PG_ADMIN_PASSWORD=$(grep '^POSTGRES_PASSWORD=' "$dkco/datasql/.env" | cut -d= -f2-)
```

No usar `source .env`; un secreto puede contener caracteres con significado
para Bash. Pasar la contraseña explícitamente al proceso dentro del contenedor:

```bash
svc exec datasql postgres \
  env PGPASSWORD="$PG_ADMIN_PASSWORD" \
  psql -U "$PG_ADMIN_USER" -d "$PG_ADMIN_DB"
```

Cuando `psql` muestre el prompt `aipostgres=#`, ejecutar el SQL. No pegar SQL
directamente en Bash. Al terminar:

```text
\q
```

```bash
unset PG_ADMIN_USER PG_ADMIN_DB PG_ADMIN_PASSWORD
```

### Receta canónica para un consumidor

Sustituye los nombres por los que declare el servicio real. No inventes una
contraseña: léela del `.env` de la aplicación y no la muestres.

```bash
APP_DB_PASSWORD=$(grep '^FLOWISE_DB_PASSWORD=' "$dkco/flowise/.env" | cut -d= -f2-)
PGPASS=$(grep '^POSTGRES_PASSWORD=' "$dkco/datasql/.env" | cut -d= -f2-)
PGUSER=$(grep '^POSTGRES_USER=' "$dkco/datasql/.env" | cut -d= -f2-)
PGDB=$(grep '^POSTGRES_DB=' "$dkco/datasql/.env" | cut -d= -f2-)

svc exec datasql postgres \
  env PGPASSWORD="$PGPASS" PGUSER="$PGUSER" PGDATABASE="$PGDB" psql
```

Primera llamada, dentro de `psql`:

```sql
CREATE ROLE flowise_user LOGIN;
\password flowise_user
\q
```

Segunda llamada, en una sesión administrativa nueva:

```bash
svc exec datasql postgres \
  env PGPASSWORD="$PGPASS" PGUSER="$PGUSER" PGDATABASE="$PGDB" psql
```

```sql
CREATE DATABASE flowise_db OWNER flowise_user;
SELECT datname, pg_get_userbyid(datdba) AS owner
FROM pg_database
WHERE datname = 'flowise_db';
\q
```

Prueba el usuario dedicado y limpia las variables:

```bash
svc exec datasql postgres \
  env PGPASSWORD="$APP_DB_PASSWORD" \
  psql -U flowise_user -d flowise_db \
  -c 'SELECT current_user, current_database();'

unset APP_DB_PASSWORD PGPASS PGUSER PGDB
```

La salida debe identificar `flowise_user` y `flowise_db`. Repite el patrón para
Home Assistant o n8n solo después de confirmar su configuración real. No uses
`aiadmin` como usuario de una aplicación.

### Redis compartido

No crees otro Redis ni otra contraseña para un consumidor. Lee la contraseña
local y prueba el servicio así:

```bash
REDIS_PASSWORD=$(grep '^REDIS_PASSWORD=' "$dkco/datasql/.env" | cut -d= -f2-)
svc exec datasql redis \
  env REDISCLI_AUTH="$REDIS_PASSWORD" redis-cli PING
unset REDIS_PASSWORD
```

La respuesta debe ser `PONG`. Configura el consumidor con `dataredis:6379` y
`REDISCLI_AUTH` o la variable equivalente que documente su imagen.

## Consumidores conocidos

| Servicio | PostgreSQL | Redis | Estado |
|---|---|---|---|
| Flowise | `flowise_db` vía `datapostgres:5432` | `dataredis:6379` | Verificar main y worker después de recrear |
| Home Assistant | `homeassistant_db` vía `127.0.0.1:5432` | No confirmado | Mantiene `network_mode: host` |
| n8n | `n8n_db` solo si su compose lo confirma | Por auditar | No levantar con una configuración supuesta |

Después de cambiar un consumidor, verifica ese servicio de forma independiente:

```bash
svc recreate flowise
svc ps flowise
svc logs flowise
```

No uses `depends_on` contra un servicio que pertenece a otro compose; comprueba
la disponibilidad de la base con `svc health` y logs.

## Operación rápida

```bash
svc ps datasql
svc health
svc net
svc port-map
svc stats datasql
svc logs datasql
svc restart datasql
svc update datasql
svc backup datasql
```

La salida completa de `svc config datasql` puede incluir secretos interpolados;
revísala solo localmente y no la publiques.
