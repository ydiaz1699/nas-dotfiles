# Stack DataSQL — Guía Completa para NAS Debian

> PostgreSQL · pgAdmin · Redis · Red aislada `db_net` · Datos en `$dkco/datasql`

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

Crear la red una sola vez:

```bash
docker network create db_net
```

Verificar:

```bash
dnet | grep db_net
```

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
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      PGDATA: /var/lib/postgresql/data/pgdata
      # TZ se hereda de ../.env; no duplicar en environment
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

**Síntoma:** `docker compose config` devolvía error de parsing YAML.

**Causa:** al editar con `nano`, la línea `pgadmin:` quedó sin los 2 espacios de sangría requeridos.

**Solución:** verificar antes de levantar:

```bash
docker compose config --quiet && echo "OK"
```

Si no dice `OK`, abrir `nano` y asegurarse de que `postgres:`, `pgadmin:` y `redis:` tengan exactamente 2 espacios de indentación.

---

### Error 3: Permisos incorrectos en carpeta `pgadmin`

**Síntoma:** el contenedor arrancaba pero pgAdmin mostraba errores de permisos en los logs.

**Causa:** la carpeta `/docker/datasql/data/pgadmin` fue creada por `root`, pero el contenedor corre como usuario `pgadmin` (uid `5050`).

**Solución:**

```bash
chown -R 5050:5050 /docker/datasql/data/pgadmin
svc restart datasql
```

---

### Error 4: Datos corruptos en `pgadmin`

**Síntoma:** pgAdmin no iniciaba; la carpeta `data/pgadmin` contenía múltiples archivos `pgadmin4.db.XXXXXXXXXX` (backups de intentos fallidos).

**Causa:** intentos previos fallidos dejaron la base de datos SQLite de pgAdmin en estado inconsistente.

**Solución:** borrar todo y dejar que pgAdmin recree desde cero:

```bash
docker rm -f datapgadmin
rm -rf /docker/datasql/data/pgadmin
mkdir -p /docker/datasql/data/pgadmin
chown -R 5050:5050 /docker/datasql/data/pgadmin
svc up datasql
sleep 15 && docker logs datapgadmin 2>&1 | tail -10
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

Inspeccionar la red:

```bash
docker network inspect db_net
```

---

## Fase 10 — Expansión IoT

Cuando agregues Home Assistant, Node-RED, EMQX, etc.:

```bash
docker network create iot_net
```

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

| Servicio | DB sugerida | Cómo se configura |
|----------|-------------|-------------------|
| Home Assistant | `homeassistant_db` | `configuration.yaml` → `recorder:` |
| Node-RED | `nodered_db` | Nodo postgresql en la UI |
| EMQX | `emqx_db` | Dashboard → Data Integration |
| n8n | `n8n_db` | Variables de entorno en `compose.yml` |
| Flowise | `flowise_db` | `DATABASE_TYPE=postgres`, `DATABASE_HOST=datapostgres`, `DATABASE_NAME=flowise_db`, usuario y contraseña dedicados |

### Aplicaciones en otro compose

Si la aplicación vive en un compose separado (por ejemplo, Flowise en
`$dkco/flowise/`), comparte `db_net` con DataSQL, pero **no** uses `depends_on` contra `datapostgres`: `depends_on` solo controla
servicios definidos en el mismo compose. Verifica primero `svc health` y configura el host como `datapostgres`.
El compose de la aplicación debe incluir `env_file: [../.env, .env]`,
`extends.file: ../_common.yml` y sus labels `homepage.*`.

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
