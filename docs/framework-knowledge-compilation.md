# Compilación de conocimiento del framework

> **Estado:** documento canónico de arquitectura y continuidad
> **Fecha de esta compilación:** 2026-08-17
> **Alcance:** `nas-dotfiles` + `DebMenux-` como un solo sistema interconectado
> **Propósito:** conservar las ideas, decisiones, arquitectura objetivo, gaps y criterios de verificación de la conversación sin copiar el chat completo.

Este documento responde a una pregunta distinta de un inventario: **¿cómo se conecta el sistema y cómo sabemos que una modificación dejó algo desincronizado?** Es el mapa canónico para orientarse. No reemplaza las guías operativas, los contratos ejecutables, el mapa de cascadas ni el historial de decisiones.

## 1. Problema original e intención del usuario

El problema no era solamente que faltaran features. El framework ya tenía shell, CLI, agente, servicios, catálogo, skill, documentación y automatizaciones, pero una modificación podía crear un archivo correcto y dejar el resto del sistema desincronizado:

- un script podía existir sin estar conectado a `svc.sh`, Python, completions o el prompt del agente;
- un compose podía cambiar sin actualizar ficha, guía, catálogo, DebMenux, `AGENTS.md` o la skill;
- Bash y Python podían anunciar distintos comandos;
- el `dependency-map` podía describir una cascada esperada sin comprobar que la conexión existiera;
- un LLM podía implementar una feature y cerrar la sesión sin registrar el razonamiento ni actualizar las superficies de conocimiento.

La intención expresada por el usuario fue construir un sistema que:

1. conserve el **porqué** de las decisiones para futuras sesiones;
2. describa **qué debería estar conectado**;
3. descubra **qué existe realmente y dónde se conecta**;
4. detecte automáticamente gaps, drift, huérfanos y diferencias entre superficies;
5. permita al LLM consultar el impacto real antes de inventar una cascada de archivos;
6. mantenga la continuidad entre sesiones sin almacenar todo el chat;
7. permita comprobar posteriormente si las ideas originales se cumplieron.

### Lo que se rechazó

No se debe guardar una transcripción completa de la conversación como memoria del proyecto. Es ruidosa, cuesta contexto, mezcla hechos con hipótesis y no ofrece una estructura para verificar resultados. La alternativa adoptada es una **compilación del conocimiento**: decisiones históricas separadas de arquitectura, estado actual, gaps y criterios de aceptación.

## 2. Evolución de las ideas

La arquitectura actual se desarrolló por capas, a partir de errores concretos:

1. **Operación fiable del NAS.** Se resolvieron notificaciones headless con ntfy, USB API nativa, montajes por LABEL, Homepage mediante labels, configuración de Home Assistant con `!include` y workarounds reales de ntfy.
2. **Documentación en cascada.** El problema de olvidar ficha, guía, `.env.example`, script DebMenux o skill llevó a `catalog-sync`, integración bidireccional y hooks. La generación evita sobrescribir documentación existente y ofrece `--dry-run`/`--status`.
3. **Conocimiento utilizable por cualquier agente.** La skill 2.0 introdujo registry, lazy loading, progressive updates y trigger proactivo. `AGENTS.md` extendió las reglas a agentes que no cargan la skill de Kiro.
4. **Reglas de impacto.** `docs/dependency-map.md` formalizó qué archivos revisar después de tocar un servicio, script, tool, plugin, template, documento o variable global.
5. **El fallo que cambió el objetivo.** Se creó `catalog-sync.sh`, pero durante un tiempo no estuvo conectado al CLI. Esto demostró que “el archivo existe” no significa “la capacidad existe”. La misma clase de fallo apareció entre Bash/Python y en documentación desactualizada.
6. **Arquitectura verificable.** Se añadieron `contracts.json`, `project_index.py` y la integración de contratos en `project_scanner.py`. El `dependency-map` sigue expresando expectativas; el índice descubre conexiones; el scanner compara ambas cosas.
7. **Continuidad verificable.** `docs/session-handoff.md` define cómo conservar decisiones, errores y pendientes accionables. Esta compilación es el documento permanente; un `SESSION-*` es el estado de una sesión concreta y su punto de reanudación.

