# Meta-prompt: Unificar diagnósticos dispersos sin perder contenido

> Copia este prompt completo al inicio de la conversación con cualquier LLM
> (Claude, ChatGPT, Gemini) cuando necesites que unifique notas desordenadas
> en una guía de ejecución.

---

## El prompt (copiar desde aquí)

```
INSTRUCCIONES ESTRICTAS — LEER ANTES DE PROCESAR

Voy a pegarte fragmentos de varias conversaciones sobre un mismo tema.
Tu trabajo es unificarlos en UNA SOLA guía de ejecución. Reglas:

1. PRESERVACIÓN DE INFORMACIÓN. No eliminar información relevante durante la
   unificación. Todo comando, configuración o decisión que sea INTEGRADO debe
   conservarse íntegramente en la guía. Si un contenido no aparece en la guía
   final por ser DUPLICADO, REEMPLAZADO, RECHAZADO, FUERA DE ALCANCE o
   BLOQUEADO, debe conservarse en la auditoría de trazabilidad con el motivo.
   Se permite deduplicar contenido operacionalmente equivalente siempre que
   todas sus fuentes y decisiones queden registradas en la auditoría.

2. NO INVENTAR. Solo usa información que aparece en los fragmentos.
   Si hay un hueco (paso que falta), marcalo como "⚠️ PENDIENTE: [qué falta]".

3. DETECTAR CONTRADICCIONES. Si dos fragmentos dicen cosas diferentes sobre
   lo mismo, lista ambas opciones como "DECISIÓN PENDIENTE" con las dos
   alternativas numeradas. No elijas por mí.

4. ORDEN DE EJECUCIÓN. Los pasos deben estar en el orden en que se ejecutan
   en la realidad (primero crear carpetas, después archivos, después arrancar).
   No agrupes por tema — agrupa por secuencia temporal.

4.1. CAPAS DE TRABAJO. Separa explícitamente estas etapas:
   - RECONSTRUCCIÓN: qué dicen literalmente las fuentes.
   - VALIDACIÓN: qué puede comprobarse con las fuentes y análisis estático.
   - RECONCILIACIÓN: qué puede combinarse sin contradicción y qué queda pendiente.
   - PRESENTACIÓN: cómo ordenar y mostrar la guía sin perder trazabilidad.
   - OPTIMIZACIÓN: solo si el usuario la solicita explícitamente o una regla
     aprobada la autoriza. No convertir una unificación en una mejora técnica
     silenciosa.

4.2. TIPO DE AFIRMACIÓN Y CONFIANZA (campos independientes).

   Tipo (qué es la afirmación):
   - HECHO: la fuente lo dice o muestra literalmente.
   - INFERENCIA SEGURA: consecuencia directa de una relación técnica inequívoca,
     pero no una afirmación textual de la fuente.
   - INFERENCIA NO CONFIRMADA: parece razonable, pero depende de información
     ausente.
   - DESCONOCIDO: no hay evidencia suficiente.

   Confianza (cuánta certeza hay, independiente del tipo):
   - ALTA: evidencia directa, sin ambigüedad.
   - MEDIA: evidencia indirecta pero consistente.
   - BAJA: evidencia débil o parcial.
   - DESCONOCIDA: no se puede determinar.

   Estos dos campos son independientes. Una INFERENCIA SEGURA puede tener
   confianza ALTA si la relación técnica es inequívoca. Un HECHO puede tener
   confianza MEDIA si la fuente es ambigua o incompleta. Nunca presentes una
   inferencia como hecho ni conviertas una inferencia no confirmada en decisión
   tomada.

4.3. AUDITORÍA PREVIA OBLIGATORIA. Antes de redactar la guía final, lee y
   analiza CADA fragmento por separado. No selecciones el primer comando que
   encuentres ni deduzcas que dos comandos son equivalentes sin compararlos.
   Produce un inventario con: documento, ubicación, comando o configuración
   completa, propósito, archivo/ruta afectada, precondiciones, postcondiciones y
   dependencias.

4.4. EQUIVALENCIA OPERACIONAL Y COMPARACIÓN DE VARIANTES.

   Dos comandos no son duplicados porque "se parecen". Son duplicados únicamente
   si son operacionalmente equivalentes para el objetivo del procedimiento.
   Distingue:
   - Equivalencia textual: mismo texto exacto.
   - Equivalencia semántica: mismo significado aparente.
   - Equivalencia operacional: mismo efecto verificable sobre los mismos
     artefactos, en las mismas condiciones.

   Solo la equivalencia operacional puede justificar la eliminación de una
   variante. Las otras dos requieren comparación detallada.

   Cuando dos comandos hagan aparentemente lo mismo, compara sus efectos, modo
   de ejecución, idempotencia, seguridad, timeout, cantidad de observaciones,
   salida verificable, reversibilidad y compatibilidad con el entorno.
   Ejemplo: `ping -c 3 -W 2 1.1.1.1` puede ser mejor para un diagnóstico
   acotado que `ping -c 7 1.1.1.1`, pero la decisión depende del propósito.
   Si las fuentes no permiten determinar el objetivo o la superioridad, conserva
   ambas como `DECISIÓN PENDIENTE`; no declares una variante mejor por intuición.

4.5. NO SOBRE-UNIFICAR. No fusionar operaciones únicamente porque tienen el
   mismo propósito. Dos operaciones solo pueden considerarse duplicadas si:
   - afectan el mismo artefacto o conjunto de artefactos;
   - producen el mismo efecto relevante;
   - no existe ninguna diferencia operacional significativa.

   Ejemplo:
   ```
   cp /etc/a.conf /backup/a.conf
   cp /etc/b.conf /backup/b.conf
   ```
   Tienen el MISMO PROPÓSITO (backup) pero son OPERACIONES DISTINTAS sobre
   artefactos diferentes. No fusionarlas ni eliminar una.

4.6. DIFERENCIAR MUTACIÓN Y VERIFICACIÓN. No tratar como equivalentes comandos
   que cambian el sistema y comandos que solo consultan su estado. Por ejemplo:
   `systemctl enable systemd-networkd` modifica el arranque; `systemctl
   is-enabled systemd-networkd` solo verifica el resultado. Cada mutación debe
   ir seguida por las verificaciones o precondiciones necesarias antes de ejecutar
   una operación que dependa de que haya tenido éxito; no existe una secuencia
   universal de "mutar y verificar" para todos los sistemas.

4.7. GRAFO DE DEPENDENCIAS, NO ORDEN DE LOS DOCUMENTOS. Reconstruye las
   dependencias reales aunque los drafts presenten otro orden. Para cada operación
   registra, cuando aplique: `requiere`, `produce`, `crea`, `modifica`, `elimina`,
   `respalda`, `restaura`, `consume`, `verifica`, `habilita`, `deshabilita`,
   `inicia`, `detiene`, `reinicia`, `precondición` y `postcondición`.
   Un backup debe preceder cualquier operación que pueda modificar, reemplazar,
   eliminar o dejar en un estado no recuperable el artefacto que protege; no todo
   `restart` exige backup de un recurso que no afecta. Si las dependencias forman
   un ciclo, no fuerces un orden: marca `⚠️ CICLO DE DEPENDENCIAS`, muestra las
   operaciones involucradas y deja la resolución como pendiente.

4.8. IDENTIDAD DE ARTEFACTOS. Para cada recurso mencionado, registra:
   - **Tipo**: archivo, directorio, symlink, servicio, contenedor, volumen,
     variable, usuario, grupo, interfaz de red, paquete, otro.
   - **Identificador**: ruta, nombre o referencia única.
   - **Estado inicial** (antes de la operación): existe/no existe/desconocido.
   - **Operación**: crear, modificar, eliminar, respaldar, restaurar, verificar.
   - **Estado esperado** (después de la operación): existe con contenido X,
     habilitado, corriendo, etc.
   - **Fuente**: qué documento lo declara.

   Esto permite detectar incoherencias como:
   - backup de `/etc/a.conf` seguido de modificación de `/etc/b.conf`
     (no hay relación entre backup y operación protegida);
   - verificación que consulta un artefacto diferente al que se modificó.

4.9. PRESERVAR RUTAS Y ARTEFACTOS. Si dos fuentes crean backups en rutas o con
   nombres diferentes, no los fusiones silenciosamente. Conserva cada artefacto
   necesario, elige una ruta canónica solo después de comprobar que todos los
   comandos posteriores la consumen y registra las rutas alternativas como
   `DECISIÓN PENDIENTE`, `compatibilidad` o `RECHAZADA` con motivo. Toda ruta
   usada para restaurar debe haber sido creada antes y su existencia debe
   verificarse antes de editar el original.

4.10. VALIDACIÓN ESTÁTICA DE LA SECUENCIA. Antes de entregar la guía, realiza
   una simulación estática desde un estado inicial declarado: directorios,
   archivos, servicios y rutas esperados. Revisa que cada precondición esté
   satisfecha, que el backup preceda la operación que protege, que las variables
   existan, que las mutaciones tengan verificaciones o precondiciones adecuadas y
   que el rollback consuma una ruta realmente publicada. No afirmes que ejecutaste
   un comando ni que verificaste un resultado si no hubo ejecución real.

4.11. SALIDA DE TRAZABILIDAD. La guía final debe incluir una sección compacta
   `AUDITORÍA DE FUENTES Y VARIANTES` con una fila por idea/comando relevante:
   fuente(s), tipo de afirmación, confianza, variante elegida, propósito,
   decisión y destino. Clasifica cada contenido como `INTEGRADO`, `DUPLICADO`,
   `REEMPLAZADO`, `RECHAZADO` con motivo, `FUERA DE ALCANCE` con destino,
   `PENDIENTE` o `BLOQUEADO`.

4.12. CATEGORÍAS DE CLASIFICACIÓN (definiciones únicas).

   | Categoría | Significado |
   |-----------|-------------|
   | INTEGRADO | Incluido en la guía final tal cual o con ajuste de formato |
   | DUPLICADO | Operacionalmente equivalente a otro contenido ya integrado; conservado en auditoría |
   | REEMPLAZADO | Sustituido por una variante superior con criterio documentado |
   | RECHAZADO | Excluido por motivo técnico específico (seguridad, incompatibilidad, etc.) |
   | FUERA_DE_ALCANCE | No pertenece a esta guía; se indica destino alternativo |
   | PENDIENTE | Requiere decisión que puede resolverse comparando las fuentes |
   | BLOQUEADO | No se puede continuar porque falta información indispensable que no está en ninguna fuente disponible |

   Diferencia clave entre PENDIENTE y BLOQUEADO:
   - PENDIENTE: la información existe en las fuentes pero es contradictoria o
     ambigua; puede resolverse con análisis o decisión del usuario.
   - BLOQUEADO: la información no existe en ninguna fuente disponible; no puede
     resolverse sin input externo.

5. FORMATO OBLIGATORIO para cada paso:

   ## Paso N: [nombre corto]

   ### Artefacto(s)
   - Tipo: [archivo/directorio/servicio/contenedor/variable/...]
   - Identificador: [ruta exacta o nombre]
   - Estado inicial → Estado esperado

   ### Acción y contenido completo
   ```[lenguaje]
   (código o config ÍNTEGRO — nunca parcial, nunca "...")
   ```

   ### Verificación
   - **Comando proporcionado por las fuentes:** [comando exacto, si existe]
   - **Si no existe en las fuentes:** `⚠️ NO ESPECIFICADO`
   - No inventar comandos de verificación dentro de la guía unificada. Una
     propuesta externa debe estar rotulada como `PROPUESTA NO PROPORCIONADA POR
     LAS FUENTES` y no formar parte de un script ejecutable sin autorización.

   ### Precondiciones y postcondiciones
   - Precondiciones conocidas por las fuentes o `⚠️ NO ESPECIFICADAS`
   - Postcondiciones conocidas por las fuentes o `⚠️ NO ESPECIFICADAS`

   ### Depende de
   - Paso X (si aplica)

6. HECHOS CONFIRMADOS POR LAS FUENTES. Lista solo afirmaciones explícitas
   de los fragmentos, separadas de cualquier decisión del agente.
   Las decisiones expresadas explícitamente por las fuentes deben conservarse
   sin reinterpretarlas. Ejemplo: si un documento dice "Elegimos nginx", eso es
   un HECHO de la fuente, no una decisión del agente.

7. DECISIONES DERIVADAS DURANTE LA UNIFICACIÓN. Lista decisiones de
   reconciliación, su tipo, confianza y evidencia. Nunca atribuir a una fuente
   una decisión que tomó el agente. Ejemplo: "Por compatibilidad, mantengo
   nginx" es una decisión derivada, no una cita de la fuente.

8. DECISIONES PENDIENTES Y BLOQUEADAS.
   - PENDIENTES: contradicciones, ciclos, rutas no confirmadas, verificaciones
     ausentes e inferencias de confianza baja que pueden resolverse con análisis
     o decisión del usuario.
   - BLOQUEADAS: información referenciada pero ausente de todas las fuentes
     disponibles. Si el usuario no puede proporcionar el contenido faltante,
     generar la guía hasta donde sea posible y marcar explícitamente el punto
     como `⚠️ BLOQUEADO POR INFORMACIÓN FALTANTE` con descripción de qué se
     necesita. No bloquear toda la guía por un punto irresoluble.

9. NUNCA decir "como se mencionó antes" ni "ver fragmento 3". La guía debe ser
   autocontenida — alguien que no leyó los fragmentos originales debe poder
   seguirla paso a paso.

10. Si el contenido es demasiado largo para una sola respuesta, DILO al
    principio: "La guía tiene N pasos, te la doy en M partes." No cortes a
    mitad de un paso.

11. IDIOMA: responder en el mismo idioma que los fragmentos.

Antes de generar la guía final, la respuesta de análisis debe incluir, aunque
sea en formato compacto:

- todos los fragmentos identificados, cada uno con estado `LEÍDO`, `PENDIENTE`
  o `NO DISPONIBLE`;
- hechos separados de inferencias, cada uno con tipo y confianza independientes;
- la comparación de variantes con criterio de equivalencia operacional y la
  decisión o razón de mantenerla pendiente;
- el grafo de dependencias con artefactos tipados, precondiciones,
  postcondiciones y ciclos;
- las rutas de archivos y backups y qué operación posterior consume cada una;
- la clasificación de cada contenido como `INTEGRADO`, `DUPLICADO`,
  `REEMPLAZADO`, `RECHAZADO` con motivo, `FUERA_DE_ALCANCE` con destino,
  `PENDIENTE` o `BLOQUEADO`.

Si falta información necesaria, no inventarla. Si el usuario no puede
proporcionar el contenido faltante, generar la guía hasta donde sea posible y
marcar explícitamente los puntos como `⚠️ BLOQUEADO POR INFORMACIÓN FALTANTE`.
No bloquear toda la guía por un punto irresoluble.

### Ejemplo de mutación y verificación

```text
Paso A — Mutación: systemctl enable systemd-networkd
Paso B — Verificación: systemctl is-enabled systemd-networkd
Dependencia: B requiere que A termine correctamente.
```

`is-enabled` no sustituye a `enable`: uno consulta y el otro cambia el estado.

### Ejemplo de backup y modificación

```text
Paso A — Crear directorio de backup
Paso B — Copiar el archivo original a la ruta de backup
Paso C — Verificar que la copia existe y no está vacía
Paso D — Modificar el archivo original
Paso E — Verificar la modificación
Paso F — Registrar la ruta exacta para rollback
```

Si otro draft pone la copia en una ruta diferente, conservar ambas solo si son
necesarias; de lo contrario, documentar por qué se adopta una única ruta. Nunca
reordenar por número de paso ni asumir que dos backups protegen el mismo archivo.

### Si la guía se convertirá en script

Antes de considerar el resultado ejecutable, revisar que cada comando tenga:

- variables y rutas definidas antes de usarse;
- manejo explícito de errores cuando corresponda;
- backup antes de cualquier mutación;
- comprobación después de cada mutación crítica;
- parada segura ante un fallo;
- rollback con la ruta exacta creada por el propio script;
- confirmación para acciones irreversibles o destructivas.

Elementos como `set -euo pipefail`, wrappers del proyecto (`svc`, `dk`, `instal`)
o parametrización de valores literales (`${SERVER_IP}`) son REGLAS DE OPTIMIZACIÓN
O CONTEXTO DEL PROYECTO. No deben introducirse automáticamente durante la
reconciliación si no estaban en las fuentes. El flujo correcto es:

```text
PROPUESTA DE ENDURECIMIENTO / ADAPTACIÓN AL CONTEXTO:
  Agregar: [qué]
  Motivo: [por qué]
  Estado: NO FORMA PARTE DE LA FUENTE. Requiere autorización.
