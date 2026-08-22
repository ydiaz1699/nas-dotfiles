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
| ~~**emqx**~~ | ~~guía ❌~~ → ✅ **HECHO 2026-08-17** (emqx-guide.md) |
| ~~**esphome**~~ | ~~guía ❌, DebMenux script ❌~~ → ✅ **HECHO 2026-08-17** (esphome-guide.md + esphome.sh) |
| ~~**datasql**~~ | ~~DebMenux script ❌~~ → ✅ **HECHO 2026-08-17** (datasql.sh) |
| ~~**node-red**~~ | ~~DebMenux script ❌~~ → ✅ **HECHO 2026-08-17** (node-red.sh) |
| ~~**homepage**~~ | ~~DebMenux script ❌~~ → ✅ **HECHO 2026-08-17** (homepage.sh) |

**Pendiente aún:** n8n y vaultwarden (no están instalados aún en el NAS).

### Correcciones adicionales (sesión Kiro Web 2026-08-17 #2):
- ~~emqx/compose.yml: quitar db_net~~ → ✅ PR #33
- ~~emqx/ficha.md: quitar db_net~~ → ✅ PR #33
- ~~homepage/compose.yml: TZ inline → env_file dual~~ → ✅ PR #33
- ~~homepage/ficha.md: quitar TZ de env_required~~ → ✅ PR #33
- ~~ntfy/ficha.md: quitar TZ de env_required~~ → ✅ PR #33

---

## 2. catalog-sync en Python CLI

~~**Problema:** `catalog-sync` solo está en bash CLI (`svc.sh`). El usuario usa
`NAS_CLI=python` por defecto. Resultado: `svc catalog-sync` da error.~~

✅ **RESUELTO 2026-08-17:** Creado `svc_py/commands/catalog.py` con:
- `svc catalog-sync` → wrapper del bash script (o fallback nativo)
- `svc catalog-sync --status` → tabla Rich nativa (sin depender de bash)
- `svc catalog-sync --regenerate-index` → invoca `python3 -m agent.catalog._index`
- `svc catalog-sync --dry-run` → muestra qué haría sin ejecutar

---

## 3. Dual CLI (bash vs Python) — documentar en dependency-map

~~**Ya documentado:** El dependency-map ahora tiene sección de arquitectura dual
con tabla de qué comandos están en cuál CLI.~~

~~**Pendiente:** Decidir estrategia a futuro:~~
~~- ¿Todos los comandos nuevos van a ambos CLIs?~~
~~- ¿O el Python CLI es la versión "bonita" y el bash la "completa"?~~
~~- ¿Los comandos que solo existen en bash deberían tener un passthrough en Python?~~

