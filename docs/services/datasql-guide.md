# DataSQL — consumidores y creación de bases sobre ParadeDB

> **Esta guía se conserva como la referencia para aplicaciones consumidoras.**
> El stack operativo único vive en `$dkco/datasql` y ejecuta ParadeDB
> PostgreSQL 17, pgAdmin 9.17 y Redis 7.
>
> La guía de instalación, renombrado, permisos, recreación y recuperación del
> stack es [`aipostgres-guide.md`](aipostgres-guide.md). Esta guía no duplica
> esas fases: documenta cómo conectar nuevos servicios y cómo crear sus bases,
> roles y credenciales dedicados.

## 1. Estado final compartido

| Componente | Contenedor | Uso de los consumidores |
|---|---|---|
| PostgreSQL 17 ParadeDB | `datapostgres` | `datapostgres:5432` desde `db_net` |
| pgAdmin 9.17 | `datapgadmin` | `http://${SERVER_IP}:5050` desde la LAN |
| Redis 7 | `dataredis` | `dataredis:6379` desde `db_net` |

La base administrativa inicial de PostgreSQL es `aipostgres` y el usuario
administrativo es `aiadmin`. Esos nombres no deben reutilizarse como base o
usuario de una aplicación.

### Exposición y redes

- Los contenedores consumidores se conectan a la red externa `db_net`.
- PostgreSQL se publica en `127.0.0.1:5432` únicamente para Home Assistant,
  porque utiliza `network_mode: host`. Un contenedor en `db_net` debe usar
  `datapostgres:5432`, no `127.0.0.1`.
- Redis no tiene `ports:` y nunca debe aparecer publicado en `svc port-map`.
- pgAdmin sí se publica en `5050:80` como excepción documentada de dashboard
  LAN; esto no expone PostgreSQL ni Redis.
- Los consumidores no deben usar `depends_on` contra un contenedor de otro
  compose. Se comprueba la disponibilidad con `svc health`, `svc ps datasql`
  y los logs.

### Extensiones ParadeDB

La imagen `paradedb/paradedb:0.25.4-pg17` ofrece `vector` (`pgvector`),
`pg_search` y `pg_cron`. El compose ya precarga `pg_search,pg_cron` y establece
`cron.database_name` con `POSTGRES_DB`.

Las extensiones se habilitan por base. No las habilites en cada base por
costumbre: una aplicación solo necesita `CREATE EXTENSION` si su diseño usa
vectores, búsqueda ParadeDB o tareas de `pg_cron`.

Para una aplicación que use embeddings o búsqueda semántica, después de crear
su base con la receta de esta guía, conéctate a esa base como administrador y
ejecuta únicamente las extensiones que necesite:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_search;
```

`pg_cron` solo debe habilitarse en la base configurada por
`cron.database_name`. En la instalación final esa base es `aipostgres`; no
habilites `pg_cron` en una base de aplicación sin confirmar primero su
configuración.

## 2. Preflight antes de crear una base

Ejecuta siempre estas comprobaciones antes de crear roles, bases o conexiones:

```bash
svc health
svc ps datasql
svc net
```

Continúa solo si `datapostgres` y `dataredis` están saludables y `db_net` está
presente. Si PostgreSQL no está saludable, lee primero
[`aipostgres-guide.md`](aipostgres-guide.md) y corrige el stack antes de tocar
una base de aplicación.

Lee los valores administrativos desde el `.env` sin hacer `source .env` y sin
mostrar contraseñas:

```bash
PG_ADMIN_PASSWORD="$(awk -F= '$1=="POSTGRES_PASSWORD"{print substr($0,index($0,"=")+1)}' "$dkco/datasql/.env")"
PG_ADMIN_USER="$(awk -F= '$1=="POSTGRES_USER"{print substr($0,index($0,"=")+1)}' "$dkco/datasql/.env")"
PG_ADMIN_DB="$(awk -F= '$1=="POSTGRES_DB"{print substr($0,index($0,"=")+1)}' "$dkco/datasql/.env")"

if [[ -z "$PG_ADMIN_PASSWORD" || -z "$PG_ADMIN_USER" || -z "$PG_ADMIN_DB" ]]; then
  printf 'Falta una variable administrativa en %s/.env.\n' "$dkco/datasql" >&2
  unset PG_ADMIN_PASSWORD PG_ADMIN_USER PG_ADMIN_DB
  return 1 2>/dev/null || exit 1
