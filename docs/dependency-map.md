# Mapa de Dependencias — Sistema Completo (nas-dotfiles + DebMenux)

> **Mapa canónico relacionado:** [`framework-knowledge-compilation.md`](framework-knowledge-compilation.md). Este archivo conserva las cascadas esperadas y checklists de impacto; el scanner es quien verifica conexiones observadas.

> Cuando modificas un archivo, ¿qué otros deben actualizarse?
> Cubre AMBOS repos como un solo sistema interconectado.
> Actualizado: 2026-08-16

---

## Vista general del sistema

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SISTEMA COMPLETO                                     │
│                                                                              │
│  ┌─── nas-dotfiles (/nas-dotfiles) ────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌─ Shell ──────┐  ┌─ CLI Docker ─┐  ┌─ Agente IA ──────────────┐ │    │
│  │  │ init.sh      │  │ svc.sh       │  │ nas_agent.py             │ │    │
│  │  │ lib/         │  │ lib/         │  │ tools/ plugins/ events/  │ │    │
│  │  │  aliases.sh  │  │  discovery   │  │ catalog/ memory/         │ │    │
│  │  │  nav.sh      │  │  health      │  │ config/ scheduler/       │ │    │
│  │  │  prompt.sh   │  │  backup      │  └──────────────────────────┘ │    │
│  │  │  system.sh   │  │  menu        │                                │    │
│  │  │  instal.sh   │  │  notifications│  ┌─ Skill (Kiro/LLMs) ─────┐ │    │
│  │  │  git.sh      │  │  catalog-sync│  │ SKILL.md                 │ │    │
│  │  │  completions │  └──────────────┘  │ references/nas-context   │ │    │
│  │  └──────────────┘                     │ references/entorno,svc.. │ │    │
│  │                                       └──────────────────────────┘ │    │
│  │  ┌─ Docs ──────────────────────────────────────────────────────┐  │    │
│  │  │ AGENTS.md  README.md  GUIDE.md  TODO.md  INSTALL.md         │  │    │
│  │  │ docs/docker-entorno.md  docs/dependency-map.md               │  │    │
│  │  │ docs/ideas-decisions.md  docs/nas-manual.md                  │  │    │
│  │  │ docs/catalog-sync-pipeline.md                                │  │    │
│  │  │ docs/services/<svc>-guide.md (por servicio)                  │  │    │
│  │  └─────────────────────────────────────────────────────────────┘  │    │
│  │                                                                      │    │
│  │  ┌─ Catálogo (agent/catalog/services/<svc>/) ──────────────────┐  │    │
│  │  │ ficha.md + compose.yml + .env.example  (por servicio)        │  │    │
│  │  └─────────────────────────────────────────────────────────────┘  │    │
│  └──────────────────────────────────────────────────────────────────────┘    │
│                              │                                                │
│                    Integración bidireccional                                  │
│                              │                                                │
│  ┌─── DebMenux (/debmenux) ────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌─ Core ───────┐  ┌─ Scripts ────────────┐  ┌─ Templates ───────┐ │    │
│  │  │ menu         │  │ services/             │  │ usb-automount/    │ │    │
│  │  │ install.sh   │  │   _template.sh        │  │   usb-automount.sh│ │    │
│  │  │ services.json│  │   adguard.sh          │  │   *.service       │ │    │
│  │  └──────────────┘  │   emqx.sh            │  │   *.rules         │ │    │
│  │                     │   ntfy.sh            │  └───────────────────┘ │    │
│  │  ┌─ Lib ────────┐  │   usb-api.sh         │                        │    │
│  │  │ utils.sh     │  │   homeassistant.sh    │  ┌─ Docs ────────────┐ │    │
│  │  │ docker.sh    │  └───────────────────────┘  │ AGENTS.md         │ │    │
│  │  │ integration  │                             │ README.md         │ │    │
│  │  │ notifications│                             └───────────────────┘ │    │
│  │  └──────────────┘                                                    │    │
│  └──────────────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## Grafos de dependencias por tipo de cambio

### A. Servicio Docker (compose.yml)

