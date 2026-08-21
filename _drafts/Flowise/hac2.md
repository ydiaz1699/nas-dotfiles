Perfecto, eliminamos Nginx y Certbot. Te dejo el stack **PostgreSQL + Redis + Flowise Main + Workers**, directamente accesible por puerto. Escalable y listo para producción igualmente.

---

## Estructura del proyecto

```
flowise-production/
├── .env
├── docker-compose.yml
└── data/
    ├── postgres/
    ├── flowise/
    └── redis/
```

---

## 1. `.env` — Configuración (sin Nginx)

```bash
# ── PUERTO ──
PORT=3000

# ── URL (cambia por la IP o dominio si lo tienes) ──
APP_URL=http://localhost:3000
CORS_ORIGINS=*
IFRAME_ORIGINS=*
SECURE_COOKIES=false

# ── POSTGRESQL ──
DATABASE_TYPE=postgres
DATABASE_HOST=postgres
DATABASE_PORT=5432
DATABASE_NAME=flowise
DATABASE_USER=flowise
DATABASE_PASSWORD=ChangeMe_Postgres_StrongPass

# ── REDIS ──
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=ChangeMe_Redis_StrongPass

# ── FLOWISE MODO PRODUCCIÓN ──
MODE=queue
QUEUE_NAME=flowise-queue
WORKER_CONCURRENCY=100000
NUMBER_OF_PROXIES=0
DISABLE_FLOWISE_TELEMETRY=true
SHOW_COMMUNITY_NODES=true
LOG_LEVEL=info
FLOWISE_FILE_SIZE_LIMIT=50mb

# ── SECRETOS (generar con: openssl rand -hex 32) ──
JWT_AUTH_TOKEN_SECRET=<openssl rand -hex 32>
JWT_REFRESH_TOKEN_SECRET=<openssl rand -hex 32>
EXPRESS_SESSION_SECRET=<openssl rand -hex 32>
TOKEN_HASH_SECRET=<openssl rand -hex 32>
FLOWISE_SECRETKEY_OVERWRITE=<openssl rand -hex 32>

# ── JWT ──
JWT_ISSUER=Flowise
JWT_AUDIENCE=Flowise
JWT_TOKEN_EXPIRY_IN_MINUTES=360
JWT_REFRESH_TOKEN_EXPIRY_IN_MINUTES=43200

# ── SEGURIDAD ──
HTTP_SECURITY_CHECK=true
PATH_TRAVERSAL_SAFETY=true
OAUTH2_SECURITY_CHECK=true
TRUST_PROXY=false
DATABASE_SSL=false

# ── RUTAS DE DATOS ──
DATABASE_PATH=/home/node/.flowise
SECRETKEY_PATH=/home/node/.flowise
LOG_PATH=/home/node/.flowise/logs
BLOB_STORAGE_PATH=/home/node/.flowise/storage
```

> **Genera los secretos:** ejecuta 5 veces `openssl rand -hex 32` y asigna cada resultado a los campos marcados.
> 

---

## 2. `docker-compose.yml` — Solo Flowise + PostgreSQL + Redis

