# nas-dotfiles

Shell framework, Docker CLI y agente inteligente para administrar un NAS Debian/Ubuntu con Docker.

## Filosofía

**Todo el código vive exclusivamente en `/nas-dotfiles/`.** Ruta fija en la raíz del sistema, independiente del usuario. No se crean symlinks. El único rastro fuera son 2 líneas en cada `.bashrc` (tu usuario + root).

Borrar el proyecto = `./uninstall.sh && sudo rm -rf /nas-dotfiles/`

## Estructura

```
nas-dotfiles/
├── install.sh              # Configurar ~/.bashrc (sin symlinks)
├── uninstall.sh            # Revertir instalación completamente
├── requirements.txt        # Dependencias Python del agente
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
│       └── lib/
│           ├── discovery.sh  # Detección de servicios
│           ├── docker.sh     # update-all
│           ├── health.sh     # Dashboard de salud
│           ├── backup.sh     # Backup/restore de volúmenes
│           ├── extras.sh     # port-map, size, net, env, create, open, watch
│           ├── menu.sh       # TUI interactivo con fzf
│           └── help.sh       # Ayuda
└── agent/                    # Agente Python (Strands Agents SDK)
    ├── nas_agent.py          # Punto de entrada del agente
    ├── catalog/              # Fichas de servicios catalogados
    └── tools/                # Tools del agente (docker, backup, etc.)
```

## Instalación

```bash
# Clonar en /nas-dotfiles (raíz del sistema, independiente del usuario)
sudo git clone git@github.com:ydiaz1699/nas-dotfiles.git /nas-dotfiles
cd /nas-dotfiles
sudo chown -R $(whoami):$(whoami) /nas-dotfiles
./install.sh
source ~/.bashrc
```

El instalador configura automáticamente tanto `~/.bashrc` como `/root/.bashrc`:
```bash
# nas-dotfiles shell framework
export NAS_DOTFILES="/nas-dotfiles"
source "$NAS_DOTFILES/shell/init.sh"
```

**No se crean symlinks.** El comando `svc` se define como alias dentro de `init.sh`.
Funciona para tu usuario y para root.

### Ruta fija

El proyecto siempre vive en `/nas-dotfiles/`. No depende de ningún home de usuario.
Si cambiás de usuario o creás uno nuevo, solo agregás las 2 líneas a su `.bashrc`.

## Desinstalación

```bash
cd /nas-dotfiles
./uninstall.sh
sudo rm -rf /nas-dotfiles
```

Esto deja el sistema completamente limpio, sin residuos.

## Uso rápido

```bash
# Shell
adm           # cd $HOME
dk traefik    # cd /docker/traefik
nas           # dashboard del NAS
instal htop   # instalar paquete con log

# Docker (svc)
svc lista              # ver servicios con estado
svc up nextcloud       # levantar servicio
svc logs grafana       # ver logs
svc health             # dashboard de salud
svc port-map           # mapa de puertos
svc size               # consumo de disco
svc backup plex        # backup de volúmenes
svc restore plex       # restaurar backup
svc create mi-app      # scaffolding de nuevo servicio
svc watch              # monitoreo continuo
svc menu               # TUI interactivo

# Agente (requiere Strands SDK + GOOGLE_API_KEY)
cd ~/nas-dotfiles
python -m agent.nas_agent "¿Qué servicios están caídos?"
python -m agent.nas_agent "Quiero instalar Vaultwarden"

# Con Bedrock (Claude) en vez de Gemini
NAS_AGENT_MODEL=bedrock python -m agent.nas_agent "..."

# Con Ollama local (gratis, sin API key)
NAS_AGENT_MODEL=ollama python -m agent.nas_agent "..."
```

## Requisitos

- Bash 4.2+
- Docker + Docker Compose v2
- `eza` (reemplazo de ls)
- Opcional: `fzf`, `qrencode`, `apt-fast`

### Para el agente Python (opcional)

```bash
pip install -r requirements.txt
```

### Configuración del agente