```
$dkco/<svc>/compose.yml  (FUENTE DE VERDAD)
    │
    │  nas-dotfiles:
    ├──→ agent/catalog/services/<svc>/compose.yml    (copia en catálogo)
    ├──→ agent/catalog/services/<svc>/ficha.md       (metadatos extraídos)
    ├──→ agent/catalog/services/<svc>/.env.example   (sanitizado de .env)
    ├──→ docs/services/<svc>-guide.md                (guía operativa)
    ├──→ docker-nas/SKILL.md                         (tabla de guías)
    ├──→ docker-nas/references/nas-context.md        (skill registry)
    ├──→ AGENTS.md                                   (tabla de servicios)
    ├──→ docs/nas-manual.md                          (tabla servicios + puertos)
    ├──→ README.md                                   (si cambia estructura)
    │
    │  DebMenux:
    ├──→ /debmenux/scripts/services/<svc>.sh         (instalador)
    └──→ /debmenux/services.json                     (catálogo DebMenux)
```

### B. Script/comando de svc

```
docker/cli/lib/<nuevo>.sh  (SCRIPT CREADO)
    │
    │  Conexión al CLI:
    ├──→ docker/cli/svc.sh                  (case "comando)" — OBLIGATORIO)
    ├──→ shell/lib/completions.sh           (autocompletado TAB)
    │
    │  Documentación:
    ├──→ GUIDE.md                           (sección "Comandos de svc")
    ├──→ README.md                          (estructura del proyecto)
    ├──→ docker-nas/references/svc.md       (referencia completa de svc)
    ├──→ docker-nas/SKILL.md                (comandos esenciales)
    ├──→ AGENTS.md                          (si es comando frecuente)
    └──→ docs/dependency-map.md             (tabla CLI — marcar ✅)
```

### C. Módulo de shell (aliases, navegación, prompt)

```
shell/lib/<modulo>.sh  (MÓDULO CREADO/MODIFICADO)
    │
    │  Carga:
    ├──→ shell/init.sh                      (source del módulo — OBLIGATORIO)
    │
    │  Documentación:
    ├──→ GUIDE.md                           (sección del módulo)
    ├──→ README.md                          (si cambia estructura)
    ├──→ docker-nas/references/entorno.md   (referencia shell)
    ├──→ docker-nas/references/nas-context.md (encoded preferences si es alias)
    └──→ AGENTS.md                          (si es alias que el LLM debe conocer)
```

### D. Plugin del agente

```
agent/plugins/<plugin>.py  (PLUGIN CREADO)
    │
    │  Registro:
    ├──→ agent/plugins/__init__.py          (importar — para carga dinámica)
    │
    │  Documentación:
    ├──→ agent/README.md                    (tabla de plugins)
    ├──→ docker-nas/references/agent.md     (referencia del agente)
    ├──→ README.md                          (si cambia estructura)
    └──→ GUIDE.md                           (sección agente → plugins)
```

### E. Tool del agente

```
agent/tools/<tool>.py  (TOOL CREADA)
    │
    │  Registro:
    ├──→ agent/tools/__init__.py            (importar)
    │
    │  Documentación:
    ├──→ agent/README.md                    (tabla de 28+ tools)
    ├──→ docker-nas/references/agent.md     (referencia)
    └──→ GUIDE.md                           (lista de tools)
```

### F. Template de DebMenux (usb-automount, etc.)

```
/debmenux/templates/<template>/  (TEMPLATE CREADO/MODIFICADO)
    │
    │  Instalación (se copia al sistema):
    ├──→ /usr/local/bin/<script>            (copiar manualmente o via post-install)
    ├──→ /etc/systemd/system/<unit>         (si tiene .service/.timer)
    │
    │  Documentación:
    ├──→ /debmenux/README.md                (si cambia arquitectura)
    ├──→ nas-dotfiles/docs/services/<svc>-guide.md  (si afecta un servicio)
    ├──→ nas-dotfiles/docs/nas-manual.md    (si cambia comportamiento del NAS)
    └──→ nas-dotfiles/AGENTS.md             (si cambia un comando/ruta)
```

### G. Script de servicio en DebMenux