```

Aplicar estos elementos solo durante la fase de OPTIMIZACIÓN, cuando el usuario
la solicite o cuando una regla del proyecto explícitamente lo autorice.

La guía no debe presentarse como script seguro si esta revisión no se completó.

FORMATO DE LA GUÍA:

# Guía: [título descriptivo]

## Estado: borrador
## Fecha: [hoy]
## Resumen: [1 línea de qué se logra al completar todos los pasos]

---

## Auditoría de fuentes y variantes

| Fuente(s) | Afirmación/operación | Tipo | Confianza | Propósito | Variante/decisión y por qué | Clasificación |
|---|---|---|---|---|---|---|
| [doc y sección] | [contenido exacto] | HECHO / INF.SEGURA / INF.NO CONFIRMADA / DESCONOCIDO | ALTA / MEDIA / BAJA / DESCONOCIDA | [qué hace] | [criterio o DECISIÓN PENDIENTE] | INTEGRADO / DUPLICADO / REEMPLAZADO / RECHAZADO / FUERA_DE_ALCANCE / PENDIENTE / BLOQUEADO |

> Esta tabla no reemplaza el código completo de los pasos. Evita que una
> deduplicación o una reordenación oculte una variante, una ruta de backup o una
> decisión de seguridad.

## Hechos confirmados por las fuentes

1. [afirmación explícita, fuente y cita]

## Decisiones derivadas durante la unificación

1. [decisión del agente — tipo, confianza, evidencia y alcance]

## Artefactos identificados

| Tipo | Identificador | Estado inicial | Operación | Estado esperado | Fuente |
|------|---------------|----------------|-----------|-----------------|--------|
| [archivo/servicio/...] | [ruta/nombre] | [existe/no/desconocido] | [crear/modificar/...] | [esperado] | [doc] |

---

## Paso 1: [nombre]
[contenido según formato del punto 5]

## Paso 2: [nombre]
[...]

---

## Decisiones pendientes

1. [contradicción o ambigüedad resoluble]
   - Opción A: [qué dice un fragmento]
   - Opción B: [qué dice otro]

## Bloqueados

1. [información referenciada pero ausente de todas las fuentes]
   - Qué se necesita: [descripción]
   - Impacto: [qué pasos no pueden completarse]

---

Ahora te pego los fragmentos. EMPIEZA A PROCESAR SOLO CUANDO YO DIGA "FIN DE FRAGMENTOS":
```

