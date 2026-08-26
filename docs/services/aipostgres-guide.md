# ParadeDB en `datasql` — instalación limpia y operación

> Esta es la guía canónica del stack final desplegado en `$dkco/datasql`.
> El nombre operativo del directorio es `datasql`; `aipostgres` es la base
> administrativa y también un alias histórico del stack. No debe existir un
> segundo stack PostgreSQL IA separado para esta instalación.
>
> **Estado final:** ParadeDB PostgreSQL 17 (`datapostgres`), pgAdmin 9.17
> (`datapgadmin`) y Redis 7 (`dataredis`). La instalación descrita aquí parte
> de cero y no conserva las bases antiguas del DataSQL que fue eliminado.
>
> Esta guía no contiene contraseñas reales. Los comandos leen secretos desde
> `$dkco/datasql/.env` sin hacer `source .env` ni imprimir sus valores.

## 1. Estado final y nombres que no se deben cambiar

```text
$dkco/datasql/
├── datapostgres  → ParadeDB PostgreSQL 17 + pgvector + pg_search + pg_cron
├── datapgadmin   → pgAdmin 9.17
└── dataredis     → Redis 7
```

| Componente | Contenedor | Acceso correcto |
|---|---|---|
| PostgreSQL | `datapostgres` | `127.0.0.1:5432` desde el host; `datapostgres:5432` en `db_net` |
| pgAdmin | `datapgadmin` | `http://${SERVER_IP}:5050` desde la LAN |
| Redis | `dataredis` | `dataredis:6379` solo en `db_net` |

La base administrativa es `aipostgres` y el usuario administrativo es
`aiadmin`. Estos nombres pertenecen a PostgreSQL; no son los nombres que debe
usar un consumidor Docker como hostname. Las aplicaciones en `db_net` usan
`datapostgres` y `dataredis`.

El compose final está en:

```text
$NAS_DOTFILES/agent/catalog/services/datasql/compose.yml
```

Al desplegarlo en `$dkco/datasql/`, `extends.file` debe apuntar a
`../_common.yml`. El catálogo conserva `../../_common.yml` porque está dos
niveles más abajo.

### Puertos y exposición

- PostgreSQL se publica únicamente como `127.0.0.1:5432:5432`. Esta excepción
  host-only permite que Home Assistant, que usa `network_mode: host`, conecte
  al Recorder sin exponer la base a la LAN.
- pgAdmin se publica como `5050:80` para que el panel esté disponible desde la
  LAN. Es una excepción documentada para un dashboard administrativo.
- Redis no tiene `ports:`. Nunca debe aparecer como puerto publicado en
  `svc port-map`.

### Extensiones

La imagen `paradedb/paradedb:0.25.4-pg17` incluye `vector`, `pg_search` y
`pg_cron`. El compose precarga `pg_search,pg_cron` y configura
`cron.database_name=${POSTGRES_DB}`. Las extensiones se habilitan por base;
no se crean por adelantado en bases de aplicaciones que todavía no existen.

RustFS no forma parte de este stack. Solo se instalará como servicio S3
independiente cuando exista un consumidor real como LobeHub.

## 2. Dos escenarios de primera instalación

Usa **solo uno** de los escenarios siguientes.

### Escenario A — NAS nuevo, sin ningún stack anterior

Usa esta ruta si `$dkco/datasql/` no existe o no contiene datos que deban
conservarse. Las fases completas están en la sección 3.

### Escenario B — ParadeDB ya está en `$dkco/aipostgres` y se elimina DataSQL

Este es el procedimiento que corresponde a la instalación real que usó
nombres temporales (`aipostgres`, `aipgadmin`, `airedis`) y puertos temporales
(`5433`, `5051`). Es **destructivo** para el stack DataSQL antiguo: no hace
backups y elimina sus bind mounts. No lo ejecutes si necesitas recuperar sus
bases.

Antes de detener nada, verifica que la fuente ParadeDB sea la correcta y que
el destino que vas a eliminar sea realmente el DataSQL viejo:

```bash
if [[ ! -f "$dkco/aipostgres/compose.yml" || ! -f "$dkco/aipostgres/.env" ]]; then
  printf 'Falta compose.yml o .env en %s; no se elimina nada.\\n' "$dkco/aipostgres" >&2
  exit 1
fi

if ! grep -q 'paradedb/paradedb:0.25.4-pg17' "$dkco/aipostgres/compose.yml"; then
  printf 'La fuente no contiene la imagen ParadeDB esperada; no se elimina nada.\\n' >&2
  exit 1
fi

if grep -q '__pega_aqui__' "$dkco/aipostgres/.env"; then
  printf 'El .env de la fuente todavía contiene placeholders; no se elimina nada.\\n' >&2
  exit 1
fi

dk aipostgres
svc config aipostgres
```

