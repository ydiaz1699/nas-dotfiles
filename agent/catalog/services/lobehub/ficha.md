---
id: "lobehub"
name: "LobeHub"
description: "LobeHub server/database version con PostgreSQL y Redis de DataSQL y RustFS S3"
aliases:
  - lobehub
  - lobe
  - lobechat
  - ai-chat
  - agentes-ia
image: "lobehub/lobehub:2.2.14"
category: "desarrollo"
port_internal: 3210
port_default: 3210
protocol: "http"
needs_proxy: false
needs_db: true
db_type: "postgres"
needs_redis: true
needs_s3: true
volumes:
  - "./data/rustfs:/data (RustFS)"
env_required:
  - SERVER_IP
  - LOBE_DB_PASSWORD
  - KEY_VAULTS_SECRET
  - AUTH_SECRET
  - JWKS_KEY
  - AUTH_ALLOWED_EMAILS
  - REDIS_PASSWORD
  - RUSTFS_SECRET_KEY
env_optional:
  - AUTH_DISABLE_EMAIL_PASSWORD
  - S3_REGION
  - SEARXNG_URL
healthcheck: '["CMD", "/bin/node", "-e", "fetch(\u0027http://127.0.0.1:3210\u0027).then(r => process.exit(r.status < 500 ? 0 : 1)).catch(() => process.exit(1))"]'
backup_critical: true
backup_paths:
  - "./data/rustfs"
  - "$dkco/datasql/data/postgres/backups/lobehub_db_*.sql"
  - "./bucket.config.json"
protected: false
runtime_status: prepared
target_status: pending-runtime-verification
docs_url: "docs/services/lobehub-guide.md"
notes: "Configuración preparada, no evidencia de despliegue runtime. LobeHub 2.2.14 está fijado por tag y digest. Requiere AUTH_ALLOWED_EMAILS no vacío para no dejar el registro abierto en la LAN. Usa lobehub_db/lobehub_user en datapostgres:5432 y dataredis:6379 mediante db_net externa, sin crear PostgreSQL/Redis propios ni repetir n8n_user/n8n_db. RustFS 1.0.0-rc.3 es S3 separado en la red física lobe_storage: el endpoint 9000 se publica en LAN porque el navegador debe resolverlo; la consola 9001 queda en loopback. SearXNG no se incluye porque la búsqueda online es opcional. La política bucket.config.json permite solo GET público de objetos; revisar si la exposición LAN no es adecuada. El healthcheck de LobeHub es local del catálogo: la imagen oficial no publica un endpoint /health, pero su Dockerfile v2.2.14 incluye Node en /bin/node y la aplicación sirve HTTP en 3210. La guía incluye dump lógico PostgreSQL no probado en este entorno. Verificar en NAS antes de afirmar que funciona."
networks:
  - db_net
  - lobe_storage
ports:
  http: 3210
  rustfs_s3: 9000
  rustfs_console_loopback: 9001
resources:
  memory_limit: "2g"
  memory_reservation: "512m"
security_extra:
  rustfs_console: "127.0.0.1:9001"
---

# LobeHub

La guía operativa única es `docs/services/lobehub-guide.md`; esta ficha solo
contiene metadatos para descubrimiento y configuración del agente.