---

## Cómo usarlo

1. Pega el prompt de arriba al inicio de un chat nuevo
2. Pega todos tus fragmentos desordenados (uno tras otro, separados por `---`)
3. Al final escribe: `FIN DE FRAGMENTOS`
4. El LLM genera la guía unificada

---

## Tips para que funcione mejor

- **Fragmentos largos**: si pegas >50K chars, algunos LLMs cortan. Divide en
  2-3 mensajes y pon "CONTINUACIÓN" al inicio de cada uno. El "FIN DE FRAGMENTOS"
  solo va al final del último.

- **Si el LLM empieza a resumir**: responde inmediatamente con:
  "STOP. Relee la regla 1: PRESERVAR INFORMACIÓN. Dame el código COMPLETO del paso N."

- **Si omite un paso**: responde con:
  "Falta el paso de [X]. Está en el fragmento que dice [cita textual de 5 palabras]."

- **Para ChatGPT específicamente**: agrega al inicio del prompt:
  "Usa respuestas largas. No te preocupes por la longitud. Prioriza completitud."

- **Para Claude**: funciona bien sin modificaciones. Si aún así corta,
  pide: "Continúa desde donde cortaste, sin repetir lo anterior."

---

## Variante: documentos largos (análisis por partes)

Si los fragmentos son muy largos (>30K chars total) y el LLM pierde
información, usa esta variante en dos fases:

### Fase 1 — Análisis individual

Agrega esta instrucción ANTES de pegar fragmentos:

```
MODO: ANÁLISIS POR PARTES

En vez de generar la guía final directamente:

1. Analiza CADA fragmento por separado y registra su estado (`LEÍDO`,
   `PENDIENTE` o `NO DISPONIBLE`).
2. Para cada uno, genera un análisis estructurado con:
   - tipo de cada afirmación (HECHO / INFERENCIA SEGURA / NO CONFIRMADA /
     DESCONOCIDO) y confianza (ALTA / MEDIA / BAJA / DESCONOCIDA);
   - comandos/configs concretos (textual, sin resumir);
   - orden de ejecución detectado;
   - artefactos: tipo, identificador, estado, operación;
   - contradicciones con fragmentos anteriores;
   - variantes y criterio de equivalencia operacional.
3. Construye una matriz de dependencias global: backup antes de edición,
   mutación antes de verificación, y cada ruta de rollback creada antes de ser
   consumida.
4. Clasifica cada contenido con las 7 categorías definidas.
5. Al final de todos los análisis, pregunta: "¿Genero la guía final?"
6. Solo entonces combina los análisis en la guía unificada.

IMPORTANTE: Los análisis intermedios sirven como índice y estructura de trabajo,
pero NUNCA sustituyen completamente las fuentes originales. Si durante la fase 2
necesitas comprobar un comando, ruta, valor o contexto, vuelve al fragmento
original. Un análisis intermedio puede haber omitido un detalle.
```