```
/debmenux/scripts/services/<svc>.sh  (INSTALADOR CREADO)
    │
    │  Registro:
    ├──→ /debmenux/services.json            (agregar entrada — OBLIGATORIO)
    │
    │  Integración (si habilitada):
    ├──→ register_to_catalog() genera:
    │     ├──→ nas-dotfiles/agent/catalog/services/<svc>/ficha.md
    │     ├──→ nas-dotfiles/agent/catalog/services/<svc>/compose.yml
    │     ├──→ nas-dotfiles/agent/catalog/services/<svc>/.env.example
    │     ├──→ nas-dotfiles/docs/services/<svc>-guide.md
    │     └──→ ntfy notification (topic: docker)
    │
    │  Documentación:
    ├──→ /debmenux/README.md                (tabla de servicios)
    └──→ /debmenux/AGENTS.md                (si cambia estructura)
```

### H. Documentación (docs/, guías, README)

```
docs/<nuevo-archivo>.md  (DOCUMENTO CREADO)
    │
    ├──→ README.md                          (tabla de documentación)
    ├──→ docker-nas/SKILL.md                (si es guía de servicio → tabla)
    ├──→ docker-nas/references/nas-context.md (lazy loading table)
    └──→ AGENTS.md                          (tabla "Documentación adicional")
```

### I. Variables globales ($dkco/.env)

```
$dkco/.env  (MODIFICADO)
    │
    ├──→ Todos los compose con env_file: ../.env  (re-interpolar al recrear)
    ├──→ docs/docker-entorno.md             (documentar cambio)
    ├──→ AGENTS.md                          (si cambia IP)
    ├──→ docker-nas/references/nas-context.md (si cambia IP)
    ├──→ docs/nas-manual.md                 (si cambia IP)
    └──→ /etc/usb-automount.conf            (si cambia NTFY_URL)
```

### J. Contenido en _drafts/ (carpeta temporal de ideas)

```
_drafts/<archivo>  (CONTENIDO NUEVO — ideas, planes, fragmentos, composes copiados)
    │
    │  El LLM debe IDENTIFICAR qué tipo de contenido es:
    │
    ├─ ¿Es un PLAN de implementación? (como PLAN-ntfy-usb-api.md)
    │     └──→ Leer, entender alcance, preguntar si implementar
    │
    ├─ ¿Son FRAGMENTOS dispersos sobre un tema? (diagnósticos, notas, chat logs)
    │     └──→ Usar docs/meta-prompt-unificar.md para unificar en UNA guía coherente
    │          └──→ Resultado va a docs/services/<svc>-guide.md o docs/<tema>.md
    │               Si es infraestructura transversal del host, usar
    │               docker-nas/references/<tema>.md y derivaciones junto a él
    │
    ├─ ¿Es un COMPOSE copiado de internet?
    │     └──→ Ajustar a convenciones (docs/docker-entorno.md)
    │          └──→ Resultado va a $dkco/<svc>/compose.yml → cascade completa
    │
    ├─ ¿Es una IDEA o feature request?
    │     └──→ Agregar a TODO.md en la sección correspondiente
    │
    ├─ ¿Es DOCUMENTACIÓN de otra sesión/LLM? (como Skills_2.0.md)
    │     └──→ Extraer ideas aplicables → implementar o agregar a ideas-decisions.md
    │
    └─ ¿Ya se implementó lo que describe?
          └──→ Se puede eliminar o mover a docs/ como referencia histórica
```

---

## Tabla de impacto completa

