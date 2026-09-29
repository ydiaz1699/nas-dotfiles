---
name: dependency-cascade
description: >
  Completa la CASCADA de dependencias de edición ANTES de dar por terminado un
  cambio, para no dejar el trabajo a medias y que el usuario descubra el fallo
  ejecutándolo. Cuando editas un archivo del framework (compose, script svc,
  módulo shell, tool/plugin del agente, doc, .env global, layers.conf, skill,
  hook), hay OTROS archivos que deben actualizarse en la misma sesión. Usar
  SIEMPRE que agregues o modifiques código/config/docs del proyecto: al crear un
  comando, una tool, un alias, un servicio o al cambiar un puerto/red/variable.
  NO cubre unificar drafts ni auditar variantes (eso es documentation-evolution),
  ni diagnosticar un servicio que falla (eso es nas-diagnostics).
license: MIT
metadata:
  author: ydiaz1699
  version: "1.0"
  scope: [docs]
  auto_invoke:
    - "Completar la cascada de dependencias tras editar un archivo del framework"
    - "Antes de entregar un cambio: verificar qué otros archivos deben actualizarse"
---

# dependency-cascade

Un cambio en el framework casi nunca es un solo archivo. Si tocas la superficie
de verdad (un `compose.yml`, un comando `svc`, una tool del agente), hay
archivos **derivados** que deben actualizarse en el MISMO turno. Esta skill
existe para cerrar esa cascada de forma **proactiva**, no reactiva: el objetivo
es que el trabajo se entregue completo, sin esperar a que el usuario ejecute y
reporte "esto no funciona porque falta en tal sitio" o "el README quedó viejo".

> Problema real que originó esta skill: se creó `catalog-sync.sh`, se conectó al
> CLI Bash, pero **no** al CLI Python ni al prompt del agente. Nadie lo detectó
> hasta que el usuario ejecutó el comando y falló. Esta skill obliga a mirar la
> cadena completa antes de cerrar.

## Fuente dueña (no duplicar aquí)

La tabla completa "si modifico X → debo actualizar Y y Z", con los grafos de
cascada por tipo de cambio y las reglas del LLM al crear algo nuevo, vive en:

```text
docs/dependency-map.md
```

Esta skill **no copia** esa tabla: la enlaza. Antes de completar una cascada,
abrir `docs/dependency-map.md` y localizar la fila / grafo del tipo de cambio
que hiciste. La verificación ejecutable vive en:

```text
agent/architecture/contracts.json   # conexiones mínimas obligatorias
agent/tools/project_index.py         # descubre conexiones reales
agent/tools/project_scanner.py       # compara contratos vs realidad → huecos
```

## Protocolo obligatorio antes de entregar

Cuando hayas editado o creado uno o más archivos del framework, ANTES de decir
que terminaste:

1. **Clasifica cada archivo tocado** por su tipo de cambio (ver tabla rápida
   abajo). Un mismo cambio puede ser de varios tipos a la vez.
2. **Abre `docs/dependency-map.md`** y lee el grafo/fila de ese tipo. Ahí está
   la lista de derivados obligatorios (`OBLIGATORIO`) y opcionales.
3. **Completa los derivados obligatorios en la misma sesión.** No los dejes
   "para después" salvo que el usuario lo pida explícitamente.
4. **Verifica** con el scanner/índice (ver "Verificación" abajo) que no quedan
   conexiones rotas ni derivados ausentes.
5. **Reporta** al usuario, en una lista, qué archivos tocaste y qué derivados
   actualizaste. Si algo quedó `PENDIENTE`, dilo explícitamente; nunca afirmes
   "cascada completa" sin haberlo verificado.

La existencia de un archivo derivado **no prueba** que esté sincronizado: si el
puerto cambió en el compose, la guía puede existir pero con el puerto viejo.
Cuando cambies un valor concreto (puerto, red, imagen, variable), revisa que los
derivados mencionen el valor NUEVO, no solo que existan.

## Tabla rápida — qué tipo de cambio dispara qué cascada

Resumen accionable; el detalle exhaustivo está en `docs/dependency-map.md`.