El historial narrativo completo permanece en [`docs/ideas-decisions.md`](ideas-decisions.md), especialmente las entradas 5, 6, 7, 11, 12, 13, 14 y 15. La entrada 16 documenta la decisión de centralizar defaults con `extends` y `_common.yml`.

## 3. Modelo arquitectónico

### 3.1 Dos repositorios, un sistema

```text
usuario / LLM
    │
    ├── Shell y aliases
    │      ~/.bashrc → shell/init.sh → svc()
    │
    ├── CLI operacional
    │      NAS_CLI=bash   → docker/cli/svc.sh → libs Bash
    │      NAS_CLI=python → svc_py/app.py → wrappers/UI → bash_bridge cuando aplica
    │
    ├── Agente IA
    │      agent/nas_agent.py → tools/plugins → servicios, catálogo y diagnóstico
    │
    ├── Verificación y documentación
    │      contracts.json + project_index.py + project_scanner.py + catalog-sync
    │
    └── DebMenux
           scripts/services/*.sh + services.json + templates
           integración hacia el catálogo de nas-dotfiles
```

`nas-dotfiles` contiene el shell, CLI, agente, catálogo, skill y documentación. `DebMenux-` contiene el menú, instalador, registro de servicios, scripts y templates. Un cambio que afecta una capacidad puede cruzar ambos repositorios; por eso el mapa de dependencias y los contratos usan ambos como alcance.

### 3.2 Cinco clases de conocimiento

| Capa | Pregunta que responde | Fuente principal | No debe convertirse en |
|---|---|---|---|
| Código/runtime | ¿Qué ejecuta la capacidad? | scripts, módulos, compose y servicios | una promesa basada solo en docs |
| Estado/observación | ¿Qué existe y qué cambió? | `project-index.json`, snapshot y scanner | una fuente manual editada a mano |
| Contratos | ¿Qué conexiones mínimas son obligatorias? | `agent/architecture/contracts.json` | un inventario de todos los detalles |
| Conocimiento operativo | ¿Cómo se usa y recupera? | guías, `AGENTS.md`, skill y referencias | copia completa de cada compose |
| Continuidad/historia | ¿Por qué se decidió así? | `ideas-decisions.md`, `SESSION-*`, drafts | estado actual sin reconciliar |

### 3.3 Autoridad cuando hay contradicciones

Al encontrar discrepancias, el LLM debe aplicar esta precedencia y registrar el conflicto en lugar de elegir silenciosamente:

1. **Código y configuración fuente** para saber qué puede ejecutarse (`svc.sh`, `svc_py`, scripts, compose real).
2. **Contratos y salida verificable** para saber qué conexiones mínimas se exigen y qué se detectó.
3. **Estado del NAS real**, solo cuando se ejecuten verificaciones autorizadas en el NAS; el sandbox no lo sustituye.
4. **Catálogo generado** como representación para el agente, no como autoridad superior al compose fuente.
5. **Guías y referencias operativas** para procedimientos, permisos, errores y recuperación.
6. **`AGENTS.md` y skill** para reglas de comportamiento y contexto comprimido.
7. **Historial y drafts** para el porqué y la evidencia de evolución; nunca asumir que un pendiente histórico sigue abierto sin comprobarlo.

Cada estado de este documento debe distinguir `verificado` (comprobado en código o comando indicado), `declarado` (documentado pero no comprobado en esta sesión) y `pendiente`.

## 4. Ownership: qué documento posee cada cosa

