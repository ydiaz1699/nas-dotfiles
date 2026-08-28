# DataSQL — guía única operativa de ParadeDB PostgreSQL

> Esta es la única guía de PostgreSQL del NAS y describe un único stack:
> `$dkco/datasql`.
>
> El stack ejecuta ParadeDB PostgreSQL 17 con `pgvector`, `pg_search` y
> `pg_cron`, además de pgAdmin 9.17 y Redis 7. `aipostgres` es el nombre de la
> base administrativa y un alias histórico de una ruta anterior; no es otro
> stack.
>
> La guía no contiene secretos reales. Los comandos leen valores desde los
> archivos `.env` sin hacer `source .env` ni imprimir contraseñas.

## Resumen del resultado final

| Componente | Contenedor | Acceso correcto |
|---|---|---|
| ParadeDB PostgreSQL 17 | `datapostgres` | `127.0.0.1:5432` desde el host; `datapostgres:5432` desde `db_net` |
| pgAdmin 9.17 | `datapgadmin` | `http://${SERVER_IP}:5050` desde la LAN |
| Redis 7 | `dataredis` | `dataredis:6379` solamente dentro de `db_net` |

El compose fuente del catálogo está en:

```text
$NAS_DOTFILES/agent/catalog/services/datasql/compose.yml
```

Cuando se copia a `$dkco/datasql/`, su `extends.file` debe apuntar a
`../_common.yml`. En el catálogo aparece `../../_common.yml` porque el archivo
está dos niveles más abajo.

### Exposición y redes

- Los consumidores Docker se conectan a la red externa `db_net`.
- PostgreSQL solo se publica en `127.0.0.1:5432:5432` para Home Assistant,
  que usa `network_mode: host`. No se expone PostgreSQL a la LAN.
- Los contenedores Docker deben usar `datapostgres:5432`, nunca
  `127.0.0.1:5432`.
- pgAdmin se publica como excepción documentada de dashboard LAN en `5050:80`.
- Redis no tiene `ports:` y nunca debe aparecer publicado en `svc port-map`.
- Un consumidor no debe declarar `depends_on` contra un contenedor de otro
  compose. Debe tolerar el arranque independiente y verificarse con `svc`.

### Extensiones

La imagen `paradedb/paradedb:0.25.4-pg17` proporciona:

- `vector` — pgvector.
- `pg_search` — búsqueda de ParadeDB.
- `pg_cron` — tareas programadas dentro de PostgreSQL.

El compose precarga `pg_search,pg_cron` y configura
`cron.database_name=${POSTGRES_DB}`. Las extensiones se habilitan por base: no
se instalan automáticamente en cada base de aplicación. `pg_cron` solo debe
habilitarse en la base configurada por `cron.database_name`.

RustFS no forma parte de este stack. Solo se instalará como servicio S3
separado cuando exista un consumidor real de objetos.

---

## Auditoría de fuentes y variantes

| Fuente | Operación o afirmación | Tipo | Confianza | Decisión y propósito | Clasificación |
|---|---|---|---|---|---|
| Guía histórica `guía histórica de instalación`, §§1–4 | Stack final `datasql` con ParadeDB 17, pgAdmin, Redis, nombres y puertos | HECHO | ALTA | Integrar como arquitectura e instalación del único stack | INTEGRADO |
| Guía histórica `guía histórica de instalación`, §2 | Migración destructiva desde la ruta histórica `$dkco/aipostgres` | HECHO | ALTA | Mantener como escenario explícito y no confundirlo con otro stack | INTEGRADO |
| Guía histórica `guía histórica de instalación`, §§3–4 | Orden de instalación, permisos, validación y verificación inicial | HECHO | ALTA | Mantener la secuencia directorios → archivos → permisos → servicio | INTEGRADO |
| Guía histórica `guía histórica de instalación`, §§5–6 | Operación, problemas de pgAdmin/Redis/pg_cron y datos críticos | HECHO | ALTA | Integrar en la única guía y mejorar la navegación | INTEGRADO |
| Guía anterior `datasql-guide.md`, §§1–7 | Consumidores, creación de roles/bases, Redis compartido y hostnames | HECHO | ALTA | Integrar después de verificar el clúster | INTEGRADO |
| Ambas guías | Enlaces cruzados entre dos documentos | HECHO | ALTA | Reemplazar por referencias internas a esta guía única | REEMPLAZADO |
| Ambas guías | Nombres temporales `aipgadmin`, `airedis` y puertos `5433`/`5051` | HECHO | ALTA | Conservar solo en el escenario histórico de migración | FUERA_DE_ALCANCE del estado final |
| Conversación/runtime n8n | Auditoría real de rol, base, compose, logs, migraciones y healthcheck | HECHO | ALTA | Integrar n8n como consumidor PostgreSQL confirmado; mantener el hardening/version pin como pendiente | INTEGRADO |
| Fuentes disponibles | Instalación de RustFS | HECHO | ALTA | Mantener fuera del stack PostgreSQL; destino: servicio S3 separado | FUERA_DE_ALCANCE |