| Si modifico... | Debo actualizar en nas-dotfiles... | Debo actualizar en DebMenux... |
|----------------|-----------------------------------|-------------------------------|
| **compose.yml de servicio** | catálogo, guía, SKILL.md, nas-context, AGENTS.md, nas-manual | services.json, script .sh (si no existe) |
| **Mejoro compose existente** | guía (ANTES/DESPUÉS), ficha, compose catálogo | — |
| **Puerto de servicio** | ficha, guía, AGENTS.md, nas-manual, nas-context | services.json |
| **Red de servicio** | ficha, guía, AGENTS.md, nas-manual, docker-entorno | — |
| **Variables .env** | .env.example catálogo, ficha | — |
| **$dkco/.env global** | docker-entorno, AGENTS.md, nas-context, nas-manual | — |
| **Labels Homepage** | guía, homepage-guide | — |
| **Script nuevo para svc** | svc.sh, completions, GUIDE, README, svc.md, SKILL, AGENTS, dependency-map | — |
| **Alias nuevo de shell** | aliases.sh, init.sh (si nuevo módulo), GUIDE, AGENTS, nas-context | — |
| **Plugin del agente** | plugins/__init__, agent/README, agent.md, GUIDE | — |
| **Tool del agente** | tools/__init__, agent/README, agent.md, GUIDE | — |
| **Template DebMenux** | guía del servicio, nas-manual, AGENTS | README.md |
| **Script servicio DebMenux** | (auto: register_to_catalog genera) | services.json, README |
| **Documento nuevo en docs/** | README (tabla docs), SKILL (si guía), nas-context (lazy loading), AGENTS | — |
| **usb-automount.sh (template)** | copiar a /usr/local/bin/, ntfy-guide troubleshooting | README si cambia estructura |
| **notifications.sh** | — | Si cambió API de ntfy_send → sincronizar en nas-dotfiles |
| **integration.sh** | — | README si cambia cascada |
| **init.sh (shell loader)** | GUIDE (si cambia qué carga), README | — |
| **Documento nuevo en docker-nas/references/** | README, SKILL.md, nas-context.md, AGENTS.md si es referencia operativa | — |
| **IP del NAS** | $dkco/.env, AGENTS, nas-context, nas-manual, ntfy-guide, usb-automount.conf | — |

---

## Archivos espejo entre repos

Archivos que existen en AMBOS repos y deben estar sincronizados:

| nas-dotfiles | DebMenux | Sincronización |
|---|---|---|
| `docker/cli/lib/notifications.sh` | `lib/notifications.sh` | Misma función `ntfy_send()` — si cambia en uno, actualizar el otro |
| `agent/catalog/services/<svc>/compose.yml` | `$dkco/<svc>/compose.yml` (host real) | Catálogo = copia del real |
| — | `templates/usb-automount/usb-automount.sh` | Se copia a `/usr/local/bin/` en el NAS |
| `AGENTS.md` | `AGENTS.md` | Independientes pero complementarios |

---

## Herramientas CLI — Estado de conexión

> **IMPORTANTE:** `svc` tiene DOS implementaciones (bash y Python).
> La variable `NAS_CLI=bash|python` decide cuál se ejecuta.
> Un comando agregado a svc.sh NO funciona si el usuario usa `NAS_CLI=python` (y viceversa).

### Arquitectura dual del CLI

```
Usuario escribe: svc <comando>
    │
    └─→ función svc() en shell/init.sh
          │
          ├─ NAS_CLI=bash (default)
          │     └──→ $NAS_DOTFILES/docker/cli/svc.sh
          │            └── lib/*.sh (discovery, health, backup, menu, catalog-sync...)
          │
          └─ NAS_CLI=python
                └──→ python3 -m svc_py
                       └── svc_py/ (Typer + Rich + InquirerPy + Docker SDK)
```

**Regla al agregar comando nuevo a svc:**
1. ¿A cuál CLI se agrega? (bash, python, o ambos)
2. Si el usuario usa Python (`NAS_CLI=python`), agregar SOLO a bash no sirve
3. Lo ideal: implementar en bash primero, después port a Python si se necesita
4. Documentar en cuál está: ver tabla abajo

### Tabla de comandos y en cuál CLI están

| Comando | Bash (svc.sh) | Python (svc_py) | Notas |
|---------|:-------------:|:---------------:|-------|
| `lista` | ✅ | ✅ | Ambos |
| `health` | ✅ | ✅ | Ambos |
| `up/down/restart/stop/start` | ✅ | ✅ | Ambos (passthrough) |
| `logs` | ✅ | ✅ | Ambos |
| `update` / `update-all` | ✅ | ✅ | Ambos |
| `backup` / `restore` | ✅ | ✅ | Ambos |
| `menu` | ✅ | ✅ | Bash=fzf, Python=InquirerPy |
| `doctor` | ✅ | ✅ | Ambos |
| `port-map` | ✅ | ✅ | Ambos |
| `create` | ✅ | ✅ | Ambos |
| `diff` | ✅ | ❌ | Solo bash |
| `size` | ✅ | ❌ | Solo bash |
| `net` | ✅ | ❌ | Solo bash |
| `watch` | ✅ | ❌ | Solo bash |
| `catalog-sync` | ✅ | ✅ | Ambos (Python wrapper via bash_bridge) |
| `scan` | ✅ | ✅ | Ambos (Python: subprocess al scanner) |
| `backup-all` | ✅ | ❌ | Solo bash — Python hereda via passthrough |
| `logs-grep` | ✅ | ❌ | Solo bash |
| `clone` | ✅ | ❌ | Solo bash |
| `cron` | ✅ | ❌ | Solo bash |
| `doctor-history` | ✅ | ❌ | Solo bash |
| `lock` / `unlock` | ✅ | ❌ | Solo bash |
| `snapshot` | ✅ | ✅ | Python registra el comando y delega a Bash mediante `bash_bridge.py` |
| `rollback` | ✅ | ❌ | Bash; usar `NAS_CLI=bash svc rollback <svc>` desde Python mientras no tenga wrapper |
| `depends` | ✅ | ✅ | Ambos |
| `open` | ✅ | ✅ | Ambos |
| `env` | ✅ | ✅ | Ambos |

> **Estrategia:** Comando nuevo → implementar SOLO en bash → Python lo hereda via `bash_bridge.py` si necesita UI elaborada. Los que están "solo bash" funcionan porque la función `svc()` invoca svc.sh cuando el comando no está registrado en Typer.

### Al agregar comando nuevo, actualizar:

```
Nuevo comando para svc
    │
    ├──→ ¿En cuál CLI?
    │     ├── Bash: docker/cli/svc.sh (case) + docker/cli/lib/<script>.sh
    │     ├── Python: svc_py/ (agregar comando Typer)
    │     └── Ambos: implementar en los dos
    │
    ├──→ shell/lib/docker.sh (_SVC_GLOBAL_CMDS o _SVC_SERVICE_CMDS) ← completions
    ├──→ GUIDE.md (lista de comandos)
    ├──→ references/svc.md
    ├──→ AGENTS.md (si es frecuente)
    ├──→ dependency-map (esta tabla — marcar en cuál CLI está)
    └──→ Si solo está en UN CLI → documentar como pendiente para el otro
```

---

## Reglas del LLM al crear algo nuevo

### Si creo un SERVICIO:
```
1. compose.yml + .env + carpetas (mkdir)
2. svc up <svc>
3. catalog-sync (o manual): ficha + guía + .env.example
4. AGENTS.md: agregar a tabla de servicios
5. nas-manual.md: agregar puerto
6. nas-context.md: agregar al registry
7. DebMenux: services.json + script .sh (si aplica)
8. README.md: si cambia estructura del proyecto
```

### Si creo un SCRIPT para svc:
```
1. Crear docker/cli/lib/<nombre>.sh
2. Conectar en svc.sh (case statement) ← OBLIGATORIO
3. Agregar completions en shell/lib/completions.sh
4. GUIDE.md: agregar a lista de comandos
5. references/svc.md: documentar uso
6. README.md: actualizar estructura
7. dependency-map: marcar ✅ en tabla CLI
8. AGENTS.md: si es comando frecuente
```

### Si creo un ALIAS de shell:
```
1. Agregar en shell/lib/<modulo>.sh (aliases.sh o nuevo módulo)
2. Si es módulo nuevo: source en init.sh
3. GUIDE.md: documentar
4. AGENTS.md: agregar a tabla de aliases
5. nas-context.md: agregar a encoded preferences (NUNCA/SIEMPRE)
6. references/entorno.md: documentar
```

### Si creo un PLUGIN del agente:
```
1. Crear agent/plugins/<nombre>_plugin.py
2. Heredar de BasePlugin, definir meta, setup()
3. agent/README.md: agregar a tabla de plugins
4. references/agent.md: documentar
5. GUIDE.md: mencionar en sección agente
```

### Si creo un SCRIPT de servicio en DebMenux:
```
1. Crear /debmenux/scripts/services/<svc>.sh
2. services.json: agregar entrada ← OBLIGATORIO
3. Al final de install_service(): register_to_catalog()
4. /debmenux/README.md: agregar a tabla de servicios
5. /debmenux/AGENTS.md: si cambia estructura
```

### Si creo un DOCUMENTO nuevo:
```
1. Crear docs/<nombre>.md
2. README.md: agregar a tabla de documentación
3. SKILL.md: si es guía de servicio → agregar a tabla de guías
4. nas-context.md: agregar a tabla lazy loading
5. AGENTS.md: si es referencia que el LLM debe conocer
```

### Si creo un TEMPLATE en DebMenux:
```
1. Crear /debmenux/templates/<nombre>/
2. Script de post-install que lo instala en el sistema
3. Documentar en guía del servicio correspondiente (nas-dotfiles)
4. /debmenux/README.md: actualizar arquitectura
5. Si se copia al sistema (/usr/local/bin/): verificar que la versión está actualizada
```

---

## Verificación rápida

```bash
# ¿Todos los scripts de svc están conectados?
grep -oP "^\s+\K[a-z-]+\)" /nas-dotfiles/docker/cli/svc.sh | sort

# ¿Todos los módulos de shell se cargan?
grep "source.*lib/" /nas-dotfiles/shell/init.sh

# ¿services.json de DebMenux tiene todos los scripts?
ls /debmenux/scripts/services/*.sh | sed 's|.*/||;s|\.sh||;s|_template||' | sort
jq -r '.services[].id' /debmenux/services.json | sort