| Documento/componente | Posee | No posee | Consumidores |
|---|---|---|---|
| Este archivo | mapa canónico, relaciones, estado de alto nivel, gaps y criterios | instrucciones exhaustivas de operación o lógica ejecutable | LLM y mantenedores al inicio de una investigación |
| `docs/ideas-decisions.md` | problema → idea → solución → aprendizaje | estado actual completo | quien necesite el porqué histórico |
| `docs/architecture-consistency.md` | diseño de contratos, niveles y alcance del scanner | inventario operativo completo | implementadores del scanner |
| `agent/architecture/contracts.json` | conexiones mínimas verificables en formato máquina | prosa, procedimientos y backlog | `project_index.py` y `project_scanner.py` |
| `agent/tools/project_index.py` | descubrimiento estructural real de archivos/conexiones | interpretación humana de por qué existe algo | scanner y diagnóstico |
| `agent/tools/project_scanner.py` | comparación y reporte de gaps, drift, orphan y parity | generar documentación faltante | `svc scan`, agente y mantenedores |
| `docs/dependency-map.md` | cascadas esperadas y checklist de impacto | prueba de que la conexión existe | LLM antes/después de cambios |
| `catalog-sync` | generación de artefactos documentales faltantes | decisión arquitectónica y validación semántica completa | catálogo, guías y DebMenux |
| `AGENTS.md` | reglas operativas breves para cualquier agente | historia detallada | agentes externos y humanos |
| `docker-nas/references/nas-context.md` | contexto comprimido, registry y comportamiento proactivo | reemplazar las guías cargadas bajo demanda | skill de Kiro/LLM |
| `docs/framework-audit.md` | orientación ejecutiva e inventario de módulos | ser la prueba de consistencia | inicio rápido de una sesión |
| `docs/session-handoff.md` + `_drafts/SESSION-*` | protocolo y estado de una sesión | convertirse en catálogo permanente | próxima sesión |
| `TODO.md` y `_drafts/` | backlog, ideas y evidencia temporal | autoridad del estado sin reconciliación | planificación y clasificación |

**Regla:** si una superficie repite un dato de otra, debe enlazarla o indicar que es un resumen derivado. No crear una tercera copia de la misma narrativa.

## 5. Flujos que deben permanecer conectados

### 5.1 Flujo de operación y CLI dual

```text
~/.bashrc
  → shell/init.sh
  → función svc()
  → NAS_CLI
      ├─ bash   → docker/cli/svc.sh → lógica en docker/cli/lib/*.sh
      └─ python → svc_py/app.py → UI/wrappers → bash_bridge cuando corresponde
```

La decisión vigente es **Bash = fuente de verdad operacional; Python = interfaz/wrapper**. No se debe duplicar lógica de negocio. Sin embargo, el passthrough genérico de Python que se afirmó históricamente no está completamente garantizado: `diff`, `size`, `net` y `watch` aparecen como Bash-only en la tabla real. Hasta corregirlo, la paridad es **reporting**, no una afirmación de equivalencia.

Al añadir un comando se debe comprobar: case o dispatch Bash, wrapper/passthrough Python, completions, prompt del agente, referencias de comandos y contrato si es una capacidad crítica. Un comando que solo funciona en Bash debe estar marcado explícitamente como tal.

### 5.2 Flujo de arquitectura verificable

```text
contracts.json
       +
archivos de ambos repositorios
       ↓
project_index.py → agent/cache/project-index.json
       ↓
project_scanner.py → issues de contratos, paridad, huérfanos y drift
       ↓
catálogo/documentación faltante → catalog-sync
       ↓
revisión humana + dependency-map + actualización manual de superficies
```

- `dependency-map` dice **qué debería estar conectado**.
- `project_index` descubre **qué existe y dónde se conecta**.
- `project_scanner` indica **qué parece roto, ausente o desincronizado**.
- `catalog-sync` genera **artefactos faltantes**, pero no decide si la arquitectura es correcta.
- `project-index.json` es mapa estructural; `project-snapshot.json` es delta/base del scan. No se deben fusionar.

El resultado verificado de esta fase fue: `237 archivos`, `16 servicios`, `4 contratos`, `0 conexiones funcionales rotas`. También se confirmaron gaps de comandos Python-only/Bash-only, conocimiento faltante de `kill` y desajustes entre scripts/registry de DebMenux. El runtime Python completo no pudo ejecutarse en el sandbox por falta de `rich` y `yaml`; la validación fue estática.

### 5.3 Flujo de servicio y documentación

```text
compose real ($dkco/<svc>/compose.yml)
  → catálogo (ficha + compose + .env.example)
  → guía operativa docs/services/<svc>-guide.md
  → skill/AGENTS/manuales
  → DebMenux script + services.json
  → scanner verifica presencia/conexiones
```

El compose real es la fuente de verdad de configuración. La ficha contiene metadatos para descubrimiento, la guía contiene conocimiento operativo no inferible (errores, permisos, recuperación, backups) y la skill solo resume hechos accionables. Para servicios nuevos se debe respetar `docs/docker-entorno.md`, leer primero la guía de dependencias si aplica y ejecutar la secuencia `mkdir → archivos → permisos → levantar`.

