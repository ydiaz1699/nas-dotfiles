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
  - ENGINE_TYPE=baileys
healthcheck: '["CMD", "curl", "-f", "http://localhost:2785/api/health/ready"]'
backup_critical: true
backup_paths:
  - "./data"
protected: false
docs_url: "docs/services/openwa-guide.md"
notes: "RUNTIME CONFIRMADO en el NAS: arranca healthy, dashboard OK con CSP/CORS, sesión vinculada y envío de texto funcionando (messageId _out). IMPORTANTE: la API usa el id (UUID) de la sesión en las URLs, NO el name (usar el name da 'Validation failed uuid is expected'); resolver name->id con GET /api/sessions. API_KEY_PEPPER invalida el hash de las keys existentes al añadirlo/cambiarlo (re-sembrar borrando data/main.sqlite). Script de envío: wa-send.sh. Gateway NO oficial de WhatsApp: riesgo real de baneo, usar número dedicado. Imagen ghcr.io/rmyndharis/openwa:0.23.5 verificada accesible en GHCR (HTTP 200). Base SQLite local en ./data (autocontenido); migrable a PostgreSQL de DataSQL más adelante. EXCEPCIÓN DE SEGURIDAD: NO usar cap_drop:[ALL] a secas — ejecuta Chromium/Puppeteer (motor whatsapp-web.js) y necesita read_only + tmpfs /tmp + pids_limit + caps CHOWN/DAC_OVERRIDE/FOWNER/SETGID/SETUID (postura replicada de la imagen upstream). Header de la API: X-API-Key. Integración oficial con n8n mediante el nodo de comunidad @rmyndharis/n8n-nodes-openwa; n8n lo alcanza por http://openwa:2785 dentro de db_net. Dashboard/API/Swagger en el puerto 2785. MOTOR: baileys por defecto — whatsapp-web.js tiene ROTO el envío de imágenes/media con la versión actual de WhatsApp Web (error 'Data passed to getter must include an id property'), verificado en runtime; con baileys el envío de imagen base64/binario a un número real FUNCIONA (messageId sin _lid). Cambiar de motor obliga a re-escanear QR. GOTCHAS de envío de media: (1) NO enviar media al propio número vinculado (self-chat) — falla; usar un número destino distinto. (2) SSRF: con SSRF_ALLOWED_HOSTS restringido NO se pueden enviar imágenes por URL externa (se bloquea el fetch); usar binario/base64 o ampliar el allowlist. (3) Para el nodo n8n, el campo 'Chat Name or ID' resuelve a @lid del remitente; para recibir la foto en un número fijo, poner ese número con @c.us; vaciar 'Quoted Message ID' y 'Mentions' (los ejemplos rompen el envío). Ver logs sin follow: docker logs --tail N openwa | grep -iE 'ready|error|qr'."
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
runtime_status: "confirmed"
target_status: "confirmed"
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
- Motor por defecto `baileys` (más ligero, sin Chromium). `whatsapp-web.js`
  queda como alternativa PERO tiene roto el envío de media (ver notes).
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
