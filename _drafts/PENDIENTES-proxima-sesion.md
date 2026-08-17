# Pendientes para próxima sesión

> Contexto: sesión larga del 2026-08-15/16 donde se implementó ntfy, usb-api,
> Homepage, HA, pipeline auto-docs, skill 2.0, AGENTS.md, dependency-map.
> Todo lo de abajo quedó pendiente.

---

## 1. Servicios sin documentación completa

Estado actual (`svc catalog-sync --status`):

| Servicio | Falta |
|----------|-------|
| **n8n** | ficha ❌, guía ❌, DebMenux script ❌ |
| **vaultwarden** | ficha ❌, guía ❌, DebMenux script ❌, Homepage labels ❌ |
| **emqx** | guía ❌ (tiene ficha y compose) |
| **esphome** | guía ❌, DebMenux script ❌ |
| **datasql** | DebMenux script ❌ |
| **node-red** | DebMenux script ❌ |
| **homepage** | DebMenux script ❌ |

**Acción:** Ejecutar `NAS_CLI=bash svc catalog-sync` para generar todo lo automático.
Después completar manualmente guías y scripts DebMenux de los servicios importantes.

---

## 2. catalog-sync en Python CLI

**Problema:** `catalog-sync` solo está en bash CLI (`svc.sh`). El usuario usa
`NAS_CLI=python` por defecto. Resultado: `svc catalog-sync` da error.

**Workaround actual:** `NAS_CLI=bash svc catalog-sync --status`

**Solución:** Agregar comando `catalog-sync` a `svc_py/` (Python CLI con Typer).
Puede ser un wrapper que invoca el bash script o reimplementación en Python.

**Archivos a modificar:**
- `svc_py/__init__.py` o `svc_py/main.py` — agregar comando Typer
- Decidir: ¿wrapper (`subprocess.run(svc.sh catalog-sync)`) o reimplementar?

---

## 3. Dual CLI (bash vs Python) — documentar en dependency-map

**Ya documentado:** El dependency-map ahora tiene sección de arquitectura dual
con tabla de qué comandos están en cuál CLI.

**Pendiente:** Decidir estrategia a futuro:
- ¿Todos los comandos nuevos van a ambos CLIs?
- ¿O el Python CLI es la versión "bonita" y el bash la "completa"?
- ¿Los comandos que solo existen en bash deberían tener un passthrough en Python?

---

## 4. Guías de servicios importantes que faltan

### emqx-guide.md
- Ya tiene ficha completa y compose con anchors
- La guía debería documentar: setup inicial, temas MQTT, ACLs, clustering (si aplica)
- Referencia: `agent/catalog/services/emqx/ficha.md` ya tiene mucho detalle

### esphome-guide.md
- Cómo flashear ESP32 desde el NAS
- Conexión con EMQX
- Configuración de dispositivos

---

## 5. _drafts/ que ya se pueden limpiar

| Archivo | Estado | Acción |
|---------|--------|--------|
| `PLAN-ntfy-usb-api.md` | ✅ Implementado completamente | Eliminar o archivar |
| `Skills_2.0.md` | ✅ Ideas extraídas y aplicadas | Eliminar o archivar |

---

## 6. Correcciones pendientes al catálogo (de learnings anteriores)

- [x] datasql/ficha.md: quitar PGDATA de env_required ← **YA ESTABA HECHO** (sesión anterior)
- [x] datasql/ficha.md: quitar TZ de env_required (hereda del global) ← **2026-08-17**
- [x] datasql/compose.yml: quitar ports "5432:5432" de postgres ← **YA ESTABA HECHO** (sesión anterior)
- [x] datasql/compose.yml: cambiar `env_file: .env` → `env_file: [../.env, .env]` ← **2026-08-17**
- [x] datasql/compose.yml: quitar `TZ: ${TZ}` de environment postgres (hereda del global) ← **2026-08-17**
- [x] datasql/compose.yml: IP hardcodeada `192.168.1.200` → `${SERVER_IP}` en label pgadmin ← **2026-08-17**
- [x] datasql/.env.example: quitar TZ (viene del global) ← **2026-08-17**
- [x] datasql/ficha.md: actualizar notes (env_file dual, TZ global) ← **2026-08-17**
- [x] Regenerar catalog.json con `python3 -m agent.catalog._index` ← **2026-08-17** (1→7 servicios)
- [x] Crear $dkco/.env global (¿ya existe? verificar) ← **YA EXISTÍA**: `agent/catalog/.env.global.example`