| Tocaste... | Derivados que revisar (fuente: dependency-map.md) |
|---|---|
| `compose.yml` de un servicio | ficha, guía, `.env.example`, `layers.conf`, AGENTS.md, nas-manual, nas-context, DebMenux (services.json + script) |
| Script/comando nuevo de `svc` (`docker/cli/lib/*.sh` + case en `svc.sh`) | `svc.sh` (case), **CLI Python (`svc_py/`)**, `completions.sh`, `contracts.json`, GUIDE, README, `references/svc.md`, AGENTS, prompt del agente, dependency-map (tabla CLI) |
| Módulo shell (`shell/lib/*.sh`) | `init.sh` (source), GUIDE, README, `references/entorno.md`, AGENTS/nas-context si es alias |
| Tool del agente (`agent/tools/*.py`) | `tools/__init__.py`, agent/README, `references/agent.md`, GUIDE |
| Plugin del agente (`agent/plugins/*.py`) | `plugins/__init__.py`, agent/README, `references/agent.md`, GUIDE |
| Gateway MCP o su manifest | gateway/worker/manifest/Dockerfile, helper systemd, catálogo, guía, Skill, índice MCP separado |
| Doc nuevo en `docs/` | README (tabla docs), SKILL/nas-context si es guía, AGENTS |
| `$dkco/.env` global (IP, TZ) | todos los compose con `env_file: ../.env`, docker-entorno, AGENTS, nas-context, nas-manual |
| Skill nueva o modificada | **3 anclajes**: router en `dotfile-skill`, índice en `framework-audit.md`, tabla auto-invoke en `AGENTS.md`; + excepción en `.gitignore` |
| Hook nuevo | excepción en `.gitignore`; mencionar en la skill/doc que lo dispara |

### Regla especial: CLI dual

`svc` tiene DOS implementaciones (`docker/cli/svc.sh` en Bash y `svc_py/` en
Python), y `NAS_CLI=bash|python` decide cuál corre. Un comando agregado solo a
Bash **no existe** para quien use `NAS_CLI=python`. Si el comando es de paridad
obligatoria (ver `required_shared_commands` en `contracts.json`), debe estar en
ambos, en `completions.sh` y en el prompt del agente. Si es intencionalmente de
un solo lado, declararlo en `allowed_bash_only_commands` /
`allowed_python_only_commands` de `contracts.json` — o el scanner lo marcará.

### Regla especial: skill nueva → 3 anclajes o el índice se desincroniza

Al crear/modificar una skill hay que conectarla en TRES sitios o el router y los
índices quedan inconsistentes (usar `skill-creator` para la plantilla):

1. Router en `.kiro/skills/dotfile-skill/SKILL.md` (fila en la tabla de router).
2. Índice en `docs/framework-audit.md` ("Skills del LLM").
3. Tabla "Auto-invoke Skills" en `AGENTS.md` (copiar las entradas de
   `metadata.auto_invoke` del frontmatter).

Y como `.kiro/skills/*` está ignorado por defecto, añadir en `.gitignore`:
`!.kiro/skills/<n>/` + `!.kiro/skills/<n>/SKILL.md` (y `references/` si tiene).

## Verificación

Antes de cerrar, ejecutar en el repositorio (no es runtime del NAS):

```bash
python3 agent/tools/project_index.py --check
git diff --check
```

Cuando el cambio afecte servicios, CLI, hooks, tools o conexiones:

```bash
python3 agent/tools/project_scanner.py --full
```

El scanner reporta: comandos sin paridad, comandos que el agente no conoce,
`docs_url` rotos, contratos incompletos, servicios sin ficha/guía/labels. Si
reporta un hueco de algo que acabas de tocar, ciérralo antes de entregar. El
scanner puede refrescar su cache; una validación local del repositorio no
sustituye una comprobación runtime del NAS.

## Qué NO hace esta skill

- **No unifica drafts ni audita variantes de comandos** → esa es
  `documentation-evolution` (`.kiro/skills/documentation-evolution/SKILL.md`).
- **No diagnostica un servicio que falla en runtime** → esa es `nas-diagnostics`.
- **No ejecuta operaciones runtime del NAS.** Desde el sandbox/chat solo edita
  el repo y verifica con el índice/scanner; los comandos `svc` reales corren en
  el entorno autorizado.

## Cierre honesto

Si no pudiste completar toda la cascada (por falta de acceso, decisión del
usuario o ambigüedad), enumera explícitamente qué quedó `PENDIENTE` y por qué.
Es preferible un cierre parcial declarado a un "listo" que el usuario descubre
incompleto al ejecutar.
