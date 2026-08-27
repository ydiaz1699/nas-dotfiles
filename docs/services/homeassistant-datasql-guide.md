# Guía: conectar Home Assistant a PostgreSQL

## Estado: borrador operativo
## Fecha: 2026-08-25
## Resumen

Esta guía prepara externamente una base PostgreSQL dedicada para un posible uso posterior de Home Assistant. No instala PostgreSQL, no instala DataSQL y no modifica ningún archivo, secreto, configuración, contenedor o proceso de Home Assistant.

> **Alcance:** Home Assistant y PostgreSQL son decisiones independientes. Puedes usar esta guía si ya tienes PostgreSQL/DataSQL o detenerte aquí para instalar/provisionar el backend que prefieras. La instalación y recuperación del stack DataSQL están en [`datasql-guide.md`](datasql-guide.md). Esta guía solo prepara el lado PostgreSQL; la configuración de Home Assistant queda fuera de alcance.

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

Esta guía no levanta, reinicia ni configura Home Assistant. Solo prepara el rol y la base PostgreSQL que otro procedimiento podrá utilizar posteriormente.

---

## 2. Decidir los valores del backend

El usuario decide los nombres y el backend. Los valores canónicos usados en el ejemplo del NAS son:

```text
Usuario dedicado:       ha_user
Base dedicada:          homeassistant_db
Endpoint DataSQL:       127.0.0.1:5432
```

Estos nombres no son obligatorios para otro backend. Si cambias alguno, reemplázalo de forma consistente en cada comando y consulta de PostgreSQL. Esta guía no añade una URI ni ningún valor a Home Assistant.

### Regla de red del caso NAS/DataSQL

El compose de Home Assistant usa `network_mode: host`, pero esta guía no cambia ese compose ni configura HA. Para preparar DataSQL se usa el endpoint PostgreSQL publicado realmente en el host:

- En el caso canónico del NAS: `127.0.0.1` y el puerto confirmado en `.env`, `svc ps datasql` y `ss`.
- Para un PostgreSQL externo: el host y puerto que el usuario haya confirmado.
- `datapostgres:5432` es un hostname interno para consumidores conectados a `db_net`; no se usa en los comandos de administración de este flujo host-side.

No se adivinan endpoints ni se modifican archivos de Home Assistant.

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

Dentro de `psql` ejecuta:

```sql
SELECT current_user, current_database();
```

El resultado esperado es:

```text
 current_user | current_database
--------------+------------------
 ha_user      | homeassistant_db
```

Sal con `\\q`. Si la prueba falla, resuelve primero el endpoint, rol, contraseña, permisos o propietario.

**Checkpoint 7 — login PostgreSQL listo:** `ha_user` puede conectarse a `homeassistant_db`. Hasta aquí llega esta guía; Home Assistant no se levanta, reinicia ni configura en este procedimiento.

---

## 8. Resultado y límites de esta guía

Al completar el checkpoint 7, el lado PostgreSQL queda preparado:

- el rol dedicado existe y puede iniciar sesión;
- `homeassistant_db` existe y pertenece a `ha_user`;
- la contraseña dedicada fue comprobada con una conexión real;
- no se modificó ningún archivo ni configuración de Home Assistant;
- no se levantó, reinició ni inspeccionó el contenedor de Home Assistant.

Esta guía termina aquí. No contiene instrucciones para editar `configuration.yaml`, crear `secrets.yaml`, agregar `recorder:`, instalar `psycopg2`, reiniciar Home Assistant, leer logs de HA ni consultar PostgreSQL desde el contenedor de HA.

La verificación de las tablas de Home Assistant tampoco forma parte de este procedimiento, porque requiere que exista un proceso externo que configure y use ese backend. Si posteriormente se configura un consumidor, la consulta debe ejecutarse desde una sesión administrativa de PostgreSQL, nunca pegando SQL directamente en Bash.

Para el caso NAS/DataSQL, cualquier consulta posterior del lado PostgreSQL debe conservar el patrón compatible con `svc exec`:

```bash
svc exec datasql postgres \
  env PGPASSWORD="$PG_ADMIN_PASSWORD" \
      PGUSER="$PG_ADMIN_USER" \
      PGDATABASE="$PG_ADMIN_DB" \
  psql
```

Dentro de `psql` se ejecutan las consultas SQL, por ejemplo:

```sql
SELECT datname,
       pg_get_userbyid(datdba) AS owner
FROM pg_database
WHERE datname = 'homeassistant_db';
```

No se deben añadir `-U`, `-d` ni `-c` después de `svc exec`; este wrapper puede interpretarlos como opciones propias. Limpia la contraseña temporal cuando termines:

```bash
unset PG_ADMIN_PASSWORD PG_ADMIN_USER PG_ADMIN_DB HA_DB_PASSWORD HA_PG_PORT
```

---

## 9. Continuidad y recuperación del flujo

El checkpoint de preparación PostgreSQL está en:

```text
_drafts/SESSION-HA-DATASQL.md
```

Cuando pauses, registra únicamente:

- el último checkpoint confirmado;
- la salida relevante sin secretos;
- la única siguiente acción de PostgreSQL;
- cualquier error exacto que haya detenido el flujo.

No repitas una mutación ya confirmada (`CREATE ROLE`, `CREATE DATABASE` o cambio de contraseña) solo porque cambies de chat. Si aparece `already exists`, consulta y verifica; no recrees a ciegas.

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
| `agent/catalog/services/homeassistant/compose.yml` y ficha | HA usa host networking y puerto 8123 | HECHO | ALTA | Solo se conserva como contexto; esta guía no inicia ni modifica HA | FUERA_DE_ALCANCE |
| Variantes `datapostgres:5432` y `127.0.0.1:<puerto>` | Afectan redes distintas | INFERENCIA SEGURA | ALTA | Se usa el endpoint confirmado para administrar PostgreSQL; no se configura ningún hostname en HA | INTEGRADO |
| Variantes `psql -c` y sesión interactiva | Tienen el mismo propósito general, pero `svc exec` intercepta opciones | HECHO | ALTA | Se elige sesión interactiva compatible y observable | REEMPLAZADO |
| Integración opcional de PostgreSQL | El usuario puede tener o no backend antes de conectar HA | HECHO | ALTA | La existencia del backend queda como decisión/prerrequisito del usuario | INTEGRADO |

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
3. La guía termina después de verificar rol, base, propietario y login. No configura, reinicia ni inspecciona Home Assistant.

## Artefactos principales

| Tipo | Identificador | Estado inicial | Operación | Estado esperado |
|---|---|---|---|---|
| Servicio | PostgreSQL/DataSQL o backend elegido | Existe/no existe según decisión del usuario | Verificar o provisionar fuera de esta guía | Saludable y accesible |
| Rol PostgreSQL | `ha_user` | Puede no existir | Crear/verificar/habilitar login | Existe con `rolcanlogin = t` |
| Base PostgreSQL | `homeassistant_db` | Puede no existir | Crear/verificar propietario | Existe con propietario `ha_user` |
| Servicio | `datapostgres` o backend elegido | Detenido/no saludable/desconocido | Verificar externamente | Saludable y accesible |
| Servicio | `homeassistant` | Sin cambios requeridos por esta guía | No operar | Permanece sin modificar |

## Decisiones pendientes y bloqueados

1. **Pendiente por usuario:** qué backend PostgreSQL utilizará si no es DataSQL.
2. **Pendiente por usuario:** host, puerto, base administrativa, usuario administrativo y política de acceso del backend externo.
3. **Bloqueado si faltan datos:** no se puede crear ni verificar el rol/base de un PostgreSQL externo sin esos datos y un método de conexión válido.
4. **Bloqueado si el propietario difiere:** no se debe asumir que una base existente puede reasignarse sin revisar su contenido y autorización.