## 6. Decisiones y alternativas rechazadas

| Decisión | Motivo | Alternativa rechazada |
|---|---|---|
| Compilación de conocimiento, no transcripción del chat | reduce ruido y conserva razonamiento verificable | almacenar todo el historial literal |
| `dependency-map` como reglas estáticas | hace explícita la cascada humana | pretender que un documento estático prueba conexiones |
| Índice estructural separado del snapshot | existencia/conexiones y cambios tienen ciclos de vida distintos | un único JSON mezclando arquitectura y estado incremental |
| Contratos por niveles | distingue errores funcionales de warnings de interfaz/conocimiento e info histórica | lista plana que bloquea o ignora todo por igual |
| Bash como verdad y Python como UI | evita duplicar lógica y mantiene fallback sin dependencias | implementar la lógica dos veces |
| Paridad CLI en modo `report` por ahora | la realidad todavía tiene comandos diferentes | afirmar que ambos CLIs son equivalentes |
| `catalog-sync` no sobrescribe docs existentes | protege conocimiento operativo escrito a mano | regenerar y perder experiencia real |
| `AGENTS.md` complementa a la skill | otros agentes también necesitan reglas | depender solo de Kiro |
| guías por servicio separadas del catálogo | errores reales y recuperación no se deducen del compose | hacer que una ficha reemplace la guía |
| no modificar NAS ni subir GitHub durante esta documentación | evita cambios operativos no autorizados | probar en el NAS desde el sandbox |
| `extends` + `_common.yml` como dirección futura/gradual | centraliza defaults sin copiar anchors en cada compose | añadir una capa común antes de que el número de servicios lo justifique |

El razonamiento detallado de las decisiones de servicios, notificaciones, USB, Homepage, HA, catálogo y dual CLI está en [`ideas-decisions.md`](ideas-decisions.md). No se debe trasladar aquí toda esa narrativa.

## 7. Estado actual reconciliado

### 7.1 Implementado o presente

| Capacidad | Estado | Evidencia/fuente | Alcance de la afirmación |
|---|---|---|---|
| `contracts.json` | verificado | archivo JSON + scanner | contratos iniciales, no todos los deseos futuros |
| índice estructural | verificado | `project_index.py --check` | ambos repositorios en el workspace |
| scanner integrado con contratos | verificado | `project_scanner.py`, `svc scan --json --full` estático | reporta, no corrige automáticamente |
| `catalog-sync` Bash/Python | declarado + conexiones verificadas | `svc.sh`, `svc_py`, contracts | no implica que todas las docs estén completas |
| snapshot incremental | verificado parcialmente | `project-snapshot.json`, scanner | no tiene ledger por archivo completo |
| catálogo pre-cargado del agente | declarado | `nas_agent.py`/audit | comprobar carga física y evitar confundir resumen con skill |
| `compare_catalog` | declarado | `agent/tools/compare_tools.py` según audit | requiere ejecución con runtime/dependencias y NAS autorizado |
| snapshot/rollback de servicios | declarado | comandos/documentación de audit | no se probó contra NAS en esta tarea |
| skill registry/progressive updates | presente | `nas-context.md` | tiene contradicciones de fecha/generación que deben limpiarse |
| continuidad por handoff | protocolo presente | `docs/session-handoff.md` | este documento añade una compilación canónica |

### 7.2 Estado del ecosistema

El inventario operativo de servicios y puertos permanece en [`framework-audit.md`](framework-audit.md), [`AGENTS.md`](../AGENTS.md), [`nas-context.md`](../docker-nas/references/nas-context.md) y el manual del NAS. Esos inventarios no están totalmente reconciliados: por ejemplo, EMQX aparece con `db_net` en algunas superficies antiguas y sin ella en la corrección posterior; `spacedrive` aparece en algunas tablas, pero no en todas; los conteos de plugins/tools/guías también varían. Hasta ejecutar una reconciliación, este documento no eleva una tabla única de servicios a autoridad runtime.

### 7.3 Limitaciones del entorno de verificación

