---
id: "karakeep"
name: "Karakeep"
description: "Gestor de bookmarks 'guárdalo todo' (links, notas, imágenes, PDFs) con IA de tagging/resumen vía Ollama Cloud y búsqueda full-text"
aliases:
  - karakeep
  - hoarder
  - bookmarks
  - marcadores
  - favoritos
  - enlaces
  - read-it-later
image: "ghcr.io/karakeep-app/karakeep:0.33.2"
category: "descargas"
port_internal: 3000
port_default: 3400
protocol: "http"
needs_proxy: false
needs_db: false
db_type: "sqlite"
volumes:
  - "./data:/data"
  - "./data/meilisearch:/meili_data"
env_required:
  - NEXTAUTH_SECRET
  - MEILI_MASTER_KEY
  - OPENAI_API_KEY
env_optional:
  - OPENAI_BASE_URL=https://ollama.com/v1
  - INFERENCE_TEXT_MODEL=gpt-oss:20b
  - DISABLE_SIGNUPS
  - EMBEDDING_OPENAI_BASE_URL
  - EMBEDDING_TEXT_MODEL
healthcheck: '["CMD-SHELL", "wget -qO- http://127.0.0.1:3000/api/health || exit 1"]'
backup_critical: true
backup_paths:
  - "./data"
protected: false
docs_url: "docs/services/karakeep-guide.md"
notes: "Stack de 3 contenedores: karakeep (app web :3000 → publicado en 3400 porque Homepage usa 3000), karakeep-meilisearch (full-text) y karakeep-chrome (archivo/screenshots). DB = SQLite (recomendada por Karakeep; no usa el Postgres de DataSQL → NO entra en db_net). IA de tagging/resumen vía Ollama Cloud (endpoint OpenAI-compatible https://ollama.com/v1, API key de ollama.com). El modelo (INFERENCE_TEXT_MODEL) se fija por .env, NO se elige en la UI (issue #1325 abierto); cambiarlo = editar .env + svc restart. En la UI solo se ajusta el prompt/reglas de etiquetado (User settings → AI settings). Búsqueda semántica DESACTIVADA por defecto: Ollama Cloud no sirve embeddings; requiere proveedor de embeddings aparte (ver guía). Compatible con floccus (backend nativo) para sincronizar bookmarks del navegador. memory: karakeep 1g y chrome 1g sobreescriben el default 512m de _common.yml. NO verificado en runtime todavía."
networks: []
ports:
  http: 3400
resources:
  memory_limit: "1g"
target_status: "pending-runtime-verification"
---

# Karakeep

La guía operativa completa y autocontenida está en
`docs/services/karakeep-guide.md`. Esta ficha solo contiene metadatos, aliases
y notas de diseño para que el agente localice el servicio sin duplicar el
procedimiento.

## Resumen de arquitectura

- Stack de 3 contenedores en un solo compose:
  - `karakeep` — app web (Next.js), puerto interno 3000 → publicado en `3400`.
  - `karakeep-meilisearch` — motor de búsqueda full-text.
  - `karakeep-chrome` — Chromium headless para screenshots y archivo de páginas.
- **DB SQLite** persistida en `./data` (no usa DataSQL; no entra en `db_net`).
- **IA** de tagging/resumen por **Ollama Cloud** (OpenAI-compatible), modelo por
  `.env` (`gpt-oss:20b` por defecto).
- **Búsqueda semántica** desactivada por defecto (falta proveedor de embeddings).
- Sincronización con navegadores vía **floccus** (backend nativo "Karakeep").
- Persistencia crítica en `./data` (incluye la DB SQLite y los archivos).

## Pendiente

- Verificar en runtime: primer arranque, creación del usuario admin, tagging real
  contra Ollama Cloud y archivo de una página de prueba por el contenedor chrome.
- Decidir si se activa la búsqueda semántica con embeddings locales.
