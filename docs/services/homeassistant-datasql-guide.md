# Guía: conectar Home Assistant a PostgreSQL

## Estado: borrador operativo
## Fecha: 2026-08-25
## Resumen

Esta guía prepara PostgreSQL y configura el Recorder de Home Assistant para usarlo. No instala PostgreSQL ni DataSQL. Home Assistant puede levantarse sin esta guía porque Recorder usa SQLite por defecto; PostgreSQL solo se usa después de configurar explícitamente `recorder.db_url` en la configuración persistente de HA.

> **Alcance:** Home Assistant y PostgreSQL son decisiones independientes. Si no quieres PostgreSQL, levanta HA y conserva SQLite. Si quieres PostgreSQL, sigue todos los pasos: preparar el backend, configurar el Recorder en HA y verificar la conexión. La instalación y recuperación del stack DataSQL están en [`datasql-guide.md`](datasql-guide.md). La referencia oficial del comportamiento del Recorder es la [documentación de Home Assistant](https://www.home-assistant.io/integrations/recorder).

---

## 1. Antes de empezar: elegir el backend

Esta guía tiene dos caminos. Elige uno antes de ejecutar comandos.

### Camino A — PostgreSQL/DataSQL ya existe

Continúa solo si puedes proporcionar o leer de forma segura estos datos:

- host que Home Assistant debe usar;
- puerto PostgreSQL;
- base administrativa;
- usuario administrativo;
- contraseña administrativa;
- método para abrir `psql` contra ese servidor;
- contraseña que usarás para el usuario dedicado de Home Assistant.

La base administrativa y la base de Home Assistant no tienen que llamarse igual. La primera se usa para crear/verificar el rol y la base dedicada; la segunda será consumida por el Recorder.

### Camino B — PostgreSQL/DataSQL no existe

Detente. Esta guía no instala un motor de base de datos automáticamente ni presupone que quieras usar DataSQL.

- Si quieres usar el stack DataSQL del NAS, sigue primero [`datasql-guide.md`](datasql-guide.md) y confirma que PostgreSQL esté saludable.
- Si prefieres otro PostgreSQL, instálalo y documenta su host, puerto, base administrativa, usuario administrativo y método de acceso según la documentación de ese backend.
- Cuando el backend esté disponible y tengas esos datos, vuelve a esta guía en la sección 2.

Si eliges SQLite, no ejecutes esta guía: puedes levantar HA directamente y su Recorder usará `/config/home-assistant_v2.db`. Si eliges PostgreSQL, continúa hasta configurar y verificar HA; preparar solamente la base no conecta el servicio.

---

## 2. Decidir los valores del backend

El usuario decide los nombres y el backend. Los valores canónicos usados en el ejemplo del NAS son:

```text
Usuario dedicado:       ha_user
Base dedicada:          homeassistant_db
Endpoint DataSQL:       127.0.0.1:5432
```

Estos nombres no son obligatorios para otro backend. Si cambias alguno, reemplázalo de forma consistente en cada comando, consulta y URI de PostgreSQL. La URI se configura en Home Assistant únicamente en el paso 9, después de verificar el backend.

### Regla de red del caso NAS/DataSQL

El compose de Home Assistant usa `network_mode: host`. Para el caso NAS/DataSQL, la conexión de HA al PostgreSQL publicado en el host usa `127.0.0.1` y el puerto confirmado; no se configura `datapostgres` porque HA no está unido a `db_net`. Esta guía prepara DataSQL y después configura la URI en el archivo persistente de HA:

- En el caso canónico del NAS: `127.0.0.1` y el puerto confirmado en `.env`, `svc ps datasql` y `ss`.
- Para un PostgreSQL externo: el host y puerto que el usuario haya confirmado.
- `datapostgres:5432` es un hostname interno para consumidores conectados a `db_net`; no sirve para el HA de este compose con host networking.

No se adivinan endpoints. La configuración de HA se realiza explícitamente más adelante y no se modifica durante los pasos de preparación PostgreSQL.

---

## 3. Camino NAS/DataSQL: comprobar el endpoint y el stack

Ejecuta esta sección solamente si el backend elegido es el stack `datasql` del NAS.

### 3.1 Comprobar el puerto real publicado

```bash
dk datasql

if [[ ! -f "$dkco/datasql/.env" ]]; then
  printf 'No existe %s/.env\n' "$dkco/datasql" >&2
  exit 1
fi

HA_PG_PORT="$(awk -F= '$1=="AIPG_POSTGRES_HOST_PORT"{print substr($0,index($0,"=")+1); exit}' "$dkco/datasql/.env")"
HA_PG_PORT="${HA_PG_PORT:-5432}"
printf 'Puerto PostgreSQL para Home Assistant: 127.0.0.1:%s\n' "$HA_PG_PORT"

if ! ss -ltn | grep -Eq "127\\.0\\.0\\.1:${HA_PG_PORT}([[:space:]]|:)"; then
  printf 'No se detecta PostgreSQL escuchando en 127.0.0.1:%s.\n' "$HA_PG_PORT" >&2
  unset HA_PG_PORT
  exit 1
fi
```

No uses `5433` por memoria histórica. Usa el puerto que coincida simultáneamente con `.env`, `svc ps datasql` y `ss`.

**Checkpoint A1 — endpoint listo:** PostgreSQL escucha en `127.0.0.1:$HA_PG_PORT`.

### 3.2 Comprobar salud, contenedores y red

```bash
svc health
svc ps datasql
svc net
```

Continúa solamente si:

- `datapostgres` aparece `Up (healthy)`;
- `dataredis` aparece `Up (healthy)`;
- existe `db_net`;
- `svc ps datasql` muestra `127.0.0.1:<puerto>->5432/tcp` para PostgreSQL.

`dataredis` forma parte de la salud del stack, pero Home Assistant no necesita crear otro Redis para esta integración.

Si PostgreSQL no está saludable, detente. No levantes HA ni crees roles o bases hasta resolver DataSQL. El diagnóstico e instalación del stack están fuera del alcance de esta guía.

**Checkpoint A2 — backend DataSQL listo:** PostgreSQL está saludable y accesible por el endpoint confirmado.

### 3.3 Cargar credenciales administrativas de DataSQL

Lee las variables sin hacer `source .env` y sin imprimirlas:

```bash
PG_ADMIN_PASSWORD="$(awk -F= '$1=="POSTGRES_PASSWORD"{print substr($0,index($0,"=")+1); exit}' "$dkco/datasql/.env")"
PG_ADMIN_USER="$(awk -F= '$1=="POSTGRES_USER"{print substr($0,index($0,"=")+1); exit}' "$dkco/datasql/.env")"
PG_ADMIN_DB="$(awk -F= '$1=="POSTGRES_DB"{print substr($0,index($0,"=")+1); exit}' "$dkco/datasql/.env")"

if [[ -z "$PG_ADMIN_PASSWORD" || -z "$PG_ADMIN_USER" || -z "$PG_ADMIN_DB" ]]; then
  printf 'Falta una variable administrativa en %s/.env.\n' "$dkco/datasql" >&2
  unset PG_ADMIN_PASSWORD PG_ADMIN_USER PG_ADMIN_DB HA_PG_PORT
  exit 1
fi
```

No pegues estas variables en el chat ni las guardes en el checkpoint.

**Checkpoint A3 — credenciales administrativas cargadas:** las tres variables existen únicamente en la sesión actual.

---

## 4. Camino PostgreSQL existente que no es DataSQL

Si tu backend no es DataSQL, no uses `svc exec datasql`. Debes tener instalado un cliente `psql` en el equipo desde el que administrarás PostgreSQL y conocer el endpoint real.

Define localmente estos valores, sin guardar la contraseña en este documento:

```bash
PG_HOST='HOST_POSTGRES_CONFIRMADO'
PG_PORT='PUERTO_POSTGRES_CONFIRMADO'
PG_ADMIN_USER='USUARIO_ADMINISTRATIVO_CONFIRMADO'
PG_ADMIN_DB='BASE_ADMINISTRATIVA_CONFIRMADA'
read -r -s -p 'Contraseña administrativa de PostgreSQL: ' PG_ADMIN_PASSWORD
printf '\n'
```

La conexión administrativa genérica usa variables de entorno y opciones de `psql` directamente:

```bash
env PGPASSWORD="$PG_ADMIN_PASSWORD" \
    PGUSER="$PG_ADMIN_USER" \
    PGDATABASE="$PG_ADMIN_DB" \
  psql --host="$PG_HOST" --port="$PG_PORT"
```

En este camino, `-U`, `-d` y `-c` no pasan por el wrapper `svc`; son opciones normales de `psql`. Aun así, esta guía usa una sesión interactiva para que las consultas SQL se ejecuten dentro de `psql` y no accidentalmente en Bash.

Si no conoces alguno de los cinco datos (`PG_HOST`, `PG_PORT`, `PG_ADMIN_USER`, `PG_ADMIN_DB` o la contraseña administrativa), detente y obtén ese dato del propietario o documentación del backend. No lo adivines.

**Checkpoint B1 — backend externo identificado:** existe una sesión administrativa reproducible contra el PostgreSQL elegido.

---

## 5. Crear o verificar el rol dedicado

Este paso se ejecuta en el PostgreSQL que elegiste en la sección 1. Usa `ha_user` o el nombre dedicado que hayas decidido.

### 5.1 Generar la contraseña dedicada

Genera una contraseña local y no la pegues en el chat, el repositorio ni el historial:

```bash
openssl rand -hex 32
```

Conserva el valor solo para introducirlo con `\\password` y después guardarlo en el secreto local de HA. Si `openssl` no está disponible, usa tu gestor de secretos habitual para generar una contraseña equivalente y no continúes con una contraseña inventada o reutilizada.

### 5.2 Abrir la sesión administrativa

#### Si usas NAS/DataSQL

```bash
svc exec datasql postgres \
  env PGPASSWORD="$PG_ADMIN_PASSWORD" \
      PGUSER="$PG_ADMIN_USER" \
      PGDATABASE="$PG_ADMIN_DB" \
  psql
```

#### Si usas otro PostgreSQL

```bash
env PGPASSWORD="$PG_ADMIN_PASSWORD" \
    PGUSER="$PG_ADMIN_USER" \
    PGDATABASE="$PG_ADMIN_DB" \
  psql --host="$PG_HOST" --port="$PG_PORT"
```

**Importante para NAS/DataSQL:** no escribas `psql -U`, `psql -d` ni `psql -c` después de `svc exec`. El parser de `svc exec` puede interpretar esas opciones como opciones propias y producir `No such option: -U`. En DataSQL se pasan `PGUSER` y `PGDATABASE` mediante `env` y se usa una sesión interactiva de `psql`.

### 5.3 Consultar el rol antes de mutarlo

Dentro del prompt de `psql` ejecuta SQL, no Bash:

```sql
SELECT rolname, rolcanlogin
FROM pg_roles
WHERE rolname = 'ha_user';
```

Si no devuelve filas, crea el rol y establece su contraseña:

```sql
CREATE ROLE ha_user LOGIN;
\password ha_user
```

Introduce dos veces la contraseña dedicada. La salida de la creación debe ser:

```text
CREATE ROLE
```

Si el rol ya existe con `rolcanlogin = t`, no ejecutes `CREATE ROLE` otra vez. Si existe con `rolcanlogin = f`, habilita el login:

```sql
ALTER ROLE ha_user LOGIN;
```

Si no conoces la contraseña actual, establece una nueva sin escribirla en SQL:

```sql
\password ha_user
```

Verifica siempre el estado final en la misma sesión:

```sql
SELECT rolname, rolcanlogin
FROM pg_roles
WHERE rolname = 'ha_user';
```

Debe aparecer `ha_user` con `rolcanlogin = t`. Después sal de `psql`:

```text
\q
```

Si no puedes crear el rol, habilitar el login o establecer la contraseña, detente antes de crear la base.

**Checkpoint 5 — rol listo:** `ha_user` existe, puede iniciar sesión y su contraseña dedicada está disponible solo localmente.

---

## 6. Crear o verificar la base dedicada

### 6.1 Comprobar la base

Abre una nueva sesión administrativa usando el comando del camino elegido en la sección 5.2.

Dentro de `psql` ejecuta:

```sql
SELECT datname,
       pg_get_userbyid(datdba) AS owner
FROM pg_database
WHERE datname = 'homeassistant_db';
```

Si no devuelve filas, sal con:

```text
\q
```

### 6.2 Crear la base cuando no existe

Abre otra sesión administrativa. `CREATE DATABASE` debe ejecutarse separado de la consulta y fuera de una transacción:

```sql
CREATE DATABASE homeassistant_db OWNER ha_user;
```

La salida esperada es:

```text
CREATE DATABASE
```

Sin salir de esa sesión, verifica el propietario:

```sql
SELECT datname,
       pg_get_userbyid(datdba) AS owner
FROM pg_database
WHERE datname = 'homeassistant_db';
```

El resultado debe mostrar:

```text
homeassistant_db | ha_user
```

Después sal:

```text
\q
```

Si la base ya existe, no ejecutes `CREATE DATABASE`. Verifica únicamente el propietario. Si el propietario no es `ha_user`, detente y decide explícitamente cómo corregirlo; no cambies la propiedad de una base existente sin confirmar que es la base correcta y que no contiene datos que deban preservarse.

**Checkpoint 6 — base lista:** `homeassistant_db` existe y su propietario es `ha_user`.

---

## 7. Verificar el login dedicado

> **Límite entre Bash y `psql`:** esta sección vuelve a ejecutar comandos de Bash después de una sesión interactiva de `psql`. Antes de ejecutar `read`, `printf` o `svc exec`, debes haber salido de `psql` con `\q` y comprobar que el prompt volvió a ser parecido a `root@Nas ... #`. Si todavía ves `aipostgres=#` o `homeassistant_db=>`, sigues dentro de `psql`: ejecuta únicamente `\q` y espera el prompt de Bash. Nunca pegues comandos Bash dentro de `psql`.

Introduce temporalmente la contraseña de `ha_user` sin mostrarla:

```bash
read -r -s -p 'Contraseña de ha_user para verificar: ' HA_DB_PASSWORD
printf '\n'
```

### Si usas NAS/DataSQL

```bash
svc exec datasql postgres \
  env PGPASSWORD="$HA_DB_PASSWORD" \
      PGUSER=ha_user \
      PGDATABASE=homeassistant_db \
  psql
```

### Si usas otro PostgreSQL

```bash
env PGPASSWORD="$HA_DB_PASSWORD" \
    PGUSER=ha_user \
    PGDATABASE=homeassistant_db \
  psql --host="$PG_HOST" --port="$PG_PORT"
```

Cuando termine el comando, el prompt debe cambiar a `homeassistant_db=>` (o similar). Ese es el indicador de que estás dentro de `psql`; ahí ejecuta solamente SQL:

```sql
SELECT current_user, current_database();
```

El resultado esperado es:

```text
 current_user | current_database
--------------+------------------
 ha_user      | homeassistant_db
```

Sal con `\q`. Debes volver a un prompt parecido a `root@Nas ... #` antes de continuar con cualquier comando Bash. Si todavía ves `homeassistant_db=>`, ejecuta `\q` otra vez. Si la prueba falla, resuelve primero el endpoint, rol, contraseña, permisos o propietario.

**Checkpoint 7 — login PostgreSQL listo:** `ha_user` puede conectarse a `homeassistant_db`. Hasta aquí llega esta guía; Home Assistant no se levanta, reinicia ni configura en este procedimiento.

---

## 8. Levantar Home Assistant sin cambiar el backend por defecto

Si quieres usar SQLite, este es el camino corto. Home Assistant usa Recorder y SQLite por defecto; no necesitas crear `homeassistant_db`, `ha_user` ni editar `configuration.yaml` para levantarlo.

```bash
dk homeassistant
svc config homeassistant
svc up homeassistant
svc ps homeassistant
svc logs homeassistant
```

Abre `http://${SERVER_IP}:8123` y completa el onboarding. En este camino, el archivo esperado es `$dkco/homeassistant/data/home-assistant_v2.db` y no se debe esperar actividad de `ha_user` en PostgreSQL.

Si quieres usar PostgreSQL, no tomes este paso como verificación de PostgreSQL: continúa con el paso 9 antes de considerar la integración terminada. Puedes completar el onboarding primero, porque el onboarding inicial puede funcionar con SQLite; la configuración de PostgreSQL se aplica después en la configuración persistente de HA.

**Checkpoint 8 — HA levantado:** el contenedor está `Up` y el onboarding está completado. Este checkpoint no demuestra qué backend usa Recorder.

---

## 9. Determinar qué backend usa actualmente HA, sin modificarlo

> **Sintaxis crítica de este NAS:** `svc exec` recibe primero el nombre del proyecto/servicio (`homeassistant`) y después el nombre del servicio interno de Compose, que también es `homeassistant`. Además, la implementación Python de `svc` interpreta `-c` como una opción propia. Por eso los ejemplos que ejecutan `sh -c` fuerzan la ruta Bash y repiten el nombre interno:
>
> La forma segura para esos comandos es `NAS_CLI=bash svc exec homeassistant homeassistant sh -c 'comando'`.
>
> El comando que falló (`svc exec homeassistant sh -c ...`) omitía el nombre interno y dejaba `-c` expuesto al parser Python. No se debe reutilizar esa forma.

Estos comandos son de solo lectura. Sirven para distinguir el estado actual antes de cambiar nada.

### 9.1 Revisar la configuración persistente sin mostrar secretos

La configuración está en `$dkco/homeassistant/data/`, montada como `/config` dentro del contenedor. Busca únicamente las claves relevantes:

```bash
dk homeassistant
NAS_CLI=bash svc exec homeassistant homeassistant sh -c '
for f in /config/configuration.yaml /config/secrets.yaml /config/includes/*.yaml /config/includes/*.yml; do
  [ -f "$f" ] || continue
  awk '\''
    /^[[:space:]]*recorder:[[:space:]]*$/ { print FILENAME ":" FNR ": recorder block" }
    /^[[:space:]]*db_url:[[:space:]]*/ {
      value=tolower($0)
      if (value ~ /postgresql/) kind="PostgreSQL"
      else if (value ~ /sqlite/) kind="SQLite"
      else if (value ~ /!secret/) kind="secret reference (inspect key separately)"
      else kind="other/unknown"
      print FILENAME ":" FNR ": db_url backend=" kind
    }
  '\'' "$f"
done
'
```

No pegues en el chat una línea que contenga una contraseña o una URI completa. Si `db_url` usa `!secret`, comprueba solamente el nombre de la clave:

```bash
NAS_CLI=bash svc exec homeassistant homeassistant sh -c '
grep -nE "^[[:space:]]*[^#[:space:]][^:]*:[[:space:]]*[^#]+" /config/secrets.yaml 2>/dev/null |
sed -E "s/:[[:space:]].*/: <valor oculto>/"
'
```

Interpretación:

- `db_url` con `postgresql://` → HA está configurado para PostgreSQL, sujeto a que pueda conectarse.
- `db_url` con `sqlite:` → HA está configurado explícitamente para SQLite.
- Sin `db_url` → HA usa el SQLite por defecto.
- `db_url: !secret ...` → hay que resolver la clave localmente sin exponer su valor.

### 9.2 Comprobar el archivo SQLite por defecto

```bash
NAS_CLI=bash svc exec homeassistant homeassistant sh -c '
for f in /config/home-assistant_v2.db /config/*.db; do
  [ -e "$f" ] && stat -c "%n | %s bytes | %y" "$f"
done
'
```

La existencia de `home-assistant_v2.db` es evidencia de actividad SQLite, pero un archivo residual no demuestra por sí solo que sea el backend actual. Debe concordar con la configuración y los demás checks.

### 9.3 Confirmar conexión real desde PostgreSQL

En el NAS/DataSQL, primero carga las credenciales administrativas sin `source`:

```bash
PG_ADMIN_PASSWORD="$(awk -F= '$1=="POSTGRES_PASSWORD"{print substr($0,index($0,"=")+1); exit}' "$dkco/datasql/.env")"
PG_ADMIN_USER="$(awk -F= '$1=="POSTGRES_USER"{print substr($0,index($0,"=")+1); exit}' "$dkco/datasql/.env")"
PG_ADMIN_DB="$(awk -F= '$1=="POSTGRES_DB"{print substr($0,index($0,"=")+1); exit}' "$dkco/datasql/.env")"
```

Abre una sesión administrativa. No uses `-U`, `-d` ni `-c` después de `svc exec`:

```bash
svc exec datasql postgres \
  env PGPASSWORD="$PG_ADMIN_PASSWORD" \
      PGUSER="$PG_ADMIN_USER" \
      PGDATABASE="$PG_ADMIN_DB" \
  psql
```

Dentro de la sesión administrativa ejecuta únicamente las consultas que no requieren cambiar de base:

```sql
SELECT datname,
       pg_get_userbyid(datdba) AS owner,
       pg_encoding_to_char(encoding) AS encoding
FROM pg_database
WHERE datname = 'homeassistant_db';

SELECT usename,
       datname,
       application_name,
       client_addr,
       state
FROM pg_stat_activity
WHERE usename = 'ha_user'
  AND datname = 'homeassistant_db';
```

Sal con:

```text
\q
```

Para comprobar las tablas de `homeassistant_db`, abre **otra sesión** apuntando a esa base. No uses `\connect` en esta guía: en una entrada multilinea pegada en el terminal puede consumir tokens de la consulta siguiente y producir errores como `invalid integer value "AS" for connection option "port"`.

```bash
svc exec datasql postgres \
  env PGPASSWORD="$PG_ADMIN_PASSWORD" \
      PGUSER="$PG_ADMIN_USER" \
      PGDATABASE=homeassistant_db \
  psql
```

Dentro de la segunda sesión ejecuta:

```sql
SELECT current_database();

SELECT to_regclass('public.states') AS states_table,
       to_regclass('public.events') AS events_table;

SELECT table_schema, table_name
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name IN ('states', 'events')
ORDER BY table_name;
```

Solo si `states_table` no es `NULL`, consulta:

```sql
SELECT COUNT(*) AS states_count FROM states;
```

Sal con `\q`. Confirma que regresaste al prompt de Bash (`root@Nas ... #`) antes de ejecutar `unset` u otro comando de terminal.

Interpretación:

- Una fila en `pg_stat_activity` demuestra una conexión activa de `ha_user` a `homeassistant_db` en ese momento; contrástala con la configuración de `/config`.
- Las tablas `states` y `events` demuestran que algún consumidor creó el esquema de HA en esa base, pero por sí solas no prueban que el proceso actual esté conectado.
- Si no hay actividad, no hay tablas y la configuración no tiene `postgresql://`, HA no está usando esa base.

Limpia variables temporales:

```bash
unset PG_ADMIN_PASSWORD PG_ADMIN_USER PG_ADMIN_DB HA_PG_PORT
```

**Checkpoint 9 — backend identificado:** la configuración persistente y las evidencias de runtime indican SQLite o PostgreSQL. La mera existencia de `homeassistant_db` no cuenta como conexión.

---

## 10. Conectar explícitamente Home Assistant a PostgreSQL

Este es el paso que faltaba: crear la base en PostgreSQL no configura automáticamente el consumidor. Home Assistant tiene su propia forma de conexión: el `Recorder` lee `db_url` desde su configuración. La documentación oficial soporta PostgreSQL y muestra el formato `postgresql://usuario:contraseña@servidor/base`.

### 10.1 Comprobar el driver en la imagen actual

No instales paquetes dentro del contenedor como solución permanente: los cambios internos se pierden al recrearlo. Comprueba primero si la imagen actual trae el driver:

```bash
NAS_CLI=bash svc exec homeassistant homeassistant python3 -c 'import psycopg2; print(psycopg2.__version__)'
```

Si el comando falla con `ModuleNotFoundError`, detente y documenta la imagen/tag real antes de elegir una solución reproducible. No continúes esperando que `db_url` funcione sin el driver.

### 10.2 Crear/proteger el secreto local de HA

Realiza primero directorio, archivo y permisos:

```bash
dk homeassistant
mkdir -p data
touch data/secrets.yaml
chmod 600 data/secrets.yaml
```

Edita el archivo local, que no se publica en Git:

```bash
nano data/secrets.yaml
```

Agrega una clave con la contraseña hexadecimal que estableciste para `ha_user`. Para el NAS/DataSQL actual, el endpoint es `127.0.0.1:5432`:

```yaml
recorder_db_url: "postgresql://ha_user:CONTRASEÑA_HEX@127.0.0.1:5432/homeassistant_db"
```

No pegues la contraseña real en el chat, el repositorio ni el checkpoint. Si usas una contraseña con caracteres reservados, codifícala para URL; una contraseña hexadecimal evita normalmente ese problema.

### 10.3 Agregar una sola sección `recorder:`

Comprueba antes si ya existe una sección:

```bash
grep -n '^recorder:' data/configuration.yaml || true
```

Si no existe, edita:

```bash
nano data/configuration.yaml
```

Agrega exactamente una sección:

```yaml
recorder:
  db_url: !secret recorder_db_url
```

No agregues una segunda sección `recorder:` ni sobrescribas otras opciones existentes. Si ya existe, incorpora únicamente esta clave dentro del bloque existente:

```yaml
db_url: !secret recorder_db_url
```

Home Assistant ya trae Recorder habilitado por defecto; `db_url` cambia el backend que utiliza. No se modifica el compose para esto.

### 10.4 Reiniciar HA y comprobar logs

```bash
svc restart homeassistant
svc ps homeassistant
svc logs homeassistant
```

`svc logs homeassistant` sigue los logs; pulsa `Ctrl-C` para salir sin detener el contenedor. Busca mensajes de `recorder`, `postgres`, `database`, `connection refused` o `authentication failed`.

**Checkpoint 10 — configuración PostgreSQL aplicada:** HA tiene `recorder.db_url` apuntando a la base preparada y el contenedor reinició sin errores de configuración.

---

## 11. Verificación funcional después de conectar

Comprueba primero la respuesta HTTP, que solo confirma que HA está vivo:

```bash
curl -s -o /dev/null -w '%{http_code}\n' "http://${SERVER_IP}:8123"
svc ps homeassistant
```

Después de comprobar la configuración de HA, abre directamente una sesión administrativa contra `homeassistant_db`; no uses `\connect`:

```bash
svc exec datasql postgres \
  env PGPASSWORD="$PG_ADMIN_PASSWORD" \
      PGUSER="$PG_ADMIN_USER" \
      PGDATABASE=homeassistant_db \
  psql
```

Cuando el comando termine, confirma que el prompt cambió a `homeassistant_db=#` (o similar). Solo después de ver ese prompt debes ejecutar las consultas SQL siguientes; si ves `root@Nas ... #`, todavía estás en Bash y debes abrir la sesión de `psql` correctamente.

Dentro de `psql` ejecuta:

```sql
SELECT current_database();

SELECT usename,
       datname,
       application_name,
       client_addr,
       state
FROM pg_stat_activity
WHERE usename = 'ha_user'
  AND datname = 'homeassistant_db';

SELECT to_regclass('public.states') AS states_table,
       to_regclass('public.events') AS events_table;
```

Si `states_table` no es `NULL`, ejecuta:

```sql
SELECT COUNT(*) AS states_count FROM states;
```

Sal con `\q`. Confirma que regresaste al prompt de Bash (`root@Nas ... #`) y solo entonces limpia las variables administrativas. La verificación se considera completa cuando la configuración apunta a PostgreSQL, existe una conexión activa de `ha_user` y las tablas `states`/`events` existen; `states_count > 0` confirma además que ya se están registrando estados. Si el conteo es cero, espera a que HA genere estados y revisa logs; no crees otra base ni otro usuario.

**Checkpoint 11 — conexión PostgreSQL funcional:** configuración, conexión activa y tablas de Recorder confirmadas.

---

## 12. Continuidad y recuperación del flujo

El checkpoint de la integración está en:

```text
_drafts/SESSION-HA-DATASQL.md
```

Cuando pauses, registra únicamente:

- el último checkpoint confirmado;
- la salida relevante sin secretos;
- la única siguiente acción de PostgreSQL o de configuración de HA;
- cualquier error exacto que haya detenido el flujo.

No repitas una mutación ya confirmada (`CREATE ROLE`, `CREATE DATABASE`, cambio de contraseña o edición de `secrets.yaml`/`configuration.yaml`) solo porque cambies de chat. Si aparece `already exists`, consulta y verifica; no recrees a ciegas.

Si ejecutaste SQL directamente en Bash y recibiste errores como `SELECT: orden no encontrada`, no se modificó PostgreSQL: vuelve a abrir una sesión `psql` y ejecuta la consulta en el prompt `aipostgres=#` o equivalente.

Si aparece `No such option: -U` en `svc exec`, no es un error de PostgreSQL. Repite la conexión DataSQL con `PGUSER`, `PGDATABASE` y `env`, sin `-U`, `-d` ni `-c` después de `svc exec`.

---

## Auditoría de fuentes y variantes

| Fuente(s) | Afirmación u operación | Tipo | Confianza | Decisión y motivo | Clasificación |
|---|---|---|---|---|---|
| Conversación y salida real del NAS | `CREATE ROLE ha_user LOGIN` y `CREATE DATABASE homeassistant_db OWNER ha_user` se ejecutaron correctamente | HECHO | ALTA | Se conserva como camino idempotente: consultar antes de mutar | INTEGRADO |
| Conversación y salida real del NAS | `svc exec ... psql -U/-d/-c` falla con `No such option: -U` | HECHO | ALTA | Se reemplaza por variables `PGUSER`/`PGDATABASE` y `psql` interactivo | REEMPLAZADO |
| Conversación y salida real del NAS | Ejecutar `SELECT` en Bash produce `orden no encontrada` | HECHO | ALTA | Se documenta como error de ejecución y se exige prompt `psql` | INTEGRADO |
| `docs/services/homeassistant-guide.md` | HA usa `network_mode: host` y DataSQL se alcanza por loopback del host | HECHO | ALTA | Se conserva solo para el camino NAS/DataSQL | INTEGRADO |
| `docs/services/datasql-guide.md` | DataSQL requiere salud de PostgreSQL, `db_net` y credenciales del `.env` | HECHO | ALTA | Se usa como prerrequisito; su instalación queda fuera de alcance | FUERA_DE_ALCANCE |
| `agent/catalog/services/homeassistant/compose.yml` y ficha | HA usa host networking, monta `/config` y no configura el backend de Recorder | HECHO | ALTA | El compose se deja sin cambios; la conexión se configura en los archivos persistentes de HA | INTEGRADO |
| Variantes `datapostgres:5432` y `127.0.0.1:<puerto>` | Afectan redes distintas | INFERENCIA SEGURA | ALTA | Se usa el endpoint confirmado para administrar PostgreSQL; no se configura ningún hostname en HA | INTEGRADO |
| Variantes `psql -c` y sesión interactiva | Tienen el mismo propósito general, pero `svc exec` intercepta opciones | HECHO | ALTA | Se elige sesión interactiva compatible y observable | REEMPLAZADO |
| Documentación oficial de Home Assistant Recorder | SQLite es el backend predeterminado; PostgreSQL requiere `recorder.db_url` y el driver disponible | HECHO | ALTA | Se integra como decisión explícita: levantar con SQLite o configurar PostgreSQL | INTEGRADO |

## Hechos confirmados por las fuentes

1. El PostgreSQL/DataSQL del NAS del caso real escucha en `127.0.0.1:5432`.
2. `datapostgres` y `dataredis` estaban saludables cuando se realizó la integración real.
3. El rol `ha_user`, la base `homeassistant_db`, su propietario y el login fueron confirmados durante el caso real.
4. `svc exec` del NAS interpreta `-U`, `-d` y `-c` como opciones propias si se colocan directamente en ese flujo.
5. SQL debe ejecutarse dentro de `psql`, no en Bash.
6. Home Assistant usa `network_mode: host` en este repositorio.

## Decisiones derivadas durante la separación

1. La instalación de PostgreSQL/DataSQL no forma parte de esta guía; se enlaza como prerrequisito opcional.
2. La guía mantiene un camino específico para NAS/DataSQL y otro para un PostgreSQL existente distinto, porque sus métodos de administración y endpoints no son intercambiables.
3. Home Assistant puede levantarse con SQLite sin configuración externa; la conexión PostgreSQL requiere configurar el `Recorder` en la configuración persistente de HA.
4. La creación del rol y la base es idempotente por consulta previa, pero no se modifica silenciosamente el propietario de una base existente.
5. La prueba definitiva combina configuración de HA, actividad de `pg_stat_activity` y tablas del Recorder; la existencia de `homeassistant_db` por sí sola no prueba que HA la use.

## Artefactos principales

| Tipo | Identificador | Estado inicial | Operación | Estado esperado |
|---|---|---|---|---|
| Servicio | PostgreSQL/DataSQL o backend elegido | Existe/no existe según decisión del usuario | Verificar o provisionar fuera de esta guía | Saludable y accesible |
| Rol PostgreSQL | `ha_user` | Puede no existir | Crear/verificar/habilitar login | Existe con `rolcanlogin = t` |
| Base PostgreSQL | `homeassistant_db` | Puede no existir | Crear/verificar propietario | Existe con propietario `ha_user` |
| Servicio | `homeassistant` | Detenido/no configurado o activo | Levantar con SQLite o configurar Recorder para PostgreSQL | Backend identificado y, si corresponde, conexión funcional |
| Archivo | `$dkco/homeassistant/data/configuration.yaml` | Puede existir tras onboarding | Agregar una sola sección `recorder:` si se elige PostgreSQL | `db_url: !secret recorder_db_url` |
| Archivo | `$dkco/homeassistant/data/secrets.yaml` | Puede no existir | Crear/proteger si se elige PostgreSQL | URI PostgreSQL fuera del repositorio |
| Tabla | `homeassistant_db.states` / `events` | Puede no existir | HA las crea al usar PostgreSQL | Tablas del Recorder disponibles |

## Decisiones pendientes y bloqueados

1. **Pendiente por usuario:** qué backend PostgreSQL utilizará si no es DataSQL.
2. **Pendiente por usuario:** host, puerto, base administrativa, usuario administrativo y política de acceso del backend externo.
3. **Bloqueado si faltan datos:** no se puede crear ni verificar el rol/base de un PostgreSQL externo sin esos datos y un método de conexión válido.
4. **Bloqueado si el propietario difiere:** no se debe asumir que una base existente puede reasignarse sin revisar su contenido y autorización.