- Docker Compose no está disponible en el sandbox.
- No se debe operar el NAS real desde el sandbox.
- El CLI Python no pudo ejecutarse completamente porque faltan `rich` y `yaml`.
- Los caches `agent/cache/project-snapshot.json` y `agent/cache/project-index.json` son artefactos runtime ignorados por Git; no deben documentarse como cambios de código.
- La compilación documenta estado declarado o estático cuando no existe verificación runtime.

## 8. Gaps confirmados

Prioridad alta:

1. **Ledger incremental por archivo:** faltan estados persistentes `processed/pending/failed` (además de changed/processing/ignored), hashes y recuperación tras interrupciones.
2. **Cobertura Git completa:** el scanner no resuelve todavía de forma completa commits, staged, unstaged, no trackeados y eliminados en ambos repositorios.
3. **Contrato CLI incoherente:** `contracts.json` lista `required_shared_commands`, pero la tabla real marca `diff`, `size`, `net` y `watch` como Bash-only. Elegir passthrough real o excepciones explícitas y actualizar contrato/documentación.
4. **Sincronización de superficies de conocimiento:** `catalog-sync` no garantiza sincronizar `services.json`, `catalog.json`, `AGENTS.md`, `nas-context.md` y todas las tablas manuales.
5. **Fuente física del contexto del agente:** comprobar y documentar si `nas_agent.py` carga realmente `docker-nas/references/nas-context.md`; no basta con que el archivo exista.
6. **Reconciliación de servicios/redes:** corregir las superficies que aún muestran EMQX en `db_net` o servicios planificados como activos, y separar `deployed`, `cataloged`, `native`, `planned` y `runtime-only`.
7. **Reglas DataSQL en creación de servicios:** las reglas están en docs/skill, pero deben quedar cubiertas de forma verificable en el prompt/creador del agente (`env_file`, `extends`, `db_net`, no publicar DB, no `depends_on` cross-compose).

Prioridad media:

8. **Contenido semántico de documentación:** el scanner detecta conexiones, pero no verifica que la tabla CLI o una guía reflejen exactamente el código/configuración.
9. **Catalog index stale:** comprobar y regenerar `catalog.json` como parte de una verificación reproducible.
10. **Diferencia auto-generado/manual:** marcar bloques de `nas-context.md`, fecha de generación y reglas para no editar a mano secciones que el pipeline reemplaza.
11. **Docs/editorial:** limpiar numeración/índice de `ideas-decisions.md`, conteos antiguos en audit/README/GUIDE y referencias duplicadas.
12. **Filebrowser y servicios futuros:** mantener explícito qué falta por instalar/documentar (n8n, vaultwarden u otros) sin listarlos como activos.

## 9. Criterios de aceptación para comprobar las ideas del usuario

Estos criterios son la lista de verificación futura; “documentado” no cuenta como “cumplido” si no hay evidencia.

### Arquitectura y conexiones

- [ ] Para cada capacidad pública, el índice identifica archivo de implementación, entrypoint, consumidor y documentación relevante.
- [ ] Crear un script aislado y ejecutar el scanner produce un warning/error de conexión faltante.
- [ ] La salida diferencia `functional`, `interface`, `knowledge`, `documentation` e `historical` con severidad coherente.
- [ ] El scanner cubre ambos repositorios y distingue conexiones reales de reglas esperadas.
- [ ] Un cambio de compose puede mapear servicios afectados y listar la cascada relevante sin releer todo el repositorio.

### CLI

- [ ] La tabla Bash/Python coincide con dispatch y passthrough reales, o las excepciones Bash-only están declaradas en contracts y docs.
- [ ] Un comando nuevo tiene una prueba de invocación para Bash, Python (si se promete), completions y agente.
- [ ] Bash conserva la lógica operacional; Python no introduce una segunda implementación divergente.

### Documentación y catálogo

- [ ] Un servicio tiene compose fuente, ficha, `.env.example`, guía, script/registro DebMenux cuando corresponda y referencias de skill/agente.
- [ ] `catalog-sync --status` y el scanner identifican los archivos ausentes o stale.
- [ ] `catalog.json` puede regenerarse y su contenido coincide con los directorios del catálogo.
- [ ] Las guías contienen conocimiento operativo no inferible del compose y no se sobrescriben automáticamente.
- [ ] La tabla de cada superficie indica si el dato está derivado, manual, declarado o verificado.