### Fase 2 — Generación final

Cuando dices "sí, genera", el LLM combina los análisis Y las fuentes originales
para producir la guía con el formato estándar. Si hay duda sobre un detalle,
vuelve al fragmento original en vez de confiar solo en el análisis intermedio.

```text
FUENTES ORIGINALES
       │
       ├──────────────┐
       ▼              ▼
INVENTARIO       ANÁLISIS
       │              │
       └──────┬───────┘
              ▼
       RECONCILIACIÓN (puede volver a fuentes si hay duda)
              ▼
           GUÍA
```

---

## Patrones frecuentes de orden (no universales)

Las relaciones de dependencia tienen prioridad sobre cualquier patrón
predefinido. Los siguientes son patrones frecuentes que sirven como heurística
inicial, pero NO son un orden universal obligatorio:

```
Crear carpetas          (mkdir -p)
Crear archivos          (touch, nano, cat >)
Aplicar permisos        (chmod, chown)
Levantar/ejecutar       (systemctl start, servicio up)
Verificar               (status, curl, test)
```

Otros patrones válidos según el contexto:

```
crear archivo → validar sintaxis → backup → reemplazar → restart
crear directorio → backup → modificar → validar → restart → verificar
```

La verdadera regla es: las dependencias entre artefactos determinan el orden.
Si un archivo requiere un directorio, el directorio va primero. Si una
modificación requiere backup, el backup va primero. Pero no asumas que TODA
secuencia sigue el patrón mkdir→archivo→chmod→servicio→verificar.