```yaml
networks:
  flowise-network:
    driver: bridge

volumes:
  postgres_data:
    driver: local
  redis_data:
    driver: local
  flowise_data:
    driver: local

services:

  # ──────────────────────────────
  # POSTGRESQL
  # ──────────────────────────────
  postgres:
    image: postgres:16-alpine
    container_name: flowise-postgres
    restart: always
    networks:
      - flowise-network
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      POSTGRES_USER: ${DATABASE_USER}
      POSTGRES_PASSWORD: ${DATABASE_PASSWORD}
      POSTGRES_DB: ${DATABASE_NAME}
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DATABASE_USER} -d ${DATABASE_NAME}"]
      interval: 10s
      timeout: 5s
      retries: 5

  # ──────────────────────────────
  # REDIS
  # ──────────────────────────────
  redis:
    image: redis:7-alpine
    container_name: flowise-redis
    restart: always
    command: >
      redis-server --requirepass ${REDIS_PASSWORD}
                   --appendonly yes
    networks:
      - flowise-network
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "--raw", "incr", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # ──────────────────────────────
  # FLOWISE MAIN (servidor web + API)
  # ──────────────────────────────
  flowise:
    image: flowiseai/flowise:latest
    container_name: flowise-main
    restart: always
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - flowise-network
    ports:
      - "3000:3000"
    volumes:
      - flowise_data:/home/node/.flowise
    environment:
      - PORT=${PORT}
      - DATABASE_TYPE=${DATABASE_TYPE}
      - DATABASE_HOST=${DATABASE_HOST}
      - DATABASE_PORT=${DATABASE_PORT}
      - DATABASE_NAME=${DATABASE_NAME}
      - DATABASE_USER=${DATABASE_USER}
      - DATABASE_PASSWORD=${DATABASE_PASSWORD}
      - DATABASE_SSL=${DATABASE_SSL}
      - SECRETKEY_PATH=${SECRETKEY_PATH}
      - LOG_PATH=${LOG_PATH}
      - LOG_LEVEL=${LOG_LEVEL}
      - BLOB_STORAGE_PATH=${BLOB_STORAGE_PATH}
      - MODE=${MODE}
      - QUEUE_NAME=${QUEUE_NAME}
      - WORKER_CONCURRENCY=${WORKER_CONCURRENCY}
      - REDIS_HOST=${REDIS_HOST}
      - REDIS_PORT=${REDIS_PORT}
      - REDIS_PASSWORD=${REDIS_PASSWORD}
      - APP_URL=${APP_URL}
      - CORS_ORIGINS=${CORS_ORIGINS}
      - IFRAME_ORIGINS=${IFRAME_ORIGINS}
      - DISABLE_FLOWISE_TELEMETRY=${DISABLE_FLOWISE_TELEMETRY}
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
      - HTTP_SECURITY_CHECK=${HTTP_SECURITY_CHECK}
      - PATH_TRAVERSAL_SAFETY=${PATH_TRAVERSAL_SAFETY}
      - OAUTH2_SECURITY_CHECK=${OAUTH2_SECURITY_CHECK}
      - TRUST_PROXY=${TRUST_PROXY}
      - SECURE_COOKIES=${SECURE_COOKIES}
    healthcheck:
      test: ["CMD", "curl", "-f", "<http://localhost>:${PORT}/api/v1/ping"]
      interval: 15s
      timeout: 5s
      retries: 5
      start_period: 40s

  # ──────────────────────────────
  # FLOWISE WORKER (escalable)
  # ──────────────────────────────
  flowise-worker:
    image: flowiseai/flowise:latest
    container_name: flowise-worker
    restart: always
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      flowise:
        condition: service_started
    networks:
      - flowise-network
    volumes:
      - flowise_data:/home/node/.flowise
    environment:
      - PORT=${PORT}
      - DATABASE_TYPE=${DATABASE_TYPE}
      - DATABASE_HOST=${DATABASE_HOST}
      - DATABASE_PORT=${DATABASE_PORT}
      - DATABASE_NAME=${DATABASE_NAME}
      - DATABASE_USER=${DATABASE_USER}
      - DATABASE_PASSWORD=${DATABASE_PASSWORD}
      - DATABASE_SSL=${DATABASE_SSL}
      - SECRETKEY_PATH=${SECRETKEY_PATH}
      - LOG_PATH=${LOG_PATH}
      - LOG_LEVEL=${LOG_LEVEL}
      - BLOB_STORAGE_PATH=${BLOB_STORAGE_PATH}
      - MODE=worker
      - QUEUE_NAME=${QUEUE_NAME}
      - WORKER_CONCURRENCY=${WORKER_CONCURRENCY}
      - REDIS_HOST=${REDIS_HOST}
      - REDIS_PORT=${REDIS_PORT}
      - REDIS_PASSWORD=${REDIS_PASSWORD}
      - APP_URL=${APP_URL}
      - DISABLE_FLOWISE_TELEMETRY=${DISABLE_FLOWISE_TELEMETRY}
      - SHOW_COMMUNITY_NODES=${SHOW_COMMUNITY_NODES}
      - FLOWISE_FILE_SIZE_LIMIT=${FLOWISE_FILE_SIZE_LIMIT}
      - JWT_AUTH_TOKEN_SECRET=${JWT_AUTH_TOKEN_SECRET}
      - JWT_REFRESH_TOKEN_SECRET=${JWT_REFRESH_TOKEN_SECRET}
      - EXPRESS_SESSION_SECRET=${EXPRESS_SESSION_SECRET}
      - TOKEN_HASH_SECRET=${TOKEN_HASH_SECRET}
      - FLOWISE_SECRETKEY_OVERWRITE=${FLOWISE_SECRETKEY_OVERWRITE}
      - HTTP_SECURITY_CHECK=${HTTP_SECURITY_CHECK}
      - PATH_TRAVERSAL_SAFETY=${PATH_TRAVERSAL_SAFETY}
```

---

## 3. Despliegue

```bash
# 1. Crear carpeta y archivos
mkdir -p flowise-production
cd flowise-production

# 2. Crear .env con el contenido de arriba
nano .env

# 3. Crear docker-compose.yml con el contenido de arriba
nano docker-compose.yml

# 4. Levantar todo
docker compose up -d

# 5. Verificar que todo está corriendo
docker compose ps

# 6. Ver logs
docker compose logs -f

# 7. Abrir en el navegador
# <http://localhost:3000>   (o <http://IP-DEL-SERVIDOR:3000>)
```

---

## 4. Escalar workers

```bash
# Escalar a 3 workers
docker compose up -d --scale flowise-worker=3

# Reducir a 1
docker compose up -d --scale flowise-worker=1
```

---

## 5. Comandos útiles

```bash
# Detener sin perder datos
docker compose down

# Volver a levantar
docker compose up -d

# Ver logs de un servicio específico
docker compose logs -f flowise-worker

# Backup de PostgreSQL
docker exec flowise-postgres pg_dump -U flowise flowise > backup_$(date +%Y%m%d).sql

# Actualizar Flowise (primero prueba en staging)
docker compose pull flowise flowise-worker
docker compose up -d
```

---

**¿Qué obtienes con esta configuración?**

- **PostgreSQL** — base de datos relacional robusta en vez de SQLite
- **Redis** — cola de trabajos para procesar chats, RAG y tareas asíncronas
- **Flowise Main** — interfaz web + API REST
- **Flowise Worker** — procesamiento en background, **escalable horizontalmente** con `-scale`
- **Health checks** en todos los servicios
- **Persistencia** de datos en volúmenes Docker
- **Listo para producción** — cuando quieras agregar Nginx y HTTPS solo añades los servicios, sin tocar Flowise

Cuando más adelante quieras añadir Nginx + HTTPS, avísame y te paso la configuración para agregarlo sin romper nada.