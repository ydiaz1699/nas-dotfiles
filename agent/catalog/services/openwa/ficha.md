---
id: "openwa"
name: "OpenWA"
description: "Gateway self-hosted de WhatsApp (API REST + WebSocket + dashboard) con integración oficial a n8n"
aliases:
  - openwa
  - whatsapp
  - wa
  - gateway
  - whatsapp-api
image: "ghcr.io/rmyndharis/openwa:0.23.5"
category: "ia-automatizacion"
port_internal: 2785
port_default: 2785
protocol: "http"
needs_proxy: false
needs_db: false
db_type: "sqlite"
volumes:
  - "./data:/app/data"
env_required:
  - API_MASTER_KEY
env_optional:
  - ENGINE_TYPE=whatsapp-web.js
healthcheck: '["CMD", "curl", "-f", "http://localhost:2785/api/health/ready"]'
backup_critical: true
backup_paths:
  - "./data"
protected: false
docs_url: "docs/services/openwa-guide.md"
notes: "PENDIENTE de verificación en runtime — ficha objetivo, no estado desplegado. Gateway NO oficial de WhatsApp: riesgo real de baneo, usar número dedicado. Imagen ghcr.io/rmyndharis/openwa:0.23.5 verificada accesible en GHCR (HTTP 200). Base SQLite local en ./data (autocontenido); migrable a PostgreSQL de DataSQL más adelante. EXCEPCIÓN DE SEGURIDAD: NO usar cap_drop:[ALL] a secas — ejecuta Chromium/Puppeteer (motor whatsapp-web.js) y necesita read_only + tmpfs /tmp + pids_limit + caps CHOWN/DAC_OVERRIDE/FOWNER/SETGID/SETUID (postura replicada de la imagen upstream). Header de la API: X-API-Key. Integración oficial con n8n mediante el nodo de comunidad @rmyndharis/n8n-nodes-openwa; n8n lo alcanza por http://openwa:2785 dentro de db_net. Dashboard/API/Swagger en el puerto 2785. Motor alternativo: baileys."
networks:
  - db_net
ports:
  http: 2785
resources:
  memory_limit: "2g"
  memory_reservation: "512m"
security_extra:
  read_only: true
  tmpfs:
    - /tmp
  cap_drop:
    - ALL
  cap_add:
    - CHOWN
    - DAC_OVERRIDE
    - FOWNER
    - SETGID
    - SETUID
runtime_status: "pending-runtime-verification"
target_status: "pending-runtime-verification"
---

# OpenWA

La guía operativa completa es `docs/services/openwa-guide.md`. Esta ficha solo
contiene metadatos, aliases y el estado pendiente para que el agente pueda
localizar el servicio sin duplicar el procedimiento.

## Resumen de arquitectura

- Gateway self-hosted de WhatsApp: API REST + WebSocket + dashboard, todo en el
  puerto `2785`.
- Base de datos SQLite local en `./data/openwa.sqlite` (single-tenant / bot
  personal). No usa PostgreSQL ni Redis por defecto.
- Motor por defecto `whatsapp-web.js` (Chromium/Puppeteer); alternativa
  `baileys` (más ligero) vía `ENGINE_TYPE` en `.env`.
- Red externa `db_net`, para que n8n lo alcance por `http://openwa:2785`.
- Autenticación por cabecera `X-API-Key` con `API_MASTER_KEY`.
- Persistencia crítica en `./data` (sesiones de WhatsApp, DB, media, plugins) —
  incluir en backups.

## Excepción de seguridad (importante)

A diferencia de la mayoría de servicios simples del NAS, OpenWA **no** puede
usar `cap_drop: [ALL]` sin más: arranca Chromium para el motor whatsapp-web.js.
Se replica la postura de la imagen oficial: `read_only: true`, `tmpfs: [/tmp]`,
`pids_limit` y solo las capabilities mínimas
(`CHOWN, DAC_OVERRIDE, FOWNER, SETGID, SETUID`). `no-new-privileges` se hereda
de `_common.yml`.

## Aviso de uso

Es un gateway **no oficial** de WhatsApp. Existe riesgo real de baneo del
número. Usar un número **dedicado**, respetar los rate limits y no hacer envíos
masivos a desconocidos.