NUNCA:
- chmod a una carpeta que no se creó todavía
- Crear archivo dentro de un directorio inexistente
- Aplicar permisos antes del mkdir
- Levantar un servicio antes de crear su configuración

Si el LLM genera una guía que viola una dependencia real, responde:
"STOP. Reordena: [artefacto X] depende de [artefacto Y] que no existe todavía."


---

## Feedback y evolución del contrato (separados de la unificación)

La unificación usa este meta-prompt como contrato fijo durante la tarea. El LLM
puede proponer una mejora, pero no debe modificar silenciosamente este archivo,
la skill ni las reglas del proyecto. El flujo correcto es:

```text
feedback del usuario
  → propuesta de nueva regla con origen y ejemplo
  → revisión/aprobación explícita del usuario
  → edición versionada del meta-prompt
  → validación y registro del cambio
```

### El agente debe

1. Evaluar el resultado: pérdidas, contradicciones, inferencias y correcciones.
2. Proponer lecciones nuevas separadas del documento unificado.
3. Avisar antes de unificar si hay contradicciones, verificaciones ausentes,
   rutas incompatibles, ciclos o información insuficiente.
4. No convertir automáticamente una propuesta de optimización en una regla.

### El usuario debe

1. Corregir si la guía generada tiene errores.
2. Aprobar o rechazar explícitamente una nueva regla del meta-prompt.
3. Indicar si desea solo reconstrucción/reconciliación o también optimización.

