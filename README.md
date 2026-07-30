# nas-dotfiles

Shell framework, Docker CLI y agente inteligente para administrar un NAS Debian/Ubuntu con Docker.

## Filosofía

**Todo el código vive exclusivamente en `/nas-dotfiles/`.** Ruta fija en la raíz del sistema, independiente del usuario. No se crean symlinks. El único rastro fuera son 2 líneas en cada `.bashrc` (tu usuario + root).

Borrar el proyecto = `./uninstall.sh && sudo rm -rf /nas-dotfiles/`

## Estructura

```
nas-dotfiles/
├── setup                   # Entry point universal (auto-detecta modo)
├── install.sh              # Bash interactivo (fallback sin Python)
├── uninstall.sh            # Revertir instalación completamente
├── requirements.txt        # Dependencias Python del agente
├── pyproject.toml          # Config: ruff, pytest, mypy
├── ui/
│   ├── setup.py            # TUI moderno (Rich + InquirerPy)
│   └── requirements-setup.txt
├── shell/
│   ├── init.sh             # Loader principal (sourced por ~/.bashrc)
│   └── lib/
│       ├── aliases.sh      # Aliases del sistema
│       ├── nav.sh          # Navegación rápida (adm, dk, up, fzf)
│       ├── docker.sh       # Autocompletado de svc
│       ├── system.sh       # nas dashboard, disk, netinfo, logs
│       ├── instal.sh       # Wrapper inteligente de apt
│       ├── prompt.sh       # Prompt con docker + disco + git
│       ├── git.sh          # Aliases y helpers de git
│       └── completions.sh  # Completions adicionales
├── docker/
│   └── cli/
│       ├── svc.sh          # CLI principal de servicios Docker
│       └── lib/            # Módulos del CLI
├── agent/                  # Agente Python (Strands Agents SDK)
│   ├── nas_agent.py        # Entry point (sesión persistente)
│   ├── core/               # Lógica de negocio (managers)
│   │   ├── _result.py      # ToolResult dataclass
│   │   ├── service_manager.py  # start/stop/restart/update/logs
│   │   ├── compose_manager.py  # create/validate/read
│   │   └── backup_manager.py   # backup/restore/list
│   ├── tools/              # Thin wrappers (@tool → core)
│   │   ├── docker_tools.py
│   │   ├── compose_tools.py
│   │   ├── backup_tools.py
│   │   ├── discovery_tools.py
│   │   ├── diagnostic_tools.py
│   │   ├── system_tools.py
│   │   └── search_tools.py
│   ├── plugins/            # Sistema de plugins dinámicos
│   │   ├── base.py         # BasePlugin + PluginMeta
│   │   ├── loader.py       # Auto-discovery + load/unload
│   │   ├── docker_plugin.py    # Health check cada 5 min
│   │   ├── backup_plugin.py    # Backup diario automático
│   │   └── network_plugin.py   # Escaneo puertos cada 15 min
│   ├── events/             # Event bus pub/sub
│   │   ├── bus.py          # EventBus (exact/wildcard/global)
│   │   └── mqtt_listener.py   # MQTT → EventBus pipeline
│   ├── scheduler/          # Tareas periódicas (cron-like)
│   │   └── runner.py       # Threaded task runner
│   ├── cache/              # Cache KV con TTL
│   │   └── store.py        # Thread-safe + persistencia
│   ├── catalog/            # Fichas de servicios
│   │   ├── _rules.md       # Reglas de generación
│   │   ├── _compose_base.md   # Template base (anchors YAML)
│   │   ├── _template.md    # Template de fichas
│   │   ├── _index.py       # Generador de catalog.json
│   │   ├── catalog.json    # Índice auto-generado
│   │   └── services/       # Fichas individuales
│   │       └── emqx.md
│   └── config/
│       └── defaults.yml    # Configuración centralizada
└── tests/                  # 62 tests
    ├── conftest.py         # Mock de strands para CI
    ├── test_result.py
    ├── test_validation.py
    ├── test_compose_generation.py
    └── test_phase3.py      # Plugins, events, cache
```

## Arquitectura del Agente

```
┌─────────────────────────────────────────────────────────────┐
│                        NAS Agent                             │
├─────────────────────────────────────────────────────────────┤
│  @tool (Strands SDK)  →  Core Manager  →  safe_run()       │
│       thin wrapper        lógica real      ejecución segura  │
├─────────────────────────────────────────────────────────────┤
│  Plugins          Events           Scheduler       Cache     │
│  (dinámicos)      (pub/sub)        (periódico)     (TTL)    │
├─────────────────────────────────────────────────────────────┤
│  MQTT Broker (EMQX) ←→ MQTTListener ←→ EventBus           │
│  Home Assistant / Node-RED pueden disparar acciones          │
└─────────────────────────────────────────────────────────────┘
```

