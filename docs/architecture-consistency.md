# Architecture Consistency Scanner

> **Mapa canónico relacionado:** [`framework-knowledge-compilation.md`](framework-knowledge-compilation.md). Esta especificación conserva los contratos, niveles y límites de verificación; no duplica el estado general del framework.

> Primera especificación de contratos verificables para `nas-dotfiles` + `DebMenux-`.

## Propósito

El `dependency-map` describe conexiones esperadas, pero no demuestra que existan. Esta capa añade contratos verificables para que el scanner pueda comparar:

```text
contrato esperado + índice estructural actual → gaps, drift, orphan y parity
```

No sustituye al `dependency-map`, `catalog-sync` ni al snapshot incremental. Cada pieza tiene una responsabilidad distinta:

| Pieza | Responsabilidad |
|---|---|
| `docs/dependency-map.md` | Explicar la cascada y el razonamiento humano |
| `agent/architecture/contracts.json` | Definir conexiones mínimas verificables |
| `agent/tools/project_index.py` | Descubrir entidades y conexiones reales |
| `agent/cache/project-index.json` | Guardar el último mapa estructural generado |
| `agent/tools/project_scanner.py` | Comparar realidad contra contratos y reportar inconsistencias |
| `catalog-sync` | Generar documentación faltante después del diagnóstico |

## Niveles de dependencia

Las conexiones se clasifican para evitar que el mapa sea una lista plana:

1. **functional** — necesaria para ejecutar la capacidad; severidad `error`.
2. **interface** — necesaria para exponerla al usuario; severidad `warning`.
3. **knowledge** — necesaria para que el agente o la skill la conozcan; severidad `warning`.
4. **documentation** — necesaria para mantener referencias públicas; severidad `info`.
5. **historical** — conserva decisiones y continuidad; severidad `info`.

## Contratos iniciales

La primera versión verifica dos comandos críticos:

- `catalog-sync`
- `scan`

Para cada uno se comprueba la conexión funcional entre Bash/Python y sus módulos. También se registran las superficies de interfaz, conocimiento y documentación para que la siguiente fase pueda detectar comandos huérfanos o desactualizados.

La paridad CLI se configura inicialmente en modo `report`: las diferencias Bash/Python se muestran, pero no bloquean todo el scan. Esto permite corregir la realidad actual sin falsear el estado del sistema.

## Índice estructural

El índice generado representa entidades, archivos, comandos y conexiones observadas en ambos repositorios. Es una memoria estructural; no es una fuente de verdad manual y debe regenerarse cuando cambien los archivos.

```bash
python3 agent/tools/project_index.py
```

El resultado se guarda en:

```text
agent/cache/project-index.json
```

Este archivo es distinto de `project-snapshot.json`:

- `project-index.json` = qué existe y cómo está conectado.
- `project-snapshot.json` = estado del último scan incremental.

## Alcance de esta primera fase

Incluido:

- contratos versionados y legibles sin dependencias externas;
- descubrimiento de ambos repositorios;
- comandos Bash y Python;
- completions de `svc`;
- tools registradas en `ALL_TOOLS`;
- scripts DebMenux y entradas de `services.json`;
- documentos y hooks relevantes;
- conexiones funcionales mínimas de `catalog-sync` y `scan`.

Pendiente:

- ledger `processed/pending/failed` por archivo;
- análisis semántico profundo de documentación;
- clasificación automática completa de `_drafts/`;
- grafo de imports/source/case con resolución completa;
- detección de cambios staged/unstaged/eliminados en el scanner incremental;
- actualización automática de `AGENTS.md`, `nas-context.md` y `services.json`.

## Regla de evolución

No añadir un nuevo comando, tool, servicio o hook únicamente al código. Debe declararse como entidad o conexión verificable y luego aparecer en el índice. El scanner debe poder responder:

```text
¿Qué existe?
¿Dónde se invoca?
¿Qué superficies dependen de ello?
¿Qué quedó desincronizado después del cambio?
```