## Hechos confirmados por las fuentes

1. El stack operativo único vive en `$dkco/datasql`.
2. Sus contenedores finales son `datapostgres`, `datapgadmin` y `dataredis`.
3. PostgreSQL usa la imagen `paradedb/paradedb:0.25.4-pg17`.
4. PostgreSQL se publica en loopback para Home Assistant; Redis permanece
   interno y pgAdmin tiene la excepción LAN en `5050`.
5. Los consumidores Docker usan `datapostgres` y `dataredis` dentro de
   `db_net`.
6. Cada consumidor necesita su propio rol, base y contraseña; no debe usar
   `aiadmin` ni `aipostgres` como identidad de aplicación.
7. `CREATE ROLE` y `CREATE DATABASE` se ejecutan en llamadas separadas de
   `psql`.
8. La contraseña administrativa se pasa mediante `PGPASSWORD` y la de Redis
   mediante `REDISCLI_AUTH`; no se usa `source .env`.
9. Flowise está confirmado con `flowise_db` y Redis compartido; Home Assistant
   usa `homeassistant_db` por loopback; n8n está confirmado con `n8n_db` y
   `n8n_user` por `datapostgres:5432` dentro de `db_net`. La ficha y guía n8n
   separan el runtime comprobado del hardening/version pin aún no verificado.

## Decisiones derivadas durante la unificación

1. `docs/services/datasql-guide.md` queda como única guía canónica. La división
   anterior entre guía de instalación y guía de consumidores se elimina porque
   describía dos documentos, no dos stacks.
2. La instalación y la creación de bases aparecen en orden temporal: primero se
   valida y levanta el clúster; después se crean los consumidores.
3. La migración desde `$dkco/aipostgres` se conserva como escenario histórico
   destructivo, pero se presenta explícitamente como transición hacia el único
   stack `$dkco/datasql`.
4. Las dos formas de leer variables administrativas (`awk` y `grep`) se
   conservan donde cumplen propósitos distintos: `awk` valida claves con valor
   completo y `grep` se mantiene en verificaciones operativas heredadas. Ninguna
   hace `source .env`.

## Artefactos identificados

| Tipo | Identificador | Estado inicial | Operación | Estado esperado | Fuente |
|---|---|---|---|---|---|
| Directorio | `$dkco/datasql/` | Puede no existir | Crear o renombrar | Única ruta operativa del stack | Guía histórica §2–3 |
| Archivo | `$dkco/datasql/compose.yml` | Puede no existir o ser histórico | Copiar/modificar/validar | Compose final con tres contenedores | Guía histórica §2–3 |
| Archivo secreto | `$dkco/datasql/.env` | Puede no existir | Crear y proteger | Variables reales, modo `600` | Guía histórica §3.3–3.4 |
| Directorios de datos | `$dkco/datasql/data/postgres/pgdata`, `backups`, `pgadmin`, `redis` | Pueden no existir | Crear y proteger | Bind mounts disponibles antes de `svc up` | Guía histórica §3.2–3.4 |
| Red Docker | `db_net` | Debe existir | Verificar, no recrear aquí | Red externa compartida | Ambas guías |
| Contenedores | `datapostgres`, `datapgadmin`, `dataredis` | No creados o históricos | Crear/recrear/verificar | Estado estable y saludable | Guía histórica §2–4 |
| Base administrativa | `aipostgres` | Se crea por PostgreSQL | Usar para administración | No reutilizar como base de consumidor | Ambas guías |
| Roles/bases de aplicación | `$SERVICE_ID` | No existen o estado desconocido | Crear/verificar | Rol dedicado y base con propietario correcto | Guía anterior §§2–3 |
| Backup | `svc backup datasql` | No creado automáticamente | Crear antes de cambios futuros | Archivo verificable por `svc restore` | Guía histórica §7 |

---

## 1. Preflight común