### Registro de mejoras

Cada mejora se agrega aquí con fecha y contexto:

| Fecha | Mejora | Origen |
|-------|--------|--------|
| 2026-08-13 | Deduplicación agresiva (una sola versión, no alternativas) | filebrowser: 3 versiones del mismo contenido |
| 2026-08-13 | Reemplazar IPs por `${SERVER_IP}` | filebrowser: IP hardcodeada 192.168.1.200 |
| 2026-08-13 | Secciones estándar para guías de servicios Docker (10 secciones) | filebrowser: estructura final |
| 2026-08-13 | Usar wrappers del framework (svc, dk, bat, instal) | filebrowser: tenía docker compose directo |
| 2026-08-17 | Auditar cada fragmento y comparar variantes antes de deduplicar | riesgo de elegir la primera variante y perder una mejora técnica |
| 2026-08-17 | Reconstruir dependencias reales: backup antes de modificar y mutación antes de verificar | riesgo de ordenar por número de paso o mezclar rutas de backup |
| 2026-08-17 | Mantener trazabilidad de rutas y clasificar todo contenido no integrado | evitar que un script no encuentre su copia de rollback |
| 2026-08-17 | Separar reconstrucción, validación, reconciliación, presentación y optimización | evitar mejoras técnicas silenciosas durante una unificación |
| 2026-08-17 | Distinguir hechos, inferencias y niveles de confianza | evitar presentar deducciones del LLM como hechos de las fuentes |
| 2026-08-17 | No inventar verificaciones; marcar `NO ESPECIFICADO` | evitar comandos de prueba no proporcionados por los drafts |
| 2026-08-17 | Detectar ciclos y declarar precondiciones/postcondiciones | evitar forzar un orden inseguro o imposible |
| 2026-08-17 | Feedback sujeto a aprobación explícita | evitar modificar silenciosamente el contrato del meta-prompt |
| 2026-08-17 | Separar hechos, inferencias, validación y optimización | revisión externa: evitar presentar deducciones como hechos |
| 2026-08-17 | Verificaciones de fuente o `NO ESPECIFICADO` | revisión externa: no inventar comandos de verificación |
| 2026-08-17 | Pre/postcondiciones, ciclos y categorías DUPLICADO/REEMPLAZADO | revisión externa: hacer reconciliación auditable |
| 2026-08-20 | Tipo y confianza como campos independientes | revisión: una inferencia segura puede tener confianza alta |
| 2026-08-20 | Añadir BLOQUEADO (distinto de PENDIENTE) | revisión: diferenciar falta de decisión de falta de información |
| 2026-08-20 | Definir equivalencia operacional para deduplicar | revisión: no fusionar por semejanza textual o semántica |
| 2026-08-20 | No sobre-unificar: mismo propósito ≠ misma operación | revisión: dos backups a rutas distintas no son duplicados |
| 2026-08-20 | Análisis intermedio no sustituye fuentes originales | revisión: fase 2 debe poder volver a fragmentos |
| 2026-08-20 | IPs, wrappers, set -euo como reglas de optimización/contexto | revisión: no aplicar durante reconciliación sin autorización |
| 2026-08-20 | Identidad de artefactos (tipo, id, estado, operación) | revisión: detectar backup→modificación sobre artefactos distintos |
| 2026-08-20 | Patrones de orden como heurística, no regla universal | revisión: las dependencias reales determinan el orden |
| 2026-08-20 | Preservar decisiones de fuente sin reinterpretarlas | revisión: "Elegimos X" es hecho, "mantengo X" es derivada |
| 2026-08-20 | Bloqueo resoluble vs irresoluble; no detener toda la guía | revisión: continuar hasta el punto seguro y marcar bloqueo |
| 2026-08-25 | Separar evidencia runtime de configuración objetivo y versiones disponibles | n8n: `latest` resolvió a 2.23.4; `2.36.7` fue consultada como estable pero no se verificó desplegada; evitar afirmar que una propuesta ya está aplicada |
Lecciones aprendidas de la primera unificación real (5790 → 304 líneas):

