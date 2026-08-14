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

5. FORMATO OBLIGATORIO para cada paso:

   ## Paso N: [nombre corto]

   ### Archivo(s) a crear/modificar
   - Ruta exacta

   ### Contenido completo
   ```[lenguaje]
   (código o config ÍNTEGRO — nunca parcial, nunca "...")
   ```

   ### Comando de verificación
   ```bash
   (comando que confirma que el paso se aplicó bien)
   ```

   ### Depende de
   - Paso X (si aplica)

6. AL INICIO de la guía, incluir una sección "DECISIONES TOMADAS" con
   las conclusiones firmes de los fragmentos (lo que NO se debe volver
   a discutir).

7. AL FINAL, incluir "DECISIONES PENDIENTES" con lo que se contradice
   entre fragmentos o no está resuelto.

8. NUNCA decir "como se mencionó antes" ni "ver fragmento 3". La guía
   debe ser autocontenida — alguien que no leyó los fragmentos originales
   debe poder seguirla paso a paso.

9. Si el contenido es demasiado largo para una sola respuesta, DILO
   al principio: "La guía tiene N pasos, te la doy en M partes."
   No cortes a mitad de un paso.

10. IDIOMA: responder en el mismo idioma que los fragmentos.

FORMATO DE LA GUÍA:

# Guía: [título descriptivo]

## Estado: borrador
## Fecha: [hoy]
## Resumen: [1 línea de qué se logra al completar todos los pasos]

---

## Decisiones tomadas

1. [decisión firme extraída de los fragmentos]
2. [otra]

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

1. Analiza CADA fragmento por separado.
2. Para cada uno, genera un RESUMEN ESTRUCTURADO con:
   - Decisiones tomadas en este fragmento
   - Comandos/configs concretos (textual, sin resumir)
   - Orden de ejecución detectado
   - Contradicciones con fragmentos anteriores
3. Al final de todos los análisis, pregúntame: "¿Genero la guía final?"
4. Solo entonces combina los análisis en la guía unificada.

Esto evita que pierdas información por contexto largo.
Cada análisis debe caber en una respuesta — si un fragmento es
demasiado largo, divídelo tú en partes y analiza cada parte.
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

## Mejoras post-uso (filebrowser, 2026-08-13)

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