Ejecuta estas consultas antes de instalar, migrar, crear bases o diagnosticar:

```bash
svc health
svc ps datasql
svc net
svc port-map
nas
disk
```

Continúa solo si:

- `db_net` existe.
- No hay otro servicio usando los puertos finales.
- Si el stack ya existe, `datapostgres` y `dataredis` están saludables antes
  de crear roles o bases.

Si falta `db_net`, detente y aplica el bootstrap documentado en
`docs/docker-entorno.md`; no inventes otra red ni elimines una red compartida.

No pegues la salida de `svc config datasql` en chats, issues o PRs: puede
contener secretos interpolados.

---

## 2. Primera instalación: elige un solo escenario

### Escenario A — NAS nuevo sin datos que conservar

Usa este escenario si `$dkco/datasql/` no existe o no contiene datos que deban
conservarse. Sigue las secciones 3 y 4.

### Escenario B — Migración histórica desde `$dkco/aipostgres`

Este escenario no crea un segundo stack. Convierte una instalación histórica,
que podía usar los nombres temporales `aipostgres`, `aipgadmin`, `airedis` y los
puertos `5433`/`5051`, en el único stack final de `$dkco/datasql`.

Es **destructivo para la instalación histórica que ya está en
`$dkco/datasql`**: no hace backup de ese destino y lo elimina antes de mover la
instalación ParadeDB de `$dkco/aipostgres`. La ruta fuente y sus datos se
conservan mediante el `mv`; si necesitas una copia independiente de cualquiera
de las dos instalaciones, detente y créala fuera de este procedimiento antes de
continuar.

#### 2.1 Validar la fuente antes de detenerla

```bash
if [[ ! -f "$dkco/aipostgres/compose.yml" || ! -f "$dkco/aipostgres/.env" ]]; then
  printf 'Falta compose.yml o .env en %s; no se elimina nada.\n' "$dkco/aipostgres" >&2
  exit 1
fi

if ! grep -q 'paradedb/paradedb:0.25.4-pg17' "$dkco/aipostgres/compose.yml"; then
  printf 'La fuente no contiene la imagen ParadeDB esperada; no se elimina nada.\n' >&2
  exit 1
fi

if grep -q '__pega_aqui__' "$dkco/aipostgres/.env"; then
  printf 'El .env de la fuente todavía contiene placeholders; no se elimina nada.\n' >&2
  exit 1
fi

dk aipostgres
svc config aipostgres
```

Revisa localmente la configuración resuelta. Debe mostrar la imagen ParadeDB y
los tres servicios históricos. Si no coincide, detente.

Antes de confirmar, valida también el destino. Si `$dkco/datasql/` existe, solo
puede eliminarse si es una instalación histórica reconocible de DataSQL; un
directorio desconocido o una instalación final queda protegido:

```bash
if [[ -e "$dkco/datasql" ]]; then
  if [[ ! -f "$dkco/datasql/compose.yml" || ! -f "$dkco/datasql/.env" ]]; then
    printf 'El destino %s existe pero no es una instalación reconocible; no se elimina nada.\n' "$dkco/datasql" >&2
    exit 1
  fi

  if ! grep -q 'paradedb/paradedb:0.25.4-pg17' "$dkco/datasql/compose.yml" || \
     ! grep -qE 'aipgadmin|airedis|5433|5051' "$dkco/datasql/compose.yml"; then
    printf 'El destino %s no coincide con la instalación histórica esperada; no se elimina nada.\n' "$dkco/datasql" >&2
    exit 1
  fi
fi
```

Si el destino contiene datos de otra instalación, detente y respáldalos fuera de
este procedimiento. La comprobación evita que la confirmación destructiva borre
una ruta que no pertenece a la migración.

#### 2.2 Confirmar la eliminación del destino

```bash
read -r -p 'Escribe ELIMINAR-DATASQL para continuar sin backup del destino: ' CONFIRMACION
if [[ "$CONFIRMACION" != 'ELIMINAR-DATASQL' ]]; then
  printf 'Cancelado; no se eliminó ningún archivo.\n'
  unset CONFIRMACION
  exit 1
fi
unset CONFIRMACION
```

#### 2.3 Detener consumidores y eliminar la instalación histórica

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

El `mv` debe terminar correctamente. Si falla, detente y no continúes.

#### 2.4 Renombrar contenedores y puertos finales

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

