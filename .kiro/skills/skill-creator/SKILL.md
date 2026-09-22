---
name: skill-creator
description: >
  Crea o modifica skills de nas-dotfiles siguiendo el estándar del framework:
  frontmatter enriquecido (scope + auto_invoke), patrón "enlazar no duplicar",
  y capas guía→ficha→skill. Activar cuando el usuario pida crear una skill
  nueva, añadir instrucciones para el agente/LLM, documentar un patrón
  repetitivo, o revisar/estandarizar una skill existente.
  Palabras clave: crear skill, nueva skill, skill-creator, plantilla de skill,
  frontmatter, scope, auto_invoke, estandarizar skill.
license: MIT
metadata:
  author: ydiaz1699
  version: "1.0"
  scope: [root]
  auto_invoke:
    - "Crear una skill nueva o estandarizar una existente"
---

# Skill `skill-creator`

Meta-skill para crear/modificar skills de nas-dotfiles con formato uniforme.
Inspirada en el estándar [Agent Skills](https://agentskills.io) (Prowler,
Anthropic) pero adaptada a las reglas de ESTE framework.

Plantilla base: `assets/SKILL-TEMPLATE.md` (copiarla y rellenarla).

## Cuándo crear una skill (y cuándo NO)

**Crear** una skill cuando:
- Un patrón se repite y el LLM necesita guía específica del NAS.
- Una convención del proyecto difiere de la práctica genérica.
- Un flujo multi-paso necesita instrucciones o un árbol de decisión.

**NO crear** una skill (usar otra cosa) cuando:
- Ya existe una guía dueña → la skill solo la enlaza; no se crea otra fuente.
- El patrón es trivial o autoexplicativo.
- Es una tarea de una sola vez.

## Regla de oro del framework: enlazar, no duplicar

Cada tema tiene UNA fuente dueña. La skill **nunca copia** su contenido:

| Capa | Dueño | La skill... |
|---|---|---|
| Guía narrativa completa | `docs/services/<svc>-guide.md`, `docs/<tema>-guide.md` | la enlaza |
| Recetas / troubleshooting | `docs/troubleshooting.md`, `references/diagnostic.md` | las enlaza |
| Config final de un servicio | `agent/catalog/services/<svc>/{ficha,compose,.env.example}` | la enlaza |
| Flujo accionable para el LLM | **la skill** | lo aporta (único valor propio) |

Si la skill empieza a repetir prosa de la guía, está mal: recortar y enlazar.

## Estructura de una skill

```text
.kiro/skills/<nombre>/
├── SKILL.md          # obligatorio: frontmatter + cuerpo breve
├── references/       # opcional: apunta a archivos LOCALES del repo, no URLs
└── assets/           # opcional: plantillas, ejemplos, schemas
```

- `references/` → punteros a `docs/…`, `agent/…` existentes (no reescribir docs).
- `assets/` → plantillas o ejemplos que el LLM copia (cuanto más ejemplo, más
  "one-shot"). No poner aquí conocimiento operativo que ya vive en una guía.

## Frontmatter obligatorio

```yaml
---
name: <nombre-en-minusculas-con-guiones>
description: >
  Qué hace en 1–2 frases + CUÁNDO activarla (triggers) + palabras clave.
  Si aplica, decir qué NO cubre y a qué skill ir en su lugar (frontera).
license: MIT
metadata:
  author: ydiaz1699
  version: "1.0"
  scope: [<scope>]          # ver tabla de scopes
  auto_invoke:
    - "Acción concreta que debe disparar esta skill"
---
```

`name` y `description` los usa Kiro para activar la skill; `metadata.*` y
`license` son campos extra que Kiro ignora sin romper nada, pero que sirven al
router, al índice y (a futuro) a un sync automático.

### Scopes del framework

| Scope | Dominio | AGENTS.md / índice afectado |
|---|---|---|
| `root` | Administración general / entrada (router) | `AGENTS.md` root |
| `services` | Ciclo de vida de servicios (crear, arrancar, diagnosticar) | `AGENTS.md` root |
| `data` | Bases y secretos (PostgreSQL, Redis, .env) | `AGENTS.md` root |
| `mcp` | Gateway MCP read-only | `AGENTS.md` root |
| `docs` | Evolución documental y de herramientas | `AGENTS.md` root |

> nas-dotfiles NO es un monorepo por features (a diferencia de Prowler): hoy
> todos los scopes mapean al `AGENTS.md` raíz. Si algún día se divide por
> subproyectos, cada scope apuntaría a su `AGENTS.md`.

## Procedimiento para crear una skill

1. Confirmar que NO existe ya una guía dueña que cubra el tema (si existe, la
   skill solo la enlaza).
2. `mkdir -p .kiro/skills/<nombre>` y copiar `assets/SKILL-TEMPLATE.md` como
   `SKILL.md`.
3. Rellenar frontmatter (name, description con triggers + frontera, scope,
   auto_invoke) y cuerpo breve que enlaza a las fuentes dueñas.
4. **Versionado:** añadir la excepción en `.gitignore` (ver más abajo) o la
   skill no se sube (regla: `.kiro/skills/*` está ignorado por defecto).
5. **Conectar los índices A MANO** (no hay sync automático):
   - Fila en el router de `.kiro/skills/dotfile-skill/SKILL.md`.
   - Fila en el índice de `docs/framework-audit.md` (sección Skills del LLM).
   - Sección **Auto-invoke Skills** de `AGENTS.md` (ver plantilla del bloque).
6. Registrar la decisión en `docs/ideas-decisions.md`.
7. Verificar: el frontmatter parsea (YAML), `grep <nombre>` no deja referencias
   rotas y router+índice coinciden.

### Versionado en .gitignore

`.kiro/skills/*` está ignorado. Cada skill nueva necesita su pareja de
excepciones (igual que las demás):

```gitignore
!.kiro/skills/<nombre>/
!.kiro/skills/<nombre>/SKILL.md
```

Si la skill tiene `assets/` o `references/` que deban versionarse, añadir también
`!.kiro/skills/<nombre>/assets/` y `!.kiro/skills/<nombre>/assets/*` (idem
references).

## Auto-invoke MANUAL (sin sync.sh)

Los modelos NO auto-activan skills de forma fiable solo con el `description`; hay
que **obligarlos** desde `AGENTS.md` con una tabla explícita "Cuando hagas X →
invoca la skill Y PRIMERO". En este framework esa tabla se mantiene **a mano**
(decisión consciente: no hay `skill-sync`). Al crear/modificar una skill:

1. Copiar cada entrada de `metadata.auto_invoke` a la sección
   `### Auto-invoke Skills` de `AGENTS.md`.
2. Mantener coherentes el router de `dotfile-skill` y el índice de
   `framework-audit.md`.

> Si algún día el mantenimiento manual se vuelve pesado (muchas skills), evaluar
> un `skill-sync` que regenere estas tablas desde `metadata.scope`/`auto_invoke`
> (ver Prowler `skills/skill-sync/assets/sync.sh` como referencia). Registrado
> como mejora futura, no implementado.

## Guías de contenido

- Empezar por lo crítico (reglas SIEMPRE/NUNCA).
- Tablas para árboles de decisión.
- Ejemplos mínimos y enfocados, no tutoriales.
- Solo incluir lo que el LLM no sabe ya; el resto se enlaza.
- Cuerpo objetivo breve; el detalle vive en la guía dueña.
