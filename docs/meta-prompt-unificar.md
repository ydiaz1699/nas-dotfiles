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

1. NO RESUMIR. Si un fragmento tiene un comando, va ÍNTEGRO en la guía.
   Si tiene un archivo de configuración, va COMPLETO (no "...").
   Si tiene una decisión, va textual.

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

4.2. HECHOS, INFERENCIAS Y CONFIANZA. Clasifica cada afirmación:
   - HECHO EXPLÍCITO: la fuente lo dice o muestra literalmente.
   - INFERENCIA TÉCNICA SEGURA: consecuencia directa de una relación técnica
     inequívoca, pero no una afirmación textual de la fuente.
   - INFERENCIA NO CONFIRMADA: parece razonable, pero depende de información
     ausente.
   - DESCONOCIDO: no hay evidencia suficiente.
   Usa confianza `ALTA` para hechos explícitos, `MEDIA` para inferencias técnicas
   seguras, `BAJA` para inferencias no confirmadas y `DESCONOCIDA` cuando no se
   puede determinar. Nunca presentes una inferencia como hecho ni conviertas una
   inferencia no confirmada en decisión tomada.

4.3. AUDITORÍA PREVIA OBLIGATORIA. Antes de redactar la guía final, lee y
   analiza CADA fragmento por separado. No selecciones el primer comando que
   encuentres ni deduzcas que dos comandos son equivalentes sin compararlos.
   Produce un inventario con: documento, ubicación, comando o configuración
   completa, propósito, archivo/ruta afectada, precondiciones, postcondiciones y
   dependencias.

4.4. COMPARAR VARIANTES. Cuando dos comandos hagan aparentemente lo mismo,
   compara sus efectos, modo de ejecución, idempotencia, seguridad, timeout,
   cantidad de observaciones, salida verificable, reversibilidad y compatibilidad
   con el entorno. Ejemplo: `ping -c 3 -W 2 1.1.1.1` puede ser mejor para un
   diagnóstico acotado que `ping -c 7 1.1.1.1`, pero la decisión depende del
   propósito. Si las fuentes no permiten determinar el objetivo o la superioridad,
   conserva ambas como `DECISIÓN PENDIENTE`; no declares una variante mejor por
   intuición.

4.5. DIFERENCIAR MUTACIÓN Y VERIFICACIÓN. No tratar como equivalentes comandos
   que cambian el sistema y comandos que solo consultan su estado. Por ejemplo:
   `systemctl enable systemd-networkd` modifica el arranque; `systemctl
   is-enabled systemd-networkd` solo verifica el resultado. Cada mutación debe
   ir seguida por las verificaciones o precondiciones necesarias antes de ejecutar
   una operación que dependa de que haya tenido éxito; no existe una secuencia
   universal de "mutar y verificar" para todos los sistemas.

4.6. GRAFO DE DEPENDENCIAS, NO ORDEN DE LOS DOCUMENTOS. Reconstruye las
   dependencias reales aunque los drafts presenten otro orden. Para cada operación
   registra, cuando aplique: `requiere`, `produce`, `crea`, `modifica`, `elimina`,
   `respalda`, `restaura`, `consume`, `verifica`, `habilita`, `deshabilita`,
   `inicia`, `detiene`, `reinicia`, `precondición` y `postcondición`.
   Un backup debe preceder cualquier operación que pueda modificar, reemplazar,
   eliminar o dejar en un estado no recuperable el artefacto que protege; no todo
   `restart` exige backup de un recurso que no afecta. Si las dependencias forman
   un ciclo, no fuerces un orden: marca `⚠️ CICLO DE DEPENDENCIAS`, muestra las
   operaciones involucradas y deja la resolución como pendiente.

4.7. PRESERVAR RUTAS Y ARTEFACTOS. Si dos fuentes crean backups en rutas o con
   nombres diferentes, no los fusiones silenciosamente. Conserva cada artefacto
   necesario, elige una ruta canónica solo después de comprobar que todos los
   comandos posteriores la consumen y registra las rutas alternativas como
   `DECISIÓN PENDIENTE`, `compatibilidad` o `RECHAZADA` con motivo. Toda ruta
   usada para restaurar debe haber sido creada antes y su existencia debe
   verificarse antes de editar el original.

4.8. VALIDACIÓN ESTÁTICA DE LA SECUENCIA. Antes de entregar la guía, realiza una
   simulación estática desde un estado inicial declarado: directorios, archivos,
   servicios y rutas esperados. Revisa que cada precondición esté satisfecha,
   que el backup preceda la operación que protege, que las variables existan,
   que las mutaciones tengan verificaciones o precondiciones adecuadas y que el
   rollback consuma una ruta realmente publicada. No afirmes que ejecutaste un
   comando ni que verificaste un resultado si no hubo ejecución real.

4.9. SALIDA DE TRAZABILIDAD. La guía final debe incluir una sección compacta
   `AUDITORÍA DE FUENTES Y VARIANTES` con una fila por idea/comando relevante:
   fuente(s), tipo de afirmación, confianza, variante elegida, propósito,
   decisión y destino. Clasifica cada contenido como `INTEGRADO`, `DUPLICADO`,
   `REEMPLAZADO`, `RECHAZADO` con motivo, `FUERA DE ALCANCE` con destino o
   `PENDIENTE`.

5. FORMATO OBLIGATORIO para cada paso:

   ## Paso N: [nombre corto]

   ### Archivo(s) a crear/modificar
   - Ruta exacta

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

7. DECISIONES DERIVADAS DURANTE LA UNIFICACIÓN. Lista decisiones de
   reconciliación y su confianza. Explica la evidencia o inferencia que las
   respalda; no las presentes como si fueran citas de las fuentes.

