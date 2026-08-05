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
| **Agente** (`agent/`) | Administracion con lenguaje natural + memoria + plugins | Python |
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
nas                              # dashboard del NAS
instal htop                      # instalar paquete APT
pipins rich typer                # instalar paquete pip

# Docker CLI (bash — default)
svc lista                        # ver servicios con estado
svc up emqx                      # levantar servicio
svc logs emqx                    # ver logs
svc health                       # dashboard de salud
svc update emqx                  # pull + recrear
svc recreate emqx                # recrear sin pull
svc backup emqx                  # backup de volumenes
svc doctor                       # chequeo de 6 puntos
svc menu                         # TUI interactivo (fzf)
svc update-all                   # actualizar todos

# Docker CLI (python — NAS_CLI=python)
NAS_CLI=python svc menu          # menu con InquirerPy + fuzzy search
NAS_CLI=python svc health        # Rich tables con colores
NAS_CLI=python svc update-all    # multi-select con checkboxes

# Agente IA
agent "que servicios estan caidos"
agent "diagnostica homeassistant"
agent "instalar vaultwarden"
agent chat                           # modo conversacional (REPL)
agent --model                        # cambiar modelo
agent --status                       # info de sesion
```

## Estructura

```
nas-dotfiles/
├── shell/              Personaliza Bash (aliases, prompt, navegacion, pipins)
├── docker/cli/         CLI Bash de Docker (comando svc)
├── svc_py/             CLI Python de Docker (Rich + InquirerPy + Typer)
├── agent/              Agente IA (28 tools, memoria, plugins, MQTT, scheduler)
│   ├── core/           Managers + MemoryManager
│   ├── tools/          Tools (@tool) incluyendo memoria
│   ├── plugins/        Plugins (docker, backup, network, memory)
│   ├── memory/         Datos persistentes (MEMORY.md, USER.md, SKILLS.md)
│   └── daemon.py       Entry point del daemon (systemd)
├── systemd/            Unit file para nas-agent.service
├── tests/              Tests (pytest, 75+ tests)
├── logs/               Historial de paquetes (APT + pip)
└── ui/                 Instalador TUI
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

## Documentacion

| Archivo | Contenido |
|---------|-----------|
| [INSTALL.md](INSTALL.md) | Guia de instalacion paso a paso |
| [GUIDE.md](GUIDE.md) | Guia completa del proyecto (todo lo que puede hacer) |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Como agregar comandos, tools y plugins |
| [agent/README.md](agent/README.md) | Documentacion tecnica del agente |
| [TODO.md](TODO.md) | Roadmap y features completadas |

## Licencia

MIT
