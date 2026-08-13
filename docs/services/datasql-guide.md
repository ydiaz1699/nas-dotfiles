# Stack DataSQL — Guía Completa para NAS Debian

> PostgreSQL · pgAdmin · Redis · Red aislada `db_net` · Datos en `$dkco/datasql`

---

## Fase 1 — Estructura de Directorios

Crear toda la estructura de una sola vez:

```bash
mkdir -p $dkco/datasql/data/{postgres/{pgdata,backups},pgadmin,redis}
```

Aplicar permisos restrictivos:

```bash
chmod 700 $dkco/datasql/data/postgres/pgdata
chmod 700 $dkco/datasql/data/postgres/backups
chmod 700 $dkco/datasql/data/redis
chmod 700 $dkco/datasql/data/pgadmin
```

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
POSTGRES_DB=appdb
POSTGRES_USER=admin
POSTGRES_PASSWORD=cambia_esto_por_algo_seguro_32chars

# === pgAdmin ===
PGADMIN_EMAIL=admin@local.lan
PGADMIN_PASSWORD=cambia_esto_por_algo_seguro

# === Redis ===
REDIS_PASSWORD=cambia_esto_por_algo_seguro

# === Zona horaria ===
TZ=America/La_Paz
```

Proteger el archivo:

```bash
chmod 600 .env
```

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
    env_file: .env
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      PGDATA: /var/lib/postgresql/data/pgdata
      TZ: ${TZ}
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
    env_file: .env
    environment:
      PGADMIN_DEFAULT_EMAIL: ${PGADMIN_EMAIL}
      PGADMIN_DEFAULT_PASSWORD: ${PGADMIN_PASSWORD}
      PGADMIN_CONFIG_SERVER_MODE: "True"
      PGADMIN_CONFIG_MASTER_PASSWORD_REQUIRED: "False"
    volumes:
      - ./data/pgadmin:/var/lib/pgadmin
    ports:
      - "5050:80"
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

## Fase 6 — Verificación

### PostgreSQL

```bash
svc exec datasql postgres psql -U admin -d appdb
```

Dentro del cliente:

```sql
SELECT version();

CREATE TABLE test (id SERIAL PRIMARY KEY, val TEXT);
INSERT INTO test (val) VALUES ('ok');
SELECT * FROM test;
DROP TABLE test;

\q
```

### pgAdmin

Acceder desde Windows directamente (sin túnel SSH):

```
http://192.168.0.200:5050
```

Credenciales: las del `.env` (`PGADMIN_EMAIL` / `PGADMIN_PASSWORD`).

Agregar servidor en pgAdmin:

| Campo | Valor |
|-------|-------|
| Name | PostgreSQL |
| Host | `postgres` |
| Port | `5432` |
| Username | `admin` |
| Password | `<POSTGRES_PASSWORD>` |

> El hostname `postgres` funciona porque ambos contenedores comparten `db_net`.

### Redis

```bash
svc exec datasql redis redis-cli -a "$REDIS_PASSWORD"
```

```
PING   → PONG
SET k hola
GET k  → "hola"
DEL k
```

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

**Síntoma:** `http://192.168.0.200:5050` no respondía desde Windows.

**Causa:** el puerto estaba configurado como `127.0.0.1:5050:80`, restringiéndolo únicamente a localhost del NAS.

**Solución:** cambiar el binding en `compose.yml`:

```yaml
ports:
  - "5050:80"    # antes: "127.0.0.1:5050:80"
```

Esto expone pgAdmin a toda la LAN. Acceso directo desde cualquier dispositivo en `192.168.0.x` sin túnel SSH.

---

## Fase 8 — Script de Backup

```bash
nano $dkco/datasql/backup.sh
```

```bash
#!/bin/bash
set -euo pipefail

BASE="$dkco/datasql"
source "$BASE/.env"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP="$BASE/data/postgres/backups/appdb_${TIMESTAMP}.sql"
LOG="$BASE/data/postgres/backups/backup.log"
RETENTION=7

echo "[$(date)] Iniciando backup..." >> "$LOG"

docker exec datapostgres \
  pg_dump -U "${POSTGRES_USER}" "${POSTGRES_DB}" > "$BACKUP"

gzip "$BACKUP"
echo "[$(date)] Completado: ${BACKUP}.gz" >> "$LOG"

find "$BASE/data/postgres/backups" -name "*.sql.gz" -mtime +${RETENTION} -delete
echo "[$(date)] Limpieza: retención ${RETENTION} días" >> "$LOG"
```

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
ls -lh $dkco/datasql/data/postgres/backups/*.sql.gz

# Restaurar
gunzip -c /ruta/al/backup.sql.gz | \
  docker exec -i datapostgres psql -U admin -d appdb
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

```bash
svc exec datasql postgres psql -U admin
```

```sql
-- Ejemplo para Home Assistant (repetir el patrón para cada servicio)
CREATE USER ha_user WITH PASSWORD 'password_definitivo';
CREATE DATABASE homeassistant_db OWNER ha_user;
\q
```

| Servicio | DB sugerida | Cómo se configura |
|----------|-------------|-------------------|
| Home Assistant | `homeassistant_db` | `configuration.yaml` → `recorder:` |
| Node-RED | `nodered_db` | Nodo postgresql en la UI |
| EMQX | `emqx_db` | Dashboard → Data Integration |
| n8n | `n8n_db` | Variables de entorno en `compose.yml` |

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
