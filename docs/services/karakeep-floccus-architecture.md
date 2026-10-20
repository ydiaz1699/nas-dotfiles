# Arquitectura Karakeep + Floccus — documento maestro

> **Propósito de este documento.** Ordenar en una sola base coherente cómo encajan
> Karakeep y Floccus, y cómo se accede al mismo almacén desde las 4 interfaces
> (UI, MCP, CLI, API REST) más la "cara nativa" del navegador (Floccus).
>
> Es la **fuente de verdad conceptual**. La operación concreta del servicio está en
> [`karakeep-guide.md`](./karakeep-guide.md); la integración del MCP en Kiro CLI está en
> `Varios_tools/kiro-cli-nas/karakeep-mcp.md`. Este documento **enlaza, no duplica**.

---

## 1. El modelo mental correcto (una base, varias caras)

El error común es pensar en "Karakeep por un lado y Floccus por otro, con un puente
entre dos bases de datos". **No es así.** Hay **un único almacén** —Karakeep, en el
NAS— y varias formas de acceder a él. Floccus no es un puente entre dos bases: es la
forma de **proyectar ese almacén hacia/desde los marcadores nativos** del navegador.

```
                   ┌──────────────────────────────────────────┐
                   │        KARAKEEP (en tu NAS, :3400)         │
                   │   = EL ÚNICO ALMACÉN / fuente de verdad    │
                   │   SQLite (datos) + Meilisearch (búsqueda)  │
                   │   + Chrome headless (archivo de páginas)   │
                   └──────────────────────────────────────────┘
                     ▲          ▲           ▲             ▲
          ┌──────────┘          │           │             └───────────┐
          │                     │           │                         │
   ┌──────┴───────┐   ┌─────────┴────┐  ┌───┴─────────┐   ┌───────────┴────────┐
   │ 1. UI WEB    │   │ 2. MCP       │  │ 3. CLI      │   │ 4. API REST        │
   │ + extensión  │   │ (el LLM)     │  │ (tú +       │   │ (scripts/cron/n8n) │
   │   navegador  │   │ @karakeep/mcp│  │  automatiz.)│   │ Bearer token       │
   │ "día a día"  │   │              │  │ @karakeep/  │   │                    │
   │              │   │              │  │   cli       │   │                    │
   └──────┬───────┘   └──────────────┘  └─────────────┘   └────────────────────┘
          │
   ┌──────┴──────────────┐
   │ FLOCCUS              │   La 5ª vía: la "cara nativa" del almacén en el
   │ marcadores nativos   │   navegador. Backend oficial "Karakeep",
   │ (la estrellita)      │   sincronización BIDIRECCIONAL.
   │ PC ↔ Android         │
   └─────────────────────┘

   Las 4 interfaces operan sobre el MISMO almacén.
   Floccus es la cara nativa en el navegador (no un segundo almacén).
```

---

## 2. Las 4 interfaces (+ Floccus) — cuándo usar cada una

Todas apuntan al mismo almacén; la diferencia es **quién las usa y para qué**.

| # | Interfaz | Quién la usa | Para qué | Cómo se habilita |
|---|----------|--------------|----------|------------------|
| 1 | **UI web + extensión** | Tú, a diario | Guardar/leer/organizar, ver PDFs y archivo offline, ajustar reglas de IA | Nativa del servicio (`:3400`) + extensión de navegador |
| 2 | **MCP** | El LLM (Kiro CLI) | Buscar, crear, etiquetar y organizar bookmarks por lenguaje natural | `@karakeep/mcp` en Kiro CLI (`karakeep-mcp.md`) |
| 3 | **CLI** | Tú + automatizaciones | Manipulación avanzada, import/export masivo, scripts puntuales | `@karakeep/cli` (`npm i -g` o Docker) |
| 4 | **API REST** | Scripts / cron / n8n | Integraciones automáticas deterministas (p. ej. "guarda favoritos de RSS") | Bearer token (Settings → API Keys) |
| 5 | **Floccus** | Tú, en el navegador | Sincronizar los marcadores **nativos** (estrellita) PC ↔ Android contra el almacén | Extensión Floccus, backend "Karakeep" |

**Regla de oro de uso (la que recomienda la propia comunidad de Karakeep):** para las
operaciones normales de bookmarks/listas/tags, **prefiere el MCP**; usa **CLI y API**
como vías concretas para lo que el MCP no cubra (import/export masivo, depuración,
cron). La UI es para el trabajo cotidiano humano y para lo que solo se ve en Karakeep
(PDFs, copia offline, resúmenes). *(Contenido reformulado para cumplimiento de licencia.)*

---

## 3. Floccus vs Karakeep — dos modelos de datos distintos

Esta es la clave para no llevarse sorpresas con el sync.

| | **Marcador nativo** (lo que mueve Floccus) | **Bookmark de Karakeep** |
|---|---|---|
| Qué guarda | URL + título + carpeta | URL + notas + PDF + imagen + **copia offline** + tags IA + resumen |
| Dónde vive | En el navegador | En la BD (SQLite) de Karakeep |
| Riqueza | Mínima | Alta |

**Consecuencia:** cuando Floccus sincroniza contra Karakeep, lo hace por el **mínimo
común denominador**. Un marcador nativo se vuelve un bookmark-link simple en Karakeep,
y un bookmark de Karakeep aparece como marcador nativo (solo URL + título) en el
navegador. La riqueza de Karakeep (notas, PDF, copia offline) **no cabe** en un
marcador nativo: eso solo se ve en la UI/app de Karakeep.

### Validación contra la documentación oficial

