# PostgreSQL IA — Stack sucesor de DataSQL y migración gradual

> Este servicio no es solo un contenedor PostgreSQL. Es el stack sucesor de
> DataSQL: PostgreSQL 17 + `pgvector` + `pg_search`, pgAdmin 4 y Redis 7.
>
> RustFS queda fuera del stack porque es almacenamiento de objetos S3, no una
> parte de PostgreSQL. Se instalará únicamente con LobeHub u otro consumidor
> real de objetos.
>
> Estado: scaffolding para instalar y verificar el stack. Esta guía no afirma
> que el NAS ya haya sido modificado.

## 1. Arquitectura decidida

### DataSQL actual durante la coexistencia

```text
DataSQL ($dkco/datasql)
├── datapostgres  → postgres:16-alpine, loopback 5432
├── datapgadmin   → pgAdmin, LAN :5050
└── dataredis     → Redis 7, interno
```

Consumidores actuales que todavía dependen de este stack:

- Flowise → `flowise_db` y `dataredis`.
- Home Assistant → `homeassistant_db` mediante `127.0.0.1:5432`.
- n8n → existe `n8n_db`; su compose/runtime debe auditarse antes de migrarlo.

### Stack sucesor

```text
PostgreSQL IA ($dkco/aipostgres)
├── aipostgres  → PostgreSQL 17 + pgvector + pg_search
├── aipgadmin   → pgAdmin 4
└── airedis     → Redis 7
```

Durante la coexistencia se usan nombres distintos para que ambos stacks puedan
levantarse sin conflicto:

| Componente | DataSQL actual | Stack sucesor | Acceso inicial |
|---|---|---|---|
| PostgreSQL | `datapostgres` | `aipostgres` | `127.0.0.1:5433` y `aipostgres:5432` en `db_net` |
| pgAdmin | `datapgadmin` | `aipgadmin` | `${SERVER_IP}:5051` |
| Redis | `dataredis` | `airedis` | `airedis:6379` en `db_net` |

La publicación en `5433` es solo loopback y existe para poder migrar Home
Assistant mientras DataSQL conserva `5432`. No se expone PostgreSQL a la LAN.

### Qué significa “sucesor”

Levantar `aipostgres` y comprobar sus extensiones **no autoriza todavía a
borrar DataSQL**. DataSQL solo se retira después de:

1. Migrar y verificar cada base y cada consumidor.
2. Cambiar los endpoints de PostgreSQL y Redis de las aplicaciones.
3. Migrar Home Assistant desde `127.0.0.1:5432` a `127.0.0.1:5433`.
4. Auditar n8n y confirmar que ya no usa `datapostgres` ni `dataredis`.
5. Ejecutar backups y una prueba de recuperación.
6. Confirmar que ningún servicio activo depende de los contenedores antiguos.

Por tanto, el stack nuevo reemplaza funcionalmente a DataSQL por etapas; no se
elimina DataSQL inmediatamente después del primer `svc up`.

## 2. Qué contiene PostgreSQL IA

La imagen `paradedb/paradedb:0.25.4-pg17` es PostgreSQL 17 empaquetado por
ParadeDB con estas extensiones disponibles:

- `pg_cron`: tareas programadas dentro de PostgreSQL; la imagen la intenta
  habilitar durante su bootstrap.

- `vector` (`pgvector`): embeddings, tipos vectoriales, operadores e índices
  para memoria semántica y RAG.
- `pg_search`: búsqueda full-text con ranking BM25 y búsqueda híbrida.

Además, el compose contiene:

- **pgAdmin 4**, para administrar el nuevo clúster.
- **Redis 7**, para reemplazar gradualmente `dataredis` en consumidores que lo
  necesiten.

Las extensiones se habilitan por base, no globalmente en todas las bases:

```sql
CREATE EXTENSION vector;
CREATE EXTENSION pg_search;
```

La primera prueba las habilita solo en la base administrativa `aipostgres`.
No crea todavía `lobehub_db`, `nas_agent_db`, ni bases de migración.

## 3. Por qué RustFS no se incluye aquí

RustFS no es una extensión, una base de datos ni un componente interno de
PostgreSQL. Es un servidor de almacenamiento de objetos compatible con S3.
Debe tener su propio contenedor, datos, credenciales, backups y ciclo de
actualización.

