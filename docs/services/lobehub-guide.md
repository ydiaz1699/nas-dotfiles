# Guía: LobeHub server/database en el NAS

> **Estado:** archivos preparados en una rama de revisión; todavía no es una
> instalación confirmada en el NAS porque esta sesión no ejecutó `svc` contra el
> servidor. No afirmar `lobehub_user`, `lobehub_db`, RustFS ni el contenedor como
> existentes hasta completar la verificación de la sección 10.
>
> Esta guía no repite ni recrea `n8n_user`/`n8n_db`. LobeHub usa una identidad
> PostgreSQL nueva y dedicada: `lobehub_user` / `lobehub_db`.

## 1. Decisión auditada y fuentes oficiales

La versión elegida es **LobeHub 2.2.14**, publicada el 16 de agosto de 2026.
La imagen se fija como `lobehub/lobehub:2.2.14` y además por el digest
multi-arquitectura confirmado en Docker Hub:
`sha256:1b571d94183ffee33759906b21e4c666d4bb5133a9f97f1266fc2a0b585b2b33`.

Fuentes oficiales consultadas y decisiones derivadas:

| Tema | Evidencia oficial | Decisión para este NAS |
|---|---|---|
| Imagen/tag | [Release v2.2.14](https://github.com/lobehub/lobehub/releases/tag/v2.2.14) y [tag de Docker Hub](https://hub.docker.com/layers/lobehub/lobehub/2.2.14/images/sha256-1b571d94183ffee33759906b21e4c666d4bb5133a9f97f1266fc2a0b585b2b33) | Pin `2.2.14` + digest; no usar `latest` |
| Variables | [Docker deployment](https://lobehub.com/docs/self-hosting/platform/docker) y [.env.example de v2.2.14](https://raw.githubusercontent.com/lobehub/lobehub/v2.2.14/docker-compose/deploy/.env.example) | Usar `DATABASE_URL`, secretos de auth, S3, Redis y `INTERNAL_APP_URL`; no copiar `POSTGRES_PASSWORD` del PostgreSQL incluido por upstream |
| PostgreSQL | La [guía oficial de Docker](https://lobehub.com/docs/self-hosting/platform/docker) indica ParadeDB/pgvector/pg_search y migración automática | Reutilizar `datapostgres:5432` de DataSQL, crear `lobehub_user`/`lobehub_db`, habilitar `pg_search` solo si la prueba oficial/runtime lo requiere |
| Redis | La [guía oficial de Redis](https://lobehub.com/docs/self-hosting/advanced/redis) lo declara opcional; con `REDIS_URL` aporta sesiones/cache | Reutilizar `dataredis:6379` de DataSQL, con `REDIS_PASSWORD` existente y prefijo `lobehub`; no crear otro Redis |
| S3/RustFS | La [guía oficial S3](https://lobehub.com/docs/self-hosting/advanced/s3) y la [guía de knowledge base](https://lobehub.com/docs/self-hosting/advanced/knowledge-base) lo requieren para archivos, imágenes y knowledge base en la versión server/database | Sí instalar RustFS separado; no agregarlo al compose de DataSQL |
| SearXNG | La [guía oficial de búsqueda online](https://lobehub.com/docs/self-hosting/advanced/online-search) lo presenta como un proveedor opcional | No incluirlo en esta primera instalación; añadirlo solo si se habilita búsqueda web |
| Puerto | La [guía oficial Docker Compose](https://lobehub.com/docs/self-hosting/platform/docker-compose) muestra LobeHub en `3210` | Publicar `3210:3210` en LAN durante esta fase |
| Persistencia | El compose oficial persiste RustFS en `/data`; la DB externa conserva el esquema; LobeHub no necesita un bind mount propio en el despliegue oficial | Persistir `./data/rustfs`; respaldar además `lobehub_db` y `bucket.config.json` |
| Healthcheck | El compose oficial comprueba RustFS, PostgreSQL y Redis; no publica un endpoint HTTP de salud de LobeHub. Su Dockerfile v2.2.14 copia Node a `/bin/node` y define `PORT=3210` | Usar un healthcheck local con Node contra la raíz HTTP; validarlo en el NAS antes de tratarlo como evidencia |
| Recursos | La documentación Docker Compose oficial indica mínimo 2 cores, 4 GB RAM, 20 GB; recomienda 4+ cores, 8 GB y 50+ GB según uploads | El T20 tiene 2 cores/8 GB: cumple el mínimo, no el recomendado. LobeHub limita a 1.5 CPU/2 GB y RustFS a 0.5 CPU/512 MB; medir antes de endurecer más |

El compose oficial incluye PostgreSQL, Redis, RustFS, `rustfs-init` y SearXNG.
Este compose del NAS elimina PostgreSQL y Redis propios porque DataSQL ya es el
stack operativo único, conserva RustFS porque S3 sí es parte funcional de la
versión server/database y omite SearXNG porque la búsqueda online no es
obligatoria.

> Contenido externo consultado y reescrito de forma resumida; no se copian
> bloques extensos de las fuentes originales.

## 2. Arquitectura final

```text
LAN
 ├── http://${SERVER_IP}:3210 ── lobehub:3210
 └── http://${SERVER_IP}:9000 ── lobehub-rustfs:9000 (S3/browser)
                                  127.0.0.1:9001 (consola local)

 db_net (externa, existente)
 ├── datapostgres:5432 ── lobehub_db / lobehub_user
 └── dataredis:6379 ──── prefijo lobehub, REDIS_PASSWORD compartida

 lobe_storage (privada del compose)
 ├── lobehub:3210
 ├── lobehub-rustfs:9000
 └── rustfs-init (crea bucket y política GET)
```

Decisiones de aislamiento:

- `db_net` es externa y no se crea ni se elimina desde este compose.
- `lobe_storage` es una red privada del stack con nombre físico explícito para que RustFS no entre en la red de bases. Se justifica porque LobeHub necesita hablar con su S3 privado.
- El registro de cuentas queda restringido por `AUTH_ALLOWED_EMAILS`; no iniciar el servicio con una lista vacía.
- No hay `depends_on` contra `datapostgres` ni `dataredis`: pertenecen a otro
  compose. Se valida su salud antes de levantar LobeHub.
- RustFS publica el endpoint S3 en la LAN porque la documentación oficial avisa
  que el navegador no puede resolver `http://rustfs:9000`. La consola `9001`
  queda limitada a loopback y no es necesaria para el funcionamiento.
- `bucket.config.json` permite `s3:GetObject` anónimo únicamente para los
  objetos de `lobe`. Esto permite que el navegador/LLM recupere archivos, pero
  implica que cualquier cliente con acceso a la LAN que conozca una URL puede
  leer esos objetos. Si esa política no es aceptable, detenerse y decidir una
  estrategia de proxy/auth antes de usar uploads.

## 3. Requisitos y preflight

Antes de crear directorios o archivos, desde el contexto con permisos para que
`svc` lea los `.env` locales:

```bash
svc health
svc ps datasql
svc net
svc port-map
nas
disk
```

Continuar solo si:

- `datapostgres` y `dataredis` están saludables.
- `db_net` existe.
- Los puertos `3210` y `9000` están libres.
- `AUTH_ALLOWED_EMAILS` está definido con al menos una cuenta autorizada.
- `$dkco/_common.yml` y `$dkco/.env` existen.
- Se entiende que `9000` es un endpoint S3 de LAN y no una consola admin.

No pegar en GitHub ni en el chat la salida de `svc config`, porque puede
contener secretos interpolados.

## 4. Crear directorios primero

El despliegue usa estos artefactos:

```text
$dkco/lobehub/
├── compose.yml
├── .env                         # secretos, modo 600
├── bucket.config.json           # política no secreta de lectura S3
└── data/
    └── rustfs/                  # objetos de LobeHub
```

Crear únicamente las carpetas antes de crear archivos:

```bash
mkdir -p "$dkco/lobehub/data/rustfs"
```

No ejecutar `chmod` o `chown` antes de este `mkdir`, y no levantar el compose
mientras falten `compose.yml`, `.env` o `bucket.config.json`.

## 5. Crear el `.env` local y protegerlo

Crear el archivo vacío después de la carpeta:

```bash
touch "$dkco/lobehub/.env"
```

Editar `$dkco/lobehub/.env` y sustituir cada `__pega_aqui__` por un valor real
solo en el NAS:

```env
# Permitir solo estas cuentas, separadas por comas; no dejar vacío en LAN.
AUTH_ALLOWED_EMAILS=usuario@ejemplo.invalid

# PostgreSQL dedicado de LobeHub en DataSQL.
LOBE_DB_PASSWORD=__pega_aqui__

# Copiar localmente el valor de $dkco/datasql/.env; no generar otro Redis.
REDIS_PASSWORD=__pega_aqui__

# Generar valores nuevos y conservarlos estables para esta instalación.
KEY_VAULTS_SECRET=__pega_aqui__
AUTH_SECRET=__pega_aqui__
JWKS_KEY=__pega_aqui__

# Secreto de la cuenta RustFS usada por LobeHub y rustfs-init.
RUSTFS_SECRET_KEY=__pega_aqui__
```

Generar secretos sin compartirlos. Para `LOBE_DB_PASSWORD` y `RUSTFS_SECRET_KEY`
conviene usar caracteres URL-safe porque la contraseña de PostgreSQL se inserta
en `DATABASE_URL`:

```bash
openssl rand -base64 36 | tr -dc 'A-Za-z0-9_-' | head -c 32; printf '\n'
openssl rand -base64 36 | tr -dc 'A-Za-z0-9_-' | head -c 32; printf '\n'
openssl rand -base64 36 | tr -dc 'A-Za-z0-9_+=/' | head -c 48; printf '\n'
```

La primera salida puede usarse para `LOBE_DB_PASSWORD`, la segunda para
`RUSTFS_SECRET_KEY` y la tercera para `AUTH_SECRET` o `KEY_VAULTS_SECRET`.
`JWKS_KEY` debe generarse siguiendo la [sección oficial de JWKS_KEY](https://lobehub.com/docs/self-hosting/environment-variables/auth#jwks_key), no inventarse ni copiarse del ejemplo de upstream. Mantener todas estas variables estables después del primer arranque. La lista
`AUTH_ALLOWED_EMAILS` debe ser no vacía: LobeHub permite el registro de cualquier
cuenta cuando esa variable queda vacía. Si se necesita cambiar la lista, tomar un
snapshot y revisar el acceso resultante antes de recrear el servicio.

Copiar `REDIS_PASSWORD` localmente sin imprimirlo. No usar `source .env`:

```bash
REDIS_PASSWORD_FROM_DATASQL="$(awk -F= '$1=="REDIS_PASSWORD"{print substr($0,index($0,"=")+1); exit}' "$dkco/datasql/.env")"
if [[ -z "$REDIS_PASSWORD_FROM_DATASQL" ]]; then
  printf 'No se encontró REDIS_PASSWORD en %s/datasql/.env.\n' "$dkco" >&2
  unset REDIS_PASSWORD_FROM_DATASQL
  exit 1
fi
# Colocar el valor en $dkco/lobehub/.env con el editor local, sin imprimirlo.
unset REDIS_PASSWORD_FROM_DATASQL
```

Aplicar permisos solo después de crear y editar el archivo:

```bash
chmod 600 "$dkco/lobehub/.env"
```

`SERVER_IP` y `TZ` no se duplican: llegan desde `$dkco/.env` mediante
`env_file: [../.env, .env]`.

## 6. Aprovisionar PostgreSQL sin repetir n8n

LobeHub requiere su propia identidad. No tocar `n8n_user`, `n8n_db`, `aiadmin`
ni `aipostgres` como identidad de aplicación. Los valores de esta instalación
son:

```text
APP_DB_USER=lobehub_user
APP_DB_NAME=lobehub_db
APP_DB_PASSWORD=LOBE_DB_PASSWORD del .env de LobeHub
```

Preflight ya ejecutado en la sección 3. Leer las credenciales administrativas
sin hacer `source` ni mostrarlas:

```bash
PG_ADMIN_PASSWORD="$(awk -F= '$1=="POSTGRES_PASSWORD"{print substr($0,index($0,"=")+1); exit}' "$dkco/datasql/.env")"
PG_ADMIN_USER="$(awk -F= '$1=="POSTGRES_USER"{print substr($0,index($0,"=")+1); exit}' "$dkco/datasql/.env")"
PG_ADMIN_DB="$(awk -F= '$1=="POSTGRES_DB"{print substr($0,index($0,"=")+1); exit}' "$dkco/datasql/.env")"
APP_DB_PASSWORD="$(awk -F= '$1=="LOBE_DB_PASSWORD"{print substr($0,index($0,"=")+1); exit}' "$dkco/lobehub/.env")"

if [[ -z "$PG_ADMIN_PASSWORD" || -z "$PG_ADMIN_USER" || -z "$PG_ADMIN_DB" || -z "$APP_DB_PASSWORD" ]]; then
  printf 'Falta una credencial necesaria; no se crea ni modifica nada.\n' >&2
  unset PG_ADMIN_PASSWORD PG_ADMIN_USER PG_ADMIN_DB APP_DB_PASSWORD
  exit 1
fi
```

Comprobar si el rol ya existe antes de crear nada. Si ya existe, no cambiar su
contraseña a ciegas: comparar primero con `LOBE_DB_PASSWORD` del `.env` efectivo.

```bash
svc exec datasql postgres \
  env PGPASSWORD="$PG_ADMIN_PASSWORD" \
      PGUSER="$PG_ADMIN_USER" \
      PGDATABASE="$PG_ADMIN_DB" \
  psql
```

Dentro de `psql`:

```sql
SELECT rolname, rolcanlogin
FROM pg_roles
WHERE rolname = 'lobehub_user';
```

Si no devuelve filas, crear el rol y asignar la contraseña de forma interactiva:

```sql
CREATE ROLE lobehub_user LOGIN;
\password lobehub_user
```

Cuando `psql` solicite la contraseña, introducir localmente el valor de
`LOBE_DB_PASSWORD` del `.env`; no pegarlo en el chat. Es importante que
`\password lobehub_user` es un prompt interactivo de `psql`: una variable Bash
con el mismo secreto **no** rellena ese prompt automáticamente. Salir con
`\q`. Si el rol ya existe, no repetir `CREATE ROLE` ni `\password` sin una
comparación explícita.

Crear o verificar la base en **otra** sesión, fuera de una transacción:

```bash
svc exec datasql postgres \
  env PGPASSWORD="$PG_ADMIN_PASSWORD" \
      PGUSER="$PG_ADMIN_USER" \
      PGDATABASE="$PG_ADMIN_DB" \
  psql
```

Dentro de `psql`, consultar primero:

```sql
SELECT datname, pg_get_userbyid(datdba) AS owner
FROM pg_database
WHERE datname = 'lobehub_db';
```

Si no existe:

```sql
CREATE DATABASE lobehub_db OWNER lobehub_user;
```

Si existe, no ejecutar `CREATE DATABASE` otra vez. Continuar solo si el owner
verificado es `lobehub_user`. No combinar `CREATE ROLE` y `CREATE DATABASE` en
una llamada o transacción. Salir con `\q`.

Verificar el login dedicado en una tercera sesión usando la contraseña de
LobeHub, no la administrativa:

```bash
svc exec datasql postgres \
  env PGPASSWORD="$APP_DB_PASSWORD" \
      PGUSER=lobehub_user \
      PGDATABASE=lobehub_db \
  psql
```

En `psql`:

```sql
SELECT current_user, current_database();
\q
```

La salida esperada es `lobehub_user | lobehub_db`. Limpiar secretos temporales:

```bash
unset PG_ADMIN_PASSWORD PG_ADMIN_USER PG_ADMIN_DB APP_DB_PASSWORD
```

No habilitar `vector`, `pg_search` o `pg_cron` sin confirmarlo en la prueba de
migración/runtime. DataSQL ya provee el clúster compatible; preparar el clúster
no implica habilitar extensiones en todas las bases.

## 7. Compose final

Crear `$dkco/lobehub/compose.yml` con el contenido completo de
`agent/catalog/services/lobehub/compose.yml`. La única diferencia entre ambos
contextos es `extends.file`:

- catálogo: `../../_common.yml`;
- NAS: `../_common.yml`.

El archivo del catálogo es la configuración final auditada y está incluido en
esta PR junto con `bucket.config.json`; no copiar el compose oficial sin estos
ajustes:

- elimina PostgreSQL/Redis propios y sus puertos;
- añade `db_net` externa y el usuario/base dedicados;
- añade autenticación al Redis compartido;
- fija LobeHub 2.2.14 por digest;
- añade RustFS S3 persistente y `rustfs-init` versionados;
- crea `lobe_storage` con nombre físico explícito, sin depender del prefijo del proyecto;
- no publica la consola RustFS `9001` en la LAN;
- no usa `depends_on` contra DataSQL;
- añade healthcheck local compatible con la imagen `scratch` de LobeHub;
- añade labels de Homepage y límites iniciales de recursos.

Crear también `$dkco/lobehub/bucket.config.json` copiando el archivo del
catálogo. El bucket debe existir antes de que LobeHub intente guardar objetos.

## 8. Validar configuración antes de levantar

```bash
dk lobehub
svc config lobehub
svc port-map
```

`svc config` no debe mostrar variables sin resolver. No compartir su salida:
puede contener `DATABASE_URL`, `JWKS_KEY`, `REDIS_PASSWORD` o credenciales S3.
Si el wrapper local necesita leer el `.env` global, ejecutar desde el contexto
con permisos adecuado; el handoff de n8n documenta el `permission denied` que
puede aparecer desde un usuario sin acceso a `$dkco/.env`.

## 9. Levantar en el orden real

Después de directorios → archivos → permisos → validación:

```bash
svc pull lobehub
svc up lobehub
svc ps lobehub
svc logs lobehub
svc health
svc stats lobehub
```

La primera ejecución debe mostrar, en el contenedor LobeHub, migración de base
completada y el servidor Next.js listo. `rustfs-init` debe terminar con código 0
tras crear `lobe`; no debe imprimir secretos. No usar `svc update` sobre otro
servicio y no detener DataSQL como parte de esta instalación.

## 10. Verificación posterior y criterios de aceptación

La instalación solo puede declararse operativa si se verifican todos estos
puntos en el NAS:

1. `svc ps lobehub` muestra `lobehub` y `lobehub-rustfs` activos; el init terminó
   correctamente.
2. `svc health` muestra LobeHub y RustFS saludables; si el healthcheck de
   LobeHub falla por una diferencia de imagen, registrar el motivo antes de
   cambiarlo, no desactivarlo silenciosamente.
3. `curl -fsS http://${SERVER_IP}:3210` devuelve HTTP válido desde el NAS/LAN y
   la UI carga en el navegador.
4. `curl -fsS http://${SERVER_IP}:9000/health` devuelve éxito y el endpoint S3
   es accesible desde el navegador de la LAN.
5. Los logs contienen migración completada, sin errores de PostgreSQL, Redis o
   S3 y sin reinicios repetidos.
6. La sesión de prueba de la sección 6 devuelve
   `lobehub_user | lobehub_db`.
7. Redis responde `PONG` usando el secreto existente, sin crear otro contenedor:

   ```bash
   REDIS_PASSWORD="$(awk -F= '$1=="REDIS_PASSWORD"{print substr($0,index($0,"=")+1); exit}' "$dkco/datasql/.env")"
   svc exec datasql redis env REDISCLI_AUTH="$REDIS_PASSWORD" redis-cli PING
   unset REDIS_PASSWORD
   ```

8. Después del primer login, validar un chat y, si se habilita, una imagen o
   archivo para comprobar realmente S3; el bucket debe conservar objetos en
   `$dkco/lobehub/data/rustfs`.
9. `svc port-map` no muestra `5432` ni `6379` publicados por LobeHub y `9001`
   solo está en loopback.
10. Medir `svc stats lobehub` y `svc stats datasql` antes de ajustar límites.

La presencia de `db_net` por sí sola no prueba que la aplicación use la base o
Redis correctos: deben coincidir compose, variables, logs y consultas runtime.

## 11. Backup, actualización y recuperación

Antes del primer arranque y antes de actualizar:

```bash
svc snapshot lobehub
```

Respaldar el almacenamiento de objetos y la base dedicada. `svc backup lobehub`
protege el bind mount de RustFS según la implementación del NAS; el dump
PostgreSQL debe hacerse aparte con credenciales temporales no impresas. El
procedimiento lógico siguiente escribe el dump en el directorio de backups de
DataSQL y no versiona el secreto:

```bash
BACKUP_TS="$(date +%Y%m%d-%H%M%S)"
DUMP_FILE="$dkco/datasql/data/postgres/backups/lobehub_db_${BACKUP_TS}.sql"
APP_DB_PASSWORD="$(awk -F= '$1=="LOBE_DB_PASSWORD"{print substr($0,index($0,"=")+1); exit}' "$dkco/lobehub/.env")"

if [[ -z "$APP_DB_PASSWORD" ]]; then
  printf 'No se encontró LOBE_DB_PASSWORD en %s/lobehub/.env.\n' "$dkco" >&2
  unset BACKUP_TS DUMP_FILE APP_DB_PASSWORD
  exit 1
fi

if ! svc exec datasql postgres \
  env PGPASSWORD="$APP_DB_PASSWORD" \
      PGUSER=lobehub_user \
      PGDATABASE=lobehub_db \
  pg_dump --format=plain --no-owner --no-privileges > "$DUMP_FILE"; then
  printf 'El dump de LobeHub falló; se elimina solo el archivo parcial.\n' >&2
  rm -f "$DUMP_FILE"
  unset BACKUP_TS DUMP_FILE APP_DB_PASSWORD
  exit 1
fi

printf 'Dump lógico creado en %s.\n' "$DUMP_FILE"
unset BACKUP_TS DUMP_FILE APP_DB_PASSWORD
```

Este comando debe ejecutarse con DataSQL saludable y después de verificar que
el archivo no está vacío. La restauración sobre `lobehub_db` no se automatiza en
esta guía: es una operación potencialmente destructiva que debe planificarse,
confirmar el dump y detener LobeHub antes de usar `psql --set ON_ERROR_STOP=1`.
El procedimiento de dump está documentado pero no fue ejecutado en este entorno;
verificarlo en el NAS antes de tratarlo como backup probado. Seguir también el
procedimiento de backups de [`docs/services/datasql-guide.md`](datasql-guide.md)
y no presentar un tar del bind mount como sustituto de un dump lógico.

Para una actualización de LobeHub, primero consultar las release notes y cambiar
el tag/digest en catálogo y compose; luego validar `svc config`, tomar snapshot,
crear dump, usar `svc pull lobehub` y verificar migraciones. No borrar
`$dkco/lobehub/data/rustfs` ni el contenido de `lobehub_db` para resolver un fallo.

Si una migración falla:

1. conservar logs y el tag/digest usado;
2. no ejecutar `rm -rf data`;
3. detenerse y revisar compatibilidad de release, PostgreSQL y RustFS;
4. recuperar desde backup/snapshot solo con confirmación explícita;
5. repetir las verificaciones de la sección 10.

## 12. Fuera de alcance y pendientes

- No se instala SearXNG en esta primera versión; la búsqueda web es opcional.
- No se instala proxy/TLS ni se afirma que la exposición HTTP en LAN sea apta
  para Internet; la lista de `AUTH_ALLOWED_EMAILS` es obligatoria antes del
  primer arranque.
- No se crea un script DebMenux en esta PR; `debmenu install lobehub` queda
  fuera de alcance y esta propuesta se despliega manualmente siguiendo esta
  guía.
- No se modifica ni verifica n8n; `n8n_user`, `n8n_db` y su clave de cifrado se
  conservan intactos.
- No se instala un PostgreSQL, Redis o RustFS dentro de DataSQL.
- La política pública de lectura S3 debe revisarse si se manejarán documentos
  sensibles.
- Debe hacerse la prueba runtime de healthcheck, recursos, migración, uploads y
  backups antes de marcar la ficha como `protected` o decir que el servicio está
  operativo.