8. DECISIONES PENDIENTES. Lista contradicciones, ciclos, rutas no confirmadas,
   verificaciones ausentes e inferencias de confianza baja o desconocida.

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
- hechos explícitos separados de inferencias, con nivel de confianza;
- la comparación de comandos/configuraciones equivalentes y la variante
  elegida o la razón de mantener la decisión pendiente;
- el grafo de dependencias, precondiciones, postcondiciones y ciclos;
- las rutas de archivos y backups y qué operación posterior consume cada una;
- la clasificación de cada contenido como `INTEGRADO`, `DUPLICADO`,
  `REEMPLAZADO`, `RECHAZADO` con motivo, `FUERA DE ALCANCE` con destino o
  `PENDIENTE`.

No generes todavía la guía final si falta un fragmento, una variante relevante,
una ruta de backup o una dependencia. Pide el fragmento faltante o marca la
incertidumbre explícitamente.

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
- `set -euo pipefail` o manejo explícito de errores cuando corresponda;
- backup antes de cualquier mutación;
- comprobación después de cada mutación crítica;
- parada segura ante un fallo;
- rollback con la ruta exacta creada por el propio script;
- confirmación para acciones irreversibles o destructivas.

La guía no debe presentarse como script seguro si esta revisión no se completó.

FORMATO DE LA GUÍA:

# Guía: [título descriptivo]

## Estado: borrador
## Fecha: [hoy]
## Resumen: [1 línea de qué se logra al completar todos los pasos]

---

## Auditoría de fuentes y variantes

| Fuente(s) | Afirmación/operación | Tipo y confianza | Propósito | Variante/decisión y por qué | Clasificación/destino |
|---|---|---|---|---|---|
| [documento y sección] | [contenido exacto o referencia] | HECHO / INFERENCIA SEGURA / NO CONFIRMADA / DESCONOCIDO — ALTA/MEDIA/BAJA/DESCONOCIDA | [qué hace] | [criterio técnico o DECISIÓN PENDIENTE] | INTEGRADO / DUPLICADO / REEMPLAZADO / RECHAZADO / FUERA DE ALCANCE / PENDIENTE |

> Esta tabla no reemplaza el código completo de los pasos. Evita que una
> deduplicación o una reordenación oculte una variante, una ruta de backup o una
> decisión de seguridad.

## Hechos confirmados por las fuentes

1. [afirmación explícita y fuente]

## Decisiones derivadas durante la unificación

1. [decisión del agente, evidencia, confianza y alcance]

---

## Paso 1: [nombre]
[contenido según formato del punto 5]

## Paso 2: [nombre]
[...]

---

## Decisiones pendientes

1. [contradicción o hueco detectado]
   - Opción A: [qué dice un fragmento]
   - Opción B: [qué dice otro]

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
  "STOP. Relee la regla 1: NO RESUMIR. Dame el código COMPLETO del paso N."

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
   - decisiones tomadas en este fragmento;
   - comandos/configs concretos (textual, sin resumir);
   - orden de ejecución detectado;
   - archivo, ruta y backup que cada comando crea, modifica o consume;
   - contradicciones con fragmentos anteriores;
   - variantes equivalentes y criterios para compararlas.
3. Construye una matriz de dependencias global: backup antes de edición,
   mutación antes de verificación, y cada ruta de rollback creada antes de ser
   consumida.
4. Clasifica cada contenido como `INTEGRADO`, `RECHAZADO` con motivo,
   `FUERA DE ALCANCE` con destino o `PENDIENTE`.
5. Al final de todos los análisis, pregunta: "¿Genero la guía final?"
6. Solo entonces combina los análisis en la guía unificada. No elijas comandos
   por aparecer primero o repetirse más; elige por el objetivo y registra la
   decisión técnica.

Esto evita que un fragmento largo o una respuesta previa oculte una variante.
Si un análisis individual no cabe en una respuesta, divídelo en partes y
conserva el inventario y el estado de lectura hasta completar ese fragmento.
```

### Fase 2 — Generación final

Cuando dices "sí, genera", el LLM usa sus propios análisis como
fuente (no los fragmentos originales) y produce la guía con el
formato estándar (pasos numerados, código completo, verificación).

---

## Regla de oro: orden de ejecución

Las guías generadas DEBEN respetar el orden temporal real:

```
1. Crear carpetas          (mkdir -p)
2. Crear archivos          (touch, nano, cat >)
3. Aplicar permisos        (chmod, chown)
4. Levantar/ejecutar       (svc up, systemctl start)
5. Verificar               (svc ps, curl, test)
```

NUNCA:
- chmod a una carpeta que no se creó todavía
- Crear archivo dentro de un directorio inexistente
- Aplicar permisos antes del mkdir
- Levantar un servicio antes de crear su .env

Si el LLM genera una guía que viola este orden, responde:
"STOP. Reordena: primero mkdir, después el archivo, después chmod."


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

Lecciones aprendidas de la primera unificación real (5790 → 304 líneas):

### Deduplicación agresiva

Los fragmentos suelen tener 2-3 versiones del mismo contenido (de distintos LLMs).
La guía final debe tener UNA sola versión de cada sección — la más completa/correcta.
No mantener "alternativas" a menos que sean decisiones reales sin resolver.

### Variables de entorno del proyecto

Al unificar, reemplazar IPs hardcodeadas por `${SERVER_IP}` y otros valores
por sus variables correspondientes (`$dkco`, `$NAS_DOTFILES`). La guía debe
ser portable entre instalaciones.

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

### Integración con el entorno

Los comandos en la guía deben usar los wrappers del framework:
- `svc up/down/logs` en vez de `docker compose up/down/logs`
- `dk servicio` en vez de `cd /docker/servicio`
- `bat` en vez de `cat`
- `instal` en vez de `apt install`
