Sí, se puede adaptar perfecto — de hecho es mejora neta: te quedás con las variables buenas que trae este (JWT, CORS, seguridad) pero sin duplicar Postgres/Redis. Te dejo la versión adaptada a tu stack `datasql`, con los errores corregidos y el hardening que venís aplicando en todo lo demás.

```yaml
# Flowise — constructor visual de agentes y flujos LLM
# $dkco/flowise/compose.yml
# Reutiliza Postgres y Redis del stack datasql (db_net)

networks:
  db_net:
    external: true

volumes:
  flowise_data:
    driver: local

services:

  # ──────────────────────────────
  # FLOWISE MAIN (servidor web + API)
  # ──────────────────────────────
  flowise:
    image: flowiseai/flowise:latest
    container_name: flowise-main
    restart: unless-stopped
    networks:
      - db_net
    ports:
      - "8100:3000"
    volumes:
      - flowise_data:/home/node/.flowise
    environment:
      - PORT=${PORT}
      - MODE=${MODE}
      - QUEUE_NAME=${QUEUE_NAME}
      - WORKER_CONCURRENCY=${WORKER_CONCURRENCY}

      # --- Postgres compartido (datasql) ---
      - DATABASE_TYPE=postgres
      - DATABASE_HOST=datapostgres
      - DATABASE_PORT=5432
      - DATABASE_NAME=${FLOWISE_DB_NAME}
      - DATABASE_USER=${FLOWISE_DB_USER}
      - DATABASE_PASSWORD=${FLOWISE_DB_PASSWORD}
      - DATABASE_SSL=false

      # --- Redis compartido (datasql) ---
      - REDIS_HOST=dataredis
      - REDIS_PORT=6379
      - REDIS_PASSWORD=${REDIS_PASSWORD}

      - SECRETKEY_PATH=/home/node/.flowise
      - LOG_PATH=/home/node/.flowise/logs
      - LOG_LEVEL=${LOG_LEVEL}
      - BLOB_STORAGE_PATH=/home/node/.flowise/storage

      - APP_URL=${APP_URL}
      - CORS_ORIGINS=${CORS_ORIGINS}
      - IFRAME_ORIGINS=${IFRAME_ORIGINS}
      - DISABLE_FLOWISE_TELEMETRY=true
      - SHOW_COMMUNITY_NODES=${SHOW_COMMUNITY_NODES}
      - FLOWISE_FILE_SIZE_LIMIT=${FLOWISE_FILE_SIZE_LIMIT}
      - NUMBER_OF_PROXIES=${NUMBER_OF_PROXIES}

      - JWT_AUTH_TOKEN_SECRET=${JWT_AUTH_TOKEN_SECRET}
      - JWT_REFRESH_TOKEN_SECRET=${JWT_REFRESH_TOKEN_SECRET}
      - JWT_ISSUER=${JWT_ISSUER}
      - JWT_AUDIENCE=${JWT_AUDIENCE}
      - JWT_TOKEN_EXPIRY_IN_MINUTES=${JWT_TOKEN_EXPIRY_IN_MINUTES}
      - JWT_REFRESH_TOKEN_EXPIRY_IN_MINUTES=${JWT_REFRESH_TOKEN_EXPIRY_IN_MINUTES}
      - EXPRESS_SESSION_SECRET=${EXPRESS_SESSION_SECRET}
      - TOKEN_HASH_SECRET=${TOKEN_HASH_SECRET}
      - FLOWISE_SECRETKEY_OVERWRITE=${FLOWISE_SECRETKEY_OVERWRITE}

      - HTTP_SECURITY_CHECK=true
      - PATH_TRAVERSAL_SAFETY=true
      - OAUTH2_SECURITY_CHECK=true
      - CUSTOM_MCP_SECURITY_CHECK=true
      - TRUST_PROXY=${TRUST_PROXY}
      - SECURE_COOKIES=${SECURE_COOKIES}
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/api/v1/ping"]
      interval: 15s
      timeout: 5s
      retries: 5
      start_period: 40s
    security_opt:
      - no-new-privileges:true
    cap_drop: [ALL]
    labels:
      - homepage.group=IA y Automatización
      - homepage.name=Flowise
      - homepage.icon=flowise
      - homepage.href=http://${SERVER_IP}:8100
      - homepage.description=Constructor visual de agentes y flujos LLM
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 1G
        reservations:
          cpus: '0.25'
          memory: 256M
    entrypoint: /bin/sh -c "sleep 3; flowise start"

  # ──────────────────────────────
  # FLOWISE WORKER (escalable)
  # ──────────────────────────────
  flowise-worker:
    image: flowiseai/flowise:latest
    container_name: flowise-worker
    restart: unless-stopped
    depends_on:
      - flowise
    networks:
      - db_net
    volumes:
      - flowise_data:/home/node/.flowise
    environment:
      - PORT=${PORT}
      - MODE=worker
      - QUEUE_NAME=${QUEUE_NAME}
      - WORKER_CONCURRENCY=${WORKER_CONCURRENCY}

      - DATABASE_TYPE=postgres
      - DATABASE_HOST=datapostgres
      - DATABASE_PORT=5432
      - DATABASE_NAME=${FLOWISE_DB_NAME}
      - DATABASE_USER=${FLOWISE_DB_USER}
      - DATABASE_PASSWORD=${FLOWISE_DB_PASSWORD}
      - DATABASE_SSL=false

      - REDIS_HOST=dataredis
      - REDIS_PORT=6379
      - REDIS_PASSWORD=${REDIS_PASSWORD}

      - SECRETKEY_PATH=/home/node/.flowise
      - LOG_PATH=/home/node/.flowise/logs
      - LOG_LEVEL=${LOG_LEVEL}
      - BLOB_STORAGE_PATH=/home/node/.flowise/storage

      - APP_URL=${APP_URL}
      - DISABLE_FLOWISE_TELEMETRY=true
      - SHOW_COMMUNITY_NODES=${SHOW_COMMUNITY_NODES}
      - FLOWISE_FILE_SIZE_LIMIT=${FLOWISE_FILE_SIZE_LIMIT}

      - JWT_AUTH_TOKEN_SECRET=${JWT_AUTH_TOKEN_SECRET}
      - JWT_REFRESH_TOKEN_SECRET=${JWT_REFRESH_TOKEN_SECRET}
      - EXPRESS_SESSION_SECRET=${EXPRESS_SESSION_SECRET}
      - TOKEN_HASH_SECRET=${TOKEN_HASH_SECRET}
      - FLOWISE_SECRETKEY_OVERWRITE=${FLOWISE_SECRETKEY_OVERWRITE}

      - HTTP_SECURITY_CHECK=true
      - PATH_TRAVERSAL_SAFETY=true
    security_opt:
      - no-new-privileges:true
    cap_drop: [ALL]
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 128M
    entrypoint: /bin/sh -c "sleep 5; flowise worker"
```

