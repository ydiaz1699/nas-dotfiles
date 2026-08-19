# Sesión 2026-08-17 — Compilación de conocimiento arquitectónico

> Se consolidó el conocimiento de la conversación sobre arquitectura verificable en un documento canónico y se enlazaron las fuentes existentes. No se modificaron servicios del NAS, no se ejecutó Docker real y no se subió nada a GitHub.

## 1. Objetivo original

El usuario pidió documentar en el repositorio todas las ideas, decisiones y aprendizajes de la conversación para poder mejorar el framework, solucionar problemas futuros y comprobar si se cumplieron las ideas originales del usuario. La decisión central fue no copiar el chat completo: había que crear una compilación estructurada y autocontenida.

La preocupación arquitectónica concreta era que el framework tenía las piezas principales, pero no una capa que demostrara cómo se conectan ni detectara automáticamente cuándo una modificación deja algo desincronizado.

## 2. Evolución del trabajo

1. Se revisó el inventario existente de `nas-dotfiles` + `DebMenux-` y la auditoría del otro chat.
2. Se distinguió inventario de arquitectura: saber que existe un archivo no demuestra que esté conectado.
3. Se separaron las responsabilidades: `dependency-map` expresa reglas esperadas; `project_index` descubre conexiones reales; `project_scanner` compara y reporta; `catalog-sync` genera documentación faltante; handoff conserva continuidad.
4. Se revisaron `ideas-decisions.md`, `framework-audit.md`, `architecture-consistency.md`, `dependency-map.md`, `session-handoff.md`, `AGENTS.md`, `nas-context.md` y los drafts históricos.
5. Se detectaron duplicaciones y contradicciones: paridad Bash/Python declarada de forma incompatible, estado histórico obsoleto, EMQX/redes en registros distintos, fechas de skill ambiguas, catálogos potencialmente stale y un índice duplicado en `ideas-decisions.md`.
6. Se creó `docs/framework-knowledge-compilation.md` como mapa canónico. El documento separa problema original, evolución, arquitectura, ownership, flujos, decisiones, estado, gaps, criterios de aceptación y roadmap.
7. Se corrigió el índice duplicado de `docs/ideas-decisions.md` y se agregaron enlaces desde las superficies relevantes.

## 3. Decisiones tomadas

| # | Decisión | Por qué | Alternativa descartada |
|---|---|---|---|
| 1 | Mantener una compilación canónica separada del historial | El LLM necesita mapa actual y criterios, no una transcripción ruidosa | Guardar todo el chat |
| 2 | Mantener ownership separado por documento | Evita que ficha, skill, audit y dependency-map repitan prosa distinta | Crear una única mega-documentación que sustituya todo |
| 3 | Marcar `verificado`, `declarado` y `pendiente` | El sandbox no puede demostrar runtime/NAS y los docs históricos pueden estar obsoletos | Presentar toda afirmación documental como hecho actual |
| 4 | No afirmar paridad completa entre CLIs | La tabla actual muestra comandos Bash-only aunque contracts tenga `required_shared_commands` | Ocultar la diferencia bajo el concepto de passthrough |
| 5 | Preservar `project-index.json` y `project-snapshot.json` separados | Mapa estructural y delta incremental tienen ciclos de vida diferentes | Fusionar ambos caches |
| 6 | No tocar servicios ni subir cambios | La tarea era documental y el usuario no aprobó operación NAS/GitHub | Probar o desplegar en el NAS real |

Las decisiones operativas anteriores (ntfy, USB, Homepage, HA, catálogo, skill, AGENTS, dependency-map, dual CLI y defaults Compose) siguen narradas en `docs/ideas-decisions.md`; la compilación solo las relaciona con la arquitectura.

## 4. Hallazgos y problemas

| Hallazgo | Fuente/alcance | Estado |
|---|---|---|
| El `dependency-map` es expectativa, no prueba | `docs/dependency-map.md` + `architecture-consistency.md` | Documentado |
| El índice y scanner representan la nueva capa verificable | `contracts.json`, `project_index.py`, `project_scanner.py` | Verificado estáticamente |
| Resultado del índice: 237 archivos, 16 servicios, 4 contratos, 0 conexiones funcionales rotas | Validación de esta línea de trabajo | Verificado según output registrado |
| Scanner encuentra diferencias Bash-only/Python-only, conocimiento faltante de `kill` y desajustes DebMenux | Validación registrada | Gap real, no corregido aquí |
| Scanner incremental no tiene ledger persistente por archivo | audit, nas-context y draft | Gap confirmado |
| `contracts.json` trata varios comandos como shared, pero docs marcan `diff`, `size`, `net`, `watch` Bash-only | contrato vs tabla CLI | Contradicción abierta |
| Hay documentos y tablas con estados o conteos históricos | audit, TODO, PENDIENTES y nas-context | Reconciliación pendiente |
| `nas-context.md` mezcla “auto-generado” con actualizaciones manuales y fechas distintas | encabezado + progressive updates | Clarificar ownership |
| El runtime Python no pudo ejecutarse completamente | sandbox sin `rich`/`yaml` | Limitación conocida |
| Docker Compose y NAS real no están disponibles/autorizados | entorno de trabajo | No intentar desde sandbox |