No continúes si `.env` no existe o si alguna variable de puerto no está
presente. Agrega únicamente las variables faltantes en el NAS; no escribas
contraseñas en el repositorio.

#### 2.5 Verificar antes de recrear

```bash
grep -n 'container_name' compose.yml
grep -nE 'AIPG_POSTGRES_HOST_PORT|AIPGADMIN_PORT' .env
svc config datasql
```

La configuración debe contener exactamente `datapostgres`, `datapgadmin` y
`dataredis`, `127.0.0.1:5432:5432` y `5050:80`. No debe contener una publicación
`5433`, `5051`, `aipgadmin`, `airedis` ni `ipv4_address`.

#### 2.6 Recrear el único stack final

```bash
svc up datasql --force-recreate
svc ps datasql
svc port-map
```

Resultado esperado, sin mostrar credenciales:

```text
datapostgres  paradedb/paradedb:0.25.4-pg17  Up (healthy)  127.0.0.1:5432->5432/tcp
datapgadmin   dpage/pgadmin4:9.17             Up             5050->80/tcp
dataredis     redis:7-alpine                  Up (healthy)  6379/tcp
```

`svc ps datasql` es la comprobación autoritativa del bind loopback. `svc
port-map` debe mostrar `5050` y no `6379`; puede omitir `5432` por ser loopback.
No levantes todavía Flowise, Home Assistant ni n8n: sus bases y roles se crean
después de verificar el clúster.

---

## 3. Instalación limpia desde cero

Sigue siempre la secuencia temporal real: **directorios → archivos → permisos
→ validación → servicio**. No ejecutes `chmod` o `chown` sobre rutas que aún no
existen.

### 3.1 Crear directorios

Si `$dkco/datasql/` ya existe, el escenario limpio solo es válido cuando está
vacío. No sobrescribas un `.env` ni reutilices un `pgdata` existente con
credenciales recién generadas:

```bash
if [[ -d "$dkco/datasql" ]] && \
   [[ -n "$(find "$dkco/datasql" -mindepth 1 -maxdepth 1 -print -quit)" ]]; then
  printf 'Existe contenido en %s; no es una instalación limpia. Usa el escenario de migración o detente.\n' "$dkco/datasql" >&2
  exit 1
fi
```

Después crea los directorios requeridos:

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

### 3.2 Copiar compose y crear el `.env`

```bash
cp "$NAS_DOTFILES/agent/catalog/services/datasql/compose.yml" \
  "$dkco/datasql/compose.yml"
cp "$NAS_DOTFILES/agent/catalog/services/datasql/.env.example" \
  "$dkco/datasql/.env"
sed -i \
  's#file: ../../_common.yml#file: ../_common.yml#g' \
  "$dkco/datasql/compose.yml"
```

El `.env` local debe contener variables reales únicamente en el NAS. El
repositorio usa placeholders:

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

### 3.3 Aplicar permisos

Este paso ocurre después de crear los directorios y archivos. pgAdmin necesita
UID/GID `5050:5050` en su bind mount:

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
no añadas una segunda clave local igual.

### 3.4 Validar antes de levantar

```bash
dk datasql
svc config datasql
```

La salida debe mostrar:

- `paradedb/paradedb:0.25.4-pg17`.
- `datapostgres`, `datapgadmin` y `dataredis`.
- `db_net` externa.
- `127.0.0.1:5432:5432` y `5050:80`.
- Redis sin `ports:`.
- `shared_preload_libraries=pg_search,pg_cron`.
- `cron.database_name=aipostgres` una vez interpolado.
- `env_file` global y local.

No levantes si aparece `0.0.0.0:5432`, `5433`, `5051`, `ipv4_address`, una ruta
incorrecta de `_common.yml` o un puerto publicado para Redis.

### 3.5 Levantar y verificar el stack

```bash
svc pull datasql
svc up datasql
svc ps datasql
```

Revisa los logs sin mostrar secretos:

```bash
svc logs datasql
```

`Ctrl-C` termina la vista de logs, no detiene los contenedores. Después ejecuta:

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
- No hay reinicios repetidos.

Confirma el bind de PostgreSQL en el host:

```bash
ss -ltnp | grep ':5432'
```

La salida debe contener `127.0.0.1:5432`. Si contiene `0.0.0.0:5432` o
`[::]:5432`, detente: la base quedó expuesta a la LAN.

---

## 4. Verificación inicial de PostgreSQL, extensiones, Redis y pgAdmin

### 4.1 PostgreSQL y extensiones

