# nas-dotfiles

Shell framework, Docker CLI y agente inteligente para administrar un NAS Debian/Ubuntu con Docker.

## Filosofia

**Todo el codigo vive exclusivamente en `/nas-dotfiles/`.** Ruta fija en la raiz del sistema, independiente del usuario. No se crean symlinks. El unico rastro fuera son 2 lineas en cada `.bashrc` (tu usuario + root).

Borrar el proyecto = `./uninstall.sh && sudo rm -rf /nas-dotfiles/`

## Estructura

```
nas-dotfiles/
├── setup                   # Entry point universal (auto-detecta modo)
├── install.sh              # Bash interactivo (fallback sin Python)
├── uninstall.sh            # Revertir instalacion completamente
├── requirements.txt        # Dependencias Python del agente
├── pyproject.toml          # Config: ruff, pytest, mypy
├── logs/
│   └── packages.txt        # Historial de paquetes APT instalados (portable)
├── ui/
│   ├── setup.py            # TUI moderno (Rich + InquirerPy)
│   └── requirements-setup.txt
├── shell/
│   ├── init.sh             # Loader principal (sourced por ~/.bashrc)
│   ├── scripts/            # Scripts standalone (portable)
│   │   ├── start-all.sh    # Levantar servicios en orden con health checks
│   │   ├── stop-all.sh     # Detener servicios y apagar (poweroff)
│   │   ├── restart-all.sh  # Detener servicios y reiniciar (reboot)
│   │   └── install_docker.sh  # Instalacion de Docker Engine en Debian
│   └── lib/
│       ├── aliases.sh      # Aliases del sistema + bat
│       ├── nav.sh          # Navegacion rapida (adm, dk, up, fzf)
│       ├── docker.sh       # Autocompletado de svc
│       ├── system.sh       # nas dashboard, disk, netinfo, logs
│       ├── instal.sh       # Wrapper inteligente de apt (loguea en logs/)
│       ├── prompt.sh       # Prompt con docker + disco + git
│       ├── git.sh          # Aliases y helpers de git
│       └── completions.sh  # Completions adicionales
├── docker/
│   └── cli/
│       ├── svc.sh          # CLI principal de servicios Docker
│       └── lib/            # Modulos del CLI
├── agent/                  # Agente Python (Strands Agents SDK)
│   ├── nas_agent.py        # Entry point (sesion persistente)
│   ├── core/               # Logica de negocio (managers)
│   │   ├── _result.py      # ToolResult dataclass
│   │   ├── service_manager.py  # start/stop/restart/update/logs
│   │   ├── compose_manager.py  # create/validate/read
│   │   └── backup_manager.py   # backup/restore/list
│   ├── tools/              # Thin wrappers (@tool -> core)
│   │   ├── docker_tools.py
│   │   ├── compose_tools.py
│   │   ├── backup_tools.py
│   │   ├── discovery_tools.py  # + export_service, bulk_discover
│   │   ├── diagnostic_tools.py
│   │   ├── system_tools.py     # + list_files, read_file_content
│   │   └── search_tools.py
│   ├── plugins/            # Sistema de plugins dinamicos
│   │   ├── base.py         # BasePlugin + PluginMeta
│   │   ├── loader.py       # Auto-discovery + load/unload
│   │   ├── docker_plugin.py    # Health check cada 5 min
│   │   ├── backup_plugin.py    # Backup diario automatico
│   │   └── network_plugin.py   # Escaneo puertos cada 15 min
│   ├── events/             # Event bus pub/sub
│   │   ├── bus.py          # EventBus (exact/wildcard/global)
│   │   └── mqtt_listener.py   # MQTT -> EventBus pipeline
│   ├── scheduler/          # Tareas periodicas (cron-like)
│   │   └── runner.py       # Threaded task runner
│   ├── cache/              # Cache KV con TTL
│   │   └── store.py        # Thread-safe + persistencia
│   ├── catalog/            # Catalogo de servicios (portable)
│   │   ├── _rules.md       # Reglas de generacion
│   │   ├── _compose_base.md   # Template base (anchors YAML)
│   │   ├── _template.md    # Template de fichas
│   │   ├── _index.py       # Generador de catalog.json
│   │   ├── catalog.json    # Indice auto-generado
│   │   └── services/       # Servicios exportados
│   │       └── emqx/
│   │           ├── ficha.md       # Metadata + docs
│   │           ├── compose.yml    # Config real exportada
│   │           └── .env.example   # .env sin secretos
│   └── config/
│       └── defaults.yml    # Configuracion centralizada
└── tests/                  # 62 tests
    ├── conftest.py
    ├── test_result.py
    ├── test_validation.py
    ├── test_compose_generation.py
    └── test_phase3.py
```

