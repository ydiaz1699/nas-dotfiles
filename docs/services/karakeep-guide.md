# Karakeep — Guía de instalación y operación

> Gestor de bookmarks "guárdalo todo" (links, notas, imágenes, PDFs) con IA de
> auto-tagging y resumen, búsqueda full-text y archivo de páginas.
> GUI web: `http://$SERVER_IP:3400`
>
> Antes "Hoarder". Imagen `ghcr.io/karakeep-app/karakeep`. Esta guía es
> autocontenida: lleva el conocimiento dentro para que cualquier LLM pueda
> operar el servicio sin releer el repo entero.

---

## Arquitectura del stack (3 contenedores)

```
[karakeep]            app web Next.js (:3000 → publicado en :3400)   ─┐
[karakeep-meilisearch] motor de búsqueda full-text (:7700, interno)   ├─ 1 solo compose
[karakeep-chrome]     Chromium headless para screenshots/archivo       ─┘
```

- **DB = SQLite** (opción recomendada por Karakeep), guardada en `./data`.
  Karakeep **no** usa el PostgreSQL de DataSQL → **no entra en `db_net`**.
- La app habla con Meilisearch y Chrome por el nombre de servicio dentro de la
  red por defecto del compose (`karakeep-meilisearch:7700`, `karakeep-chrome:9222`).

### Por qué el puerto 3400 y no 3000

La imagen expone `3000` internamente, pero en el NAS el `3000` del host ya lo
usa **Homepage**. Por eso se publica en `3400:3000`. `NEXTAUTH_URL` **debe**
coincidir con la URL real de acceso (`http://$SERVER_IP:3400`) o el login falla.

---

## La IA: Ollama Cloud (tagging y resumen)

Karakeep usa un proveedor LLM para **auto-etiquetar y resumir**. Se configura
con el endpoint **OpenAI-compatible** de Ollama Cloud:

| Variable | Valor |
|---|---|
| `OPENAI_API_KEY` | tu API key de `ollama.com` (Settings → API keys) |
| `OPENAI_BASE_URL` | `https://ollama.com/v1` |
| `INFERENCE_TEXT_MODEL` | `gpt-oss:20b` (por defecto) |

Modelos cloud disponibles (sin el sufijo `-cloud` para la API): `gpt-oss:20b`
(recomendado, barato), `gpt-oss:120b` (más capaz, gasta más cupo),
`qwen3-coder:480b`, `deepseek-v3.x`, etc. Lista actual en `https://ollama.com`.

> **El modelo NO se elige en la UI de Karakeep.** Se fija por la variable
> `INFERENCE_TEXT_MODEL` en el `.env` (hay un issue abierto, #1325, pidiendo
> moverlo a la UI, pero aún no existe). Para cambiarlo:
>
> ```bash
> dk karakeep
> nano .env            # editar INFERENCE_TEXT_MODEL
> svc restart karakeep
> ```
>
> Lo que **sí** se ajusta en la UI es el **prompt/reglas de etiquetado**:
> *User settings → AI settings* (p.ej. "etiqueta en español"). Eso es en caliente.

### Búsqueda semántica (embeddings) — desactivada por defecto

Ollama Cloud (a fecha de este despliegue) sirve modelos de **chat**, no de
**embeddings**. La búsqueda semántica necesita un modelo de embeddings, así que
queda **desactivada**. Tienes dos salidas si la quieres:

- **(A) Embeddings locales** con un Ollama local ligero (`embeddinggemma`),
  apuntando `EMBEDDING_OPENAI_BASE_URL` a ese Ollama.
- **(B) Otro proveedor** OpenAI-compatible solo para embeddings.

Sin esto tienes **tagging + resumen por IA + búsqueda FULL-TEXT** (Meilisearch),
que ya cubre la mayoría de los casos. Ver variables comentadas en `.env.example`.

---

## Estructura de directorios