---

## 7. Homepage labels faltantes

| Servicio | Tiene labels | Acción |
|----------|:------------:|--------|
| vaultwarden | ❌ | Agregar al compose |
| homepage | ❌ | No necesita (es el propio dashboard) |

---

## 8. Verificaciones rápidas para empezar la próxima sesión

```bash
# Estado de docs
NAS_CLI=bash svc catalog-sync --status

# IP hardcodeada (debería ser 0)
grep -r "192.168.1.200" $dkco/*/compose.yml

# TZ duplicado (debería ser 0)
grep -rn "TZ=America" $dkco/*/compose.yml | grep "environment"

# env_file faltante
for f in $dkco/*/compose.yml; do
  grep -qL "env_file" "$f" && echo "⚠️  Falta env_file: $f"
done

# Servicios sin labels Homepage
for f in $dkco/*/compose.yml; do
  grep -qL "homepage\." "$f" && echo "⚠️  Sin labels: $f"
done
```

---

## Cómo retomar sin contexto

1. Leer `AGENTS.md` (se inyecta automáticamente en Kiro)
2. Si la skill se activa: leer `docker-nas/references/nas-context.md`
3. Antes de tocar compose: leer `docs/docker-entorno.md`
4. Para saber qué actualizar: leer `docs/dependency-map.md`
5. Para entender decisiones pasadas: leer `docs/ideas-decisions.md`
6. Para estado de docs: `NAS_CLI=bash svc catalog-sync --status`



---

## 9. Scanner de proyecto (herramienta que DETECTA lagunas automáticamente)

**Problema real:**
- El dependency-map es estático — solo sirve si el LLM lo lee
- Se creó `catalog-sync` pero ni el agente local ni el dependency-map lo detectaron
- El agente local no sabe de comandos nuevos (su prompt/tools están desactualizados)
- Pueden haber MUCHAS lagunas que nadie ve (scripts sin conectar, docs desactualizadas, etc.)

**Lo que se necesita:** Una herramienta que:
1. **Escanee** todos los archivos del proyecto (ambos repos)
2. **Identifique** qué es cada archivo (script, módulo, compose, doc, plugin, tool)
3. **Mapee conexiones** (quién carga a quién, qué sourcea qué, qué case llama qué)
4. **Detecte huecos** (script existe pero no está en svc.sh, comando en bash pero no en python, etc.)
5. **Genere reporte** de inconsistencias sin saturar el contexto del LLM

**Posible implementación:**
- Script Python: `agent/tools/project_scanner.py` o `docker/cli/lib/project-scan.sh`
- Lee progresivamente (no carga todo de golpe)
- Output: reporte de inconsistencias tipo:
  ```
  ⚠️  docker/cli/lib/catalog-sync.sh → no registrado en svc_py/ (Python CLI)
  ⚠️  svc catalog-sync → no documentado en agent/memory/SKILLS.md
  ⚠️  n8n tiene compose pero no ficha.md ni guía
  ⚠️  vaultwarden tiene compose pero no labels Homepage
  ✅  ntfy: compose → ficha → guía → script → labels → conectado
  ```

**Relación con dependency-map:**
- dependency-map = reglas estáticas (qué DEBERÍA estar conectado)
- scanner = verificación dinámica (qué REALMENTE está conectado)
- Juntos: dependency-map dice las reglas, scanner verifica que se cumplan

