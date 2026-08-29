# nas-dotfiles

Framework completo para administrar un servidor Linux/NAS con Docker. Convierte la terminal en una consola de administracion con tres capas: shell personalizado, CLI de Docker, y un agente de IA que entiende lenguaje natural.

> **Documentacion detallada:** Ver [GUIDE.md](GUIDE.md) para la explicacion completa de cada componente, comando y funcion.

---

## Componentes

| Componente | Que hace | Lenguaje |
|------------|----------|----------|
| **Shell** (`shell/`) | Aliases, prompt, navegacion, dashboard | Bash |
| **CLI Bash** (`docker/cli/`) | Administracion de servicios Docker (`svc`) | Bash |
| **CLI Python** (`svc_py/`) | CLI alternativa con Rich + InquirerPy (`svc`) | Python |
| **Agente** (`agent/`) | Administracion con lenguaje natural + tools + memoria + plugins | Python |
| **Gateway MCP histórico** (`agent/lobehub_mcp.py`) | Integración read-only específica de LobeHub, mantenida por compatibilidad | Python/HTTP |
| **Gateway MCP NAS** (`agent/mcp/nas_mcp_gateway/`) | Frontera MCP read-only independiente con manifest, front-door lazy, worker y helper host allowlisted | Python/stdio+HTTP |
| **Daemon** (`agent/daemon.py`) | Scheduler + plugins corriendo 24/7 (systemd) | Python |

## Instalacion

```bash
sudo git clone git@github.com:ydiaz1699/nas-dotfiles.git /nas-dotfiles
cd /nas-dotfiles
sudo chown -R $(whoami):$(whoami) /nas-dotfiles
./setup
source ~/.bashrc
```

## Uso rapido

```bash
# Shell
adm                              # cd /home/aadm
dk emqx                          # cd /docker/emqx
nasfk                            # cd /nas-dotfiles (código del framework)
nas                              # dashboard del NAS
instal htop                      # instalar paquete APT
pipins rich typer                # instalar paquete pip

# Docker CLI (bash — default)
svc lista                        # ver servicios con estado
svc up emqx                      # levantar servicio
svc logs emqx                    # ver logs
svc health                       # dashboard de salud
svc update emqx                  # pull + recrear
svc recreate emqx                # recrear sin pull (force-recreate)
svc backup emqx                  # backup de volumenes
svc doctor                       # chequeo de 6 puntos
svc menu                         # TUI interactivo (fzf)
svc update-all                   # actualizar todos
svc capabilities --service lobehub # descubrir operaciones y guards
svc lobehub verify               # verificar runtime sin mostrar secretos
svc lobehub backup-db             # dump lógico de la base de LobeHub

# Docker CLI (python — NAS_CLI=python)
NAS_CLI=python svc menu          # menu con InquirerPy + fuzzy search
NAS_CLI=python svc health        # Rich tables con colores
NAS_CLI=python svc update-all    # multi-select con checkboxes

# Agente IA
agent "que servicios estan caidos"
agent "diagnostica homeassistant"
agent "instalar vaultwarden"
agent "recuerda que emqx necesita 512MB"    # memoria persistente
agent chat                           # modo conversacional (REPL)
agent --model                        # cambiar modelo
agent --status                       # info de sesion
```

## Estructura