LobeHub sí necesita un almacenamiento S3 compatible para imágenes, archivos y
la base de conocimiento cuando se usa su modalidad server. RustFS es una
opción local para ese papel. Sin embargo:

- `pgvector` y `pg_search` funcionan sin RustFS.
- La memoria semántica de un agente puede vivir en PostgreSQL sin RustFS.
- Si no se instala LobeHub, Hermes ni otro consumidor de archivos/objetos, no
  hay beneficio inmediato en instalar RustFS.
- Instalarlo antes añade consumo de RAM, espacio, credenciales, buckets y otra
  rutina de backup.

La decisión es:

```text
PostgreSQL IA → ahora, como sucesor completo de DataSQL
RustFS       → después, como servicio separado cuando exista LobeHub/S3
```

No se debe incrustar RustFS dentro del compose de `aipostgres`. Cuando se elija
LobeHub se creará `$dkco/rustfs/` con su propio `compose.yml`, y LobeHub se
conectará mediante S3. La documentación de LobeHub advierte que el endpoint S3
no debe ser solamente `http://rustfs:9000` si el navegador necesita descargar
objetos; debe existir un endpoint accesible y resoluble por los clientes. Para
RustFS también se debe habilitar el modo path-style que LobeHub documenta.

## 4. Preflight de la instalación

Estos comandos solo leen el estado actual:

```bash
svc health
svc ps datasql
svc net
svc port-map
nas
disk
```

Continuar solo si:

- DataSQL está saludable.
- Existe `db_net`.
- `5433` y `5051` no están ocupados.
- Hay espacio suficiente para un segundo clúster PostgreSQL temporal.
- No se pretende detener ni modificar DataSQL en esta fase.

Si `db_net` no existe, detenerse y seguir el bootstrap documentado en
`docs/docker-entorno.md`. No crear otra red con un nombre alternativo.

## 5. Instalación del stack sucesor

### 1. Crear directorios

```bash
mkdir -p $dkco/aipostgres/data/postgres/{pgdata,backups} $dkco/aipostgres/data/{pgadmin,redis}
```

```bash
mkdir -p $dkco/aipostgres/data/postgres/{pgdata,backups}
mkdir -p $dkco/aipostgres/data/{pgadmin,redis}
```
o

```bash
mkdir -p \
  $dkco/aipostgres/data/postgres/{pgdata,backups} \
  $dkco/aipostgres/data/{pgadmin,redis}
```

### 2. Copiar los archivos

```bash
cp "$NAS_DOTFILES/agent/catalog/services/aipostgres/compose.yml" \
  "$dkco/aipostgres/compose.yml"

if [[ ! -f "$dkco/aipostgres/.env" ]]; then
  cp "$NAS_DOTFILES/agent/catalog/services/aipostgres/.env.example" \
    "$dkco/aipostgres/.env"
fi
```

El archivo del catálogo está dos niveles debajo de `agent/catalog/` y usa
`../../_common.yml`; el archivo desplegado desde `$dkco/aipostgres/` necesita
`../_common.yml`:

```bash
sed -i \
  's#file: ../../_common.yml#file: ../_common.yml#g' \
  "$dkco/aipostgres/compose.yml"
```

No copiar el `.env` real al repositorio.

### 3. Generar los secretos

Para este stack se generan tres secretos nuevos e independientes:

- `POSTGRES_PASSWORD`: administrador del PostgreSQL IA.
- `PGADMIN_PASSWORD`: acceso al pgAdmin IA.
- `REDIS_PASSWORD`: contraseña del nuevo `airedis`.

**No copiar `REDIS_PASSWORD` desde `$dkco/datasql/.env`**. Esa contraseña
solo debe reutilizarse cuando un consumidor continúa conectado al Redis antiguo
`dataredis`, como Flowise antes de su migración. El Redis nuevo `airedis` debe
tener una credencial propia.

La siguiente receta usa el patrón de generar valores en variables y escribir el
archivo mediante un heredoc. Los valores reales no se escriben literalmente en
el comando ni se guardan en Git. `openssl rand -hex 32` evita caracteres de
shell problemáticos y produce secretos de 64 caracteres hexadecimales.

