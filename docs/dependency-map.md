# Mapa de Dependencias — Sistema Completo (nas-dotfiles + DebMenux)

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

| Script | Comando | Conectado a | Estado |
|--------|---------|-------------|--------|
| `docker/cli/svc.sh` | `svc` | alias en shell/lib/docker.sh | ✅ |
| `docker/cli/lib/discovery.sh` | (interno) | sourced por svc.sh | ✅ |
| `docker/cli/lib/health.sh` | `svc health` | case en svc.sh | ✅ |
| `docker/cli/lib/backup.sh` | `svc backup` | case en svc.sh | ✅ |
| `docker/cli/lib/menu.sh` | `svc menu` | case en svc.sh | ✅ |
| `docker/cli/lib/notifications.sh` | `ntfy_send()` | source manual | ✅ |
| `docker/cli/lib/catalog-sync.sh` | `svc catalog-sync` | case en svc.sh | ✅ Conectado |
| `shell/lib/aliases.sh` | aliases (ll, dps, bat...) | sourced por init.sh | ✅ |
| `shell/lib/nav.sh` | dk, adm, nasfk, up | sourced por init.sh | ✅ |
| `shell/lib/prompt.sh` | (prompt PS1) | sourced por init.sh | ✅ |
| `shell/lib/system.sh` | nas, disk, netinfo, logs | sourced por init.sh | ✅ |
| `shell/lib/instal.sh` | instal | sourced por init.sh | ✅ |
| `shell/lib/pipins.sh` | pipins | sourced por init.sh | ✅ |
| `shell/lib/git.sh` | gs, ga, gc, gp, gpl... | sourced por init.sh | ✅ |
| `shell/lib/completions.sh` | TAB completions | sourced por init.sh | ✅ |
| `shell/scripts/start-all.sh` | (directo o cron) | en PATH via init.sh | ✅ |
| `shell/scripts/stop-all.sh` | `off` | alias en aliases.sh | ✅ |
| `/debmenux/menu` | `debmenu` | symlink en /usr/local/bin/ | ✅ |

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