- **Floccus = conector navegador ↔ sync.** Floccus se describe como una herramienta
  para sincronizar de forma privada los marcadores **nativos** del navegador entre
  navegadores y dispositivos, apoyándose en un backend elegido por el usuario (que
  actúa de intermediario neutral). *(Reformulado de la doc de Floccus para cumplimiento.)*
  Fuente: <https://floccus.org/> y <https://github.com/floccusaddon/floccus>.
- **Karakeep necesita su extensión/UI para guardar**, porque **no** escribe en los
  marcadores nativos del navegador: guarda en **su propia base de datos** con un modelo
  más rico (links, notas, imágenes, PDFs, copia offline, auto-tagging por IA).
  *(Reformulado de la doc de Karakeep para cumplimiento.)*
  Fuente: <https://github.com/karakeep-app/karakeep>.
- **Karakeep es backend oficial de Floccus.** La doc de Karakeep lista como feature
  *"sincronización automática con los marcadores del navegador vía floccus"* y Floccus
  lista "KaraKeep" entre sus backends (junto a Nextcloud, Linkwarden, Google Drive,
  Dropbox, Git, WebDAV). Por tanto la integración es **soportada y bidireccional**.

---

## 4. Los 3 roles (arquitectura de uso)

1. **Floccus → marcadores nativos cotidianos.** La estrellita del navegador,
   sincronizada PC ↔ Android. Rápido y sin fricción.
2. **Karakeep → "biblioteca seria".** Lo que quieres guardar de verdad: leer después,
   archivar la página por si el link muere, notas, PDFs. Se guarda con su extensión/app,
   se gestiona en su UI, y el **LLM** lo opera vía el **MCP**.
3. **El vínculo (opcional pero recomendado como fin).** Configurar Floccus con backend
   Karakeep hace que ambos mundos sean el mismo almacén: tus marcadores nativos aparecen
   en Karakeep (como links simples, que la IA puede etiquetar) y los de Karakeep aparecen
   en el navegador. **El objetivo final del usuario es tener esto activo**, no dejarlo
   como islas separadas.

---

## 5. El primer sync de Floccus — cómo encenderlo sin romper nada

El vínculo es el objetivo, pero **el riesgo no está en la arquitectura (correcta), sino
en el estado inicial de cada lado el día que conectas.** El primer sync de Floccus
**fusiona** el árbol del navegador con el del servidor; si ambos lados tienen datos, se
mezclan y se propagan a todos los dispositivos a la vez. Además, Floccus trae
**failsafes** que abortan el sync si detecta que borraría o multiplicaría demasiados
marcadores (errores tipo "borraría el 101% de tus marcadores" o "aumentaría tus links
un 16389%"). Fuente: issues del repo de Floccus.

**Procedimiento recomendado (un solo origen, sin fusión caótica):**

1. Monta Karakeep (UI + MCP) — ver `karakeep-guide.md`.
2. Elige **qué lado es la semilla** antes de conectar Floccus:
   - **Opción limpia (recomendada):** un lado vacío. P. ej. Karakeep recién montado
     (vacío) + conectas Floccus desde el navegador que tenga tus marcadores buenos →
     suben a Karakeep, y de ahí al resto de dispositivos. Un solo origen.
   - **Si los dos lados ya tienen datos:** haz el primer sync desde **un solo
     dispositivo**, revisa el resultado en la UI de Karakeep, y solo después conecta los
     demás dispositivos.
3. Conecta el resto de dispositivos uno a uno, verificando entre cada uno.

El procedimiento detallado (URL, API key, orden exacto, qué hacer si salta un failsafe)
está en la sección *"Sincronizar con el navegador vía floccus"* de
[`karakeep-guide.md`](./karakeep-guide.md).

> **No cuesta nada esperar.** Encender el vínculo es ir a la extensión Floccus → añadir
> cuenta → backend Karakeep → URL + API key: 2 minutos, cuando el lado semilla esté
> listo. Si prefieres activarlo el mismo día que montas Karakeep, puedes — siempre que
> controles cuál es la semilla.

---

## 6. Dónde vive cada pieza (y dónde no)

| Pieza | Dónde vive | Se despliega en el NAS |
|-------|-----------|------------------------|
| Karakeep (UI + API + almacén) | Servicio Docker en `$dkco/karakeep/` | ✅ Sí |
| MCP de Karakeep | Proceso stdio dentro de Kiro CLI (`Varios_tools/kiro-cli-nas`) | ⚙️ Dentro de Kiro CLI |
| CLI de Karakeep | `npm i -g @karakeep/cli` o imagen Docker, donde lo necesites | ⚙️ Opcional |
| Floccus | **Extensión de navegador** (PC + Android) | ❌ No (es del navegador) |

**Floccus no se instala en el NAS.** Es una extensión de cada navegador. Lo único que
puede vivir en el NAS es su *backend* — y ese rol lo cumple Karakeep. Por eso en
`nas-dotfiles` montamos **Karakeep**; Floccus lo instalas tú en los navegadores y lo
apuntas a Karakeep.

---

## 7. Referencias

- Guía operativa del servicio: [`karakeep-guide.md`](./karakeep-guide.md)
- Integración MCP en Kiro CLI: `Varios_tools/kiro-cli-nas/karakeep-mcp.md`
- Karakeep (repo e imagen): <https://github.com/karakeep-app/karakeep>
- Karakeep MCP: <https://docs.karakeep.app/mcp>
- Karakeep CLI: <https://docs.karakeep.app/command-line>
- Karakeep API REST: <https://docs.karakeep.app/API/karakeep-api>
- Floccus: <https://floccus.org/> · <https://github.com/floccusaddon/floccus>

_Contenido reescrito/resumido a partir de la documentación oficial de Karakeep y
Floccus; se enlaza a la fuente. Verificado contra el código/doc, no de memoria._
