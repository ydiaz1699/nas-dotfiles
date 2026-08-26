# Stack DataSQL — Guía Completa para NAS Debian

> PostgreSQL y Redis no se exponen a la LAN. PostgreSQL mantiene una excepción
> host-only (`127.0.0.1:5432:5432`) porque Home Assistant usa `network_mode: host`
> y su Recorder conecta al loopback del NAS. Los consumidores Docker usan
> `datapostgres:5432` y `dataredis:6379` por `db_net`.

## Fuente de verdad para aplicaciones consumidoras

Esta guía es la fuente canónica del procedimiento DataSQL. La skill
`.kiro/skills/datasql/SKILL.md` resume las reglas para el agente, pero no
reemplaza esta secuencia ni sus verificaciones.

Antes de crear una base, un rol PostgreSQL o configurar Redis para otra
aplicación, seguir siempre este orden:

1. Comprobar DataSQL con `svc health` y `svc ps datasql`.
2. Leer las credenciales reales desde `$dkco/datasql/.env`; nunca asumir
   `admin/appdb` ni ejecutar `source .env`.
3. Crear el rol y la base PostgreSQL en llamadas separadas.
4. Validar Redis con `REDISCLI_AUTH` y reutilizar `dataredis`.
5. Configurar la aplicación en `db_net` con los hostnames `datapostgres` y
   `dataredis`.
6. Limpiar las variables temporales con `unset`.

### Regla crítica de PostgreSQL

`CREATE DATABASE` no debe combinarse con `CREATE USER`/`CREATE ROLE` en la
misma transacción o llamada a `psql`. Si la creación de la base falla, la
transacción puede revertir también el rol. La receta idempotente y segura está
en la Fase 5A; usarla para Flowise, Home Assistant, Node-RED o cualquier otro
consumidor.

---

## Fase 1 — Estructura de Directorios

Crear toda la estructura de una sola vez:

```bash
mkdir -p $dkco/datasql/data/{postgres/{pgdata,backups},pgadmin,redis}
```

No aplicar todavía `chmod`/`chown`: primero deben existir los archivos de
configuración y debe completarse la creación de directorios.

Árbol resultante:

```
$dkco/datasql/
├── compose.yml
├── .env                  ← permisos 600
└── data/
    ├── postgres/
    │   ├── pgdata/
    │   └── backups/
    ├── pgadmin/
    └── redis/
```

---

## Fase 2 — Red Docker

`db_net` es una red externa compartida. Verificarla sin modificarla:

```bash
svc net
```