Lee las variables sin `source` y abre `psql` dentro del servicio:

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
deben aparecer en `pg_extension` después de ejecutar el SQL en la base
administrativa. Sal de `psql` y limpia las variables:

```text
\q
```

```bash
unset PGPASS PGUSER PGDB
```

No pegues `SELECT`, `SHOW` o `CREATE` directamente en Bash. Tampoco uses una
variante como `svc exec datasql -v ...`: el parser de `svc` puede interpretar
`-v` como una opción propia.

### 4.2 Redis

```bash
REDIS_PASSWORD=$(grep '^REDIS_PASSWORD=' "$dkco/datasql/.env" | cut -d= -f2-)
svc exec datasql redis \
  env REDISCLI_AUTH="$REDIS_PASSWORD" redis-cli PING
unset REDIS_PASSWORD
```

La respuesta debe ser `PONG`. `REDISCLI_AUTH` evita colocar la contraseña en
los argumentos de `redis-cli`.

### 4.3 pgAdmin

Abre desde la LAN:

```text
http://${SERVER_IP}:5050
```

Usa `PGADMIN_EMAIL` y `PGADMIN_PASSWORD` para el login. En **Add New Server**:

```text
Host: datapostgres
Port: 5432
Maintenance DB: aipostgres
Username: aiadmin
Password: POSTGRES_PASSWORD
```

Desde pgAdmin no uses `127.0.0.1`: ese loopback sería el contenedor de pgAdmin,
no PostgreSQL. El hostname correcto entre contenedores es `datapostgres` por
`db_net`. Si aparece `The CSRF session token is missing`, recarga la sesión,
cierra sesión y vuelve a entrar; no cambies la base para resolverlo.

---

## 5. Crear una base y un rol para un servicio nuevo

No levantes una aplicación consumidora hasta crear su base y rol dedicados.
`db_net` solo permite comunicación; no demuestra que la aplicación esté
configurada para usar la base correcta.

### 5.1 Preflight administrativo

Ejecuta siempre antes de crear roles, bases o conexiones:

```bash
svc health
svc ps datasql
svc net
```

Continúa solo si `datapostgres` y `dataredis` están saludables y `db_net` está
presente.

Lee los valores administrativos desde el `.env` sin mostrar contraseñas:

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

### 5.1.1 Ruta rápida por terminal — Home Assistant

Para un servicio nuevo, no es necesario usar pgAdmin para crear el rol y la
base. Esta es la ruta recomendada en el NAS: usa `svc exec`, no `docker exec`,
no hace `source .env` y no escribe la contraseña en el SQL.

El CLI `svc exec` del NAS puede interpretar opciones como `-U`, `-d` y `-c`
como opciones propias. Por eso se pasan `PGUSER` y `PGDATABASE` mediante
`env`, y las consultas se escriben dentro de sesiones interactivas de `psql`.

Las variables administrativas de la sección anterior ya están cargadas. Crea
el rol en una sesión interactiva:

```bash
svc exec datasql postgres \
  env PGPASSWORD="$PG_ADMIN_PASSWORD" \
      PGUSER="$PG_ADMIN_USER" \
      PGDATABASE="$PG_ADMIN_DB" \
  psql
```

En `psql` ejecuta:

```sql
CREATE ROLE ha_user LOGIN;
\password ha_user
```

Introduce dos veces la contraseña dedicada de Home Assistant y sal:

```text
\q
```

Crea la base en una sesión separada. Así `CREATE DATABASE` no queda atrapado
en una transacción:

```bash
svc exec datasql postgres \
  env PGPASSWORD="$PG_ADMIN_PASSWORD" \
      PGUSER="$PG_ADMIN_USER" \
      PGDATABASE="$PG_ADMIN_DB" \
  psql
```

En `psql` ejecuta:

```sql
CREATE DATABASE homeassistant_db OWNER ha_user;

SELECT datname,
       pg_get_userbyid(datdba) AS owner
FROM pg_database
WHERE datname = 'homeassistant_db';
```

La consulta debe devolver `homeassistant_db | ha_user`. Si `CREATE DATABASE`
responde que la base ya existe, no la recrees: ejecuta solo la consulta y
verifica el propietario. Sal de `psql`:

```text
\q
```

Verifica la conexión con el usuario dedicado. Después de salir de `psql`, vuelve
a introducir temporalmente la misma contraseña en la terminal para probar el
login; no la escribas en esta guía ni en el chat:

