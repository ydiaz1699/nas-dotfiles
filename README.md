# nas-dotfiles

Framework completo para administrar un servidor Linux/NAS con Docker. Convierte la terminal en una consola de administracion con tres capas: shell personalizado, CLI de Docker, y un agente de IA que entiende lenguaje natural.

> **Documentacion detallada:** Ver [GUIDE.md](GUIDE.md) para la explicacion completa de cada componente, comando y funcion.

---

## Componentes

| Componente | Que hace | Lenguaje |
|------------|----------|----------|
| **Shell** (`shell/`) | Aliases, prompt, navegacion, dashboard | Bash |
| **CLI** (`docker/cli/`) | Administracion de servicios Docker (`svc`) | Bash |
| **Agente** (`agent/`) | Administracion con lenguaje natural | Python |

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
instal htop                      # instalar paquete

# Docker CLI
svc lista                        # ver servicios con estado
svc up emqx                      # levantar servicio
svc logs emqx                    # ver logs
svc health                       # dashboard de salud
svc update emqx                  # actualizar imagen
svc backup emqx                  # backup de volumenes
svc doctor                       # chequeo de 6 puntos
svc menu                         # TUI interactivo (fzf)

# Agente IA
agent "que servicios estan caidos"
agent "diagnostica homeassistant"
agent "instalar vaultwarden"
agent "exportar emqx al catalogo"
agent --status
```

## Estructura

```
nas-dotfiles/
├── shell/              Personaliza Bash (aliases, prompt, navegacion)
├── docker/cli/         CLI de Docker (comando svc)
├── agent/              Agente IA (23 tools, plugins, MQTT, scheduler)
├── tests/              Tests (pytest)
├── logs/               Historial de paquetes
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

## Documentacion

| Archivo | Contenido |
|---------|-----------|
| [GUIDE.md](GUIDE.md) | Guia completa del proyecto (todo lo que puede hacer) |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Como agregar comandos, tools y plugins |
| [agent/README.md](agent/README.md) | Documentacion tecnica del agente |
| [TODO.md](TODO.md) | Roadmap y features completadas |

## Licencia

MIT