## 5. Archivos creados o modificados en esta sesión

| Archivo | Acción | Estado |
|---|---|---|
| `docs/framework-knowledge-compilation.md` | Creado | ✅ Documento canónico completo |
| `_drafts/SESSION-2026-08-architecture-knowledge.md` | Creado | ✅ Handoff autocontenido |
| `docs/ideas-decisions.md` | Modificado | ✅ Índice duplicado corregido y enlace canónico añadido |
| `docs/framework-audit.md` | Modificado | ✅ Enlaza al mapa canónico y lo clasifica como inventario ejecutivo |
| `docs/architecture-consistency.md` | Modificado | ✅ Enlaza al mapa canónico; conserva contratos y límites |
| `docs/dependency-map.md` | Modificado | ✅ Enlaza al mapa canónico; conserva cascadas |
| `AGENTS.md` | Modificado | ✅ Añade la referencia del mapa canónico |
| `docker-nas/references/nas-context.md` | Modificado | ✅ Enlaza al mapa canónico y cambia el orden de carga inicial |

Otros archivos que aparezcan modificados en `git status` pueden corresponder a la implementación previa del scanner y contratos; no deben atribuirse a esta consolidación si no están en la tabla anterior.

## 6. Gaps accionables para la próxima sesión

1. Reconciliar `contracts.json` con la realidad Bash/Python: implementar passthrough verificable o declarar excepciones Bash-only.
2. Implementar ledger incremental por archivo con hash y estados `changed/pending/processing/processed/failed/ignored`.
3. Completar detección de staged, unstaged, no trackeados y eliminados en ambos repositorios.
4. Verificar si `nas_agent.py` carga físicamente `docker-nas/references/nas-context.md` o si solo incorpora bloques equivalentes.
5. Reconciliar servicios, redes, estados `deployed/cataloged/native/planned/runtime-only`, conteos y fechas entre audit, AGENTS, skill, catálogo y DebMenux.
6. Añadir detectores para `catalog.json`, `services.json` y las superficies de conocimiento/manuales.
7. Limpiar los estados históricos en `TODO.md` y `_drafts/PENDIENTES-proxima-sesion.md` sin borrar evidencia histórica.
8. Verificar semánticamente la tabla de comandos y actualizar `README.md`/`GUIDE.md` si el flujo de documentación lo requiere.
9. No implementar `common.yml`/perfiles todavía: reevaluar cuando la cantidad de servicios lo justifique.

## 7. Estado del sistema al cerrar

- Repositorios en workspace: `/projects/sandbox/nas-dotfiles` y `/projects/sandbox/DebMenux-`.
- La tarea fue documental; no se operó el NAS real.
- Docker Compose no está disponible en el sandbox.
- Python completo no pudo ejecutarse por `ModuleNotFoundError: yaml` y `ModuleNotFoundError: rich`; sí se usaron validaciones estáticas previas.
- `agent/cache/project-snapshot.json` y `agent/cache/project-index.json` son artefactos runtime ignorados; no modificarlos deliberadamente.
- Las modificaciones de la sesión se listan en la sección 5. No hacer commit ni push automáticamente.

## 8. Instrucciones para continuar

1. Leer este handoff.
2. Leer `docs/framework-knowledge-compilation.md` como mapa canónico.
3. Leer `docs/architecture-consistency.md` para contratos y `docs/dependency-map.md` para cascadas.
4. Si se va a cambiar un compose, leer primero `docs/docker-entorno.md` y la guía del servicio correspondiente.
5. Ejecutar solo verificaciones disponibles en el sandbox; no simular runtime del NAS.
6. Resolver primero la contradicción de paridad CLI y el ledger incremental antes de añadir nuevas features Docker.
7. Tras cada modificación, verificar referencias cruzadas y actualizar el documento dueño, no copiar la misma prosa en todas las superficies.
8. Al terminar una sesión larga, crear otro `SESSION-*` con hechos verificados, limitaciones y pendientes.

## 9. Contexto que no debe perderse

- `dependency-map` = qué debería estar conectado.
- `project-index` = qué existe y dónde se conecta.
- `project-scanner` = qué parece estar roto o desincronizado.
- `catalog-sync` = cómo generar artefactos faltantes; no reemplaza revisión semántica.
- `session-handoff` = cómo continuar entre sesiones.
- `_drafts` = entrada temporal que debe clasificarse.
- Bash es la fuente de verdad operacional y Python la interfaz/wrapper, pero la paridad real aún debe medirse y documentarse honestamente.
- Una documentación correcta debe permitir comprobar las ideas del usuario con criterios de aceptación, no solo describir que las ideas existen.
