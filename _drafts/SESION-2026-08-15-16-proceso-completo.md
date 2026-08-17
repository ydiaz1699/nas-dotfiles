# Sesión 2026-08-15/16 — Proceso Completo de Pensamiento

> Este documento captura el CAMINO de razonamiento de esta sesión.
> No es un resumen de "qué se hizo" (eso está en TODO.md y ideas-decisions.md).
> Es HOW y WHY — cómo evolucionó cada idea paso a paso, qué problemas
> surgieron, cómo se resolvieron, y qué lecciones se extrajeron.
>
> **Para otro LLM:** Leer esto te da el contexto que NO tienes de la conversación.
> Cada sección explica un problema que fue EVOLUCIONANDO conforme se trabajaba.

---

## La evolución del problema central

El usuario empezó pidiendo algo simple: "implementar el plan ntfy + usb-api".
Pero conforme se implementaba, surgieron problemas en cascada que revelaron
un problema sistémico más profundo:

```
Implementar ntfy/usb-api (simple)
    → El LLM no sabía qué estaba ya instalado (Homepage, redes)
    → El LLM sugirió cosas incorrectas (IP hardcodeada, TZ duplicado)
    → El LLM creó un script (catalog-sync) pero no lo conectó al CLI
    → El LLM dijo "no necesitas cambiar nada" sin leer la config real
    → El agente local no sabe de los comandos nuevos
    → Otro LLM (en otro chat) dio config incorrecta de HA+ntfy
    
    ↓ Problema real descubierto:
    
"No existe un sistema que conecte todo el conocimiento del proyecto
 y detecte automáticamente cuando algo está desincronizado"
```

---

## Fase 1: Implementación directa (ntfy + usb-api)

### Lo que se pidió
Implementar el plan de `_drafts/PLAN-ntfy-usb-api.md` en ambos repos.

### Lo que se hizo
1. DebMenux: `lib/notifications.sh`, `scripts/services/ntfy.sh`, `scripts/services/usb-api.sh`
2. nas-dotfiles: catálogo (ficha+compose+.env), guía, plugin agente, SKILL.md

### Primer problema: el usuario tenía redes que el LLM no conocía
El LLM propuso `homepage_net` pero el usuario no la tenía. Las redes reales eran:
adguard_macvlan_NET, db_net, iot_net, bridge, etc.

**Lección 1:** El LLM necesita conocer el estado REAL del NAS antes de sugerir.

---

## Fase 2: Puesta en marcha (errores reales)

### Problemas encontrados al instalar en el NAS real:

1. **`debmenu install ntfy` falló** — el PR no estaba mergeado a main
2. **Android no conecta** — celular en subred .0.x, NAS en .1.x (redes distintas)
3. **USB no notifica al montar** — `ENABLE_NOTIFICATIONS="false"` en config
4. **El script en /usr/local/bin/ era versión vieja** — no tenía ntfy_send
5. **usb-api listaba el disco del sistema** — filtro `startswith(MOUNT_BASE)` muy amplio
6. **Mountpoint fantasma** — USB desconectado bruscamente, carpeta queda como mount

**Lección 2:** La implementación en papel vs la realidad del NAS son MUY diferentes.
El LLM debe verificar estado real, no asumir que todo está como él lo dejó.

---

## Fase 3: Homepage (labels vs services.yaml)

### Cómo evolucionó:
1. LLM puso TODOS los servicios en services.yaml
2. Usuario dijo "AdGuard ya usa labels en su compose"
3. LLM quitó AdGuard de services.yaml
4. EMQX en services.yaml causó error (widget sin auth)
5. Usuario mostró que EMQX YA tenía labels en su compose
6. **Decisión final:** Labels en compose SIEMPRE. services.yaml SOLO para nativos (usb-api).

**Lección 3:** El LLM debe leer los compose reales antes de crear services.yaml.
Si un servicio ya tiene labels, NO duplicar en services.yaml.

---

## Fase 4: El compose de HA y los problemas de convenciones

### Lo que pasó:
1. LLM dijo "el compose no necesita modificación"
2. Después tuvimos que: agregar env_file, quitar TZ duplicado, usar ${SERVER_IP}
3. El usuario preguntó "por qué no cambiaste TZ si ya está en el .env global"
4. Cada corrección revelaba que el LLM NO había leído las convenciones del proyecto

**Lección 4:** ANTES de decir "no necesita cambios", el LLM DEBE leer un documento
de convenciones. Esto llevó a crear `docs/docker-entorno.md`.

---

## Fase 5: Documentación en cascada (el dependency-map)

### Cómo surgió la idea:
1. El LLM creó el compose de HA pero no actualizó la guía
2. El LLM creó ntfy pero no creó el script de DebMenux (el usuario tuvo que recordarle)
3. Cada vez que se cambiaba algo, faltaba actualizar 5+ archivos más

**Pregunta del usuario:** "¿Cómo hacer que la documentación se conecte entre sí?"

### Evolución de la solución:
1. Primero: `catalog-sync.sh` (script que genera docs en cascada)
2. Después: Hook de Kiro (dispara al guardar compose.yml)
3. Después: DebMenux `register_to_catalog()` (cascada al instalar)
4. Después: `dependency-map.md` (mapa estático de qué conecta con qué)

---

## Fase 6: La skill 2.0 (nas-context.md)