Ejecutarla después de crear los directorios y copiar los archivos:

```bash
dk aipostgres

ENV_FILE="$dkco/aipostgres/.env"

if [[ -f "$ENV_FILE" ]] && ! grep -q '__pega_aqui__' "$ENV_FILE"; then
  printf 'El archivo %s ya contiene valores reales; no se sobrescribe.\n' "$ENV_FILE"
else
  (
    umask 077
    set +x

    POSTGRES_PASS=$(openssl rand -hex 32)
    PGADMIN_PASS=$(openssl rand -hex 32)
    REDIS_PASS=$(openssl rand -hex 32)

    cat > "$ENV_FILE" <<EOF
# Secretos locales de aipostgres — no copiar al repositorio.
POSTGRES_DB=aipostgres
POSTGRES_USER=aiadmin
POSTGRES_PASSWORD=${POSTGRES_PASS}

PGADMIN_EMAIL=admin@local.lan
PGADMIN_PASSWORD=${PGADMIN_PASS}

REDIS_PASSWORD=${REDIS_PASS}

# Puertos temporales mientras DataSQL siga activo.
AIPG_POSTGRES_HOST_PORT=5433
AIPGADMIN_PORT=5051
EOF

    chmod 600 "$ENV_FILE"
    unset POSTGRES_PASS PGADMIN_PASS REDIS_PASS
    printf 'Generado %s con permisos 600.\n' "$ENV_FILE"
  )
fi
unset ENV_FILE
```

La condición evita sobrescribir un `.env` que ya contiene secretos reales. Si
el archivo todavía es el `.env.example` con `__pega_aqui__`, lo reemplaza por
valores nuevos. No ejecutar `source .env`, no imprimir las variables y no usar
`set -x` durante este procedimiento.

No poner `SERVER_IP` ni `TZ` en este `.env`; se heredan desde el global mediante
`env_file: [../.env, .env]`.

### 4. Aplicar permisos

La imagen `dpage/pgadmin4:latest` ejecuta pgAdmin con UID/GID `5050:5050`.
El `bind mount` completo debe pertenecer a ese usuario; `chmod 700` por sí solo
no basta si la carpeta fue creada por `root`.

```bash
chown -R 5050:5050 "$dkco/aipostgres/data/pgadmin"
chmod 700 "$dkco/aipostgres/data/postgres/pgdata"
chmod 700 "$dkco/aipostgres/data/postgres/backups"
chmod 700 "$dkco/aipostgres/data/pgadmin"
chmod 700 "$dkco/aipostgres/data/redis"
chmod 600 "$dkco/aipostgres/.env"
```

El `chown` recursivo también corrige archivos creados por intentos anteriores,
como `pgadmin4.db` o `sessions`. No usar `chmod -R 777` ni aplicar este
ownership a los datos de PostgreSQL, Redis o DataSQL.

### 5. Validar sin levantar todavía

```bash
dk aipostgres
svc config aipostgres
```

La configuración resuelta debe mostrar:

- `paradedb/paradedb:0.25.4-pg17`.
- Servicios `postgres`, `pgadmin` y `redis`.
- Contenedores `aipostgres`, `aipgadmin` y `airedis`.
- `db_net` externa.
- PostgreSQL en `127.0.0.1:5433:5432`.
- pgAdmin en `5051:80`.
- Redis sin `ports`.
- `shared_preload_libraries=pg_search,pg_cron`.
- Volúmenes persistentes en `./data/postgres`, `./data/pgadmin` y
  `./data/redis`.
- `env_file` global y local.

No continuar si `svc config` muestra `0.0.0.0:5432`, una IP fija de Docker, otra
red o una ruta incorrecta de `_common.yml`.

### 6. Levantar el nuevo stack

```bash
svc pull aipostgres
svc up aipostgres
svc ps aipostgres
```

Después revisa los logs:

```bash
svc logs aipostgres
```

Ctrl-C en `svc logs` solo termina la vista de logs; no detiene los contenedores.

## Lo que espero ver

Los tres contenedores deben quedar activos:

```text
aipostgres  Up (healthy)
aipgadmin   Up
airedis     Up (healthy)
```

Después verifica el estado global y la exposición de puertos:

```bash
svc health
svc ps aipostgres
svc net
svc port-map
```