fi
```

No pegues la salida de `svc config datasql` en un chat: puede contener secretos
interpolados. La guía de instalación explica cómo validar el Compose sin
exponerlos.

## 3. Crear una base y un rol para un servicio nuevo

Esta es la receta canónica. Sustituye los valores de aplicación por los que
realmente declare el nuevo servicio. No inventes la contraseña: primero debe
estar escrita en el `.env` del consumidor.

### 3.1 Definir los nombres y leer la contraseña del consumidor

Ejemplo para Flowise; para un servicio nuevo cambia solo estas variables y el
nombre de la variable de contraseña local:

```bash
SERVICE_ID=flowise
SERVICE_PASSWORD_VAR=FLOWISE_DB_PASSWORD
APP_DB_NAME=flowise_db
APP_DB_USER=flowise_user
APP_DB_PASSWORD="$(awk -F= -v key="$SERVICE_PASSWORD_VAR" '$1==key{print substr($0,index($0,"=")+1)}' "$dkco/$SERVICE_ID/.env")"

if [[ -z "$APP_DB_PASSWORD" ]]; then
  printf 'No se encontró %s en %s/.env.\n' "$SERVICE_PASSWORD_VAR" "$SERVICE_ID" >&2
  unset SERVICE_ID SERVICE_PASSWORD_VAR APP_DB_NAME APP_DB_USER APP_DB_PASSWORD
  return 1 2>/dev/null || exit 1
fi
```

Si el servicio todavía no tiene `.env`, créalo y guarda su secreto antes de
continuar. Después aplica sus permisos y configura el compose, en este orden:

```bash
mkdir -p "$dkco/$SERVICE_ID/data"
# Crear el .env y compose completos del servicio antes de aplicar permisos.
chmod 600 "$dkco/$SERVICE_ID/.env"
```

El bloque anterior es una plantilla de orden; no sobrescribas un `.env` real ni
uses la variable de otro servicio sin confirmar su nombre.

### 3.2 Crear el rol primero

Abre una sesión administrativa interactiva. `svc exec` debe recibir la
contraseña mediante `PGPASSWORD`; no uses `source .env`.

```bash
svc exec datasql postgres \
  env PGPASSWORD="$PG_ADMIN_PASSWORD" \
  psql -U "$PG_ADMIN_USER" -d "$PG_ADMIN_DB"
```

En el prompt `aipostgres=#`, ejecuta solamente SQL:

```sql
CREATE ROLE flowise_user LOGIN;
\password flowise_user
```

Cuando `psql` solicite la contraseña, introduce el valor que el consumidor
lee desde `FLOWISE_DB_PASSWORD`. No escribas ese valor en la guía, en el SQL ni
en un commit. Sal de la sesión:

```text
\q
```

> **Regla:** `CREATE ROLE` y `CREATE DATABASE` no se combinan. El rol se crea
> primero y la base se crea en una llamada posterior, fuera de una transacción.
> Si el rol ya existe, no lo recrees: verifica que sea el rol correcto y que
> su contraseña coincida con el `.env` del consumidor.

### 3.3 Crear la base con el rol como propietario

Abre una nueva sesión administrativa para que `CREATE DATABASE` quede separado:

```bash
svc exec datasql postgres \
  env PGPASSWORD="$PG_ADMIN_PASSWORD" \
  psql -U "$PG_ADMIN_USER" -d "$PG_ADMIN_DB"
```

En `psql`:

```sql
CREATE DATABASE flowise_db OWNER flowise_user;

SELECT datname,
       pg_get_userbyid(datdba) AS owner
FROM pg_database
WHERE datname = 'flowise_db';
```

La consulta debe devolver `flowise_db | flowise_user`. Sal de `psql`:

```text
\q
```

`CREATE DATABASE` no tiene una forma portable `IF NOT EXISTS`. Si la base ya
existe, no ejecutes el comando a ciegas: consulta primero su propietario y
corrígelo solo después de confirmar la configuración del servicio.

### 3.4 Verificar la conexión con el usuario dedicado

Prueba la base con la contraseña del consumidor, no con la contraseña
administrativa:

```bash
svc exec datasql postgres \
  env PGPASSWORD="$APP_DB_PASSWORD" \
  psql -U "$APP_DB_USER" -d "$APP_DB_NAME" \
  -c 'SELECT current_user, current_database();'
```