# ¿IP hardcodeada en algún compose?
grep -r "192.168.1.200" $dkco/*/compose.yml

# ¿TZ duplicado?
grep -rn "TZ=America" $dkco/*/compose.yml | grep -v "^.*:#"

# ¿Falta env_file en algún compose?
for f in $dkco/*/compose.yml; do
  grep -qL "env_file" "$f" && echo "⚠️  Falta env_file: $f"
done

# ¿Catálogo sincronizado con servicios reales?
diff <(ls $dkco/*/compose.yml | sed 's|.*/\(.*\)/compose.yml|\1|' | sort) \
     <(ls /nas-dotfiles/agent/catalog/services/ | sort)
```



---

## K. Consistencia arquitectónica verificable

`dependency-map.md` continúa siendo la explicación humana de la cascada. La verificación ejecutable vive en tres piezas:

```text
agent/architecture/contracts.json  → contratos y niveles de dependencia
agent/tools/project_index.py       → descubre conexiones reales en ambos repos
agent/tools/project_scanner.py     → compara contratos contra el índice
```

El índice generado se guarda localmente en `agent/cache/project-index.json` y no reemplaza `agent/cache/project-snapshot.json`:

- `project-index.json` = qué existe y dónde está conectado.
- `project-snapshot.json` = estado del último scan incremental.

Niveles de conexión:

| Nivel | Significado | Severidad base |
|---|---|---|
| `functional` | Sin la conexión, la capacidad no puede ejecutarse | error |
| `interface` | Falta una superficie de usuario, como completion | warning |
| `knowledge` | El agente o skill no conoce la capacidad | warning |
| `documentation` | Falta o está desactualizada una referencia | info |
| `historical` | Falta contexto de decisión o continuidad | info |

Antes de declarar conectado un comando nuevo, el scanner debe poder responder:

1. ¿Está registrado en Bash y/o Python?
2. ¿Tiene completion si corresponde?
3. ¿El agente conoce el comando?
4. ¿Está declarado en `contracts.json` si la paridad es obligatoria?
5. ¿La documentación y el mapa reflejan su superficie real?

Comandos locales del índice:

```bash
python3 agent/tools/project_index.py --check
python3 agent/tools/project_index.py
```

La primera versión verifica especialmente `catalog-sync`, `scan`, paridad Bash/Python y la relación scripts DebMenux ↔ `services.json`.