En `svc port-map` deberían aparecer `5051` y posiblemente `5433` como
loopback. No debe aparecer `6379`.

No continúes si PostgreSQL o Redis no están saludables; conserva la salida de
`svc ps aipostgres` y `svc logs aipostgres` para diagnosticar antes de cambiar
permisos o eliminar datos.

### Error de bootstrap `pg_cron`

Si los logs muestran:

```text
ERROR:  pg_cron can only be loaded via shared_preload_libraries
HINT:  Add pg_cron to the shared_preload_libraries configuration variable
```

la imagen de ParadeDB sí encontró `pg_search`, pero su script de bootstrap
`10_bootstrap_paradedb.sh` también intenta crear la extensión `pg_cron`. El
compose debe precargar ambas bibliotecas:

```text
shared_preload_libraries=pg_search,pg_cron
```

No borres `./data/postgres/pgdata`: el primer intento puede haber creado ya el
clúster y dejar datos válidos aunque el bootstrap de la extensión haya fallado.
Después de sincronizar el compose corregido, valida y recrea únicamente el
stack sucesor:

```bash
dk aipostgres
svc config aipostgres
svc up aipostgres
svc ps aipostgres
svc logs aipostgres
```

Si PostgreSQL queda saludable, verifica que `pg_cron` esté disponible y crea la
extensión solo si aún no existe en la base administrativa:

```sql
SELECT name, default_version, installed_version
FROM pg_available_extensions
WHERE name IN ('vector', 'pg_search', 'pg_cron')
ORDER BY name;

CREATE EXTENSION IF NOT EXISTS pg_cron;
```

No detengas ni modifiques DataSQL como parte de esta recuperación.

### Error de permisos en pgAdmin

Si los logs de `aipgadmin` muestran:

```text
Failed to create the directory /var/lib/pgadmin/sessions:
[Errno 13] Permission denied
```

el directorio persistente de pgAdmin no pertenece al usuario de la imagen. No
es un problema de PostgreSQL, Redis ni de `db_net`. Corrige solo ese bind mount
(en el orden: ownership y luego permisos) y reinicia el stack sucesor:

```bash
chown -R 5050:5050 "$dkco/aipostgres/data/pgadmin"
chmod 700 "$dkco/aipostgres/data/pgadmin"
svc restart aipostgres
svc ps aipostgres
```

La salida esperada es `aipgadmin Up` y los logs ya no deben mostrar el error de
`/var/lib/pgadmin/sessions`. No borres `data/pgadmin` salvo que aparezcan además
los síntomas específicos de corrupción SQLite documentados en la guía de
DataSQL. No ejecutes `svc down datasql`.

### Error de migración inicial de pgAdmin (`EOFError`)

Si, después de corregir el ownership, los logs muestran:

```text
Configuring authentication for SERVER mode.
Enter the email address and password to use for the initial pgAdmin user account:
EOFError: EOF when reading a line
RuntimeError: Migration failed
```

la carpeta contiene una base `pgadmin4.db` creada durante un arranque parcial.
El contenedor está intentando migrarla y pedir el usuario inicial de forma
interactiva, pero `svc up` no proporciona una terminal. En una instalación
nueva en la que todavía no se configuraron servidores en pgAdmin, aparta la
carpeta completa en vez de borrarla:

```bash
svc down aipostgres

TS="$(date +%Y%m%d-%H%M%S)"
mv "$dkco/aipostgres/data/pgadmin" \\
  "$dkco/aipostgres/data/pgadmin.partial-$TS"
mkdir -p "$dkco/aipostgres/data/pgadmin"
chown -R 5050:5050 "$dkco/aipostgres/data/pgadmin"
chmod 700 "$dkco/aipostgres/data/pgadmin"
unset TS

svc up aipostgres
svc ps aipostgres
svc logs aipostgres
```

Esto elimina solo los contenedores del stack `aipostgres` y conserva la carpeta
anterior como respaldo. No afecta PostgreSQL, Redis ni DataSQL. Si ya habías
configurado servidores o conexiones en pgAdmin, no apartes la carpeta: detente
y conserva ese directorio para una recuperación específica.