### Qué cambié respecto al original que trajiste

- Elimina servicios `postgres` y `redis` propios → usa `datapostgres`/`dataredis` de `datasql` en `db_net`.
- Arreglé el healthcheck roto (`<http://localhost>` → `http://localhost`).
- Agregué `cap_drop: [ALL]` y `no-new-privileges` a ambos servicios.
- Agregué límites de recursos (`deploy.resources`) y labels de `homepage` para mantener consistencia con tu Flowise anterior.
- `flowise_data` sigue siendo volumen nombrado (no bind) porque así viene del original — si preferís bind a `./data` para verlo directo con `ls`, decime y lo cambio.

### `.env` necesario (`$dkco/flowise/.env`)

```bash
PORT=3000
MODE=queue
QUEUE_NAME=flowise-queue
WORKER_CONCURRENCY=5

FLOWISE_DB_NAME=flowise_db
FLOWISE_DB_USER=flowise_user
FLOWISE_DB_PASSWORD=<generado con openssl rand -base64 32>

REDIS_PASSWORD=<mismo valor que $dkco/datasql/.env>

LOG_LEVEL=info
APP_URL=http://<SERVER_IP>:8100
CORS_ORIGINS=*
IFRAME_ORIGINS=*
SHOW_COMMUNITY_NODES=true
FLOWISE_FILE_SIZE_LIMIT=50mb
NUMBER_OF_PROXIES=0
TRUST_PROXY=false
SECURE_COOKIES=false

JWT_AUTH_TOKEN_SECRET=<openssl rand -hex 32>
JWT_REFRESH_TOKEN_SECRET=<openssl rand -hex 32>
JWT_ISSUER=flowise
JWT_AUDIENCE=flowise-users
JWT_TOKEN_EXPIRY_IN_MINUTES=60
JWT_REFRESH_TOKEN_EXPIRY_IN_MINUTES=43200
EXPRESS_SESSION_SECRET=<openssl rand -hex 32>
TOKEN_HASH_SECRET=<openssl rand -hex 32>
FLOWISE_SECRETKEY_OVERWRITE=<openssl rand -hex 24>
```

Con `SERVER_IP` ya definido en tu `../.env` global (como usás en el compose anterior).

¿Querés que te dé los comandos para generar todos esos secrets de una sola pasada y armar el `.env` completo?