---
name: documentation-evolution
description: >
  Unifica borradores y fragmentos, detecta contradicciones y lagunas, y hace
  evolucionar las herramientas y la documentación del proyecto sin perder
  comandos ni configuración. Usar cuando el usuario mencione drafts, fragmentos,
  unificar, meta-prompt, mejorar documentación, errores documentales, scanner,
  gaps, contratos, herramientas del LLM o evolución del framework.
---

# Evolución documental y de herramientas

Esta skill es el punto de entrada del chat LLM para dos trabajos relacionados:

- Para otro proveedor LLM que no cargue `.kiro/`, usar el bloque portable de
  `docs/llm-context-bootstrap.md` como instrucción del proyecto.

1. **Unificar evidencia:** convertir fragmentos de `_drafts/` y conversaciones en
   una guía canónica usando `docs/meta-prompt-unificar.md`.
2. **Cerrar el ciclo de mejora:** detectar qué quedó sin conectar, corregir la
   superficie dueña y verificar que la herramienta/documentación evolucionó.

## Activación obligatoria

Antes de responder o editar cuando la petición trate de cualquiera de estos
casos, leer primero:

```text
docs/meta-prompt-unificar.md
```

Además, leer según el caso:

```text
agent/tools/project_scanner.py       # implementación del auditor
agent/tools/project_index.py         # índice estructural
agent/architecture/contracts.json    # conexiones mínimas esperadas
docs/architecture-consistency.md     # ownership y criterios
.kiro/hooks/                         # automatizaciones del chat
```

No afirmar que una herramienta está disponible, conectada o automática sin
comprobar su archivo de implementación y su punto de entrada.

## Clasificación rápida

| Evidencia de la petición | Acción inicial |
|---|---|
| `_drafts/`, fragmentos, diagnósticos dispersos | Leer `meta-prompt-unificar.md` y clasificar los fragmentos antes de redactar |
| “hay un error”, “falta conectar”, “no se detectó” | Leer `project_scanner.py`, `project_index.py` y `contracts.json` |
| “evolucionar la herramienta”, “hacerla automática” | Revisar implementación, entrypoints, hooks, docs y contrato; no limitarse a añadir texto |
| cambio en un servicio Docker | Leer primero su guía y ficha; después usar el pipeline de catálogo |
| cambio en red del NAS | Leer primero `docker-nas/references/networking.md` y la derivación aplicable |

## Protocolo de auditoría antes de unificar

No redactes directamente desde el primer draft ni desde la variante que más se
repite. El trabajo debe pasar por estas capas:

```text
RECONSTRUCCIÓN → VALIDACIÓN → RECONCILIACIÓN → PRESENTACIÓN
                                      ↓
                         OPTIMIZACIÓN solo si se solicita
```

Antes de producir la guía final:

1. Inventaría todos los fragmentos y marca cada uno como `LEÍDO`, `PENDIENTE`
   o `NO DISPONIBLE`.
2. Extrae comandos, configuraciones, archivos, rutas, backups, precondiciones,
   postcondiciones y dependencias de cada fragmento por separado.
3. Clasifica las afirmaciones como `HECHO EXPLÍCITO`, `INFERENCIA TÉCNICA
   SEGURA`, `INFERENCIA NO CONFIRMADA` o `DESCONOCIDO`, con confianza
   `ALTA`, `MEDIA`, `BAJA` o `DESCONOCIDA`.
4. Agrupa solo variantes realmente equivalentes. Compara propósito, mutación vs.
   consulta, seguridad, idempotencia, timeout, observabilidad, reversibilidad y
   compatibilidad. Si no se puede determinar cuál es mejor, deja `PENDIENTE`.
5. Reconstruye un grafo temporal con `requiere`, `produce`, `crea`, `modifica`,
   `elimina`, `respalda`, `restaura`, `consume`, `verifica`, `habilita`,
   `deshabilita`, `inicia`, `detiene`, `reinicia`, `precondición` y
   `postcondición`. Un backup precede las operaciones que puedan afectar el
   artefacto que protege; no todo restart requiere backup.