---

## 10. Actualizar prompt del agente local

**Problema:** El agente local (`agent "que comandos tengo"`) no sabe de:
- `svc catalog-sync`
- `svc diff` (tampoco lo mencionó)
- Comandos que se agregaron después de que se escribió el prompt

**Causa:** El prompt del agente (`agent/` system prompt) tiene una lista fija
de comandos. No se actualiza automáticamente al agregar comandos nuevos.

**Solución posible:**
- Que el prompt del agente lea dinámicamente los comandos disponibles desde svc.sh
- O que el prompt referencie `docker-nas/references/svc.md` en vez de listar inline
- O agregar un tool que ejecute `svc --help` y parsee la salida

---

## 11. Resumen de "lagunas del sistema" detectadas en esta sesión

| Laguna | Cómo se detectó | Solución implementada | Falta |
|--------|----------------|----------------------|-------|
| catalog-sync no conectado a svc | Usuario ejecutó comando | Conectado a bash CLI | Falta en Python CLI |
| catalog-sync no conocido por el agente | Usuario preguntó al agente | — | Actualizar prompt/skills del agente |
| Dual CLI no documentado | catalog-sync falló con Python | Documentado en dependency-map | Scanner automático |
| Servicios sin docs (n8n, vaultwarden) | catalog-sync --status | — | Ejecutar catalog-sync |
| IP hardcodeada en compose de HA | Revisión manual | Corregido con ${SERVER_IP} | Scanner detectaría automáticamente |
| TZ duplicado en HA compose | Revisión manual | Corregido (quitar environment TZ) | Scanner detectaría |
| ntfy.publish no soporta imágenes | Error en runtime | Documentado + shell_command workaround | — |
| Carpeta www/snapshots/ no existía | Error en runtime | mkdir -p | Scanner verificaría paths de volumes |



---

## 📋 Registro de sesión 2026-08-17 (Kiro Web)

### Tarea: Corregir catálogo datasql

| # | Acción | Archivo | Detalle | Estado |
|---|--------|---------|---------|:------:|
| 1 | Quitar TZ de env_required | ficha.md | Era redundante: TZ viene de ../.env global | ✅ |
| 2 | Actualizar notes | ficha.md | Documenta env_file dual y que TZ/PGDATA no requieren .env local | ✅ |
| 3 | Actualizar sección "Variables de entorno" | ficha.md | Separar "Requeridas (.env local)" de "Heredadas del global" | ✅ |
| 4 | Cambiar env_file a formato dual | compose.yml | `env_file: .env` → `env_file: [../.env, .env]` en postgres y pgadmin | ✅ |
| 5 | Quitar TZ de environment | compose.yml | En postgres: `TZ: ${TZ}` eliminado (hereda del global) | ✅ |
| 6 | Reemplazar IP hardcodeada | compose.yml | `192.168.1.200` → `${SERVER_IP}` en label homepage.href de pgadmin | ✅ |
| 7 | Quitar TZ del .env.example | .env.example | Ya no es responsabilidad del .env local | ✅ |
| 8 | Regenerar catalog.json | catalog.json | 1 servicio → 7 servicios indexados | ✅ |

### Hallazgos (cosas que YA estaban corregidas de sesiones anteriores)

- `PGDATA` ya NO estaba en env_required (corregido previamente)
- Puerto `5432:5432` ya NO estaba expuesto al host (corregido previamente)
- `.env.global.example` ya existía en `agent/catalog/`

### Pendientes que NO se tocaron en esta sesión (verificar en la sesión original)

- [ ] emqx/ficha.md: quitar db_net (mínimo privilegio) — el learning dice hacerlo, pero el compose actual SÍ usa db_net → **requiere decisión**: ¿emqx necesita db_net o no?
- [ ] Tabla de `docs/docker-entorno.md` muestra datasql con "env en compose" → actualizar para reflejar que ahora usa env_file dual