La imagen de pgAdmin está fijada a `9.17` para evitar que el tag mutable
`latest` avance la base SQLite sin una actualización coordinada. Las variables
`PGADMIN_DEFAULT_EMAIL` y `PGADMIN_DEFAULT_PASSWORD` deben seguir presentes en
el `.env`; son las que crean la cuenta inicial en un directorio limpio.

## Avisos del preflight actual

### `tasmoadmin unhealthy`

No bloquea la instalación de `aipostgres`. No reinicies ni modifiques
`tasmoadmin` como parte de esta instalación; se investigará separadamente,
leyendo primero su guía y su composición.

### Error de `nas`

Si aparece:

```text
-bash: 3,9Gi: valor demasiado grande para la base
```

alguna función del dashboard está intentando convertir el tamaño localizado
`3,9Gi` como si fuera un número. Es un bug del comando `nas`, no un problema de
almacenamiento. El dato útil del diagnóstico es, por ejemplo:

```text
/ usado: 32G de 285G
Uso: 12%
```

Este error tampoco bloquea la instalación mientras `disk` confirme espacio
suficiente.

## 7. Verificar los tres componentes

### PostgreSQL y extensiones

```bash
POSTGRES_DB="$(awk -F= '$1=="POSTGRES_DB"{print substr($0,index($0,"=")+1)}' .env)"
POSTGRES_USER="$(awk -F= '$1=="POSTGRES_USER"{print substr($0,index($0,"=")+1)}' .env)"
POSTGRES_PASSWORD="$(awk -F= '$1=="POSTGRES_PASSWORD"{print substr($0,index($0,"=")+1)}' .env)"

svc exec aipostgres postgres env \
  PGPASSWORD="$POSTGRES_PASSWORD" \
  PGUSER="$POSTGRES_USER" \
  PGDATABASE="$POSTGRES_DB" \
  psql
```

En `psql`:

```sql
SELECT version();

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

Las extensiones requeridas deben aparecer en `pg_extension`. Esto solo afecta
la base `aipostgres` del nuevo clúster.

Salir y limpiar:

```text
\q
```

```bash
unset POSTGRES_DB POSTGRES_USER POSTGRES_PASSWORD
```

### Redis

```bash
REDIS_PASSWORD="$(awk -F= '$1=="REDIS_PASSWORD"{print substr($0,index($0,"=")+1)}' .env)"
svc exec aipostgres redis env \
  REDISCLI_AUTH="$REDIS_PASSWORD" \
  redis-cli PING