✅ **RESUELTO 2026-08-17:** Decisión documentada en `docs/ideas-decisions.md` (#14):
- **Bash = fuente de verdad** (toda la lógica, 0 deps, siempre funciona)
- **Python = interfaz bonita** (Rich tables, InquirerPy, embellece output de bash)
- **bash_bridge.py** creado en `svc_py/core/` — helper genérico que invoca `svc.sh`
- Comando nuevo → implementar SOLO en bash → Python lo hereda via passthrough
- Si Python se beneficia de UI elaborada → wrapper explícito que llama bash + embellece

---

## 4. Guías de servicios importantes que faltan

### ~~emqx-guide.md~~ → ✅ **HECHO 2026-08-17**
Guía operativa completa: instalación, configuración, puertos/protocolos, dashboard web,
temas MQTT y estructura, clientes, autenticación/ACLs, integración con ESPHome/HA/Node-RED,
Homepage labels, backup/recuperación, troubleshooting.

### ~~esphome-guide.md~~ → ✅ **HECHO 2026-08-17**
Guía operativa completa: instalación, configuración (secrets.yaml, network_mode:host),
dashboard web, crear dispositivos (wizard + YAML manual), flashear (USB + OTA + CLI),
integración con EMQX (MQTT), Home Assistant (API vs MQTT), Homepage widget,
backup/recuperación, troubleshooting.

---

## 5. _drafts/ que ya se pueden limpiar

| Archivo | Estado | Acción |
|---------|--------|--------|
| `PLAN-ntfy-usb-api.md` | ✅ Implementado completamente | Eliminar o archivar |
| `Skills_2.0.md` | ✅ Ideas extraídas y aplicadas | Eliminar o archivar |
| `IDEA-scanner-incremental-git.md` | ✅ Implementado (PR #33) | Eliminar o archivar |

---

## 6. Correcciones pendientes al catálogo (de learnings anteriores)

- [x] datasql/ficha.md: quitar PGDATA de env_required ← **YA ESTABA HECHO** (sesión anterior)
- [x] datasql/ficha.md: quitar TZ de env_required (hereda del global) ← **2026-08-17**
- [x] datasql/compose.yml: limitar PostgreSQL a `127.0.0.1:5432:5432` para Home Assistant ← **Opción A en PR #56**
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

~~**Problema real:**~~
~~- El dependency-map es estático — solo sirve si el LLM lo lee~~
~~- Se creó `catalog-sync` pero ni el agente local ni el dependency-map lo detectaron~~

✅ **RESUELTO 2026-08-17:** Implementado `agent/tools/project_scanner.py` con:
- 5 categorías de verificación: servicios, compose hygiene, CLI parity, prompt agente, docs refs
- Accesible via: `svc scan` (bash y python), `python3 agent/tools/project_scanner.py`, tool del agente
- Soporta `--verbose`, `--json`, `--full`, `--changed`
- Detecta: servicios sin ficha/guía/script, IP hardcodeada, TZ duplicado, env_file faltante,
  comandos no documentados en el prompt del agente, docs_url rotos

### ✅ Scanner INCREMENTAL (git-based) implementado (PR #33, sesión Kiro Web #2):
- Snapshot persistido en `agent/cache/project-snapshot.json`
- `svc scan` → incremental (si hay snapshot) o full (primera vez)
- `svc scan --full` → forzar scan completo + regenerar snapshot
- `svc scan --changed` → solo listar qué archivos cambiaron desde último scan
- Clasificador reconoce 12 tipos de archivo (compose, ficha, guide, script, plugin, tool, etc.)
- git diff detecta cambios → solo verifica servicios afectados → reporte corto

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

~~**Problema:** El agente local (`agent "que comandos tengo"`) no sabe de:~~
~~- `svc catalog-sync`~~
~~- `svc diff` (tampoco lo mencionó)~~
~~- Comandos que se agregaron después de que se escribió el prompt~~

✅ **RESUELTO 2026-08-17:** BLOCK_CONTEXTO_NAS actualizado con:
- `svc lista` — listar servicios con estado
- `svc catalog-sync [servicio]` — sincronizar documentación
- `svc scan` — detectar lagunas del proyecto
- `svc scan --full` — scan completo (ignorar snapshot)
- `svc scan --changed` — solo listar qué archivos cambiaron
- `svc depends <servicio>` — ver dependencias
- `svc backup-all` — backup de todos + resumen + ntfy
- `svc doctor-history` — historial con tendencia
- `svc clone <origen> <nuevo>` — duplicar servicio
- `svc logs-grep <patrón>` — buscar en logs de todos
- `svc cron` — agendar backups/updates via crontab
- `svc lock/unlock <servicio>` — proteger/desproteger

BLOCK_HERRAMIENTAS actualizado con:
- `project_scan(verbose)` — tool que ejecuta el scanner

Tool registrada en `agent/tools/__init__.py` → ALL_TOOLS.

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

### Tarea: Guías operativas

| # | Archivo creado | Contenido | Estado |
|---|----------------|-----------|:------:|
| 1 | `docs/services/emqx-guide.md` | Instalación, config, puertos, dashboard, MQTT topics, auth/ACLs, integración ESPHome/HA/Node-RED, backup, troubleshooting | ✅ |
| 2 | `docs/services/esphome-guide.md` | Instalación, config, dashboard, crear dispositivos, flash USB/OTA, integración MQTT/HA, backup, troubleshooting | ✅ |

### Tarea: Scripts DebMenux

| # | Archivo creado | Características | Estado |
|---|----------------|-----------------|:------:|
| 1 | `scripts/services/datasql.sh` | Stack PostgreSQL+pgAdmin+Redis, genera passwords auto, db_net, no expone puertos DB, pgAdmin uid 5050 | ✅ |
| 2 | `scripts/services/esphome.sh` | network_mode:host, privileged, secrets.yaml template, detecta USB, sin cap_drop | ✅ |
| 3 | `scripts/services/homepage.sh` | Config completa (settings/docker/services/widgets/bookmarks YAML), Docker socket, homepage_net | ✅ |
| 4 | `scripts/services/node-red.sh` | iot_net, uid 1000, sin cap_drop, conexión a EMQX via hostname, healthcheck | ✅ |

### Tarea: catalog-sync en Python CLI

| # | Archivo | Cambio | Estado |
|---|---------|--------|:------:|
| 1 | `svc_py/commands/catalog.py` | Nuevo módulo: --status (tabla Rich), wrapper bash, --regenerate-index, fallback nativo | ✅ |
| 2 | `svc_py/app.py` | Registrado comando `catalog-sync` en la app Typer | ✅ |

### Hallazgos adicionales

- `emqx/compose.yml` tiene IP hardcodeada en label homepage.href (`192.168.1.200`) → debería corregirse (no se tocó en esta sesión, era solo para datasql)
- `catalog.json` pasó de 1 servicio a 7 al regenerar — indica que nunca se había regenerado después de agregar servicios
- `filebrowser` no tiene script DebMenux — no estaba en PENDIENTES pero se detectó con `--status`
- `homepage` no tiene labels Homepage — es normal (no se auto-descubre a sí mismo)



### Tarea: Project Scanner + actualizar prompt del agente

| # | Archivo | Cambio | Estado |
|---|---------|--------|:------:|
| 1 | `agent/tools/project_scanner.py` | Nuevo: scanner con 5 categorías de verificación (servicios, compose hygiene, CLI parity, prompt agente, docs refs). Standalone + @tool compatible | ✅ |
| 2 | `svc_py/commands/scanner.py` | Nuevo: comando `svc scan` en Python CLI (subprocess al scanner) | ✅ |
| 3 | `svc_py/app.py` | Registrado comando `scan` en app Typer | ✅ |
| 4 | `docker/cli/svc.sh` | Registrado case `scan` que invoca el script Python | ✅ |
| 5 | `agent/nas_agent.py` → BLOCK_CONTEXTO_NAS | Agregados: `svc lista`, `svc catalog-sync`, `svc scan`, `svc depends` | ✅ |
| 6 | `agent/nas_agent.py` → BLOCK_HERRAMIENTAS | Agregado: `project_scan(verbose)` | ✅ |
| 7 | `agent/tools/__init__.py` | Import + ALL_TOOLS: `project_scan` registrado | ✅ |

### Resultado del scanner tras correcciones

```
📊 Scan completado: 8 servicios
   ✅ Completos: 7
   🔴 Errores: 0
   ⚠️  Warnings: 0
```

Solo queda filebrowser sin script DebMenux (info, no urgente).


---

## 📋 Registro de sesión 2026-08-17 — Kiro Web #2 (Resolver gaps)

### PR #33: fix/gaps-completions-scanner-incremental

| # | Archivo | Cambio | Estado |
|---|---------|--------|:------:|
| 1 | `shell/lib/docker.sh` | +8 comandos en `_SVC_GLOBAL_CMDS` (TAB completions) | ✅ |
| 2 | `AGENTS.md` | Tablas completas: 20 globales + 17 con servicio | ✅ |
| 3 | `.kiro/skills/.../svc.md` | Tabla de globales completa + listing archivos | ✅ |
| 4 | `emqx/compose.yml` | Quitar db_net (mínimo privilegio) | ✅ |
| 5 | `emqx/ficha.md` | Quitar db_net + nota reconexión futura | ✅ |
| 6 | `agent/tools/project_scanner.py` | Scanner INCREMENTAL (git-based, snapshot, clasificador, 3 modos) | ✅ |
| 7 | `agent/nas_agent.py` | +9 comandos en BLOCK_CONTEXTO_NAS | ✅ |
| 8 | `homepage/compose.yml` | Quitar TZ inline, agregar env_file dual | ✅ |
| 9 | `homepage/ficha.md` | Quitar TZ de env_required, actualizar notes | ✅ |
| 10 | `ntfy/ficha.md` | Quitar TZ de env_required (viene del global) | ✅ |

### Hallazgos

- `homepage_net` es CORRECTA — existe en el NAS real (Homepage la crea, ntfy se conecta como external)
- emqx/compose.yml YA usaba ${SERVER_IP} (no había IP hardcodeada como se pensaba)
- El scanner detecta correctamente que nas_agent.py no conoce los comandos nuevos

### Lo que queda pendiente tras esta sesión

- **n8n, vaultwarden**: sin documentar (no están instalados aún)
- **filebrowser**: sin script DebMenux (info, no urgente)
- **TODO.md items pendientes**: svc dashboard (TUI Textual), catálogo pre-cargado en agente, compare_catalog, resumen post-sesión, auto-heal, psutil
- **Seguridad**: confirmación doble canal para servicios protected
- **Backups**: backup remoto (rclone/S3), svc snapshot/rollback