## Arquitectura del Agente

```
┌──────────────────────────────────────────────────────────────┐
│                         NAS Agent                             │
├──────────────────────────────────────────────────────────────┤
│  @tool (Strands SDK)  ->  Core Manager  ->  safe_run()       │
│       thin wrapper         logica real       ejecucion segura │
├──────────────────────────────────────────────────────────────┤
│  Plugins          Events           Scheduler       Cache      │
│  (dinamicos)      (pub/sub)        (periodico)     (TTL)     │
├──────────────────────────────────────────────────────────────┤
│  MQTT Broker (EMQX) <-> MQTTListener <-> EventBus           │
│  Home Assistant / Node-RED pueden disparar acciones           │
└──────────────────────────────────────────────────────────────┘
```

### Pipeline de eventos

```
MQTT topic (nas-agent/command/backup)
       |
MQTTListener (traduce topic -> event_type)
       |
EventBus.emit("agent.command.backup", {service: "emqx"})
       |
BackupPlugin._on_backup_command()
       |
BackupManager.backup("emqx")
```

## Funciones principales

### Sesion persistente

El agente recuerda el contexto entre invocaciones. Si le dices "revisar tasmoadmin" y luego "si reiniciar", sabe que te refieres a tasmoadmin.

```bash
agent "revisar tasmoadmin"        # Diagnostica con troubleshoot + logs
agent "si reiniciar"              # Recuerda el contexto: reinicia tasmoadmin
agent --status                    # Ver sesion actual (turnos, ultima actividad)
agent --new "instalar X"          # Forzar sesion nueva (sin contexto previo)
agent --clear                     # Borrar memoria completamente
```

Auto-reset tras 30 min de inactividad (configurable con `NAS_AGENT_SESSION_TIMEOUT`).

### Modo ejecutivo

El agente **actua**, no sugiere. Operaciones de lectura y seguras se ejecutan inmediatamente:

- `troubleshoot()`, `service_logs()`, `read_compose()` -> ejecuta sin preguntar
- `service_restart()`, `service_update()` -> ejecuta directamente (son seguros)
- `service_stop()`, `restore_service()` -> unicas que piden confirmacion

### Catalogo de servicios (portabilidad)

Cada servicio se exporta al catalogo para ser portable y versionable:

```bash
# Exportar un servicio existente
agent "exportar emqx al catalogo"

# Exportar todos de golpe
agent "exportar todos los servicios al catalogo"
```

Resultado:
```
agent/catalog/services/emqx/
├── ficha.md         # Metadata (imagen, puertos, vars, redes)
├── compose.yml      # Config REAL copiada de /docker/emqx/
├── .env.example     # .env con secretos reemplazados por __pega_aqui__
└── README.md        # Documentacion
```

Para versionar y subir a GitHub:
```bash
cd /nas-dotfiles
git add agent/catalog/services/
git commit -m "catalog: exportar servicios"
git push origin main
```

En una reinstalacion:
```bash
git clone ... /nas-dotfiles
agent "recrear emqx desde el catalogo"
# Lee compose.yml del catalogo, copia a /docker/emqx/, pide secretos
```

### Seguridad de credenciales

Las credenciales **nunca salen del NAS**:

| Capa | Que hace |
|------|----------|
| `export_service` | `.env` real -> `.env.example` con `__pega_aqui__` (para git) |
| `read_file_content` | `.env` real -> `***REDACTED***` (lo que ve el LLM) |
| `scan_compose` | Variables sensibles -> `***REDACTED***` (lo que ve el LLM) |

Patterns detectados: `password`, `secret`, `token`, `cookie`, `key`, `user`, `login`, `credential`, `auth`, `api_key`, `private`

### Dependencias del sistema

Antes de crear un servicio Docker, el agente verifica `logs/packages.txt` y te indica si falta algo:

```
"Quiero instalar Frigate" -> "Ejecuta instal nvidia-container-toolkit primero"
```

El log de paquetes (`logs/packages.txt`) viaja con el framework para saber que herramientas hay disponibles.

### Exploracion del filesystem

El agente puede explorar el NAS (rutas permitidas):

```bash
agent "que tengo en /home/aadm/scripts"
agent "mostrame el compose de homeassistant"
agent "leer /var/log/syslog ultimas 50 lineas"
```