### Deduplicación con equivalencia operacional

Los fragmentos suelen tener 2-3 versiones del mismo contenido (de distintos LLMs).
La guía final debe tener UNA sola versión de cada operación — la que cumpla el
criterio de equivalencia operacional. No mantener "alternativas" a menos que sean
decisiones reales sin resolver. Pero recordar: mismo propósito no implica misma
operación; dos comandos que afectan artefactos diferentes no son duplicados.

### Variables de entorno del proyecto (regla de optimización)

Al unificar, los valores literales se preservan tal como están en las fuentes
durante la reconciliación. La parametrización (reemplazar IPs por `${SERVER_IP}`,
rutas por `$dkco`, etc.) es una regla de OPTIMIZACIÓN del proyecto que se aplica
solo cuando el usuario solicita optimización o el contexto del proyecto lo exige
explícitamente.

### Secciones estándar para guías de servicios Docker

```
1. Descripción (qué es, para qué sirve, URL de acceso)
2. Arquitectura (diagrama de montaje/red)
3. Estructura de directorios (árbol del stack + datos)
4. Conceptos previos (si aplica: bind mounts, network_mode, etc.)
5. Instalación paso a paso (en orden de ejecución)
6. Gestión operativa (agregar/quitar bind mounts, configurar usuarios)
7. Mantenimiento (backup, restore, update)
8. Verificación y diagnóstico (comandos para comprobar que funciona)
9. Problemas comunes (tabla: síntoma | causa | solución)
10. Notas técnicas (decisiones de diseño, seguridad)
```

### Integración con el entorno (regla de optimización/contexto)

Cuando la fuente o el contexto del proyecto establezca explícitamente que estos
wrappers son obligatorios, los comandos deben usarlos:
- `svc up/down/logs` en vez de `docker compose up/down/logs`
- `dk servicio` en vez de `cd /docker/servicio`
- `bat` en vez de `cat`
- `instal` en vez de `apt install`

Esta regla aplica solo cuando el proyecto lo exige. Si las fuentes provienen de
un contexto externo donde estos wrappers no existen, no transformar comandos
estándar en wrappers. Eso sería una mejora silenciosa.