### Problema:
- El LLM no sabía aliases (gpl, dk, nasfk)
- El LLM sugería `cd /docker/X` en vez de `dk X`
- El LLM no sabía qué servicios existían
- Otro LLM (en otro chat) dio info incorrecta sobre ntfy porque no leyó el proyecto

### Evolución:
1. El usuario compartió videos sobre Skills 2.0 de Anthropic
2. Conceptos extraídos: registry ligero, lazy loading, self-learning, trigger pushy
3. Se creó `nas-context.md` con 7 secciones:
   - Trigger (cuándo activar)
   - Entorno (lo justo para no improvisar)
   - Encoded preferences (NUNCA/SIEMPRE — no caducan)
   - Skill registry (índice de servicios + path a docs)
   - Lazy loading (solo cargar cuando se necesita)
   - Progressive updates (self-learning — errores no se repiten)
   - Checklist de verificación (antes de responder)

### Después: AGENTS.md
4. El usuario preguntó por el formato abierto (60k+ repos)
5. Se creó AGENTS.md en ambos repos para que CUALQUIER agente lo lea

---

## Fase 7: El problema del script sin conexión

### Lo que pasó:
1. Se creó `catalog-sync.sh` y se documentó como `svc catalog-sync`
2. Se conectó al bash CLI (case en svc.sh)
3. El usuario ejecutó `svc catalog-sync` → ERROR (usaba Python CLI)
4. Se descubrió que `NAS_CLI=python` hacía que fuera al CLI Python
5. El script solo estaba en bash, no en Python

**Lección 5:** Crear un archivo ≠ conectarlo al sistema. Hay que verificar:
- ¿En cuál CLI está? (bash, python, ambos)
- ¿El usuario puede ejecutarlo?
- ¿El agente local lo conoce?

### Esto reveló un problema más grande:
El dependency-map era ESTÁTICO — decía reglas pero no VERIFICABA que se cumplieran.

---

## Fase 8: La necesidad del scanner (idea final)

### El problema:
- dependency-map = reglas escritas (pasivo)
- catalog-sync = genera docs faltantes (reactivo)
- Pero NADIE detecta activamente que algo está mal

### Idea del usuario (brillante):
Usar `git diff` como detector de cambios:
- Primera vez: escanea TODO → genera snapshot
- Siguientes veces: solo procesa los archivos que cambiaron (git diff)
- El LLM recibe solo lo necesario (no se satura)

### Relación de las 3 herramientas:
```
dependency-map = REGLAS (qué debería conectar)
scanner        = VERIFICACIÓN (¿se cumplen las reglas?)
catalog-sync   = GENERACIÓN (crear lo que falta)
```

---

## Decisiones arquitecturales tomadas en esta sesión

| # | Decisión | Razón |
|---|----------|-------|
| 1 | Labels en compose > services.yaml | Auto-descubrimiento, sin archivo centralizado |
| 2 | env_file: [../.env, .env] obligatorio | Nunca hardcodear IP/TZ |
| 3 | security_opt siempre, cap_drop con criterio | No romper servicios que instalan en runtime |
| 4 | resource limits solo después de medir | Evitar OOM kills en servicios nuevos |
| 5 | USB monta con LABEL | Más legible que usb-sdb1 |
| 6 | ntfy.publish para texto, shell_command para imágenes | Limitación de la integración HA |
| 7 | priority numérica en HA (1-5) | La integración no acepta texto |
| 8 | _drafts/ como inbox de ideas | El LLM clasifica y procesa |
| 9 | Skill 2.0 con progressive updates | Errores no se repiten |
| 10 | AGENTS.md formato abierto | Funciona con cualquier agente |
| 11 | dependency-map cubre TODO (servicios + scripts + shell + plugins) | No solo composes |
| 12 | Dual CLI: bash=verdad, python=interfaz | Una sola fuente de verdad |
| 13 | Scanner incremental con git | No releer todo cada vez |
| 14 | El LLM debe ser PROACTIVO | No esperar a que le pidan, anticipar |

---

## Gaps que quedaron (para próxima sesión)

1. **Scanner incremental (git-based)** — solo existe la IDEA documentada, no la implementación
2. **Completions de los nuevos comandos** — scan, backup-all, logs-grep, clone, cron, lock, unlock no están en TAB
3. **AGENTS.md y nas-context.md** — no reflejan los comandos nuevos del otro chat
4. **Agente local** — su prompt no sabe de `svc scan`, `svc lock`, etc.
5. **n8n y vaultwarden** — sin documentar (no están instalados aún)

---

## Cómo usar este documento

### Si eres un LLM en una sesión nueva:

1. Lee esto para entender el CAMINO de pensamiento
2. Lee `_drafts/PENDIENTES-proxima-sesion.md` para saber qué falta
3. Lee `docs/dependency-map.md` para saber las reglas de conexión
4. Lee `docs/docker-entorno.md` antes de tocar cualquier compose
5. Lee `docker-nas/references/nas-context.md` para el contexto operativo

### Si quieres continuar donde quedamos:

Los gaps de la sección anterior son las prioridades. El más importante
es actualizar las completions y AGENTS.md con los comandos que el otro
chat ya implementó.

### Si quieres implementar el scanner incremental:

Lee `_drafts/IDEA-scanner-incremental-git.md` — tiene el diseño completo.
El `agent/tools/project_scanner.py` que ya existe hace full scan.
El siguiente paso es agregarle la capa de git diff + snapshot.