### Continuidad y mejora

- [ ] Cada sesión larga crea un `SESSION-*` con objetivo, decisiones, errores, archivos, pendientes y estado.
- [ ] Los drafts se clasifican como plan, fragmentos, compose, idea, histórico o implementado; no se toman como estado vigente automáticamente.
- [ ] El feedback del usuario se registra en la superficie adecuada, sin duplicar toda la conversación.
- [ ] Al cerrar una feature, el LLM consulta dependency-map, ejecuta verificaciones disponibles y reporta explícitamente lo que no pudo comprobar.

### Operación segura

- [ ] Cambiar un compose exige leer `docs/docker-entorno.md` y, si existe, la guía específica antes de proponer cambios.
- [ ] Las guías de instalación respetan `mkdir → archivos → permisos → levantar`.
- [ ] La documentación no ejecuta Docker/NAS desde un entorno que no tiene autorización o herramientas para hacerlo.

## 10. Roadmap recomendado

### Fase 1 — Reconciliación documental (siguiente)

- Usar esta compilación como índice canónico desde audit, architecture-consistency, dependency-map, AGENTS y nas-context.
- Resolver duplicados del índice de `ideas-decisions.md`.
- Reconciliar servicios, redes, conteos y fechas; marcar fuentes y estados.
- Corregir la declaración de comandos shared/Bash-only en `contracts.json` y documentación.

### Fase 2 — Scanner verificable de extremo a extremo

- Implementar ledger por archivo y cobertura completa de estados Git.
- Añadir detectores de sincronización entre compose, catálogo, `catalog.json`, `services.json`, AGENTS y skill.
- Verificar semántica mínima (por ejemplo, tabla CLI frente a dispatch/completions) sin intentar comprender toda la prosa.
- Añadir salida accionable: archivo origen, conexión esperada, conexión observada, severidad y siguiente acción.

### Fase 3 — Reducción de duplicación

- Definir qué tablas se generan y cuáles son manuales.
- Hacer que `catalog-sync` actualice solo superficies seguras y deje warnings para conocimiento operativo manual.
- Separar en cada registro estado `deployed/cataloged/native/planned`.
- Verificar la carga física de `nas-context.md` y del catálogo pre-cargado del agente.

### Fase 4 — Estandarización gradual

- Evaluar `common.yml`/perfiles cuando el número de servicios justifique la complejidad; no implementarlo prematuramente.
- Mantener `extends` y los defaults definidos por las reglas actuales, validando primero compatibilidad por servicio.
- Añadir pruebas de contrato para comandos, servicios, hooks y cascadas cross-repo.

## 11. Protocolo para futuras sesiones

1. Leer este documento para entender el modelo y los gaps.
2. Leer `docs/session-handoff.md` y el `SESSION-*` más reciente si existe.
3. Para cambios de servicio/compose, leer primero `docs/docker-entorno.md` y la guía del servicio.
4. Para el impacto de un cambio, leer `docs/dependency-map.md`; para implementación verificable, revisar `contracts.json` e índice.
5. Ejecutar solo verificaciones permitidas por el entorno y separar resultados `verificados` de `declarados`.
6. No modificar el NAS real ni subir a GitHub sin aprobación del usuario.
7. Antes de cerrar, actualizar el documento dueño del conocimiento, registrar decisiones nuevas en `ideas-decisions.md` si corresponde y crear un handoff si la sesión fue larga.

## 12. Referencias

- [Auditoría ejecutiva](framework-audit.md)
- [Contratos y scanner](architecture-consistency.md)
- [Mapa de dependencias](dependency-map.md)
- [Historial de ideas y decisiones](ideas-decisions.md)
- [Protocolo de handoff](session-handoff.md)
- [Reglas del entorno Docker](docker-entorno.md)
- [Contexto operativo de la skill](../docker-nas/references/nas-context.md)
- [Contratos máquina](../agent/architecture/contracts.json)
- [Índice estructural](../agent/tools/project_index.py)
- [Scanner](../agent/tools/project_scanner.py)
- [Guía de continuidad histórica](../_drafts/SESSION-2026-08-architecture-knowledge.md)
