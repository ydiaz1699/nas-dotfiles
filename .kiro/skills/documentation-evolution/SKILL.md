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
| "hay un error", "falta conectar", "no se detectó" | Leer `project_scanner.py`, `project_index.py` y `contracts.json` |
| "evolucionar la herramienta", "hacerla automática" | Revisar implementación, entrypoints, hooks, docs y contrato; no limitarse a añadir texto |
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
3. Clasifica afirmaciones con **tipo** y **confianza** como campos
   independientes:
   - Tipo: `HECHO`, `INFERENCIA SEGURA`, `INFERENCIA NO CONFIRMADA`,
     `DESCONOCIDO`.
   - Confianza: `ALTA`, `MEDIA`, `BAJA`, `DESCONOCIDA`.
   Una INFERENCIA SEGURA puede tener confianza ALTA si la relación técnica es
   inequívoca. Un HECHO puede tener confianza MEDIA si la fuente es ambigua.
4. Identifica artefactos con: tipo (archivo, directorio, servicio, contenedor,
   variable, etc.), identificador, estado inicial, operación y estado esperado.
5. Agrupa solo variantes **operacionalmente equivalentes** (mismo efecto sobre
   los mismos artefactos). No fusionar por equivalencia textual o semántica si
   el efecto difiere. Compara propósito, mutación vs. consulta, seguridad,
   idempotencia, timeout, observabilidad, reversibilidad y compatibilidad. Si no
   se puede determinar cuál es mejor, deja `PENDIENTE`.
6. Reconstruye un grafo temporal con `requiere`, `produce`, `crea`, `modifica`,
   `elimina`, `respalda`, `restaura`, `consume`, `verifica`, `habilita`,
   `deshabilita`, `inicia`, `detiene`, `reinicia`, `precondición` y
   `postcondición`. Un backup precede las operaciones que puedan afectar el
   artefacto que protege; no todo restart requiere backup.
7. Si aparece un ciclo, marca `⚠️ CICLO DE DEPENDENCIAS` y no fuerces un orden.
8. Conserva las rutas exactas de backups y comprueba que el rollback consume el
   artefacto creado.
9. Clasifica cada elemento con las 7 categorías: `INTEGRADO`, `DUPLICADO`,
   `REEMPLAZADO`, `RECHAZADO` con motivo, `FUERA_DE_ALCANCE` con destino,
   `PENDIENTE` o `BLOQUEADO`.
   - PENDIENTE: la información existe pero es contradictoria o ambigua.
   - BLOQUEADO: la información no existe en ninguna fuente disponible.

No sobre-unificar: dos operaciones con el mismo propósito pero sobre artefactos
diferentes no son duplicados. Solo la equivalencia operacional justifica
eliminación.

Distingue siempre `systemctl enable ...` (mutación) de
`systemctl is-enabled ...` (verificación). Si la guía se convertirá en script,
revisa errores, paradas seguras y rollback antes de llamarla ejecutable.

La salida debe incluir una sección compacta `AUDITORÍA DE FUENTES Y VARIANTES`
con tipo y confianza como columnas separadas. No inventes verificaciones: si una
fuente no proporciona ninguna, marca `⚠️ NO ESPECIFICADO` y separa cualquier
propuesta externa. No afirmes que se verificó algo si no se ejecutó realmente.

## Reglas de optimización y contexto del proyecto

Elementos como `set -euo pipefail`, wrappers (`svc`, `dk`, `instal`),
parametrización (`${SERVER_IP}`) o convenciones del framework son reglas de
OPTIMIZACIÓN o CONTEXTO. No se aplican automáticamente durante la reconciliación:

- Durante RECONSTRUCCIÓN y RECONCILIACIÓN: preservar los valores y comandos
  literales de las fuentes.
- Durante OPTIMIZACIÓN (solo si se solicita): aplicar las reglas del proyecto
  con propuesta explícita y autorización.
- Si las fuentes provienen de un contexto externo donde los wrappers no existen,
  no transformar comandos estándar en wrappers del proyecto.

## Flujo obligatorio de unificación

1. Identificar la fuente de cada afirmación: conversación, draft, código o
   configuración actual.
2. Leer el meta-prompt completo y respetar sus reglas: preservar información,
   no inventar, detectar contradicciones y marcar huecos como pendientes o
   bloqueados.
3. Clasificar el resultado en una sola fuente canónica y derivaciones mínimas;
   no copiar la misma prosa en varias capas.
4. Respetar las dependencias reales entre artefactos (los patrones
   mkdir→archivo→chmod→servicio→verificar son heurísticas frecuentes, no un
   orden universal obligatorio).
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

## Autoalimentación desde evidencia runtime

