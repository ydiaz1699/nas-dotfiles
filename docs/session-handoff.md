# Session Handoff — Herramienta de Transferencia de Contexto entre Sesiones

> **Qué es:** Plantilla + proceso para que al cerrar una sesión, el próximo
> LLM pueda continuar sin perder el hilo.
>
> **Cuándo usar:** Al final de CADA sesión de trabajo (Kiro, Claude, Cursor, etc.)
> **Dónde guardar:** `_drafts/SESSION-<fecha>-<tema>.md`
> **Quién lo usa:** El próximo LLM al inicio de la nueva sesión

---

## Proceso (para el LLM al cerrar sesión)

### Paso 1: Generar el handoff

Al final de la sesión (o cuando el usuario diga "guardar para continuar después"),
crear `_drafts/SESSION-<YYYY-MM-DD>-<tema-corto>.md` con la plantilla de abajo.

### Paso 2: Llenar las secciones

Completar cada sección basándose en la conversación real.
NO resumir genéricamente — incluir detalles específicos, errores reales,
y el razonamiento detrás de cada decisión.

### Paso 3: Verificar coherencia

- ¿Los pendientes son accionables (no vagos)?
- ¿Las decisiones incluyen el POR QUÉ?
- ¿Los gaps tienen suficiente contexto para que otro LLM los entienda?
- ¿Los archivos modificados están listados?

### Paso 4: Commit y push

```bash
git add _drafts/SESSION-*.md && gc "docs: session handoff para continuidad" && gp
```

---

## Plantilla

```markdown
# Sesión <FECHA> — <Título descriptivo>

> Resumen en 1-2 líneas de qué se hizo y dónde quedó.

---

## 1. Objetivo original

¿Qué pidió el usuario al inicio?
(Copiar textualmente si es posible)

---

## 2. Evolución del trabajo

Cómo el objetivo inicial evolucionó durante la sesión.
Cada paso que cambió la dirección o amplió el alcance:

1. Empezamos con X → descubrimos Y → cambiamos a Z
2. ...

---

## 3. Decisiones tomadas

| # | Decisión | Por qué | Alternativa descartada |
|---|----------|---------|------------------------|
| 1 | ... | ... | ... |

---

## 4. Problemas encontrados y cómo se resolvieron

| Problema | Causa | Solución | Lección |
|----------|-------|----------|---------|
| ... | ... | ... | ... |

---

## 5. Archivos creados/modificados

| Archivo | Acción | Estado |
|---------|--------|--------|
| `path/archivo` | Creado/Modificado/Eliminado | ✅ Completo / ⚠️ Parcial |

---

## 6. Lo que quedó pendiente (accionable)

| # | Pendiente | Contexto necesario | Prioridad |
|---|-----------|-------------------|-----------|
| 1 | ... | (por qué es importante, qué pasa si no se hace) | Alta/Media/Baja |

---

## 7. Estado del sistema al cerrar

Snapshot de cómo quedó todo (para que el próximo LLM no tenga que descubrirlo):

- Servicios corriendo: ...
- Últimos commits: ...
- Branches activas: ...
- Errores conocidos sin resolver: ...

---

## 8. Instrucciones para continuar

Pasos exactos que el próximo LLM debe seguir al inicio:

1. Leer este archivo
2. Leer `docs/dependency-map.md` (reglas de conexión)
3. Leer `docs/docker-entorno.md` (si va a tocar compose)
4. Ejecutar: `NAS_CLI=bash svc scan` (verificar inconsistencias)
5. Continuar con pendiente #X de la sección 6

---

## 9. Contexto que el próximo LLM NO tendrá (y debe saber)

Cosas que se discutieron verbalmente pero no están en ningún archivo:
- El usuario prefiere X sobre Y porque...
- La razón detrás de la decisión Z fue...
- Cuidado con A porque pasó B...

```

---

## Ejemplo de uso

Al final de una sesión, el LLM genera:

```
_drafts/SESSION-2026-08-17-scanner-y-cli.md
```

Al inicio de la SIGUIENTE sesión, el nuevo LLM:
1. Ve que hay archivos `SESSION-*` en `_drafts/`
2. Lee el más reciente
3. Sabe exactamente dónde retomar

---

## Integración con la skill (nas-context.md)

La sección de comportamiento proactivo (#8 en nas-context.md) ya dice:

> "Cuando hay archivos en _drafts/ → analizarlos proactivamente"

El LLM al inicio de sesión debería:
1. Verificar si hay `_drafts/SESSION-*.md`
2. Si sí → leer el más reciente → "Veo que la sesión anterior trabajó en X. ¿Continuamos?"
3. Si no → sesión nueva sin contexto previo

---

## Integración con el hook de Kiro

Se puede crear un hook `SessionStart` que recuerde al LLM verificar _drafts/:

```json
{
  "version": "v1",
  "hooks": [{
    "name": "Verificar sesiones anteriores",
    "trigger": "SessionStart",
    "action": {
      "type": "agent",
      "prompt": "Verifica si hay archivos _drafts/SESSION-*.md en el repo nas-dotfiles. Si hay alguno, lee el más reciente y ofrece al usuario continuar donde quedó la sesión anterior. Si no hay, no hacer nada."
    }
  }]
}
```

---

## Cuándo NO generar handoff

- Sesiones cortas de una sola pregunta/respuesta
- Si todo lo hecho se refleja completamente en commits (sin contexto perdido)
- Si el usuario dice "no hace falta guardar"

## Cuándo SÍ generar handoff (obligatorio)

- Sesiones largas (>1 hora de trabajo)
- Cuando quedan pendientes que dependen de contexto discutido
- Cuando se tomaron decisiones que no están en ningún documento
- Cuando el usuario dice "guardar para continuar después"
- Cuando se descubrieron problemas que otro LLM podría repetir
