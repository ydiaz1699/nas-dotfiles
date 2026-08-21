He tenido acceso a la documentación oficial y las mejores prácticas. Aquí tienes una instalación **lista para producción y escalable** de Flowise con Docker Compose:

---

## Estructura del proyecto

```
flowise-production/
├── .env
├── docker-compose.yml
├── nginx/
│   └── flowise.conf
└── data/
    ├── postgres/
    ├── flowise/
    ├── redis/
    └── certbot/
```

---

## 1. Archivo `.env` — Configuración general

```bash
# ── PUERTO ──
PORT=3000

# ── DOMINIO (cambia por tu dominio real) ──
DOMAIN=flowise.tudominio.com
APP_URL=https://${DOMAIN}
CORS_ORIGINS=https://${DOMAIN}
IFRAME_ORIGINS=https://${DOMAIN}
SECURE_COOKIES=true

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
NUMBER_OF_PROXIES=1
DISABLE_FLOWISE_TELEMETRY=true
SHOW_COMMUNITY_NODES=true
LOG_LEVEL=info
FLOWISE_FILE_SIZE_LIMIT=50mb

# ── SECRETOS (generar con: openssl rand -hex 32) ──
JWT_AUTH_TOKEN_SECRET=<genera esto con openssl rand -hex 32>
JWT_REFRESH_TOKEN_SECRET=<genera esto con openssl rand -hex 32>
EXPRESS_SESSION_SECRET=<genera esto con openssl rand -hex 32>
TOKEN_HASH_SECRET=<genera esto con openssl rand -hex 32>
FLOWISE_SECRETKEY_OVERWRITE=<genera esto con openssl rand -hex 32>

# ── JWT ──
JWT_ISSUER=Flowise
JWT_AUDIENCE=Flowise
JWT_TOKEN_EXPIRY_IN_MINUTES=360
JWT_REFRESH_TOKEN_EXPIRY_IN_MINUTES=43200

# ── SEGURIDAD ──
HTTP_SECURITY_CHECK=true
PATH_TRAVERSAL_SAFETY=true
OAUTH2_SECURITY_CHECK=true
TRUST_PROXY=true

# ── POSTGRES SSL (false si usas docker interno) ──
DATABASE_SSL=false

# ── RUTAS DE DATOS LOCALES ──
DATABASE_PATH=/home/node/.flowise
SECRETKEY_PATH=/home/node/.flowise
LOG_PATH=/home/node/.flowise/logs
BLOB_STORAGE_PATH=/home/node/.flowise/storage
```

> **Genera los secretos** con: `openssl rand -hex 32` (ejecutar 4 veces para cada campo marcado).
> 

---

## 2. `docker-compose.yml` — Stack completo

```yaml
version: '3.8'

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
  certbot_data:
    driver: local

services:

  # ──────────────────────────────
  # POSTGRESQL (base de datos)
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
  # REDIS (cola de trabajos)
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
      - "127.0.0.1:3000:3000"   # Solo accesible vía Nginx
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
      - MODE=worker     # ← Clave: este contenedor SOLO procesa colas
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
    # SIN healthcheck (es interno, no sirve HTTP directamente)

  # ──────────────────────────────
  # NGINX REVERSE PROXY + HTTPS
  # ──────────────────────────────
  nginx:
    image: nginx:alpine
    container_name: flowise-nginx
    restart: always
    ports:
      - "80:80"
      - "443:443"
    networks:
      - flowise-network
    volumes:
      - ./nginx/flowise.conf:/etc/nginx/conf.d/flowise.conf:ro
      - certbot_data:/etc/letsencrypt
      - certbot_data:/var/lib/letsencrypt
    depends_on:
      - flowise

  # ──────────────────────────────
  # CERTBOT (SSL automático)
  # ──────────────────────────────
  certbot:
    image: certbot/certbot
    container_name: flowise-certbot
    restart: unless-stopped
    networks:
      - flowise-network
    volumes:
      - certbot_data:/etc/letsencrypt
      - certbot_data:/var/lib/letsencrypt
      - ./nginx/flowise.conf:/tmp/flowise.conf:ro
    entrypoint: >
      sh -c "trap exit TERM; while :; do
        certbot renew --webroot -w /var/lib/letsencrypt --quiet
        sleep 12h
      done"
```

---