Revisa localmente la configuración resuelta sin compartir sus secretos. Debe
mostrar la imagen ParadeDB y los tres servicios temporales. Si la validación es
correcta, confirma explícitamente la pérdida de los datos antiguos. La guía no
hace backup por decisión de esta instalación:

```bash
read -r -p 'Escribe ELIMINAR-DATASQL para continuar sin backup: ' CONFIRMACION
if [[ "$CONFIRMACION" != 'ELIMINAR-DATASQL' ]]; then
  printf 'Cancelado; no se eliminó ningún archivo.\\n'
  unset CONFIRMACION
  exit 1
fi
unset CONFIRMACION
```

Detén las aplicaciones que todavía apunten al stack antiguo y elimina los
contenedores. `svc down` no borra los bind mounts; el `rm -rf` siguiente sí
elimina los archivos antiguos de DataSQL.

```bash
svc stop flowise
svc stop homeassistant
svc stop n8n
svc down datasql
svc down aipostgres

if [[ -d "$dkco/datasql" ]]; then
  rm -rf -- "$dkco/datasql"
fi
mv -- "$dkco/aipostgres" "$dkco/datasql"
```

El `mv` debe terminar correctamente; si falla, detente y no continúes con
`sed`.
nombres temporales de los contenedores, corrige la ruta de `_common.yml` si el
archivo fue copiado desde el catálogo y fija los puertos finales:

```bash
dk datasql

sed -i \
  -e 's#file: ../../_common.yml#file: ../_common.yml#g' \
  -e 's/container_name: aipostgres/container_name: datapostgres/' \
  -e 's/container_name: aipgadmin/container_name: datapgadmin/' \
  -e 's/container_name: airedis/container_name: dataredis/' \
  compose.yml

sed -i \
  -e 's/^AIPG_POSTGRES_HOST_PORT=.*/AIPG_POSTGRES_HOST_PORT=5432/' \
  -e 's/^AIPGADMIN_PORT=.*/AIPGADMIN_PORT=5050/' \
  .env
```

No continúes si `.env` no existe o si alguna de las dos variables de puertos
no está presente. En ese caso, abre el archivo local y agrega únicamente las
variables faltantes; no escribas contraseñas en el repositorio.

Verifica los cambios antes de recrear:

```bash
grep -n 'container_name' compose.yml
grep -nE 'AIPG_POSTGRES_HOST_PORT|AIPGADMIN_PORT' .env
svc config datasql
```

La salida de `grep` debe contener exactamente `datapostgres`, `datapgadmin` y
`dataredis`. La configuración resuelta debe mostrar `127.0.0.1:5432:5432` y
`5050:80`; no debe mostrar `5433`, `5051`, `aipgadmin`, `airedis` ni
`ipv4_address`.

Recrea el stack final. En esta instalación `svc recreate` es intencional: crea
los contenedores con los nombres definitivos sin hacer pull de una imagen
innecesariamente.

```bash
svc recreate datasql
svc ps datasql
svc port-map
```

Resultado esperado, sin publicar credenciales:

```text
datapostgres  paradedb/paradedb:0.25.4-pg17  Up (healthy)  127.0.0.1:5432->5432/tcp
datapgadmin   dpage/pgadmin4:9.17             Up             5050->80/tcp
dataredis     redis:7-alpine                  Up (healthy)  6379/tcp
```

`svc port-map` debe mostrar `5050`; puede omitir `5432` por ser loopback.
`svc ps datasql` es la comprobación autoritativa de `127.0.0.1:5432`. Redis
puede mostrar `6379/tcp` dentro de `svc ps`, pero nunca debe mostrar una
publicación del host.

No levantes todavía Flowise, Home Assistant ni n8n. Sus bases y roles se crean
vacíos después de verificar el clúster.

## 3. Instalación limpia desde cero

Sigue siempre el orden temporal: **directorios → archivos → permisos →
validación → servicio**. No ejecutes `chmod` o `chown` sobre rutas que todavía
no existen.

### 3.1 Preflight

Estos comandos solo leen el estado del NAS:

```bash
svc health
svc ps datasql
svc net
svc port-map
nas
disk
```

Continúa solo si `db_net` existe y no hay otro servicio usando los puertos
finales. Si falta `db_net`, detente y aplica el bootstrap inicial documentado
en `docs/docker-entorno.md`; no inventes otra red ni elimines una red
compartida.