El agente soporta 3 proveedores de IA. Configura con variables de entorno:

```bash
# ─── Gemini (default) ────────────────────────────────────────────────
# El más barato (~$0.15/1M tokens). Solo necesita una API key.
# Obtener gratis en: https://aistudio.google.com/apikey
export GOOGLE_API_KEY="tu-api-key"

# Modelo default: gemini-2.5-flash (override opcional)
# export NAS_AGENT_MODEL_ID="gemini-2.5-pro"

# ─── Bedrock / Claude (opcional) ─────────────────────────────────────
# Mejor razonamiento y tool-use (~$3/1M tokens). Requiere cuenta AWS.
export NAS_AGENT_MODEL=bedrock
# Necesita: aws configure (con acceso a Bedrock en us-east-1)
# export AWS_REGION=us-east-1

# Extended Thinking: Claude razona internamente entre tool calls.
# Ajustar presupuesto de tokens para pensar (default: 10000)
# export NAS_AGENT_THINKING_BUDGET=16000

# ─── Ollama (opcional) ───────────────────────────────────────────────
# Gratis, local, sin internet. Requiere Ollama instalado.
export NAS_AGENT_MODEL=ollama
# Necesita: ollama serve + ollama pull llama3.1
# export OLLAMA_HOST=http://localhost:11434
# export NAS_AGENT_MODEL_ID=llama3.1
```

### Comparación de proveedores

| Provider | Modelo | Costo/1M tokens | Setup | Razonamiento |
|----------|--------|:---------------:|-------|:------------:|
| **Gemini** (default) | gemini-2.5-flash | ~$0.15 | Solo API key | Bueno |
| **Bedrock** | Claude Sonnet 4 | ~$3.00 | AWS credentials | Excelente + thinking |
| **Ollama** | llama3.1 | Gratis | Ollama local | Básico |

### Ejecutar el agente

```bash
cd /nas-dotfiles

# Modo interactivo
python -m agent.nas_agent

# Con query directa
python -m agent.nas_agent "¿Qué servicios están caídos?"
python -m agent.nas_agent "Quiero instalar Vaultwarden"
python -m agent.nas_agent "Diagnostica nextcloud"
python -m agent.nas_agent "Hazme backup de grafana"

# Cambiar provider en el momento (sin modificar bashrc)
NAS_AGENT_MODEL=bedrock python -m agent.nas_agent "tarea compleja..."
NAS_AGENT_MODEL=ollama python -m agent.nas_agent "tarea privada..."
```

## Configuración

### Variables del shell framework (en `~/.bashrc`)

| Variable | Descripción | Valor |
|----------|-------------|-------|
| `NAS_DOTFILES` | Ruta fija al proyecto (independiente del usuario) | `/nas-dotfiles` |

Variables derivadas (definidas automáticamente en `shell/init.sh`):
- `SHELL_DIR` — `$NAS_DOTFILES/shell`
- `aadm` — home del usuario
- `dkco` — directorio base de servicios Docker (`/docker`)
- `DOCKER_BASE` — igual que `dkco`, usado por el CLI y agente

### Variables del agente (opcionales)

| Variable | Default | Descripción |
|----------|---------|-------------|
| `NAS_AGENT_MODEL` | `gemini` | Provider: `gemini`, `bedrock`, `ollama` |
| `NAS_AGENT_MODEL_ID` | (auto) | Override del modelo específico |
| `GOOGLE_API_KEY` | — | API key de Google AI Studio |
| `AWS_REGION` | `us-east-1` | Región AWS para Bedrock |
| `NAS_AGENT_THINKING_BUDGET` | `10000` | Tokens para razonamiento de Claude (solo Bedrock) |
| `OLLAMA_HOST` | `http://localhost:11434` | Host de Ollama |

## Portabilidad

La ruta es fija: `/nas-dotfiles/`. Si necesitás moverla (no recomendado),
cambiá la variable en los `.bashrc` de cada usuario:
```bash
export NAS_DOTFILES="/nueva/ruta"
```

## Licencia

MIT
