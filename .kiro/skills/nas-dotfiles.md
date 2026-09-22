# nas-dotfiles — índice de entrada (puntero)

> Este archivo **no es una skill activable** (no tiene frontmatter de skill a
> propósito): es un índice suelto para quien abre `.kiro/skills/` o pega este
> archivo en un chat sin historial. **No duplica contenido**: apunta a la fuente
> dueña de cada tema. La skill de entrada real es
> [`dotfile-skill`](dotfile-skill/SKILL.md) (router).

`nas-dotfiles` es un framework para administrar un NAS Debian con Docker, en tres
componentes: shell personalizado, CLI Docker (`svc`) y agente IA Python. El
código vive en `$NAS_DOTFILES` (default `/nas-dotfiles`); los datos de servicios
en `$dkco` (default `/docker`). No se mezclan.

## A dónde ir según lo que necesites

| Necesito... | Fuente dueña |
|---|---|
| **Router de skills** (qué skill cargar para cada tarea) + reglas de rutas | [`dotfile-skill/SKILL.md`](dotfile-skill/SKILL.md) |
| **Overview para agentes**: entorno, comandos `svc`, servicios, redes, reglas estrictas, auto-invoke | [`../../AGENTS.md`](../../AGENTS.md) |
| **Mapa ejecutivo de TODOS los componentes** (shell/lib, CLI, agent/tools, catálogo, docs, índice de skills) | [`../../docs/framework-audit.md`](../../docs/framework-audit.md) |
| **Cómo extender** el framework (nuevo comando `svc`, tool del agente, plugin, evento, variables de entorno) | [`../../CONTRIBUTING.md`](../../CONTRIBUTING.md) |
| **Bootstrap portable** para un LLM que no carga `.kiro/` automáticamente | [`../../docs/llm-context-bootstrap.md`](../../docs/llm-context-bootstrap.md) |
| **Guía operativa de un servicio** concreto (instalación, recuperación, backups) | `../../docs/services/<svc>-guide.md` |
| **Config final de un servicio** (metadatos, compose, variables) | `../../agent/catalog/services/<svc>/` |

## Skills disponibles

El índice canónico de skills (con cuándo activar cada una) está en el router
[`dotfile-skill/SKILL.md`](dotfile-skill/SKILL.md) y en la sección "Skills del
LLM" de [`framework-audit.md`](../../docs/framework-audit.md). Resumen:

`dotfile-skill` (entrada/router) · `docker-boot-order` (crear/arrancar servicios)
· `nas-diagnostics` (diagnosticar servicios existentes) · `datasql` (PostgreSQL/
Redis) · `nas-runtime-secrets` (secretos) · `nas-mcp-gateway` (gateway MCP) ·
`documentation-evolution` (unificar drafts/evolución) · `skill-creator` (crear
skills nuevas).

## Regla del framework

Enlazar, no duplicar: cada tema tiene UNA fuente dueña. Si actualizas algo,
hazlo en la fuente dueña (arriba), no aquí. Para crear o estandarizar una skill,
usa [`skill-creator/SKILL.md`](skill-creator/SKILL.md).