### Pipeline de eventos

```
MQTT topic (nas-agent/command/backup)
       ↓
MQTTListener (traduce topic → event_type)
       ↓
EventBus.emit("agent.command.backup", {service: "emqx"})
       ↓
BackupPlugin._on_backup_command()
       ↓
BackupManager.backup("emqx")
```

## Instalación

```bash
sudo git clone git@github.com:ydiaz1699/nas-dotfiles.git /nas-dotfiles
cd /nas-dotfiles
sudo chown -R $(whoami):$(whoami) /nas-dotfiles
./setup
source ~/.bashrc
```

## Uso rápido

### Shell

```bash
adm           # cd $HOME
dk traefik    # cd /docker/traefik
nas           # dashboard del NAS
instal htop   # instalar paquete con log
```

### Docker CLI (svc)

```bash
svc lista              # ver servicios con estado
svc up nextcloud       # levantar servicio
svc logs grafana       # ver logs
svc health             # dashboard de salud
svc port-map           # mapa de puertos
svc backup plex        # backup de volúmenes
svc menu               # TUI interactivo
```

### Agente IA

```bash
# Consultas directas (recuerda contexto entre invocaciones)
agent "¿Qué servicios están caídos?"
agent "revisar tasmoadmin"
agent "sí reiniciar"              # Recuerda el contexto previo

# Gestión de sesión
agent --status                    # Ver sesión actual
agent --new "instalar vaultwarden"  # Nueva sesión limpia
agent --clear                     # Borrar memoria

# Catálogo
python3 -m agent.catalog._index          # Generar catalog.json
python3 -m agent.catalog._index --check  # Verificar

# Descubrimiento masivo
agent "descubrir todos los servicios y generar fichas"

# Tests
python -m pytest tests/ -v
```

### Proveedores de IA

```bash
# Gemini (default, barato)
export GOOGLE_API_KEY="tu-api-key"

# Bedrock / Claude (mejor razonamiento)
export NAS_AGENT_MODEL=bedrock

# Ollama (local, gratis)
export NAS_AGENT_MODEL=ollama
```

## Variables de entorno

### Shell framework

| Variable | Valor | Descripción |
|----------|-------|-------------|
| `NAS_DOTFILES` | `/nas-dotfiles` | Ruta fija al proyecto |

### Agente

| Variable | Default | Descripción |
|----------|---------|-------------|
| `NAS_AGENT_MODEL` | `gemini` | Provider: `gemini`, `bedrock`, `ollama` |
| `NAS_AGENT_MODEL_ID` | (auto) | Override del modelo |
| `GOOGLE_API_KEY` | — | API key de Google AI Studio |
| `NAS_AGENT_SESSION_TIMEOUT` | `30` | Minutos de inactividad para reset de sesión |
| `NAS_AGENT_DRYRUN` | `0` | `1` = solo mostrar plan sin ejecutar |
| `NAS_AGENT_READONLY` | `0` | `1` = bloquear acciones destructivas |

### MQTT / Eventos

| Variable | Default | Descripción |
|----------|---------|-------------|
| `NAS_MQTT_ENABLED` | `false` | Activar listener MQTT |
| `NAS_MQTT_HOST` | `localhost` | Host del broker |
| `NAS_MQTT_PORT` | `1883` | Puerto MQTT |
| `NAS_MQTT_TOPICS` | `nas-agent/#` | Topics a suscribir (separados por `;`) |

## Seguridad

- `validate_service_name()` — Previene path traversal e inyección
- `safe_run(shell=False)` — Ejecución sin shell, sin inyección de comandos
- `readonly_guard()` — Modo read-only bloquea acciones destructivas
- Modo `DRYRUN` — Muestra plan completo sin ejecutar nada
- Auditoría de todas las herramientas ejecutadas
- Variables sensibles SIEMPRE en `.env`, nunca inline

## Requisitos

- Bash 4.2+
- Docker + Docker Compose v2
- Python 3.9+
- `eza` (reemplazo de ls)
- Opcional: `fzf`, `paho-mqtt`

```bash
pip install -r requirements.txt    # Agente
pip install pytest                 # Tests
```

## Comparación de proveedores

| Provider | Modelo | Costo/1M tokens | Setup |
|----------|--------|:---------------:|-------|
| **Gemini** (default) | gemini-3.1-flash-lite | ~$0.08 | Solo API key |
| **Bedrock** | Claude Sonnet 4 | ~$3.00 | AWS credentials |
| **Ollama** | llama3.1 | Gratis | Ollama local |

## Licencia

MIT
