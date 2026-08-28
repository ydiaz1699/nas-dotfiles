---
id: "n8n"
name: "n8n"
description: "Automatización de workflows con PostgreSQL dedicado en DataSQL"
aliases:
  - n8n
  - workflow
  - workflows
  - automatizacion
  - automatización
  - nodos
image: "n8nio/n8n:2.36.7"
category: "desarrollo"
port_internal: 5678
port_default: 5678
protocol: "http"
needs_proxy: false
needs_db: true
db_type: "postgres"
volumes:
  - "./data:/home/node/.n8n"
env_required:
  - DB_PASSWORD
  - N8N_ENCRYPTION_KEY
env_optional:
  - N8N_SECURE_COOKIE=false
  - WEBHOOK_URL=http://${SERVER_IP}:5678
healthcheck: '["CMD-SHELL", "node -e \\\"fetch(\\\"http://127.0.0.1:5678/healthz\\\").then(r => process.exit(r.ok ? 0 : 1)).catch(() => process.exit(1))\\\""]'
backup_critical: true
backup_paths:
  - "./data"
protected: true
docs_url: "docs/services/n8n-guide.md"
notes: "Runtime confirmado antes del hardening: n8nio/n8n:latest resolvió a 2.23.4; n8n_user autenticó correctamente, n8n_db pertenece a n8n_user, las migraciones terminaron, hubo 0 reinicios observados y /healthz respondió HTTP 200. Esta ficha y su compose representan el objetivo con n8nio/n8n:2.36.7, env_file global/local, healthcheck y db_net externa; la aplicación del objetivo debe verificarse en el NAS antes de tratarlo como estado desplegado. No usar Redis ni depends_on contra DataSQL. El acceso HTTP se publica en LAN; documentar proxy/TLS antes de exponerlo a Internet. La advertencia de Python task runner queda pendiente."
networks:
  - db_net
ports:
  http: 5678
resources:
  memory_limit: "1g"
  memory_reservation: "256m"
security_extra:
  cap_drop:
    - ALL
runtime_status: "confirmed-before-hardening"
target_status: "pending-runtime-verification"
observed_image: "n8nio/n8n:latest"
observed_version: "2.23.4"
---

# n8n

La guía operativa y de continuidad es `docs/services/n8n-guide.md`. Esta ficha
solo contiene metadatos, aliases y el estado confirmado/pendiente para que el
agente pueda localizar el servicio sin duplicar el procedimiento.

## Resumen de arquitectura

- PostgreSQL dedicado `n8n_db` con rol `n8n_user` en `datapostgres:5432`.
- Red externa `db_net`; no se publica PostgreSQL ni Redis desde n8n.
- Persistencia en `./data:/home/node/.n8n`.
- Editor/API en `${SERVER_IP}:5678`.
- Runtime comprobado con n8n `2.23.4`; pin objetivo `2.36.7` pendiente de aplicar.
- No se ha confirmado uso de Redis, queue mode, S3 ni RustFS por parte de n8n.