### 3.2 Crear directorios

```bash
mkdir -p \
  "$dkco/datasql/data/postgres/pgdata" \
  "$dkco/datasql/data/postgres/backups" \
  "$dkco/datasql/data/pgadmin" \
  "$dkco/datasql/data/redis"
```

Árbol esperado:

```text
$dkco/datasql/
├── compose.yml
├── .env
└── data/
    ├── postgres/
    │   ├── pgdata/
    │   └── backups/
    ├── pgadmin/
    └── redis/
```

### 3.3 Copiar el compose y crear el `.env` local

```bash
cp "$NAS_DOTFILES/agent/catalog/services/datasql/compose.yml" \
  "$dkco/datasql/compose.yml"
cp "$NAS_DOTFILES/agent/catalog/services/datasql/.env.example" \
  "$dkco/datasql/.env"
sed -i \
  's#file: ../../_common.yml#file: ../_common.yml#g' \
  "$dkco/datasql/compose.yml"
```

El `.env` local debe contener estas variables, con valores reales solo en el
NAS. El archivo de ejemplo del repositorio usa `__pega_aqui__`:

```text
POSTGRES_DB=aipostgres
POSTGRES_USER=aiadmin
POSTGRES_PASSWORD=__pega_aqui__
PGADMIN_EMAIL=admin@local.lan
PGADMIN_PASSWORD=__pega_aqui__
REDIS_PASSWORD=__pega_aqui__
AIPG_POSTGRES_HOST_PORT=5432
AIPGADMIN_PORT=5050
```

Genera secretos nuevos sin imprimirlos ni copiarlos a Git:

```bash
dk datasql

ENV_FILE="$dkco/datasql/.env"
(
  umask 077
  POSTGRES_PASS=$(openssl rand -hex 32)
  PGADMIN_PASS=$(openssl rand -hex 32)
  REDIS_PASS=$(openssl rand -hex 32)

  sed -i \
    -e "s/^POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=$POSTGRES_PASS/" \
    -e "s/^PGADMIN_PASSWORD=.*/PGADMIN_PASSWORD=$PGADMIN_PASS/" \
    -e "s/^REDIS_PASSWORD=.*/REDIS_PASSWORD=$REDIS_PASS/" \
    "$ENV_FILE"

  unset POSTGRES_PASS PGADMIN_PASS REDIS_PASS
)
unset ENV_FILE
```

No pongas `SERVER_IP` ni `TZ` en este archivo: se heredan desde el `.env`
global mediante `env_file: [../.env, .env]`. No uses `source .env`.

### 3.4 Aplicar permisos

Este paso ocurre después de crear los directorios y los archivos. pgAdmin
necesita UID/GID `5050:5050` en su bind mount:

```bash
chown -R 5050:5050 "$dkco/datasql/data/pgadmin"
chmod 700 "$dkco/datasql/data/postgres/pgdata"
chmod 700 "$dkco/datasql/data/postgres/backups"
chmod 700 "$dkco/datasql/data/pgadmin"
chmod 700 "$dkco/datasql/data/redis"
chmod 600 "$dkco/datasql/.env"
```

No uses `chmod -R 777` ni apliques el `chown` de pgAdmin a PostgreSQL o Redis.
Redis hereda `security_opt: no-new-privileges:true` desde `$dkco/_common.yml`;
no añadas una segunda clave local igual porque Compose puede rechazarla por
duplicada.

### 3.5 Validar antes de levantar

```bash
dk datasql
svc config datasql
```

`svc config` puede resolver y mostrar secretos. Revisa la salida solo en el
NAS; no la pegues en chats, issues o PRs.

Debe aparecer todo lo siguiente:

- `paradedb/paradedb:0.25.4-pg17`.
- `datapostgres`, `datapgadmin` y `dataredis`.
- `db_net` externa.
- `127.0.0.1:5432:5432` y `5050:80`.
- Redis sin `ports:`.
- `shared_preload_libraries=pg_search,pg_cron`.
- `cron.database_name=aipostgres` una vez interpolado.
- `env_file` global y local.

No levantes el stack si aparece `0.0.0.0:5432`, `5433`, `5051`, una IP fija
`ipv4_address`, una ruta incorrecta de `_common.yml` o un puerto publicado para
Redis.

## 4. Levantar y hacer la verificación inicial

```bash
svc pull datasql
svc up datasql
svc ps datasql
```

Revisa los logs sin mostrar secretos:

```bash
svc logs datasql
```

`Ctrl-C` termina la vista de logs, no detiene los contenedores. Después ejecuta
la verificación global:

```bash
svc health
svc ps datasql
svc net
svc port-map
```

Condiciones de aceptación:

- `datapostgres` está `Up (healthy)`.
- `dataredis` está `Up (healthy)`.
- `datapgadmin` está `Up` y responde en `http://${SERVER_IP}:5050`.
- `svc ps datasql` muestra `127.0.0.1:5432->5432/tcp`.
- `svc port-map` muestra `5050` y no muestra `6379`.
- No hay reinicios repetidos en los tres contenedores.

Confirma el bind de PostgreSQL en el host:

```bash
ss -ltnp | grep ':5432'
```

La salida debe contener `127.0.0.1:5432`. Si contiene `0.0.0.0:5432` o
`[::]:5432`, detente: la base quedó expuesta a la LAN.

### 4.1 Verificar PostgreSQL y extensiones

Lee las variables sin `source` y abre `psql` dentro del servicio Compose:

```bash
PGPASS=$(grep '^POSTGRES_PASSWORD=' "$dkco/datasql/.env" | cut -d= -f2-)
PGUSER=$(grep '^POSTGRES_USER=' "$dkco/datasql/.env" | cut -d= -f2-)
PGDB=$(grep '^POSTGRES_DB=' "$dkco/datasql/.env" | cut -d= -f2-)

svc exec datasql postgres \
  env PGPASSWORD="$PGPASS" PGUSER="$PGUSER" PGDATABASE="$PGDB" psql
```

En el prompt `aipostgres=#`, ejecuta SQL, no Bash:

```sql
SELECT version();
SHOW cron.database_name;

SELECT name, default_version, installed_version
FROM pg_available_extensions
WHERE name IN ('vector', 'pg_search', 'pg_cron')
ORDER BY name;

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_search;
CREATE EXTENSION IF NOT EXISTS pg_cron;

SELECT extname, extversion
FROM pg_extension
WHERE extname IN ('vector', 'pg_search', 'pg_cron')
ORDER BY extname;
```

`SHOW cron.database_name` debe devolver `aipostgres` y las tres extensiones
deben aparecer en `pg_extension`. Sal de `psql` y limpia las variables:

```text
\q
```

```bash
unset PGPASS PGUSER PGDB
```

No pegues `SELECT`, `SHOW` o `CREATE` directamente en Bash. Tampoco uses una
variante como `svc exec datasql -v ...`: el parser de `svc` puede interpretar
`-v` como una opción propia.

### 4.2 Verificar Redis

```bash
REDIS_PASSWORD=$(grep '^REDIS_PASSWORD=' "$dkco/datasql/.env" | cut -d= -f2-)
svc exec datasql redis \
  env REDISCLI_AUTH="$REDIS_PASSWORD" redis-cli PING
unset REDIS_PASSWORD
```

La respuesta debe ser `PONG`. `REDISCLI_AUTH` evita colocar la contraseña en
los argumentos de `redis-cli`.

### 4.3 Verificar pgAdmin

Abre desde la LAN:

```text
http://${SERVER_IP}:5050
```

Usa `PGADMIN_EMAIL` y `PGADMIN_PASSWORD` para el login web. Después selecciona
**Add New Server** con estos datos:

```text
Host: datapostgres
Port: 5432
Maintenance DB: aipostgres
Username: aiadmin
Password: POSTGRES_PASSWORD
```

Desde pgAdmin no uses `127.0.0.1`: ese loopback sería el contenedor de pgAdmin,
no PostgreSQL. El hostname correcto entre contenedores es `datapostgres` por
`db_net`. Si aparece el mensaje `The CSRF session token is missing`, recarga
la sesión, cierra sesión y vuelve a entrar; no cambies la base para resolverlo.

## 5. Crear bases limpias para consumidores

No levantes una aplicación consumidora hasta crear su base y rol dedicados.
`db_net` solo permite comunicación; no demuestra que la aplicación esté
configurada para usar PostgreSQL.

Para cada aplicación:

1. Lee su contraseña desde el `.env` propio, sin mostrarla.
2. Crea el rol en una llamada de `psql` separada.
3. Crea la base con ese rol como propietario en otra llamada.
4. Verifica conexión con el usuario de la aplicación.
5. Configura el consumidor con `datapostgres:5432` y, si necesita Redis,
   `dataredis:6379`.
6. Limpia variables temporales con `unset`.

Ejemplo para Flowise, usando la contraseña que ya existe en su `.env`:

```bash
APP_DB_PASSWORD=$(grep '^FLOWISE_DB_PASSWORD=' "$dkco/flowise/.env" | cut -d= -f2-)
PGPASS=$(grep '^POSTGRES_PASSWORD=' "$dkco/datasql/.env" | cut -d= -f2-)
PGUSER=$(grep '^POSTGRES_USER=' "$dkco/datasql/.env" | cut -d= -f2-)
PGDB=$(grep '^POSTGRES_DB=' "$dkco/datasql/.env" | cut -d= -f2-)

svc exec datasql postgres \
  env PGPASSWORD="$PGPASS" PGUSER="$PGUSER" PGDATABASE="$PGDB" psql
```

En `psql`, crea el rol y solicita su contraseña sin escribirla en la guía:

```sql
CREATE ROLE flowise_user LOGIN;
\password flowise_user
\q
```

Abre otra sesión administrativa y crea la base por separado:

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

Verifica la identidad del consumidor y limpia secretos temporales:

```bash
svc exec datasql postgres \
  env PGPASSWORD="$APP_DB_PASSWORD" psql \
  -U flowise_user -d flowise_db \
  -c 'SELECT current_user, current_database();'

unset APP_DB_PASSWORD PGPASS PGUSER PGDB
```

La consulta debe devolver `flowise_user | flowise_db`. Repite el patrón para
Home Assistant y n8n solo después de confirmar sus variables efectivas. Home
Assistant, por usar `network_mode: host`, usa `127.0.0.1:5432`; los contenedores
conectados a `db_net` usan `datapostgres:5432`.

Flowise, cuando esté confirmado, debe usar:

```text
PostgreSQL: datapostgres:5432
Redis:      dataredis:6379
```

Después de cambiar su `.env`, recrea y verifica el consumidor, no el stack de
bases a ciegas:

```bash
svc recreate flowise
svc ps flowise
svc logs flowise
```

## 6. Problemas conocidos

### ParadeDB informa que `pg_cron` no está precargado

El compose final ya contiene:

```text
shared_preload_libraries=pg_search,pg_cron
cron.database_name=aipostgres
```

Sincroniza el compose, valida y recrea únicamente `datasql`. No borres
`data/postgres/pgdata`:

```bash
dk datasql
svc config datasql
svc recreate datasql
svc ps datasql
svc logs datasql
```

En `psql`, `SHOW cron.database_name;` debe devolver `aipostgres` antes de crear
`pg_cron`.

### pgAdmin muestra `Permission denied`

El orden es ownership y después permisos:

```bash
chown -R 5050:5050 "$dkco/datasql/data/pgadmin"
chmod 700 "$dkco/datasql/data/pgadmin"
svc restart datasql
svc ps datasql
```

No borres toda la instalación.

### pgAdmin termina con `EOFError` durante la migración inicial

Solo si el directorio es nuevo y todavía no tiene servidores configurados,
aparta la carpeta incompleta en vez de borrarla:

```bash
svc down datasql
TS="$(date +%Y%m%d-%H%M%S)"
mv "$dkco/datasql/data/pgadmin" \
  "$dkco/datasql/data/pgadmin.partial-$TS"
mkdir -p "$dkco/datasql/data/pgadmin"
chown -R 5050:5050 "$dkco/datasql/data/pgadmin"
chmod 700 "$dkco/datasql/data/pgadmin"
unset TS
svc up datasql
svc ps datasql
svc logs datasql
```

Si ya configuraste servidores en pgAdmin, detente y conserva la carpeta para
una recuperación específica.

### Redis muestra `vm.overcommit_memory`

Es un warning del host si el healthcheck sigue en `healthy` y Redis responde
`PONG`. No borres ni recrees el stack por ese warning. La corrección del host
se decide aparte y no es requisito para esta instalación.

## 7. Operación y datos críticos

```bash
svc ps datasql
svc stats datasql
svc logs datasql
svc restart datasql
svc update datasql
svc backup datasql
```

Datos críticos:

- `$dkco/datasql/data/postgres/pgdata/` — clúster PostgreSQL.
- `$dkco/datasql/data/postgres/backups/` — dumps.
- `$dkco/datasql/data/pgadmin/` — configuración de pgAdmin.
- `$dkco/datasql/data/redis/` — AOF de Redis.
- `$dkco/datasql/.env` — secretos, nunca versionar.

La instalación inicial solicitada no hace backup del DataSQL antiguo. A partir
de que el stack final esté verificado, usa `svc backup datasql` antes de
cambios destructivos futuros.