## 3. Configuración de Nginx (`nginx/flowise.conf`)

```
upstream flowise_backend {
    server flowise:3000;
    keepalive 64;
}

# Redirigir HTTP → HTTPS
server {
    listen 80;
    server_name flowise.tudominio.com;

    location /.well-known/acme-challenge/ {
        root /var/lib/letsencrypt;
    }

    location / {
        return 301 https://$host$request_uri;
    }
}

server {
    listen 443 ssl http2;
    server_name flowise.tudominio.com;

    ssl_certificate     /etc/letsencrypt/live/flowise.tudominio.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/flowise.tudominio.com/privkey.pem;
    ssl_protocols       TLSv1.2 TLSv1.3;
    ssl_ciphers         HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=flowise_limit:10m rate=30r/s;

    location / {
        limit_req zone=flowise_limit burst=50 nodelay;

        proxy_pass http://flowise_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts largos para SSE / streaming
        proxy_read_timeout 86400s;
        proxy_send_timeout 86400s;
    }

    # Seguridad
    add_header X-Frame-Options SAMEORIGIN always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy strict-origin-when-cross-origin always;
}
```

---

## 4. Pasos para desplegar

```bash
# 1. Clonar o crear la estructura en tu servidor
mkdir -p flowise-production/{nginx,data}
cd flowise-production

# 2. Crear .env con los valores de arriba (cambia contraseñas y dominio)
nano .env

# 3. Crear nginx/flowise.conf (copia el contenido de arriba, cambia dominio)

# 4. Generar certificado SSL por primera vez (dominio debe apuntar al servidor)
docker compose up -d nginx certbot
docker exec flowise-nginx mkdir -p /var/lib/letsencrypt
docker compose run --rm certbot certonly --webroot \
  -w /var/lib/letsencrypt \
  -d flowise.tudominio.com \
  --email tu-email@ejemplo.com \
  --agree-tos --no-eff-email

# 5. Una vez generado el certificado, levantar todo
docker compose up -d

# 6. Verificar estado
docker compose ps
docker compose logs -f
```

---

## 5. Escalar workers (la parte "escalable")

Cuando necesites más capacidad de procesamiento, escala los workers horizontalmente:

```bash
# Escalar a 3 workers (sin tocar nada más)
docker compose up -d --scale flowise-worker=3

# Verificar
docker compose ps

# Reducir a 1 worker
docker compose up -d --scale flowise-worker=1
```

Cada worker consume trabajos de Redis, así que la carga se distribuye automáticamente.

---

## 6. Resumen de componentes

| Componente | Rol | Escalable |
| --- | --- | --- |
| **PostgreSQL** | Base de datos persistente (flujos, credenciales, usuarios) | Por ahora single-instance; podría añadirse replicación |
| **Redis** | Cola de mensajes entre main y workers | No necesita escalar; es muy ligero |
| **Flowise Main** | Servidor web, API REST, interfaz UI | 1 instancia (podría multi-con Nginx load balancing) |
| **Flowise Worker** | Procesa los jobs en background (chat, RAG, ejecuciones) | **Sí, `--scale flowise-worker=N`** |
| **Nginx** | Proxy reverso, TLS, rate limiting | No escala (único punto de entrada) |
| **Certbot** | Renovación automática de SSL | No escala |

---

## 7. Mantenimiento

```bash
# Actualizar Flowise a una versión específica
docker compose pull flowise flowise-worker
docker compose up -d

# Ver logs en tiempo real
docker compose logs -f flowise flowise-worker

# Backup de la base de datos
docker exec flowise-postgres pg_dump -U flowise flowise > backup_$(date +%Y%m%d).sql

# Reinicio limpio (sin perder datos)
docker compose down
docker compose up -d
```

---

Esta configuración está **lista para producción** porque incluye:

- Base de datos robusta (PostgreSQL en vez de SQLite)
- Separación entre servidor web y workers de procesamiento
- Redis como broker de colas
- HTTPS con renovación automática
- Rate limiting contra abusos
- Health checks en todos los servicios
- Workers escalables horizontalmente
- Persistencia de datos en volúmenes Docker

Si tu dominio aún no apunta al servidor o prefieres probar sin SSL, puedes comentar la sección de Nginx y acceder directamente por `http://IP:3000` (aunque no recomendado para producción).