Cuando el usuario entregue una salida del NAS, un Gist, un diagnóstico o una
corrección de un comando, tratarlo como **evidencia de ejecución**, no como una
pregunta aislada. La autoalimentación documental debe seguir esta cadena:

```text
evidencia runtime
  → síntoma exacto
  → causa confirmada o hipótesis separada
  → variante/comando que corrigió
  → postcondición observada
  → guía dueña actualizada
  → derivados revisados
  → aprendizaje reutilizable
  → validación y handoff siguiente
```

### Registro mínimo sin secretos

Antes de cerrar una incidencia, crear mentalmente o en el artefacto de
trazabilidad un registro con estos campos:

```yaml
incident_id: <servicio>-<síntoma-corto>
service: <servicio>
source: user-runtime-report | gist | log | code | guide
observed_at: <si la fuente lo proporciona; no inventar>
symptom: <salida sanitizada>
root_cause: <HECHO o hipótesis marcada>
mutations:
  - command: <comando completo sin valores secretos>
    target: <archivo/servicio/contenedor>
    backup: <ruta o NO_APLICA>
verification:
  - command: <verificación>
    expected: <salida segura>
postcondition: confirmed | partial | failed | unknown
owner_files:
  - <guía o documento canónico>
derived_files:
  - <compose/ficha/.env.example/skill/contexto afectados>
classification: INTEGRADO | REEMPLAZADO | RECHAZADO | PENDIENTE | BLOQUEADO
next_action: <siguiente paso único>
```

Nunca incluir contraseñas, tokens, `.env` real, hashes de secretos, salida
completa de `svc config` ni logs que los contengan. Sustituir valores por
`<secreto_local>`, conservar solo la operación y verificar mediante `PONG`,
`healthy`, `current_user`, `current_database`, `pong` u otra evidencia segura.

### Fuente de secretos: consumir, no mostrar

Cuando un comando necesite un secreto que ya existe en el NAS, el flujo preferido
es leerlo desde la fuente de verdad en una variable temporal y consumirlo dentro
del mismo bloque:

```bash
SERVICE_SECRET="$(awk -F= '$1=="KEY"{print substr($0,index($0,"=")+1); exit}' "$dkco/servicio/.env")"

if [[ -z "$SERVICE_SECRET" || "$SERVICE_SECRET" == "__pega_aqui__" ]]; then
  printf 'Falta KEY o usa el placeholder.\n' >&2
  unset SERVICE_SECRET
  exit 1
fi

# Usar "$SERVICE_SECRET" solo en la operación local autorizada.
unset SERVICE_SECRET
```

No pedir al usuario que copie o escriba manualmente una contraseña estable si el
agente puede leerla localmente y consumirla de forma segura. No sugerir comandos
que la impriman, como `grep ... | cut ...`, salvo que el usuario pida
explícitamente una inspección local y se advierta que la salida es secreta. Un
comando que muestra un valor no es equivalente a uno que lo transporta a una
operación local.

En este repositorio se prefieren `$dkco`, `$NAS_DOTFILES` y `$aadm`; no sustituirlos
por rutas hardcodeadas como `/docker` cuando el objetivo es reutilizar el flujo
en otro NAS. Si una herramienta externa requiere una ruta absoluta, marcarla
como variante externa y no convertirla en la regla canónica.

### Qué actualizar y en qué orden

1. **Guía dueña:** incorporar el problema, antes/después, causa, comando
   reproducible, verificación, rollback y límites. La guía es la única fuente de
   prosa operativa.
2. **Compose del catálogo:** actualizarlo si cambió imagen, entrypoint, red,
   volumen, healthcheck, puerto o variable. Mantener la diferencia de rutas
   `extends` entre NAS y catálogo.
3. **Ficha:** actualizar metadatos, healthcheck principal, notas y referencias
   operativas; no copiar el procedimiento completo.
4. **`.env.example`:** actualizarlo solo si cambió el contrato de variables; no
   copiar valores reales.
5. **`nas-context.md`:** añadir una línea breve si el aprendizaje evita que un
   futuro LLM repita el incidente.
6. **Esta skill:** modificarla solo si cambió el proceso general de auditoría,
   autoalimentación o continuidad; no usarla como depósito de detalles de un
   solo servicio.
7. **Scanner, contratos o hooks:** actualizar implementación y entrypoint si la
   corrección pretende ser automática. No afirmar que una conexión existe solo
   porque la skill la describe.

Después ejecutar las validaciones del repositorio y registrar qué fue realmente
comprobado. Una salida del usuario puede confirmar el runtime del NAS, pero no
sustituye `git diff --check`, `project_index.py`, `project_scanner.py` ni una
prueba del código del repositorio.

### Correcciones de comandos durante una guía

Si el usuario pega un comando que falló, conservar tres piezas:

- **Variante intentada:** comando exacto y error, clasificado como RECHAZADO o
  REEMPLAZADO; no volver a recomendarlo.
- **Causa del fallo:** parser, contexto Bash/`psql`, ruta inexistente, orden
  temporal o incompatibilidad del servicio.
- **Variante corregida:** comando completo, precondiciones y postcondición.

No convertir una línea YAML (`image:`, `entrypoint:`) en un comando Bash. No
recomendar dos mutaciones alternativas simultáneamente. Si una sustitución de
`sed` depende de una línea exacta y no coincide, documentar la variante robusta
y verificar el archivo antes de levantar el servicio.

### Handoff entre servicios

Al terminar un servicio y continuar con otro, guardar un handoff breve:

```text
COMPLETADO: <servicio>
EVIDENCIA: <salidas sanitizadas>
CAMBIOS: <archivos y runtime>
PENDIENTE: <riesgos o discrepancias>
NO_REPETIR: <operaciones destructivas o secretos ya establecidos>
SIGUIENTE: auditar <servicio siguiente> desde su guía, ficha, compose y .env.example
```

Para n8n, el siguiente agente debe empezar por auditar su compose/runtime y no
asumir que la existencia de `n8n_db` demuestra una conexión funcional. Debe leer
la guía de DataSQL y la guía/ficha de n8n si existen, comparar la contraseña de
Redis desde su fuente de verdad y comprobar healthcheck, reinicios, puertos,
redes y logs antes de modificar nada.

Si no existe un productor de eventos, un ledger o un hook que escriba estos
registros, describir este flujo como **autoalimentación asistida por la skill**,
no como automatización implementada. La skill puede obligar al LLM a extraer y
proponer el aprendizaje; persistirlo automáticamente requiere además una
herramienta, un entrypoint y una validación de conexión.


Cuando el usuario está ejecutando una guía paso a paso en el NAS, la conversación
se trata como una máquina de estados, no como una consulta nueva independiente.
La guía no debe reiniciarse ni desviarse aunque el usuario formule una pregunta
lateral.

### Detección

Considera que existe una guía activa si el usuario:

- pega la salida de un comando de la guía;
- menciona "me quedé en el paso", "continúa", "dónde estoy" o una sección de la guía;
- muestra un prompt del NAS (`root@...`, `svc`, `dk`) junto con comandos;
- pregunta por un error ocurrido dentro del flujo actual.

Antes de responder:

1. Busca el checkpoint más específico en `_drafts/SESSION-*.md`,
   `_drafts/SESION-*.md` o `_drafts/PENDIENTES-*.md`.
2. Si existe, lee solo el checkpoint relevante y compara su `Paso actual` con
   la última salida que el usuario proporcionó.
3. Si no existe, reconstruye el estado únicamente con evidencia explícita del
   chat. No infieras que una mutación terminó bien porque el usuario llegó a la
   sección siguiente.
4. Declara al inicio: `Ubicación actual: paso X — ...` y `Siguiente acción única:`.

### Reglas de avance

- Avanza un paso solo después de que la salida confirme su postcondición.
- No repitas prechecks ya confirmados, salvo que haya cambio, error o una
  dependencia que pueda haber quedado obsoleta.
- No ejecutes ni recomiendes dos mutaciones alternativas a la vez.
- Si una mutación puede ser no idempotente (`CREATE ROLE`, `CREATE DATABASE`,
  `mv`, `rm`, cambios de contraseña), primero consulta el estado o detente ante
  `already exists`.
- Si el usuario pregunta algo lateral, responde lo necesario y vuelve al mismo
  paso; no cambies de servicio, guía o arquitectura sin autorización explícita.
- Si el comando de la guía falla por la implementación real del wrapper, corrige
  primero la guía dueña y ofrece una variante compatible; no improvises una
  nueva secuencia que salte pasos.
- Antes de mostrar un comando, comprueba que sus opciones no sean consumidas por
  el wrapper. Para `svc exec` de este repositorio, evita pasar `-U`, `-d` o `-c`
  directamente; usa `PGUSER`, `PGDATABASE` y una sesión interactiva de `psql`.

### Checkpoint

Después de una mutación confirmada, actualiza el checkpoint específico de la
sesión con:

- estado (`EN_CURSO`, `PAUSADO_ESPERANDO_USUARIO`, `BLOQUEADO`, `COMPLETADO`);
- guía canónica y paso actual;
- evidencia observada, sin secretos;
- postcondición confirmada o pendiente;
- próxima acción única y salida esperada;
- operaciones que no deben repetirse.

Nunca guardes contraseñas, tokens, salidas que contengan secretos ni un `.env`
real en `_drafts/`. El checkpoint registra estado de ejecución, no sustituye la
guía canónica ni el historial completo de la conversación.