```
nas-dotfiles/
├── shell/              Personaliza Bash (aliases, prompt, navegacion, pipins, nasfk)
├── docker/cli/         CLI Bash de Docker (comando svc)
│   └── lib/
│       ├── notifications.sh   ntfy_send() para scripts
│       ├── catalog-sync.sh    Pipeline auto-documentación
│       └── lobehub.sh         Operaciones seguras de LobeHub
├── svc_py/             CLI Python de Docker (Rich + InquirerPy + Typer)
├── agent/              Agente IA (tools, memoria, plugins, MQTT, scheduler)
│   ├── core/           Managers + MemoryManager
│   ├── tools/          Tools (@tool), scanner, índice y autodescubrimiento
│   ├── lobehub_mcp.py  Gateway MCP histórico read-only para LobeHub
│   ├── mcp/
│   │   ├── Dockerfile  sidecar histórico del gateway LobeHub
│   │   └── nas_mcp_gateway/  Gateway MCP NAS independiente
│   │       ├── nas_mcp_gateway.py  front-door lazy (stdio/HTTP)
│   │       ├── nas_mcp_worker.py   worker + helper allowlisted
│   │       ├── nas_mcp_manifest.json  contrato de tools MCP
│   │       └── Dockerfile           sidecar HTTP interno
│   ├── capabilities/   Manifests versionados de operaciones por servicio
│   ├── architecture/   Contratos verificables del framework
│   ├── plugins/        Plugins (docker, backup, network, memory, notification)
│   ├── memory/         Datos persistentes (MEMORY.md, USER.md, SKILLS.md)
│   ├── catalog/        Catálogo de servicios (fichas + compose + .env.example)
│   └── daemon.py       Entry point del daemon (systemd)
├── docker-nas/         Skill de Kiro Web (SKILL.md + references/nas-context.md)
├── docs/               Documentación extendida
│   ├── nas-manual.md          Manual del NAS (hardware, redes, puertos)
│   ├── catalog-sync-pipeline.md  Pipeline auto-docs
│   ├── services/              Guías operativas por servicio (incluye LobeHub)
│   └── dependency-map.md      Cascada de archivos conectados
├── systemd/            Units para nas-agent y helper MCP de LobeHub
├── tests/              Tests (pytest, 75+ tests)
├── logs/               Historial de paquetes (APT + pip)
├── ui/                 Instalador TUI
└── AGENTS.md           Contexto para AI agents (formato abierto)
```

## Proveedores de IA

| Provider | Modelo | Costo/1M tokens | Setup |
|----------|--------|:---------------:|-------|
| **Gemini** (default) | gemini-3.1-flash-lite | ~$0.08 | Solo `GOOGLE_API_KEY` |
| **Bedrock** | Claude Sonnet 4 | ~$3.00 | AWS credentials |
| **Ollama** | llama3.1 | Gratis | Ollama local |

## Requisitos

- Debian/Ubuntu · Bash 4.2+ · Docker + Compose v2 · Python 3.9+ · `eza`
- Opcional: `fzf`, `bat`, `paho-mqtt`, `lm-sensors`
- Python CLI: `pipins typer rich InquirerPy pyyaml docker`

## Variables globales

El archivo `/docker/.env` contiene variables compartidas por todos los servicios:

```env
SERVER_IP=192.168.1.200
TZ=America/La_Paz
```

- `svc` las pasa automáticamente a `docker compose` (interpolación en labels, ports, etc.)
- `init.sh` las exporta al shell (`$SERVER_IP`, `$TZ` disponibles en terminal)
- Secretos van en `$dkco/<servicio>/.env` (nunca en el global)

## Documentacion