```bash
read -r -s -p 'Contraseña de ha_user para verificar: ' HA_DB_PASSWORD
printf '\n'

svc exec datasql postgres \
  env PGPASSWORD="$HA_DB_PASSWORD" \
      PGUSER=ha_user \
      PGDATABASE=homeassistant_db \
  psql
```

En `psql` ejecuta:

```sql
SELECT current_user, current_database();
```

El resultado esperado es `ha_user | homeassistant_db`. Sal de `psql` con
`\q` y limpia las variables:

```bash
unset PG_ADMIN_PASSWORD PG_ADMIN_USER PG_ADMIN_DB HA_DB_PASSWORD
```

Para Home Assistant, el `db_url` usa el puerto loopback real detectado en
`AIPG_POSTGRES_HOST_PORT`, normalmente `127.0.0.1:5432`; no uses
`datapostgres` ni una IP fija de Docker desde HA.

### 5.2 Definir nombres y leer la contraseña del consumidor

Sustituye únicamente los valores confirmados por el compose del nuevo
servicio. Este ejemplo usa Flowise:

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
continuar. El orden mínimo es crear la carpeta, crear los archivos y después
aplicar permisos:

```bash
mkdir -p "$dkco/$SERVICE_ID/data"
# Crear el .env y compose completos del servicio antes de aplicar permisos.
chmod 600 "$dkco/$SERVICE_ID/.env"
```

No sobrescribas un `.env` real ni uses la variable de contraseña de otro
servicio sin confirmar su nombre.

### 5.3 Crear primero el rol

Abre una sesión administrativa interactiva. `svc exec` recibe la contraseña por
`PGPASSWORD`; no uses `source .env`:

```bash
svc exec datasql postgres \
  env PGPASSWORD="$PG_ADMIN_PASSWORD" \
      PGUSER="$PG_ADMIN_USER" \
      PGDATABASE="$PG_ADMIN_DB" \
  psql
```

En el prompt, ejecuta solamente SQL:

```sql
CREATE ROLE flowise_user LOGIN;
\password flowise_user
```

Cuando `psql` solicite la contraseña, introduce el valor que el consumidor lee
desde `FLOWISE_DB_PASSWORD`. No escribas ese valor en la guía, el SQL ni un
commit. Sal de la sesión:

```text
\q
```

Si el rol ya existe, no lo recrees a ciegas: verifica que sea el rol correcto y
que su contraseña coincida con el `.env` efectivo del consumidor.

### 5.4 Crear la base en una llamada separada

`CREATE ROLE` y `CREATE DATABASE` no se combinan. Abre una nueva sesión
administrativa, fuera de una transacción:

```bash
svc exec datasql postgres \
  env PGPASSWORD="$PG_ADMIN_PASSWORD" \
      PGUSER="$PG_ADMIN_USER" \
      PGDATABASE="$PG_ADMIN_DB" \
  psql
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
existe, consulta primero su propietario y corrígelo solo después de confirmar
la configuración del servicio.

### 5.5 Verificar la conexión con el usuario dedicado

Prueba con la contraseña del consumidor, no con la administrativa:

```bash
svc exec datasql postgres \
  env PGPASSWORD="$APP_DB_PASSWORD" \
      PGUSER="$APP_DB_USER" \
      PGDATABASE="$APP_DB_NAME" \
  psql
```

La salida debe identificar `flowise_user` y `flowise_db`. Limpia todas las
variables temporales:

```bash
unset PG_ADMIN_PASSWORD PG_ADMIN_USER PG_ADMIN_DB
unset SERVICE_ID SERVICE_PASSWORD_VAR APP_DB_NAME APP_DB_USER APP_DB_PASSWORD
```

### 5.6 Habilitar extensiones en una base de aplicación

Conéctate a la base de la aplicación como administrador y habilita únicamente
lo que el diseño use:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_search;
```

No habilites `pg_cron` en una base de aplicación sin confirmar primero que
`cron.database_name` fue configurado para esa base. En el stack final,
`cron.database_name` es `aipostgres`.

---

## 6. Configurar y verificar un consumidor

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

Adapta los nombres exactos al contrato de la imagen. No supongas que todas usan
`DATABASE_*`; comprueba la documentación y el compose real del servicio.

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
en otro compose. Confirma el uso real mediante compose, configuración efectiva
y runtime; `db_net` por sí sola no prueba qué base está usando la aplicación.

### Redis compartido

No crees otro contenedor Redis ni otra contraseña para un consumidor. Valida el
Redis existente así:

```bash
REDIS_PASSWORD="$(awk -F= '$1=="REDIS_PASSWORD"{print substr($0,index($0,"=")+1)}' "$dkco/datasql/.env")"
svc exec datasql redis \
  env REDISCLI_AUTH="$REDIS_PASSWORD" redis-cli PING
unset REDIS_PASSWORD
```

La respuesta esperada es `PONG`. El consumidor usa `dataredis:6379` dentro de
`db_net` y la misma contraseña desde su configuración segura.

### Consumidores conocidos

| Servicio | PostgreSQL | Redis | Estado |
|---|---|---|---|
| Flowise | `flowise_db` vía `datapostgres:5432` | `dataredis:6379` | Confirmar main y worker después de cambios |
| Home Assistant | `homeassistant_db` vía `127.0.0.1:5432` | No confirmado | `network_mode: host` |
| n8n | `n8n_db` vía `datapostgres:5432` con `n8n_user` | No configurado en el compose auditado | Runtime confirmado; no agregar Redis sin evidencia |

Una base existente no demuestra que el runtime actual la use. Confirma siempre
compose, variables efectivas y logs.

---

## 7. Operación, backup y mantenimiento

### Estado y diagnóstico

```bash
svc health
svc ps datasql
svc stats datasql
svc top datasql
svc logs datasql
svc net
svc port-map
svc size
```

`svc logs datasql` muestra el seguimiento de logs; `Ctrl-C` termina la vista,
no detiene los contenedores.

### Operaciones normales

```bash
svc restart datasql
svc update datasql
svc up datasql --force-recreate
```

Usa `svc update` para pull y recreación cuando quieras actualizar la imagen.
Usa `svc up datasql --force-recreate` para recrear sin pull cuando solo cambió
la configuración. No borres `data/postgres/pgdata` para resolver un warning de
Redis o un problema de pg_cron.

### Backup antes de cambios

Para un cambio de configuración, guarda primero la configuración y los secretos
locales con el snapshot del framework:

```bash
svc snapshot datasql
```

Para capturar los bind mounts de datos con el servicio detenido, usa el helper
de backup en este orden:

```bash
svc stop datasql
svc backup datasql
svc up datasql
```

`svc backup` genera tarballs con rotación y verifica su contenido, pero no es un
`pg_dump` lógico y no incluye automáticamente `$dkco/datasql/.env`. Por eso no se
debe presentar como backup PostgreSQL consistente mientras el servidor está
escribiendo. El `svc stop` anterior evita capturar un `pgdata` en uso; el
snapshot conserva la configuración y el `.env` antes del cambio.

Para restaurar un bind mount, detén el stack antes de extraerlo y levántalo solo
después de completar la restauración:

```bash
svc stop datasql
svc restore datasql "archivo.tar.gz"
svc up datasql
svc ps datasql
```

La restauración es destructiva y requiere confirmar el archivo y el destino.
Antes de declarar recuperación, verifica `svc ps datasql`, salud, logs,
`svc port-map` y una conexión de prueba. Para un backup lógico PostgreSQL
independiente, queda `⚠️ PENDIENTE`: las fuentes disponibles no proporcionan un
procedimiento completo de `pg_dump`/`pg_restore` para este stack.

Datos críticos:

- `$dkco/datasql/data/postgres/pgdata/` — clúster PostgreSQL.
- `$dkco/datasql/data/postgres/backups/` — dumps o backups de PostgreSQL.
- `$dkco/datasql/data/pgadmin/` — configuración de pgAdmin.
- `$dkco/datasql/data/redis/` — AOF de Redis.
- `$dkco/datasql/.env` — secretos; nunca versionar.

---

## 8. Problemas conocidos y recuperación

### ParadeDB informa que `pg_cron` no está precargado

El compose final debe contener:

```text
shared_preload_libraries=pg_search,pg_cron
cron.database_name=aipostgres
```

Sincroniza la configuración, valida y recrea únicamente `datasql`:

```bash
dk datasql
svc config datasql
svc up datasql --force-recreate
svc ps datasql
svc logs datasql
```

En `psql`, `SHOW cron.database_name;` debe devolver `aipostgres` antes de crear
`pg_cron`. No borres `data/postgres/pgdata`.

### pgAdmin muestra `Permission denied`

El orden correcto es ownership y después permisos:

```bash
chown -R 5050:5050 "$dkco/datasql/data/pgadmin"
chmod 700 "$dkco/datasql/data/pgadmin"
svc restart datasql
svc ps datasql
```