La salida debe identificar `flowise_user` y `flowise_db`. Limpia todas las
variables temporales al terminar:

```bash
unset PG_ADMIN_PASSWORD PG_ADMIN_USER PG_ADMIN_DB
unset SERVICE_ID SERVICE_PASSWORD_VAR APP_DB_NAME APP_DB_USER APP_DB_PASSWORD
```

## 4. Configurar el nuevo consumidor

El compose del consumidor debe usar la red y los hostnames internos:

```yaml
services:
  mi-servicio:
    env_file:
      - ../.env
      - .env
    environment:
      DATABASE_HOST: datapostgres
      DATABASE_PORT: "5432"
      DATABASE_NAME: mi_servicio_db
      DATABASE_USER: mi_servicio_user
      DATABASE_PASSWORD: ${MI_SERVICIO_DB_PASSWORD}
      REDIS_HOST: dataredis
      REDIS_PORT: "6379"
    networks:
      - db_net

networks:
  db_net:
    external: true
```

Adapta los nombres exactos de las variables al contrato de la imagen. No
supongas que todas usan `DATABASE_*`; comprueba la documentación y el compose
real del servicio.

Después de crear o modificar el servicio, sigue el orden operativo:

```bash
dk mi-servicio
svc config mi-servicio
svc up mi-servicio
svc ps mi-servicio
svc logs mi-servicio
svc health
```

No uses `depends_on` para forzar una dependencia con `datapostgres` porque vive
en otro compose. La aplicación debe tolerar el arranque independiente del
clúster y mostrar un error claro si la base todavía no está disponible.

## 5. Redis compartido

No crees otro contenedor Redis ni otra contraseña para un consumidor. Lee la
contraseña del stack y valida el servicio con `REDISCLI_AUTH`:

```bash
REDIS_PASSWORD="$(awk -F= '$1=="REDIS_PASSWORD"{print substr($0,index($0,"=")+1)}' "$dkco/datasql/.env")"
svc exec datasql redis \
  env REDISCLI_AUTH="$REDIS_PASSWORD" redis-cli PING
unset REDIS_PASSWORD
```

La respuesta esperada es `PONG`. El consumidor debe usar
`dataredis:6379` dentro de `db_net` y la misma contraseña, leída de forma
segura desde su configuración.

## 6. Consumidores confirmados y pendientes

| Servicio | PostgreSQL | Redis | Estado |
|---|---|---|---|
| Flowise | `flowise_db` vía `datapostgres:5432` | `dataredis:6379` | Verificar main y worker |
| Home Assistant | `homeassistant_db` vía `127.0.0.1:5432` | No confirmado | `network_mode: host` |
| n8n | `n8n_db` si su compose lo confirma | Por auditar | No asumir SQLite/PostgreSQL |

Una base existente no demuestra que el servicio actual la use. Confirma
siempre compose, configuración efectiva y runtime.

## 7. Errores que no deben confundirse

- `datapostgres:5432` funciona desde un contenedor conectado a `db_net`.
- `127.0.0.1:5432` funciona para Home Assistant host-network, pero desde
  `datapgadmin` o cualquier otro contenedor apunta al contenedor equivocado.
- `6379` interno de Redis no debe publicarse en el host.
- Un `healthy` de PostgreSQL no crea automáticamente bases ni roles para una
  aplicación.
- `db_net` permite conexión, pero no configura las variables de la aplicación.
- ParadeDB ofrece extensiones en la imagen, pero cada base debe habilitar solo
  las extensiones que realmente necesita.

## 8. Relación con la guía de instalación

Usa [`aipostgres-guide.md`](aipostgres-guide.md) cuando necesites:

- instalar el stack desde cero;
- renombrar el stack temporal `aipostgres` a `$dkco/datasql`;
- corregir permisos de pgAdmin;
- recrear o recuperar los tres contenedores;
- comprobar los puertos, la red y el estado del stack.

Usa esta guía cuando necesites:

- crear una base o un rol para un servicio nuevo;
- conectar una aplicación a `datapostgres` o `dataredis`;
- habilitar `vector` o `pg_search` en una base concreta;
- verificar la propiedad y el acceso de una base;
- diagnosticar la configuración de un consumidor.
