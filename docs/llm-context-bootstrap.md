# Bootstrap de contexto para cualquier chat LLM

Este archivo es el punto de entrada portable cuando el proveedor LLM no carga
automáticamente `AGENTS.md`, `.kiro/skills/` o `.kiro/hooks/`.

## Prompt de arranque

Copia este bloque al comienzo del chat o configúralo como instrucciones del
proyecto:

```text
Antes de responder una tarea sobre este repositorio, lee AGENTS.md.

Si la petición menciona drafts, fragmentos, unificar, meta-prompt, errores
documentales, scanner, gaps, contratos, hooks o evolucionar herramientas,
lee primero `.kiro/skills/documentation-evolution/SKILL.md` y sigue su flujo.
Para unificar fragmentos, lee completo `docs/meta-prompt-unificar.md` antes de
redactar. Para comprobar conexiones, revisa la implementación real, sus
entrypoints, `agent/tools/project_index.py`, `agent/tools/project_scanner.py`
y `agent/architecture/contracts.json`.

No afirmes que una herramienta, hook o automatización existe sin comprobar su
archivo y consumidor. Distingue siempre entre implementado, documentado,
pendiente y verificado. No resumas comandos ni configuraciones de los drafts;
marca contradicciones y huecos explícitamente.

Al unificar fragmentos, trabaja por capas: reconstrucción, validación,
reconciliación y presentación. La optimización técnica solo se activa si el
usuario la solicita explícitamente. Lee cada fragmento por separado, separa
HECHOS de INFERENCIAS y asigna confianza ALTA/MEDIA/BAJA/DESCONOCIDA. Compara
variantes equivalentes sin elegir por frecuencia; si no hay evidencia suficiente,
marca PENDIENTE. Distingue mutaciones de verificaciones (`enable` vs.
`is-enabled`), registra precondiciones/postcondiciones, detecta ciclos y exige
backup antes de cualquier operación que pueda afectar el artefacto protegido.
Conserva las rutas exactas de los backups y comprueba que el rollback consuma la
copia creada. Si no hay comando de verificación en las fuentes, marca
`⚠️ NO ESPECIFICADO`; no lo inventes. Clasifica cada elemento como INTEGRADO,
DUPLICADO, REEMPLAZADO, RECHAZADO con motivo, FUERA DE ALCANCE o PENDIENTE.
No presentes inferencias como hechos ni afirmes ejecución real durante una
simulación estática. Si el resultado se convertirá en script, no lo presentes
como seguro hasta revisar errores, paradas y rollback.

Después de modificar documentación o herramientas, valida como mínimo:
`python3 agent/tools/project_index.py --check` y `git diff --check`.
Si cambian conexiones, CLI, hooks o contratos, ejecuta también
`python3 agent/tools/project_scanner.py --full`.
No operes el NAS desde un entorno de desarrollo remoto/sandbox.
```

## Qué se carga automáticamente según el entorno

- **Kiro con este repositorio:** `AGENTS.md` y la skill se pueden descubrir por
  el runtime; el hook `.kiro/hooks/documentation-evolution-on-prompt.json`
  solicita el bootstrap cuando la petición es relevante.
- **Otro LLM con instrucciones de proyecto:** añadir este archivo o el bloque
  anterior a las instrucciones del proyecto.
- **Chat sin acceso al repositorio:** adjuntar este archivo, la skill y el
  meta-prompt; ningún LLM puede leer archivos que el chat no recibió.

Este bootstrap no sustituye al meta-prompt ni al scanner: solo garantiza que el
chat sepa cuándo debe cargarlos y comprobar sus conexiones.