Rutas permitidas: `/docker`, `/home/aadm`, `/nas-dotfiles`, `/tmp`, `/var/log`, `/opt`

### Sistema de plugins

Plugins se cargan dinamicamente y registran tools, eventos y tareas:

```python
class DockerPlugin(BasePlugin):
    meta = PluginMeta(name="docker")
    def setup(self):
        self.register_tool(service_restart)
        self.register_schedule(ScheduleConfig(
            name="health-check",
            handler=self.check_health,
            interval_minutes=5,
        ))
        self.register_event(EventHandler(
            event_type="docker.unhealthy",
            handler=self.on_unhealthy,
        ))
```

### MQTT -> Agente (sin chat)

Home Assistant, Node-RED o cualquier servicio puede disparar acciones:

```bash
# Trigger backup via MQTT
mosquitto_pub -t "nas-agent/command/backup" -m '{"service":"emqx"}'

# El agente ejecuta BackupManager.backup("emqx") automaticamente
```

## Instalacion

```bash
sudo git clone git@github.com:ydiaz1699/nas-dotfiles.git /nas-dotfiles
cd /nas-dotfiles
sudo chown -R $(whoami):$(whoami) /nas-dotfiles
./setup
source ~/.bashrc
```

## Uso rapido

### Shell

```bash
adm              # cd /home/aadm
dk emqx          # cd /docker/emqx
nas              # dashboard del NAS
instal htop      # instalar paquete (loguea en logs/packages.txt)
bat archivo.sh   # ver con syntax highlighting
off              # apagar NAS (detiene servicios primero)
restart          # reiniciar NAS (detiene servicios primero)
```

### Docker CLI (svc)

```bash
svc lista              # ver servicios con estado
svc up nextcloud       # levantar servicio
svc logs grafana       # ver logs
svc health             # dashboard de salud
svc update emqx        # pull + recrear
svc update-all         # actualizar todos
svc backup plex        # backup de volumenes
svc menu               # TUI interactivo (fzf)
```

### Agente IA

```bash
agent "que servicios estan caidos"
agent "revisar tasmoadmin"
agent "instalar vaultwarden"
agent "exportar todos los servicios al catalogo"
agent "que tengo en /home/aadm/scripts"
```

## Variables de entorno

### Agente

| Variable | Default | Descripcion |
|----------|---------|-------------|
| `NAS_AGENT_MODEL` | `gemini` | Provider: `gemini`, `bedrock`, `ollama` |
| `NAS_AGENT_MODEL_ID` | (auto) | Override del modelo |
| `GOOGLE_API_KEY` | — | API key de Google AI Studio |
| `NAS_AGENT_SESSION_TIMEOUT` | `30` | Minutos de inactividad para reset |
| `NAS_AGENT_DRYRUN` | `0` | `1` = solo mostrar plan sin ejecutar |
| `NAS_AGENT_READONLY` | `0` | `1` = bloquear acciones destructivas |

### MQTT / Eventos

| Variable | Default | Descripcion |
|----------|---------|-------------|
| `NAS_MQTT_ENABLED` | `false` | Activar listener MQTT |
| `NAS_MQTT_HOST` | `localhost` | Host del broker |
| `NAS_MQTT_PORT` | `1883` | Puerto MQTT |
| `NAS_MQTT_TOPICS` | `nas-agent/#` | Topics a suscribir (`;` separados) |

## Seguridad

- `validate_service_name()` — Previene path traversal e inyeccion
- `safe_run(shell=False)` — Ejecucion sin shell
- `readonly_guard()` — Modo read-only bloquea acciones destructivas
- `DRYRUN` — Muestra plan completo sin ejecutar
- Credenciales auto-sanitizadas (nunca llegan al LLM ni a git)
- Auditoria de todas las herramientas ejecutadas

## Requisitos

- Bash 4.2+
- Docker + Docker Compose v2
- Python 3.9+
- `eza` (reemplazo de ls)
- Opcional: `fzf`, `bat`, `paho-mqtt`

```bash
pip install -r requirements.txt    # Agente
pip install pytest                 # Tests (62 passing)
```

## Proveedores de IA

| Provider | Modelo | Costo/1M tokens | Setup |
|----------|--------|:---------------:|-------|
| **Gemini** (default) | gemini-3.1-flash-lite | ~$0.08 | Solo API key |
| **Bedrock** | Claude Sonnet 4 | ~$3.00 | AWS credentials |
| **Ollama** | llama3.1 | Gratis | Ollama local |

## Licencia

MIT
