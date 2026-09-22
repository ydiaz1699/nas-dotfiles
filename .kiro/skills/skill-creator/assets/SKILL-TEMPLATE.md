---
name: NOMBRE-EN-MINUSCULAS-CON-GUIONES
description: >
  QUÉ HACE en 1–2 frases. Incluir CUÁNDO activarla (triggers concretos) y
  PALABRAS CLAVE que el usuario podría mencionar. Si la skill tiene una frontera
  con otra, decir qué NO cubre y a qué skill ir en su lugar. Ej.: "NO usar para
  X (usar OTRA-SKILL)".
license: MIT
metadata:
  author: ydiaz1699
  version: "1.0"
  scope: [SCOPE]            # root | services | data | mcp | docs
  auto_invoke:
    - "ACCIÓN concreta del usuario que debe disparar esta skill"
    # - "otra acción (opcional)"
---

# Skill `NOMBRE`

Una frase de propósito. Enlazar a la(s) fuente(s) dueña(s); NO duplicar su
contenido:

- Guía dueña: `docs/.../GUÍA.md`
- Ficha/compose (si aplica): `agent/catalog/services/<svc>/...`
- Recetas/troubleshooting (si aplica): `docs/troubleshooting.md`

## Cuándo usar

- BULLET de cuándo activar.
- BULLET de otro caso.

## Frontera (qué NO cubre)

- Para CASO_X → usar `OTRA-SKILL`.

## Reglas / flujo (lo único propio de la skill)

Reglas SIEMPRE/NUNCA primero, luego el flujo o árbol de decisión. Ejemplos
mínimos. Todo el detalle largo va en la guía dueña, no aquí.

```bash
# comandos accionables mínimos, usando wrappers del framework ($dkco, svc, dk)
```

## Casos abiertos / notas (opcional)

- NOTA relevante que el LLM no puede inferir.

<!--
CHECKLIST al crear/modificar esta skill (borrar antes de publicar):
[ ] Frontmatter parsea (YAML) y tiene scope + auto_invoke
[ ] No duplica prosa de la guía dueña (solo enlaza)
[ ] Excepción en .gitignore: !.kiro/skills/NOMBRE/ y !.kiro/skills/NOMBRE/SKILL.md
[ ] Fila en el router: .kiro/skills/dotfile-skill/SKILL.md
[ ] Fila en el índice: docs/framework-audit.md (Skills del LLM)
[ ] Sección Auto-invoke Skills en AGENTS.md (a mano)
[ ] Entrada en docs/ideas-decisions.md
[ ] grep NOMBRE sin referencias rotas; router e índice coinciden
-->
