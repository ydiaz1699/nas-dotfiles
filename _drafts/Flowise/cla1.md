Perfecto, Flowise con Postgres (en vez de SQLite) + modo **queue** con Redis es justo lo que lo hace escalable a futuro (podés levantar workers adicionales con `svc scale`). Uso el stack `datasql` ya existente para DB y Redis.

## 1. Crear usuario y DB en PostgreSQL

```bash
PGPASS=$(grep ^POSTGRES_PASSWORD $dkco/datasql/.env | cut -d= -f2-)
docker exec -it datapostgres bash -c "PGPASSWORD='$PGPASS' psql -U admin -d appdb"
```

```sql
CREATE USER flowise_user WITH PASSWORD '<password_seguro>';
CREATE DATABASE flowise_db OWNER flowise_user;
\q
```

> Generar password: `openssl rand -base64 32`
> 

## 2. Árbol de directorios

```
/docker/flowise/
├── compose.yml
├── .env
└── data/
    └── secrets/
```

```bash
mkdir -p $dkco/flowise/data/secrets
touch $dkco/flowise/.env
chmod 600 $dkco/flowise/.env
```

## 3. `.env`

```bash
# $dkco/flowise/.env  (permisos 600)
DB_PASSWORD=<password_seguro_generado_arriba>
REDIS_PASSWORD=<mismo_valor_que_dataredis_en_datasql/.env>
FLOWISE_USERNAME=admin
FLOWISE_PASSWORD=<password_admin_seguro>
FLOWISE_SECRETKEY_OVERWRITE=<openssl rand -hex 24>
```

## 4. `compose.yml`

Diseño: 1 contenedor **main** (UI + API) + 1 (o más) **worker** para procesar ejecuciones, comunicados por Redis (modo `queue`). Escalar workers a futuro es `svc scale flowise-worker s=3` sin tocar nada más.

```yaml
services:
  flowise:
    image: flowiseai/flowise:latest
    container_name: flowise
    restart: unless-stopped
    command: /bin/sh -c "sleep 3; flowise start"
    ports:
      - "127.0.0.1:3000:3000"
    environment:
      # --- Modo cola: separa UI/API de la ejecución de flujos ---
      MODE: queue
      QUEUE_NAME: flowise-queue
      WORKER_CONCURRENCY: "10"

      # --- Auth panel ---
      FLOWISE_USERNAME: ${FLOWISE_USERNAME}
      FLOWISE_PASSWORD: ${FLOWISE_PASSWORD}
      FLOWISE_SECRETKEY_OVERWRITE: ${FLOWISE_SECRETKEY_OVERWRITE}

      # --- Base de datos: Postgres en vez de SQLite (clave para escalar) ---
      DATABASE_TYPE: postgres
      DATABASE_HOST: datapostgres
      DATABASE_PORT: 5432
      DATABASE_NAME: flowise_db
      DATABASE_USER: flowise_user
      DATABASE_PASSWORD: ${DB_PASSWORD}
      DATABASE_SSL: "false"

      # --- Redis: cola de trabajos + cache ---
      REDIS_HOST: dataredis
      REDIS_PORT: 6379
      REDIS_PASSWORD: ${REDIS_PASSWORD}
      REDIS_USE_ICOMPRESSION: "true"

      # --- Storage local para archivos/uploads ---
      STORAGE_TYPE: local
      BLOB_STORAGE_PATH: /root/.flowise/storage

      # --- Logs ---
      LOG_LEVEL: info

      # --- Secrets file ---
      SECRETKEY_PATH: /root/.flowise/secrets
    volumes:
      - ./data:/root/.flowise
    networks:
      - db_net
    depends_on:
      - datapostgres
    security_opt:
      - no-new-privileges:true
    cap_drop: [ALL]
    healthcheck:
      test: ["CMD", "wget", "-qO-", "http://localhost:3000/api/v1/ping"]
      interval: 30s
      timeout: 10s
      retries: 3

  flowise-worker:
    image: flowiseai/flowise:latest
    container_name: flowise-worker
    restart: unless-stopped
    command: /bin/sh -c "sleep 5; flowise worker"
    environment:
      MODE: queue
      QUEUE_NAME: flowise-queue
      WORKER_CONCURRENCY: "10"

      DATABASE_TYPE: postgres
      DATABASE_HOST: datapostgres
      DATABASE_PORT: 5432
      DATABASE_NAME: flowise_db
      DATABASE_USER: flowise_user
      DATABASE_PASSWORD: ${DB_PASSWORD}
      DATABASE_SSL: "false"

      REDIS_HOST: dataredis
      REDIS_PORT: 6379
      REDIS_PASSWORD: ${REDIS_PASSWORD}
      REDIS_USE_ICOMPRESSION: "true"

      STORAGE_TYPE: local
      BLOB_STORAGE_PATH: /root/.flowise/storage
      SECRETKEY_PATH: /root/.flowise/secrets
    volumes:
      - ./data:/root/.flowise   # comparte storage/secrets con el nodo main
    networks:
      - db_net
    depends_on:
      - flowise
    security_opt:
      - no-new-privileges:true
    cap_drop: [ALL]

networks:
  db_net:
    external: true
```

## 5. Levantar y verificar

```bash
dk flowise
svc config flowise       # valida sintaxis
svc up flowise
svc ps flowise           # main + worker deben estar healthy
svc logs flowise | grep -i "error\|database\|redis"
```

Verificar que la DB quedó bien conectada:

```bash
PGPASS=$(grep ^POSTGRES_PASSWORD $dkco/datasql/.env | cut -d= -f2-)
docker exec -it datapostgres bash -c "PGPASSWORD='$PGPASS' psql -U admin -d appdb -c '\l'" | grep flowise
```

Acceso: `http://127.0.0.1:3000` (queda solo en localhost — si querés exponerlo hacia afuera, decime qué reverse proxy usás, ej. Nginx Proxy Manager / Traefik, y te doy la config).

## Por qué esto es "escalable a futuro"

- **Postgres compartido** en vez de SQLite embebido → múltiples instancias de Flowise pueden leer/escribir la misma DB sin corrupción.
- **Modo `queue` + Redis** → separa la interfaz/API de la ejecución de flujos. Los workers son *stateless* y se pueden multiplicar.
- **Escalar workers** cuando necesites más capacidad de ejecución, sin tocar el nodo principal:
    
    ```bash
    svc scale flowise-worker s=3
    ```
    
- **Volumen compartido `./data`** entre main y workers asegura que todos vean los mismos secrets/storage.

Si más adelante querés multiplicar también el nodo `flowise` (API) detrás de un load balancer, avisame y ajustamos `FLOWISE_SECRETKEY_OVERWRITE` para que sea idéntico en todas las réplicas (obligatorio para que compartan sesión/cifrado).