Si la red no existe en una instalación nueva, detenerse y seguir la sección
[Redes Docker de `docs/docker-entorno.md`](../../docs/docker-entorno.md#redes-docker),
que define el bootstrap inicial. Esa creación es una operación de instalación,
no una reparación normal: no crear o eliminar redes compartidas durante una
migración de DataSQL y nunca usar `docker network prune` como solución genérica.

---

## Fase 3 — Archivo `.env`

```bash
dk datasql
nano .env
```

Contenido (reemplazar contraseñas antes de guardar):

```
# === PostgreSQL ===
POSTGRES_DB=homelab
POSTGRES_USER=nasadmin
POSTGRES_PASSWORD=__pega_aqui__

# === pgAdmin ===
PGADMIN_EMAIL=admin@local.lan
PGADMIN_PASSWORD=__pega_aqui__

# === Redis ===
REDIS_PASSWORD=__pega_aqui__

# === TZ y SERVER_IP se heredan de $dkco/.env (global) ===
```

Proteger el archivo `.env` y las carpetas solamente después de crear el
`compose.yml` en la Fase 4:

> Tip: Generar contraseñas seguras: `openssl rand -base64 32`

---

## Fase 4 — `compose.yml` (versión final corregida)

> pgAdmin NO lleva `security_opt` ni `cap_drop` — la imagen usa `sudo` internamente y es incompatible con esas restricciones.

> El puerto de pgAdmin es `5050:80` (sin `127.0.0.1:`) para acceso directo desde la LAN sin túnel SSH.

```yaml
# $dkco/datasql/compose.yml
services:

  postgres:
    image: postgres:16-alpine
    container_name: datapostgres
    restart: unless-stopped
    env_file:
      - ../.env
      - .env
    # PostgreSQL se publica solo en loopback para Home Assistant host-network.
    ports:
      - "127.0.0.1:5432:5432"
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      PGDATA: /var/lib/postgresql/data/pgdata
      POSTGRES_INITDB_ARGS: "--auth-host=scram-sha-256 --auth-local=scram-sha-256"
    volumes:
      - ./data/postgres/pgdata:/var/lib/postgresql/data/pgdata
      - ./data/postgres/backups:/backups
    networks:
      - db_net
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 30s
    security_opt:
      - no-new-privileges:true
    cap_drop: [ALL]
    cap_add: [CHOWN, DAC_OVERRIDE, SETUID, SETGID]
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 512M

  pgadmin:
    image: dpage/pgadmin4:latest
    container_name: datapgadmin
    restart: unless-stopped
    env_file:
      - ../.env
      - .env
    environment:
      PGADMIN_DEFAULT_EMAIL: ${PGADMIN_EMAIL}
      PGADMIN_DEFAULT_PASSWORD: ${PGADMIN_PASSWORD}
      PGADMIN_CONFIG_SERVER_MODE: "True"
      PGADMIN_CONFIG_MASTER_PASSWORD_REQUIRED: "False"
    volumes:
      - ./data/pgadmin:/var/lib/pgadmin
    ports:
      - "5050:80"
    labels:
      - homepage.group=Bases de datos
      - homepage.name=pgAdmin
      - homepage.icon=pgadmin
      - homepage.href=http://${SERVER_IP}:5050
      - homepage.description=Administración de PostgreSQL (datasql)
    depends_on:
      postgres:
        condition: service_healthy
    networks:
      - db_net
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 128M

  redis:
    image: redis:7-alpine
    container_name: dataredis
    restart: unless-stopped
    command:
      - redis-server
      - --appendonly
      - "yes"
      - --requirepass
      - "${REDIS_PASSWORD}"
    volumes:
      - ./data/redis:/data
    networks:
      - db_net
    healthcheck:
      test: ["CMD", "redis-cli", "-a", "${REDIS_PASSWORD}", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 10s
    security_opt:
      - no-new-privileges:true
    cap_drop: [ALL]
    cap_add: [CHOWN, DAC_OVERRIDE, SETUID, SETGID]
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 256M
        reservations:
          cpus: '0.1'
          memory: 64M

networks:
  db_net:
    external: true
```

Aplicar permisos después de crear `.env` y `compose.yml`, y antes de levantar:

```bash
chmod 700 $dkco/datasql/data/postgres/pgdata
chmod 700 $dkco/datasql/data/postgres/backups
chmod 700 $dkco/datasql/data/redis
chmod 700 $dkco/datasql/data/pgadmin
chmod 600 $dkco/datasql/.env
```

### Migración desde un Compose legacy con IPs estáticas

Si el `compose.yml` existente contiene bloques como:

```yaml
networks:
  db_net:
    ipv4_address: 172.20.0.X
```

hay que reemplazarlo por la configuración canónica del catálogo. Las IPs
`172.20.0.3`, `172.20.0.4` y `172.20.0.5` no deben reservarse manualmente:
`db_net` es compartida por varios servicios y Docker debe asignar las IPs
dinámicamente. El error resultante de una dirección ya ocupada es:
`failed to set up container networking: Address already in use`.

La migración desde el checkout local del NAS se ejecuta en este orden:

```bash
# 1. Guardar una instantánea de la configuración actual
svc snapshot datasql

# 2. Sustituir el Compose runtime por la versión canónica del catálogo
cp "$NAS_DOTFILES/agent/catalog/services/datasql/compose.yml" \
   "$dkco/datasql/compose.yml"

# 3. Validar la configuración nueva sin levantar contenedores
svc config datasql

# 4. Recrear el stack con la nueva asignación dinámica de IPs
svc down datasql
svc up datasql

# 5. Verificar los tres servicios y la red compartida
svc ps datasql
svc net
svc port-map
```

La versión canónica conserva una publicación **solo en loopback** para el
Recorder de Home Assistant (`127.0.0.1:5432:5432`): no es accesible desde la
LAN y no debe cambiarse a `0.0.0.0:5432:5432`. Los consumidores conectados a
`db_net` siguen usando `datapostgres:5432`. No eliminar `db_net`: otros
servicios activos pueden utilizarla. Si el `svc config datasql` sigue mostrando
`ipv4_address`, `published: "5432"` sin `127.0.0.1`, `TZ` dentro de
`environment` o una IP literal en el label de Homepage, detenerse y no ejecutar
`svc up`.

Si el NAS responde `No such command 'snapshot'`, el checkout todavía está
entrando por el CLI Python anterior. Guardar el snapshot mediante la
implementación Bash, sin duplicar la lógica ni operar Docker directamente:

```bash
NAS_CLI=bash svc snapshot datasql
```

El fix del CLI Python ya está integrado en `main`: `svc snapshot datasql`
queda registrado en Python y delega al mismo `svc_snapshot` Bash mediante
`bash_bridge.py`. En un NAS que todavía tenga un checkout anterior, usar
explícitamente `NAS_CLI=bash` también para el rollback:

```bash
NAS_CLI=bash svc rollback datasql
```

### Qué significa `Address already in use` en este incidente

El mensaje real fue:

```text
failed to set up container networking: Address already in use
```

Aquí `address` era una **IP interna de Docker** ocupada en `db_net`, no un
puerto TCP del host. El Compose legacy fijaba `172.20.0.3`, `172.20.0.4` y
`172.20.0.5` mediante `ipv4_address`; como `db_net` es compartida, otra
asignación podía ocupar una de esas IPs. Por eso cambiar `5050`, `5051` o
`5432`, aun cuando esos puertos estuvieran libres, no corregía la causa.

`svc restart datasql` tampoco resuelve esta variante: reinicia contenedores,
pero no recrea la red ni reemplaza las IPs estáticas. La corrección es retirar
los bloques `ipv4_address`, validar el Compose y recrear únicamente el stack
con `svc down datasql` seguido de `svc up datasql`. No ejecutar
`docker network prune` ni eliminar manualmente `db_net`: otros servicios pueden
depender de esa red externa.

Para distinguir ambos tipos de error antes de cambiar un puerto:

```bash
svc config datasql
svc ps datasql
svc port-map
ss -ltnp | grep -E ':(5432|5050|5051)\b' || true
svc net
```

Si `ss` no muestra un listener en el puerto sospechoso, pero `svc config` aún
muestra `ipv4_address`, el problema es de direccionamiento Docker. Si el
mensaje dice `bind: address already in use` y `ss` identifica otro proceso,
entonces sí es un conflicto de puerto del host y se investiga con la guía de
troubleshooting.

---

## Fase 5 — Levantar el Stack

```bash
dk datasql

# Validar sintaxis antes de levantar
svc config datasql

# Levantar
svc up datasql

# Ver estado
svc ps datasql

# Ver logs
svc logs datasql
```

> Los tres contenedores deben aparecer en estado **Up (healthy)**.

---

## Fase 5A — Crear una base y un rol dedicados para una aplicación

Esta es la receta canónica para Flowise y para cualquier otro consumidor de
DataSQL. Se ejecuta **después** de que DataSQL esté saludable y **antes** de
levantar la aplicación consumidora.

### 1. Leer las credenciales reales de DataSQL

No asumir que el administrador es `admin` ni que la base es `appdb`: esos
valores pueden cambiar según la instalación. Tampoco ejecutar `source .env`,
porque los secretos pueden contener caracteres con significado para el shell.

El ejemplo siguiente usa Flowise. Para otra aplicación, cambia únicamente los
nombres de aplicación y la variable que contiene su contraseña local.

```bash
PG_ADMIN_USER=$(grep '^POSTGRES_USER=' "$dkco/datasql/.env" | cut -d= -f2-)
PG_ADMIN_DB=$(grep '^POSTGRES_DB=' "$dkco/datasql/.env" | cut -d= -f2-)
PG_ADMIN_PASSWORD=$(grep '^POSTGRES_PASSWORD=' "$dkco/datasql/.env" | cut -d= -f2-)

APP_DB_USER=flowise_user
APP_DB_NAME=flowise_db
APP_DB_PASSWORD=$(grep '^FLOWISE_DB_PASSWORD=' "$dkco/flowise/.env" | cut -d= -f2-)
```

Verificar que las cuatro variables administrativas y la contraseña de la
aplicación no estén vacías antes de continuar. La contraseña de la aplicación
debe ser exactamente la que usa su `.env` local; no generar otra durante este
paso.

### 2. Crear o actualizar el rol, en una llamada separada

La contraseña se pasa como variable de `psql`; no se concatena dentro del SQL.
El comando es idempotente: crea el rol si no existe y actualiza su contraseña
si ya existe.

```bash
ROLE_EXISTS=$(svc exec datasql postgres \
  env PGPASSWORD="$PG_ADMIN_PASSWORD" \
  psql -U "$PG_ADMIN_USER" -d "$PG_ADMIN_DB" -Atqc \
  "SELECT 1 FROM pg_roles WHERE rolname='flowise_user';" \
  | tr -d '[:space:]')

if [[ "$ROLE_EXISTS" == "1" ]]; then
  svc exec datasql postgres \
    env PGPASSWORD="$PG_ADMIN_PASSWORD" \
    psql -U "$PG_ADMIN_USER" -d "$PG_ADMIN_DB" \
    -v ON_ERROR_STOP=1 -v app_password="$APP_DB_PASSWORD" \
    -c "ALTER ROLE flowise_user WITH LOGIN PASSWORD :'app_password';"
else
  svc exec datasql postgres \
    env PGPASSWORD="$PG_ADMIN_PASSWORD" \
    psql -U "$PG_ADMIN_USER" -d "$PG_ADMIN_DB" \
    -v ON_ERROR_STOP=1 -v app_password="$APP_DB_PASSWORD" \
    -c "CREATE ROLE flowise_user LOGIN PASSWORD :'app_password';"
fi
```

### 3. Crear la base, en otra llamada y fuera de una transacción

`CREATE DATABASE` no se ejecuta junto con `CREATE ROLE`/`CREATE USER`. Esta
separación evita que un fallo de la base revierta también el rol.

```bash
DB_EXISTS=$(svc exec datasql postgres \
  env PGPASSWORD="$PG_ADMIN_PASSWORD" \
  psql -U "$PG_ADMIN_USER" -d "$PG_ADMIN_DB" -Atqc \
  "SELECT 1 FROM pg_database WHERE datname='flowise_db';" \
  | tr -d '[:space:]')

if [[ "$DB_EXISTS" != "1" ]]; then
  svc exec datasql postgres \
    env PGPASSWORD="$PG_ADMIN_PASSWORD" \
    psql -U "$PG_ADMIN_USER" -d "$PG_ADMIN_DB" \
    -v ON_ERROR_STOP=1 \
    -c "CREATE DATABASE flowise_db OWNER flowise_user;"
fi
```

Verificar el propietario antes de cambiarlo. Si la base ya existía con otro
propietario, no ejecutar `ALTER DATABASE` a ciegas: confirmar primero y luego
corregirlo explícitamente si la aplicación lo requiere.

```bash
svc exec datasql postgres \
  env PGPASSWORD="$PG_ADMIN_PASSWORD" \
  psql -U "$PG_ADMIN_USER" -d "$PG_ADMIN_DB" -c \
  "SELECT datname, pg_get_userbyid(datdba) AS owner FROM pg_database WHERE datname='flowise_db';"
```

### 4. Probar el acceso del consumidor y limpiar secretos temporales

```bash
svc exec datasql postgres \
  env PGPASSWORD="$APP_DB_PASSWORD" \
  psql -U "$APP_DB_USER" -d "$APP_DB_NAME" \
  -c "SELECT current_user, current_database();"

unset PG_ADMIN_USER PG_ADMIN_DB PG_ADMIN_PASSWORD
unset APP_DB_USER APP_DB_NAME APP_DB_PASSWORD ROLE_EXISTS DB_EXISTS
```

> Para otra aplicación, sustituir `flowise_user`, `flowise_db` y la lectura de
> `FLOWISE_DB_PASSWORD` por el rol, base y variable local correspondientes.
> Nunca reutilizar el administrador `POSTGRES_USER` como usuario de la aplicación.

---

## Fase 6 — Verificación

### PostgreSQL

```bash
PG_ADMIN_USER=$(grep '^POSTGRES_USER=' "$dkco/datasql/.env" | cut -d= -f2-)
PG_ADMIN_DB=$(grep '^POSTGRES_DB=' "$dkco/datasql/.env" | cut -d= -f2-)
PG_ADMIN_PASSWORD=$(grep '^POSTGRES_PASSWORD=' "$dkco/datasql/.env" | cut -d= -f2-)

svc exec datasql postgres \
  env PGPASSWORD="$PG_ADMIN_PASSWORD" \
  psql -U "$PG_ADMIN_USER" -d "$PG_ADMIN_DB" \
  -c "SELECT version();"

unset PG_ADMIN_USER PG_ADMIN_DB PG_ADMIN_PASSWORD
```

El endpoint para Home Assistant debe estar limitado al loopback del NAS:

```bash
ss -ltnp | grep ':5432'
```

La salida esperada contiene `127.0.0.1:5432`; si aparece `0.0.0.0:5432` o
`[::]:5432`, PostgreSQL quedó expuesto a la LAN y hay que detenerse antes de
continuar.

### pgAdmin

Acceder desde la LAN mediante:

```text
http://${SERVER_IP}:5050
```

Usar `PGADMIN_EMAIL` y `PGADMIN_PASSWORD` del `.env` de DataSQL. Para agregar
PostgreSQL, usar el hostname Docker `postgres`, el puerto interno `5432`,
`POSTGRES_USER` y `POSTGRES_PASSWORD` del mismo `.env`.

### Redis

Redis ya forma parte de DataSQL. No crear otro contenedor, otra contraseña ni
un usuario Redis adicional para el patrón actual `requirepass`.

```bash
REDIS_PASSWORD=$(grep '^REDIS_PASSWORD=' "$dkco/datasql/.env" | cut -d= -f2-)

svc exec datasql redis \
  env REDISCLI_AUTH="$REDIS_PASSWORD" \
  redis-cli PING

unset REDIS_PASSWORD
```

La respuesta esperada es `PONG`. `REDISCLI_AUTH` evita poner la contraseña en
los argumentos visibles del proceso; no usar `redis-cli -a "$REDIS_PASSWORD"`
como receta canónica.

---

## Fase 7 — Errores Encontrados y Soluciones

Registro de los problemas reales encontrados durante la instalación.

---

### Error 1: pgAdmin no levantaba con `no-new-privileges`

**Síntoma:** el contenedor `datapgadmin` arrancaba y moría inmediatamente.

**Causa:** la imagen `dpage/pgadmin4` usa `sudo` internamente, lo cual es incompatible con `security_opt: no-new-privileges:true` y `cap_drop: ALL`.

**Solución:** eliminar `security_opt` y `cap_drop`/`cap_add` del bloque `pgadmin` en el `compose.yml`. Postgres y Redis sí pueden mantenerlas.

---

### Error 2: Indentación incorrecta en `compose.yml`

**Síntoma:** una validación del Compose devolvía error de parsing YAML.

**Causa:** al editar con `nano`, la línea `pgadmin:` quedó sin los 2 espacios de sangría requeridos.

**Solución:** verificar antes de levantar:

```bash
svc config datasql
```

Si la configuración no se resuelve, abrir `compose.yml` y asegurarse de que
`postgres:`, `pgadmin:` y `redis:` tengan exactamente 2 espacios de
indentación.

---

### Error 3: Permisos incorrectos en carpeta `pgadmin`

**Síntoma:** el contenedor arrancaba pero pgAdmin mostraba errores de permisos en los logs.

**Causa:** la carpeta `$dkco/datasql/data/pgadmin` fue creada por `root`, pero el contenedor corre como usuario `pgadmin` (uid `5050`).

**Solución:**

```bash
chown -R 5050:5050 "$dkco/datasql/data/pgadmin"
svc restart datasql
```

---

### Error 4: Datos corruptos en `pgadmin`

**Síntoma:** pgAdmin no iniciaba; la carpeta `data/pgadmin` contenía múltiples archivos `pgadmin4.db.XXXXXXXXXX` (backups de intentos fallidos).

**Causa:** intentos previos fallidos dejaron la base de datos SQLite de pgAdmin en estado inconsistente.

**Solución:** detener primero el stack y borrar únicamente los datos de pgAdmin,
no el resto de DataSQL:

```bash
svc down datasql
rm -rf "$dkco/datasql/data/pgadmin"
mkdir -p "$dkco/datasql/data/pgadmin"
chown -R 5050:5050 "$dkco/datasql/data/pgadmin"
svc up datasql
svc logs datasql pgadmin
```

> Logs correctos: solo debe aparecer `Booting gunicorn` sin errores de permisos.

---

### Error 5: pgAdmin inaccesible desde Windows sin túnel SSH

**Síntoma:** `http://${SERVER_IP}:5050` no respondía desde Windows.

**Causa:** el puerto estaba configurado como `127.0.0.1:5050:80`, restringiéndolo únicamente a localhost del NAS.

**Solución:** cambiar el binding en `compose.yml`:

```yaml
ports:
  - "5050:80"    # antes: "127.0.0.1:5050:80"
```

Acceso directo desde cualquier dispositivo de la LAN mediante `${SERVER_IP}:5050` sin túnel SSH.

---

## Fase 8 — Script de Backup

```bash
nano $dkco/datasql/backup.sh
```

```bash
#!/usr/bin/env bash
set -euo pipefail

BASE="$dkco/datasql"
read_env() {
    grep "^${1}=" "$BASE/.env" | cut -d= -f2-
}

POSTGRES_DB=$(read_env POSTGRES_DB)
POSTGRES_USER=$(read_env POSTGRES_USER)
POSTGRES_PASSWORD=$(read_env POSTGRES_PASSWORD)
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP="$BASE/data/postgres/backups/${POSTGRES_DB}_${TIMESTAMP}.sql"
LOG="$BASE/data/postgres/backups/backup.log"
RETENTION=7

printf '[%s] Iniciando backup de %s...\n' "$(date)" "$POSTGRES_DB" >> "$LOG"

svc exec datasql -T -e "PGPASSWORD=${POSTGRES_PASSWORD}" postgres \
  pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" > "$BACKUP"

gzip "$BACKUP"
printf '[%s] Completado: %s.gz\n' "$(date)" "$BACKUP" >> "$LOG"
find "$BASE/data/postgres/backups" -name "*.sql.gz" -mtime +"$RETENTION" -delete
printf '[%s] Limpieza: retención %s días\n' "$(date)" "$RETENTION" >> "$LOG"

unset POSTGRES_DB POSTGRES_USER POSTGRES_PASSWORD
```

Este script lee solo las variables necesarias, no hace `source .env` y no
asume `admin/appdb`. El entorno de cron debe tener disponible el comando `svc`;
si no, cargar el framework del NAS en la entrada de cron antes de ejecutar el
script. Probar primero manualmente y comprobar que el `.sql.gz` existe antes
de confiar en la tarea programada.

```bash
chmod +x $dkco/datasql/backup.sh
```

Programar en crontab (backup diario a las 03:00):

```bash
crontab -e
```

```
0 3 * * * $dkco/datasql/backup.sh
```

### Restaurar un backup

```bash
# Ver backups disponibles
ls -lh "$dkco/datasql/data/postgres/backups"/*.sql.gz

# Seleccionar un archivo real antes de restaurar.
BACKUP="$dkco/datasql/data/postgres/backups/archivo.sql.gz"
PG_ADMIN_USER=$(grep '^POSTGRES_USER=' "$dkco/datasql/.env" | cut -d= -f2-)
PG_ADMIN_DB=$(grep '^POSTGRES_DB=' "$dkco/datasql/.env" | cut -d= -f2-)
PG_ADMIN_PASSWORD=$(grep '^POSTGRES_PASSWORD=' "$dkco/datasql/.env" | cut -d= -f2-)

gunzip -c "$BACKUP" | \
  svc exec datasql -T -e "PGPASSWORD=${PG_ADMIN_PASSWORD}" postgres \
  psql -U "$PG_ADMIN_USER" -d "$PG_ADMIN_DB"

unset BACKUP PG_ADMIN_USER PG_ADMIN_DB PG_ADMIN_PASSWORD
```

---

## Fase 8A — Inventario de bases y consumidores

Tener un contenedor conectado a `db_net` **no demuestra** que use PostgreSQL o
Redis. La red solo permite la comunicación. La conexión real se confirma en el
compose, la configuración del servicio y, cuando sea necesario, en el runtime.

### Inventario confirmado del NAS

Este inventario fue comprobado en el NAS el 2026-08-25. Las bases muestran
propietario y tamaño, pero la existencia de una base no prueba que el servicio
actual siga apuntando a ella.

| Base | Propietario | Tamaño observado | Consumidor | Estado |
|---|---|---:|---|---|
| `appdb` | `admin` | 7519 kB | Base administrativa de DataSQL | Confirmada |
| `flowise_db` | `flowise_user` | 9327 kB | Flowise | Configuración documentada |
| `homeassistant_db` | `ha_user` | 42 MB | Home Assistant Recorder | Configuración documentada |
| `n8n_db` | `n8n_user` | 14 MB | n8n | Base existente; configuración del compose pendiente de auditar |
| `postgres` | `admin` | 7519 kB | Base estándar de PostgreSQL | Confirmada |

No borrar ni reutilizar estas bases para otra aplicación. Cada consumidor debe
tener una base y un rol dedicados.

### Mapa de consumidores

| Servicio | PostgreSQL | Redis | Persistencia principal | Evidencia |
|---|---|---|---|---|
| DataSQL | Proveedor (`datapostgres`) | Proveedor (`dataredis`) | `datasql/data/` | compose de DataSQL |
| Flowise | `flowise_db` por `datapostgres` | `dataredis`, cola `flowise-queue` | `$dkco/flowise/data` | compose y guía de Flowise |
| Home Assistant | `homeassistant_db` por `127.0.0.1:5432` | No configurado | `$dkco/homeassistant/data` | `recorder.db_url` documentado |
| n8n | `n8n_db` existe; endpoint y modo deben comprobarse | Desconocido | Debe comprobarse en su compose real | no catalogado actualmente |
| Node-RED | No externo confirmado | No externo confirmado | `$dkco/node-red/data` | compose/guía |
| EMQX | Mnesia/archivos internos | No externo confirmado | `$dkco/emqx/data` | compose/ficha |
| ioBroker | Archivos/JSON | No habilitado | `$dkco/iobroker/data` | compose/ficha |
| File Browser | SQLite embebida | No | `$dkco/filebrowser/config` | `database.db` en compose |
| Homepage/ESPHome/ntfy | No externo confirmado | No externo confirmado | archivos/bind mounts | compose/fichas |

Las filas “no externo confirmado” no descartan que un flujo, nodo o adapter
instalado desde la interfaz use una base por su cuenta; solo indican que no hay
esa conexión declarada en el catálogo versionado.

### Ver el inventario PostgreSQL sin mostrar secretos

La implementación Python de `svc exec` abre TTY por defecto. Para consultas
interactivas, ejecutar `psql` sin pipe y pegar el SQL en el prompt:

```bash
dk datasql

POSTGRES_DB="$(awk -F= '$1=="POSTGRES_DB"{print substr($0,index($0,"=")+1)}' .env)"
POSTGRES_USER="$(awk -F= '$1=="POSTGRES_USER"{print substr($0,index($0,"=")+1)}' .env)"
POSTGRES_PASSWORD="$(awk -F= '$1=="POSTGRES_PASSWORD"{print substr($0,index($0,"=")+1)}' .env)"

svc exec datasql postgres env \
  PGPASSWORD="$POSTGRES_PASSWORD" \
  PGUSER="$POSTGRES_USER" \
  PGDATABASE="$POSTGRES_DB" \
  psql
```

Dentro de `psql`:

```sql
SELECT datname AS database,
       pg_get_userbyid(datdba) AS owner,
       pg_size_pretty(pg_database_size(datname)) AS size
FROM pg_database
WHERE datistemplate = false
ORDER BY datname;

SELECT rolname AS role,
       rolsuper AS superuser,
       rolcanlogin AS can_login
FROM pg_roles
WHERE rolname NOT LIKE 'pg_%'
ORDER BY rolname;

SELECT name, default_version, installed_version
FROM pg_available_extensions
WHERE name IN ('vector', 'pg_search')
ORDER BY name;
```

Para comprobar tablas de una base concreta, sin modificarla:

```sql
SELECT datname FROM pg_database
WHERE datname IN ('flowise_db', 'homeassistant_db', 'n8n_db');

\c n8n_db
\dt
```

Salir y limpiar variables:

```text
\q
```

```bash
unset POSTGRES_DB POSTGRES_USER POSTGRES_PASSWORD
```

La consulta de `pg_available_extensions` solo informa si la extensión está
disponible en la imagen/servidor. `pg_extension` informa si está habilitada en
la base actualmente seleccionada:

```sql
SELECT extname FROM pg_extension
WHERE extname IN ('vector', 'pg_search')
ORDER BY extname;
```

### Auditar n8n antes de crear o migrar nada

La existencia de `n8n_db` no basta para afirmar cómo funciona el n8n activo.
Inspeccionar su compose sin compartir valores secretos:

```bash
dk n8n
grep -Ein \
  'DB_|DATABASE|POSTGRES|SQLITE|REDIS|env_file|volumes|networks|image' \
  compose.yml
svc volumes n8n
svc depends n8n
```

No pegar líneas que contengan `PASSWORD`, `TOKEN`, `KEY`, `SECRET` o valores de
`.env`. Si n8n usa PostgreSQL, conservar `n8n_db` y `n8n_user`; si usa SQLite,
la base existente puede ser antigua, residual o pertenecer a otra instalación
y debe confirmarse en el runtime antes de tocarla.

### Receta para cualquier nuevo consumidor

1. Leer esta guía y la guía específica del servicio.
2. Ejecutar `svc health`, `svc ps datasql` y comprobar `svc net`.
3. Leer las credenciales administrativas desde `$dkco/datasql/.env` sin
   `source` y sin mostrar secretos.
4. Crear el rol primero y la base después, usando nombres dedicados.
5. Verificar propietario, conexión con el usuario dedicado y, si aplica, Redis.
6. Configurar `db_net` y los hostnames `datapostgres`/`dataredis`; no publicar
   `5432` ni `6379` y no usar `depends_on` contra otro compose.
7. Levantar y verificar el consumidor; después documentarlo con `svc catalog-sync`.

---

## Fase 9 — Operación Diaria

```bash
svc ps datasql            # estado de contenedores
svc stats datasql         # CPU y RAM en tiempo real
svc logs datasql          # logs de todos los servicios
svc logs datasql postgres # logs solo de postgres

svc stop datasql
svc start datasql
svc restart datasql
svc update datasql        # pull de imágenes + recrear
svc backup datasql        # backup de volúmenes
```

Inspeccionar la red mediante la interfaz del NAS:

```bash
svc net
```

---

## Fase 10 — Expansión IoT

Cuando agregues Home Assistant, Node-RED, EMQX, etc., verifica el inventario
con `svc net`. Si falta una red externa en una instalación nueva, usa el
procedimiento de bootstrap de networking; no la borres ni la recrees durante
la migración de DataSQL.

En el `compose.yml` de cada servicio IoT que necesite DB:

```yaml
networks:
  - iot_net
  - db_net

networks:
  iot_net:
    external: true
  db_net:
    external: true
```

### Crear usuario y DB al instalar cada servicio

Usar siempre la **Fase 5A**. No copiar una variante que ejecute
`CREATE USER`/`CREATE ROLE` y `CREATE DATABASE` en la misma sesión o llamada.
El patrón mantiene un usuario y una base dedicados por aplicación.

| Servicio | Estado actual | DB | Cómo se configura |
|----------|---------------|----|-------------------|
| Home Assistant | Activo/documentado | `homeassistant_db` | `configuration.yaml` → `recorder:` |
| Flowise | Activo/documentado | `flowise_db` | `DATABASE_TYPE=postgres`, `DATABASE_HOST=datapostgres` |
| n8n | Base existente; compose pendiente de auditar | `n8n_db` | Confirmar variables `DB_*` en el compose real |
| Node-RED | No usa DB externa en el catálogo | — | Solo si se instala/configura un nodo PostgreSQL |
| EMQX | No usa PostgreSQL para su estado | — | `emqx_db` sería una integración opcional, no su base interna |
| LobeHub | No instalado | futura `lobehub_db` | Requiere una imagen PostgreSQL compatible con vector/RAG |
| Agente/Hermes | No conectado a DataSQL | futura `nas_agent_db` | Requiere implementar un backend de memoria explícito |

Las bases “sugeridas” para Node-RED, EMQX, LobeHub o el agente no deben
crearse por adelantado sin una aplicación que las utilice. La tabla distingue
la arquitectura posible de las conexiones confirmadas.

### PostgreSQL con `pgvector` y `pg_search`

#### NAS actual

El DataSQL actual usa `postgres:16-alpine` y el inventario comprobó que
`vector` y `pg_search` no están disponibles. No cambiar la imagen de DataSQL
mientras Flowise, Home Assistant y n8n dependan de ella: una actualización de
imagen implica reinicio, pruebas de compatibilidad y un plan de recuperación,
aunque las extensiones solo se habiliten en una base concreta.

La opción segura es mantener:

```text
DataSQL existente
├── Flowise → flowise_db
├── Home Assistant → homeassistant_db
├── n8n → n8n_db (confirmar configuración)
└── otros consumidores actuales

PostgreSQL IA separado
├── LobeHub → lobehub_db
└── agente/Hermes futuro → nas_agent_db
```

El PostgreSQL IA debe conectarse a `db_net`, no publicar `5432`, y usar un rol
por aplicación. No se debe crear ni habilitar `CREATE EXTENSION` en las bases
de Home Assistant, Flowise o n8n desde ese servicio separado.

#### Servidor nuevo sin datos

Si el servidor se instala desde cero y el objetivo es dejarlo preparado para
LobeHub, Hermes o un agente propio, es razonable usar **un único clúster
PostgreSQL compatible con ambas extensiones** desde el principio:

```text
DataSQL compatible
├── PostgreSQL + pgvector + pg_search
├── flowise_db
├── homeassistant_db
├── n8n_db
├── lobehub_db (solo si se instala)
└── nas_agent_db (solo si se implementa)
```

Las extensiones se instalan/disponibilizan a nivel de la imagen/clúster, pero
se habilitan por base con `CREATE EXTENSION` únicamente cuando una aplicación
las necesita. Home Assistant puede usar el mismo PostgreSQL normalmente sin
usar esas extensiones.

Esta opción consume menos recursos que mantener dos servidores PostgreSQL: un
solo proceso, un solo buffer pool y una sola rutina de backup. Sin embargo,
una imagen especializada puede tener más requisitos de compatibilidad y el
trabajo vectorial/RAG puede competir por CPU, RAM, I/O y almacenamiento con el
Recorder de Home Assistant. Por eso requiere límites, backups y pruebas de
carga antes de considerarse producción.

#### ¿Conviene instalarlo si todavía no se decidió LobeHub o Hermes?

- Si el servidor es nuevo y ya se decidió que será una plataforma de IA,
  **sí**: preparar el clúster compatible desde el inicio evita migrar después.
  No hace falta crear todavía `lobehub_db`, `nas_agent_db` ni índices.
- Si aún no se sabe si habrá LobeHub, Hermes o un agente con memoria semántica,
  no hay beneficio operativo inmediato en añadir una imagen especializada.
  Mantener PostgreSQL estándar reduce complejidad hasta que exista el primer
  consumidor real.
- La decisión de tener el clúster listo no obliga a instalar ningún agente.
  Bash, Hermes, un agente Python o LobeHub podrían usarlo más adelante mediante
  sus propios roles y bases.

La separación no protege a Home Assistant de todos los problemas: evita que
una migración de imagen del DataSQL actual lo afecte, pero duplica el consumo
base de PostgreSQL y el trabajo de backup. La decisión depende de si se prioriza
compatibilidad aislada hoy o simplicidad de recursos en un servidor nuevo.

### Aplicaciones en otro compose

Si la aplicación vive en un compose separado (por ejemplo, Flowise en
`$dkco/flowise/`), comparte `db_net` con DataSQL, pero **no** uses `depends_on`
contra `datapostgres`: `depends_on` solo controla servicios definidos en el
mismo compose. Verifica primero `svc health` y configura el host como
`datapostgres`.

El compose del consumidor debe incluir:

```yaml
env_file:
  - ../.env
  - .env
networks:
  db_net:
    external: true
```

No publicar `5432` ni `6379`, no usar IPs internas fijas y no crear otro Redis
si el consumidor puede usar `dataredis`.

---

## Resumen de Seguridad

| Aspecto | Medida aplicada |
|---------|-----------------|
| Contraseñas | `openssl rand -base64 32` |
| `.env` | Permisos `600`, nunca dentro de la imagen |
| Puerto pgAdmin | `5050:80` — acceso LAN directo sin túnel SSH |
| Redis | `requirepass` obligatorio |
| PostgreSQL | `scram-sha-256` reemplaza MD5 obsoleto |
| Capacidades Linux | `cap_drop: ALL` + mínimas necesarias (excepto pgAdmin) |
| Límites de recursos | CPU y memoria acotados por contenedor |
| Datos en disco | Permisos `700` en carpetas sensibles |
| Backups | Automáticos diarios, retención 7 días, comprimidos |
| Redes | Separación lógica `db_net` / `iot_net` |