```
$dkco/karakeep/
├── compose.yml
├── .env                     ← secretos (permisos 600)
└── data/                    ← DB SQLite + archivos de páginas (CRÍTICO: backup)
    └── meilisearch/         ← índice de búsqueda full-text
```

---

## Instalación (orden de ejecución real)

```bash
# 1. Carpetas (incluida la de meilisearch ANTES de levantar)
mkdir -p $dkco/karakeep/data/meilisearch

# 2. Archivos: copiar compose y .env desde el repo
cp $NAS_DOTFILES/agent/catalog/services/karakeep/compose.yml $dkco/karakeep/compose.yml
cp $NAS_DOTFILES/agent/catalog/services/karakeep/.env.example $dkco/karakeep/.env
# Ajustar la ruta de extends al contexto del NAS:
sed -i 's#file: ../../_common.yml#file: ../_common.yml#g' $dkco/karakeep/compose.yml

# 3. Generar secretos SIN imprimirlos y pegar tu API key de Ollama Cloud
dk karakeep
(
  umask 077
  NEXTAUTH=$(openssl rand -base64 36)
  MEILI=$(openssl rand -base64 36 | tr -dc 'A-Za-z0-9')
  sed -i \
    -e "s#^NEXTAUTH_SECRET=.*#NEXTAUTH_SECRET=${NEXTAUTH}#" \
    -e "s#^MEILI_MASTER_KEY=.*#MEILI_MASTER_KEY=${MEILI}#" \
    .env
  unset NEXTAUTH MEILI
)
nano .env     # pegar tu OPENAI_API_KEY (de ollama.com) donde dice __pega_aqui__

# 4. Permisos del .env (los contenedores corren como root → ./data no necesita chown)
chmod 600 $dkco/karakeep/.env

# 5. Registrar en el arranque escalonado REAL ($dkco/scripts/layers.conf, NO versionado).
#    OBLIGATORIO con BOOT_ORDER_REQUIRE_ALL=1: sin esta línea el PRÓXIMO REBOOT FALLA.
#    Capa 5 (servicios de archivos/descargas, junto a jdownloader/filebrowser).
sed -i '/^jdownloader/a karakeep' /docker/scripts/layers.conf
grep -n karakeep /docker/scripts/layers.conf     # verificar que quedó en la Capa 5
#    Alternativa bajo demanda (no arranca en el boot): svc no-boot karakeep

# 6. Validar y levantar
svc config karakeep       # revisar que no haya errores de interpolación
svc up karakeep
svc ps karakeep           # los 3 contenedores deben quedar Up (healthy)
svc logs karakeep
```

> **Nota (hueco conocido):** desplegar con `cp` manual NO dispara el recordatorio
> `_svc_layers_reminder` que sí muestra `svc create`/`svc clone`. Por eso el
> paso 5 es explícito. Ver `docs/ideas-decisions.md` #27 (recurrencia #23).

---

## Primer uso (manual, una vez)

1. Abre `http://$SERVER_IP:3400`.
2. **Crea el usuario administrador** (el primer registro es el admin).
3. (Opcional recomendado) Para evitar que otros se registren, añade
   `DISABLE_SIGNUPS: "true"` en el `environment:` del compose (o `.env`) y
   `svc restart karakeep`.
4. Guarda un enlace de prueba y verifica en los logs que:
   - el **tagging IA** responde (llamada a `ollama.com`),
   - el **archivo** genera screenshot (lo hace `karakeep-chrome`).

---

## Carga inicial de tus bookmarks

Karakeep **importa** (Settings → Import):
- **HTML Netscape** (export estándar de cualquier navegador) — lo más fácil.
- CSV de Pocket, JSON de Omnivore.

Conserva títulos, tags y fecha. Útil para migrar todo de golpe antes de activar
la sincronización continua.

---

## Sincronizar con el navegador vía floccus

Karakeep tiene **backend nativo en floccus** (igual que Linkwarden/Nextcloud),
así que la sincronización de bookmarks del navegador es oficial y bidireccional.