No borres toda la instalación.

### pgAdmin termina con `EOFError` durante la migración inicial

Solo si el directorio es nuevo y todavía no tiene servidores configurados, aparta
la carpeta incompleta en vez de borrarla:

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
`PONG`. No borres ni recrees el stack por ese warning; la corrección del host se
decide aparte.

### PostgreSQL no está saludable

No ejecutes creación de roles, bases ni cambios de consumidores mientras el
clúster no esté saludable:

```bash
svc health
svc ps datasql
svc logs datasql
svc config datasql
```

Revisa primero imagen, variables, bind mounts, permisos, `db_net` y la
configuración resuelta. Si el problema es de datos, usa el backup/restore del
servicio; no elimines el directorio `pgdata` como primera medida.

### Un consumidor no conecta a PostgreSQL

Comprueba, en este orden:

1. El consumidor está conectado a `db_net`.
2. Usa `datapostgres:5432`, no `127.0.0.1:5432`, salvo Home Assistant
   host-network.
3. El nombre de la base y el rol coinciden con los creados en esta guía.
4. La contraseña del consumidor coincide con su `.env` efectivo.
5. `svc ps datasql` muestra PostgreSQL saludable.
6. Los logs del consumidor muestran el error real después de recrearlo.

### Un consumidor intenta arrancar antes que DataSQL

No agregues `depends_on` entre compose distintos. Comprueba el stack con
`svc health` y `svc ps datasql`, y configura el consumidor para tolerar el
arranque independiente de la base.

---

## 9. Límites y decisiones pendientes

- `n8n_db` aparece como base existente, pero su compose y runtime aún deben
  auditarse antes de afirmar que n8n usa PostgreSQL o Redis.
- El uso de Redis por Home Assistant no está confirmado; no lo configures por
  suposición.
- LobeHub, Hermes, el agente y RustFS no forman parte de este stack. Solo deben
  agregarse como consumidores o servicios separados después de confirmar una
  necesidad real.
- La migración histórica del escenario B es irreversible respecto de los
  bind mounts eliminados si no existe un backup externo; la confirmación
  `ELIMINAR-DATASQL` es obligatoria.

## 10. Checklist final

Antes de declarar el stack operativo:

- [ ] Existe solo `$dkco/datasql` como stack PostgreSQL operativo.
- [ ] Los contenedores se llaman `datapostgres`, `datapgadmin` y `dataredis`.
- [ ] PostgreSQL usa `paradedb/paradedb:0.25.4-pg17`.
- [ ] `vector`, `pg_search` y `pg_cron` aparecen disponibles; `pg_cron` está
      habilitado únicamente en la base configurada.
- [ ] PostgreSQL solo publica `127.0.0.1:5432`.
- [ ] pgAdmin publica `5050`; Redis no publica ningún puerto.
- [ ] `db_net` es externa y está presente.
- [ ] Cada consumidor tiene rol, base y contraseña dedicados.
- [ ] Los consumidores Docker usan `datapostgres`/`dataredis` y no
      `depends_on` contra DataSQL.
- [ ] Los secretos están solo en `.env` con permisos `600` y no aparecen en
      documentación, commits, chats ni salidas compartidas.
- [ ] Se verificaron `svc health`, `svc ps datasql`, logs y `svc port-map`.

## Clasificación de contenido no duplicado

- **INTEGRADO:** instalación limpia, migración histórica, permisos, validación,
  verificación, extensiones, consumidores, roles/bases, Redis, operación y
  recuperación.
- **DUPLICADO:** enlaces y explicaciones que separaban instalación y consumo en
  dos guías; se conserva una sola versión dentro de este documento.
- **REEMPLAZADO:** referencias y metadatos que separaban instalación y consumo;
  todo apunta ahora a `docs/services/datasql-guide.md`.
- **FUERA_DE_ALCANCE:** RustFS y cualquier segundo stack PostgreSQL; se mantienen
  como servicios separados o decisiones futuras.
- **PENDIENTE:** auditoría real de n8n y confirmación del uso de Redis por Home
  Assistant.
- **RECHAZADO:** usar `127.0.0.1` desde consumidores Docker, publicar Redis,
  publicar PostgreSQL en la LAN, reutilizar `aiadmin`, combinar creación de
  rol/base o usar `source .env`, por incompatibilidad con la arquitectura y
  seguridad documentadas.