unset REDIS_PASSWORD
```

La respuesta esperada es `PONG`.

### pgAdmin

Abrir desde la LAN:

```text
http://${SERVER_IP}:5051
```

En la conexión al servidor PostgreSQL usar:

```text
Host: aipostgres
Port: 5432
Usuario: aiadmin
Base inicial: aipostgres
```

No usar `127.0.0.1` dentro de pgAdmin: pgAdmin está en otro contenedor y debe
resolver PostgreSQL por `db_net`.

### Aislamiento y recursos

```bash
svc health
svc ps datasql
svc ps aipostgres
svc net
svc port-map
svc stats aipostgres
```

DataSQL debe continuar intacto. La única publicación adicional esperada es
`127.0.0.1:5433` y el panel LAN `5051`; Redis no debe aparecer en el mapa de
puertos.

## 8. Plan de migración y retiro de DataSQL

No migrar todo en el mismo cambio.

### Fase A — Stack sucesor vacío

Instalar y verificar los tres componentes como en esta guía. No crear aún
`lobehub_db` ni `nas_agent_db`.

### Fase B — Consumidor de bajo riesgo

Elegir un consumidor y auditar su compose/runtime antes de migrarlo. Para cada
servicio:

1. Ejecutar `svc snapshot <servicio>` y guardar un backup lógico.
2. Crear un rol y una base dedicados en `aipostgres`.
3. Restaurar el dump en la base nueva, si la base ya tiene datos.
4. Cambiar el host PostgreSQL a `aipostgres:5432`.
5. Cambiar Redis a `airedis:6379` solo si el servicio lo utiliza.
6. Levantar y verificar logs, health y operación funcional.
7. Mantener DataSQL intacto hasta completar la observación.

Para Flowise, conservar `flowise_db` y `flowise_user`; no reutilizar `aiadmin`.
Para n8n, auditar primero si su contenedor usa PostgreSQL o SQLite. No asumirlo
por la existencia de `n8n_db`.

### Fase C — Home Assistant

Home Assistant usa `network_mode: host`, por lo que no puede usar el hostname
Docker `aipostgres` como lo hacen los consumidores en `db_net`. La migración
requiere:

1. Crear/restaurar `homeassistant_db` y `ha_user` en `aipostgres`.
2. Comprobar PostgreSQL con `127.0.0.1:5433` desde el NAS.
3. Cambiar el `recorder.db_url` de HA a `127.0.0.1:5433`.
4. Reiniciar HA y verificar que el Recorder escribe correctamente.
5. Observar antes de retirar DataSQL.

### Fase D — Retirar DataSQL

Solo después de verificar todos los consumidores:

```bash
svc health
svc net
svc port-map
svc ps datasql
```

Confirmar que ningún compose o configuración usa `datapostgres`, `datapgadmin`
o `dataredis`. La detención/eliminación de DataSQL requiere confirmación
explícita y backup previo; no ejecutar `svc down datasql` como parte de esta
primera instalación.

El stack `aipostgres` puede continuar con sus nombres propios. No es necesario
renombrar `aipostgres` a `datapostgres`, ni `airedis` a `dataredis`; cambiar los
endpoints de los consumidores es más claro y evita ambigüedades.

## 9. RustFS y LobeHub: fase posterior

Cuando se decida instalar LobeHub:

1. Mantener PostgreSQL IA como proveedor externo y crear `lobehub_db`/usuario.
2. Crear RustFS como servicio independiente en `$dkco/rustfs/`.
3. Crear un bucket dedicado para LobeHub.
4. Usar credenciales S3 específicas, no las credenciales root para otros usos.
5. Configurar `S3_ENDPOINT`, bucket, claves y path-style en LobeHub.
6. Verificar que el endpoint S3 sea accesible por el navegador y por LobeHub.
7. Respaldar PostgreSQL y RustFS por separado.

RustFS también podría servir en el futuro para documentos, adjuntos o artefactos
del agente NAS, pero no se instala por anticipado mientras no exista ese flujo.

## 10. Backups y operación

Después de verificar el stack vacío:

```bash
svc backup aipostgres
svc stats aipostgres
svc logs aipostgres
```

Datos críticos:

- `$dkco/aipostgres/data/postgres/pgdata/` — clúster PostgreSQL.
- `$dkco/aipostgres/data/postgres/backups/` — dumps.
- `$dkco/aipostgres/data/pgadmin/` — configuración pgAdmin.
- `$dkco/aipostgres/data/redis/` — AOF de Redis.
- `$dkco/aipostgres/.env` — credenciales, nunca versionar.

No borrar estos directorios para solucionar un fallo de arranque. Primero
conservar logs, revisar `svc config`, comprobar permisos y confirmar el backup.

## Referencias oficiales

- [ParadeDB — extensiones de terceros](https://docs.paradedb.com/deploy/third-party-extensions): la imagen incluye `pg_search` y `pgvector`.
- [Docker Hub — tag fijado](https://hub.docker.com/v2/repositories/paradedb/paradedb/tags/0.25.4-pg17): confirma `0.25.4-pg17` para amd64/arm64.
- [LobeHub — base PostgreSQL](https://lobehub.com/docs/self-hosting/platform/docker): usa ParadeDB y `shared_preload_libraries=pg_search`.
- [LobeHub — Docker Compose](https://lobehub.com/docs/self-hosting/platform/docker-compose): documenta PostgreSQL con PGVector y almacenamiento S3/RustFS como servicios separados.
- [LobeHub — S3](https://lobehub.com/docs/self-hosting/advanced/s3): explica que RustFS sirve para archivos/base de conocimiento y requiere path-style.
- [RustFS — Docker](https://docs.rustfs.com/en/installation/container/docker): documenta la instancia persistente y sus puertos API/consola.
- [RustFS — API S3](https://docs.rustfs.com/en/administration/protocols/s3): documenta S3, credenciales, path-style y límites de compatibilidad.

El contenido operativo fue adaptado a las convenciones de este NAS; las fuentes
enlazadas son la referencia técnica original.