1. Instala la **extensión floccus** en tu navegador (Chrome/Firefox/Edge/Brave/
   Vivaldi/Opera; **Safari no está soportado**).
2. En Karakeep: Settings → crea un **API key**.
3. En floccus: nuevo perfil → backend **Karakeep** → URL `http://$SERVER_IP:3400`
   + el API key.
4. A partir de ahí, lo que guardes en el navegador sube a Karakeep (y se
   auto-etiqueta), y lo de Karakeep aparece en los bookmarks del navegador.

> Móvil: app floccus (Android, beta) o el navegador Kiwi. Firefox Android aún no
> soporta la API de bookmarks que floccus necesita.

---

## Arranque escalonado (layers.conf)

Karakeep se declara en la **Capa 5** (servicios de archivos/descargas, junto a
`jdownloader` y `filebrowser`). No depende de DataSQL ni de MQTT.

```
# Capa 5 — Servicios de archivos, descargas y notificaciones
filebrowser
jdownloader
karakeep
ntfy
```

- Fuera del boot sin borrarlo: `svc no-boot karakeep`.
- Reactivar: `svc boot-enable karakeep`.

---

## Operación

```bash
svc ps karakeep         # estado de los 3 contenedores
svc logs karakeep       # logs
svc restart karakeep    # reiniciar (p.ej. tras cambiar el modelo de IA)
svc update karakeep     # actualizar imágenes (pull + recrear)
svc open karakeep       # abrir la GUI web
svc backup karakeep     # respaldar (incluye ./data con la DB SQLite)
```

---

## Backup y recuperación

- **`./data` es crítico**: contiene la **DB SQLite** (bookmarks, tags, usuarios)
  y los **archivos de páginas** (screenshots/HTML). `svc backup karakeep` o un
  `tar` de `$dkco/karakeep/data`.
- `./data/meilisearch` es el índice de búsqueda; es **reconstruible** desde la
  DB, pero respaldarlo acelera la recuperación.
- Para restaurar: parar el servicio, restaurar `./data`, levantar. No mezclar un
  `data/` de una versión muy distinta sin leer las notas de la release.

---

## Notas y gotchas

- **Puerto 3400 ≠ 3000**: `NEXTAUTH_URL` debe apuntar a `http://$SERVER_IP:3400`.
  Si cambias el puerto publicado, actualiza también `NEXTAUTH_URL` y los labels
  de Homepage.
- **El modelo de IA se fija por `.env`**, no por la UI (ver sección de IA).
- **Semántica desactivada** por falta de embeddings cloud en Ollama (ver arriba).
- **RAM**: en un NAS de 8GB vigila el conjunto. `karakeep` y `karakeep-chrome`
  tienen 1g cada uno; Meilisearch 512m. Chromium es el que más puede subir al
  archivar páginas pesadas.
- **Ollama Cloud consume cupo** por tokens; el plan Free trae un cupo mensual
  pequeño. Taggear bookmarks es poco texto por link, así que suele alcanzar;
  si se agota, se puede pasar a un modelo más barato o a Ollama local.
- **Privacidad**: con Ollama Cloud, el texto de cada página sale del NAS para el
  tagging (Ollama declara "zero data retention", pero no es local puro). Si
  quieres que nada salga, usa Ollama local para la inferencia.
- **Healthcheck**: la app expone `/api/health`; se comprueba con `wget` (busybox).

---

## Referencias

- Imagen y repo: https://github.com/karakeep-app/karakeep (tag `v0.33.2`)
- Proveedores de IA: https://docs.karakeep.app/guides/different-ai-providers
- Ollama Cloud: https://docs.ollama.com/cloud
- floccus (sincronización navegador): https://github.com/floccusaddon/floccus
- My reglas del catálogo: `agent/catalog/_compose_base.md`, `agent/catalog/_common.yml`