| Archivo | Contenido |
|---------|-----------|
| [INSTALL.md](INSTALL.md) | Guia de instalacion paso a paso |
| [GUIDE.md](GUIDE.md) | Guia completa del proyecto (todo lo que puede hacer) |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Como agregar comandos, tools y plugins |
| [agent/README.md](agent/README.md) | Documentacion tecnica del agente |
| [TODO.md](TODO.md) | Roadmap y features completadas |
| [AGENTS.md](AGENTS.md) | Contexto para AI coding agents (formato abierto) |
| [docs/nas-manual.md](docs/nas-manual.md) | Manual del NAS (hardware, redes, puertos, convenciones) |
| [docker-nas/references/networking.md](docker-nas/references/networking.md) | Redes host, systemd-networkd, systemd-resolved, Avahi, IPv6 y macvlan |
| [docker-nas/references/networking-install.md](docker-nas/references/networking-install.md) | Instalación futura de networkd, shim macvlan y resolved |
| [docker-nas/references/networking-migration.md](docker-nas/references/networking-migration.md) | Migración segura de backend o rango IP |
| [docker-nas/references/networking-recovery.md](docker-nas/references/networking-recovery.md) | Recuperación de SSH, DNS, macvlan, Avahi, IPv6 y Home Assistant |
| [docs/cheatsheet.md](docs/cheatsheet.md) | Cheatsheet de operaciones manuales |
| [docs/troubleshooting.md](docs/troubleshooting.md) | Diagnósticos resueltos y soluciones |
| [docs/catalog-sync-pipeline.md](docs/catalog-sync-pipeline.md) | Pipeline de auto-documentación en cascada |
| `docs/services/ntfy-guide.md` | ntfy: notificaciones push (setup, clientes, troubleshooting) |
| [`docs/services/flowise-guide.md`](docs/services/flowise-guide.md) | Flowise: integración con DataSQL y prueba inicial |
| [`docs/services/n8n-guide.md`](docs/services/n8n-guide.md) | n8n: reparación PostgreSQL, auditoría runtime y handoff a LobeHub |
| [`docs/services/lobehub-guide.md`](docs/services/lobehub-guide.md) | LobeHub: PostgreSQL, Redis, RustFS, comandos operativos y verificación |
| [`docs/lobehub-mcp-gateway.md`](docs/lobehub-mcp-gateway.md) | Integración MCP read-only histórica de LobeHub con nas-dotfiles |
| [`docs/nas-mcp-gateway.md`](docs/nas-mcp-gateway.md) | Gateway MCP independiente: manifest, front-door lazy, worker y helper host |
| [docs/architecture-consistency.md](docs/architecture-consistency.md) | Contratos e índice de conexiones del framework |
| [docs/framework-audit.md](docs/framework-audit.md) | Inventario ejecutivo actualizado del framework |
| [docs/framework-knowledge-compilation.md](docs/framework-knowledge-compilation.md) | Mapa canónico de arquitectura, ownership y gaps |
| [docs/services/homepage-guide.md](docs/services/homepage-guide.md) | Homepage: dashboard (labels vs services.yaml) |
| [docs/github-cli.md](docs/github-cli.md) | Instalación y autenticación de gh |

## Licencia

MIT

---

## 🔗 Proyectos Relacionados

| Repo | Relación | Descripción |
|------|----------|-------------|
| **[DebMenux](https://github.com/ydiaz1699/DebMenux-)** | 🤝 Complementario | Toolkit interactivo para instalar servicios Docker en cualquier Debian. Funciona **independiente**, pero si detecta `nas-dotfiles` registra automáticamente los servicios instalados en el catálogo. |

### ¿Cómo se relacionan?

```
┌─────────────────────────────────────────────────────────┐
│  nas-dotfiles (este repo)                               │
│  "Cómo está configurado MI servidor"                    │
│  • Shell personalizado (aliases, prompt, nasfk)         │
│  • CLI Docker (svc up/down/logs)                        │
│  • Agente IA (lenguaje natural)                         │
│  • Catálogo de servicios (fichas + guías)               │
│  • Funciona SOLO en tu NAS (personal)                   │
└───────────────────────┬─────────────────────────────────┘
                        │ Integración OPCIONAL
                        │ (via ~/.config/debmenux/debmenux.conf)
┌───────────────────────▼─────────────────────────────────┐
│  DebMenux (repo independiente)                          │
│  "Qué servicios existen y cómo instalarlos"             │
│  • Menú TUI interactivo (dialog)                        │
│  • Scripts de instalación por servicio                  │
│  • Post-install: USB automount, Docker, tuning          │
│  • Funciona en CUALQUIER Debian (portable)              │
└─────────────────────────────────────────────────────────┘
```

**Cada repo funciona 100% independiente.** La integración es opcional y **bidireccional**:
- `debmenu install X` → auto-registra ficha + guía + notificación en nas-dotfiles
- `svc catalog-sync` → genera scripts DebMenux faltantes desde los compose existentes
- Hook Kiro → al guardar compose.yml genera toda la documentación automáticamente