6. Si aparece un ciclo, marca `⚠️ CICLO DE DEPENDENCIAS` y no fuerces un orden.
7. Conserva las rutas exactas de backups y comprueba que el rollback consume el
   artefacto creado.
8. Clasifica cada elemento como `INTEGRADO`, `DUPLICADO`, `REEMPLAZADO`,
   `RECHAZADO` con motivo, `FUERA DE ALCANCE` con destino o `PENDIENTE`.

Distingue siempre `systemctl enable ...` (mutación) de
`systemctl is-enabled ...` (verificación). Si la guía se convertirá en script,
revisa errores, paradas seguras y rollback antes de llamarla ejecutable.

La salida debe incluir una sección compacta `AUDITORÍA DE FUENTES Y VARIANTES`.
No inventes verificaciones: si una fuente no proporciona ninguna, marca
`⚠️ NO ESPECIFICADO` y separa cualquier propuesta externa. No afirmes que se
verificó algo si no se ejecutó realmente.

## Flujo obligatorio de unificación

1. Identificar la fuente de cada afirmación: conversación, draft, código o
   configuración actual.
2. Leer el meta-prompt completo y respetar sus reglas: no resumir código,
   no inventar, detectar contradicciones y marcar huecos como pendientes.
3. Clasificar el resultado en una sola fuente canónica y derivaciones mínimas;
   no copiar la misma prosa en varias capas.
4. Mantener el orden temporal real:

   ```text
   mkdir → archivos → permisos → levantar → verificar
   ```

5. Si el usuario corrige un resultado, separar la corrección de la tarea actual:
   aplicar la corrección al documento dueño solo con autorización y, si cambia
   el contrato del proceso, proponer una regla versionada para aprobación. No
   modificar silenciosamente el meta-prompt, la skill o las reglas del proyecto.

## Flujo obligatorio para evolucionar herramientas

Cuando se detecte una laguna, seguir esta cadena:

```text
síntoma o corrección
  → localizar implementación real
  → localizar entrypoints y consumidores
  → actualizar herramienta
  → actualizar contrato/documentación
  → ejecutar validaciones
  → registrar la lección reutilizable
```

Antes de editar, responder internamente estas preguntas:

- ¿La herramienta existe realmente o solo está documentada?
- ¿Quién la invoca: hook, CLI Bash, CLI Python, agente o usuario?
- ¿Qué entrada recibe y qué salida produce?
- ¿Qué archivo es la fuente de verdad y cuáles son derivados?
- ¿Qué conexión faltante habría permitido que el scanner la detectara?
- ¿La mejora aplica a este repositorio o es una preferencia global?

Una corrección no está completa si solo se actualiza la documentación: si el
problema fue una conexión ausente, también deben revisarse el entrypoint,
`contracts.json`, el índice y el scanner. Si no se puede implementar todo,
marcar explícitamente la parte pendiente.

## Validación local del repositorio

Para cambios de documentación, herramientas o contratos, usar como mínimo:

```bash
python3 agent/tools/project_index.py --check
git diff --check
```

Cuando el cambio afecte conexiones, servicios, CLI, hooks o herramientas:

```bash
python3 agent/tools/project_scanner.py --full
```

El scanner puede actualizar sus artefactos de cache. No confundir una validación
local del repositorio con una comprobación runtime del NAS.

Para cambios de servicios en el NAS, `svc scan` y `svc catalog-sync` se ejecutan
solo en el entorno autorizado y siempre respetando `svc`, `$NAS_DOTFILES`,
`$dkco`, `$aadm` y `compose.yml`.

## Registro de mejoras

Después de una corrección confirmada:

- actualizar `docs/meta-prompt-unificar.md` si la lección cambia cómo se
  unifican fragmentos;
- actualizar esta skill si cambia el flujo de trabajo del chat;
- actualizar `project_scanner.py`/`project_index.py`/`contracts.json` si cambia
  una conexión verificable;
- actualizar la guía dueña si cambia conocimiento operativo;
- actualizar `AGENTS.md` solo para reglas globales y puntos de entrada.

No copiar la conversación completa ni guardar secretos. Registrar una regla
reutilizable, su origen y la fecha cuando corresponda.
