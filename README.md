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
├── ui/
│   ├── setup.py            # TUI moderno (Rich + InquirerPy)
│   └── requirements-setup.txt  # Deps del TUI
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
│           ├── extras.sh     # port-map, size, net, env, create, watch, doctor, diff
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
./setup
source ~/.bashrc
```

El instalador (`./setup`) auto-detecta qué hay disponible:
- **Con Python + Rich + InquirerPy** → TUI moderno con paneles y menús (`ui/setup.py`)
- **Con Python sin deps** → ofrece instalarlas, si no puede → bash
- **Sin Python** → bash interactivo con colores (`install.sh`)

Ambos modos configuran automáticamente `~/.bashrc` y `/root/.bashrc`:
```bash
# nas-dotfiles shell framework
export NAS_DOTFILES="/nas-dotfiles"
source "$NAS_DOTFILES/shell/init.sh"
```

**No se crean symlinks.** El comando `svc` se define como alias dentro de `init.sh`.
Funciona para tu usuario y para root.

### Modos de instalación

| Modo | Cuándo se usa | Interfaz |
|------|---------------|----------|
| TUI moderno | Python + Rich + InquirerPy disponibles | Paneles, menús interactivos, progreso |
| Bash interactivo | Sin Python o sin deps del TUI | Colores, preguntas, feedback visual |
| Directo | Ya sabés qué querés | `./install.sh` sin preguntas (editar vars al inicio) |

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

### Modelos Gemini disponibles (julio 2026)

| Modelo | ID para `.env.agent` | RPD (free) | Recomendación |
|--------|---------------------|:----------:|---------------|
| Gemini 3.1 Flash Lite | `gemini-3.1-flash-lite` | 500 | **Recomendado** — máxima cuota gratis |
| Gemini 3.5 Flash Lite | `gemini-3.5-flash-lite` | 500 | Alta cuota, más nuevo |
| Gemini 3.5 Flash | `gemini-3.5-flash` | 20 | Más capaz, menos cuota |
| Gemini 3.1 Pro | `gemini-3.1-pro` | — | Razonamiento complejo |
| Gemini 2.5 Flash | `gemini-2.5-flash` | 20 | Anterior gen |
| Gemini 2.5 Pro | `gemini-2.5-pro` | — | Anterior gen (pro) |
| Gemini 2.0 Flash | `gemini-2.0-flash` | — | Legacy |
| Gemini 2.0 Flash Lite | `gemini-2.0-flash-lite` | — | Legacy lite |

Para cambiar modelo, editar `/nas-dotfiles/.env.agent`:
```bash
NAS_AGENT_MODEL_ID=gemini-3.1-flash-lite
```

O temporalmente:
```bash
NAS_AGENT_MODEL_ID=gemini-3.5-flash agent diagnostica nextcloud
```

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


### Comparación de proveedores

| Provider | Modelo recomendado | Costo/1M tokens | RPD (free) | Setup |
|----------|-------------------|:---------------:|:----------:|-------|
| **Gemini** (default) | gemini-3.1-flash-lite | ~$0.08 | 500 | Solo API key |
| **Gemini** (mejor) | gemini-3.5-flash | ~$0.15 | 20 | Solo API key |
| **Bedrock** | Claude Sonnet 4 | ~$3.00 | — | AWS credentials |
| **Ollama** | llama3.1 / gemma3:4b | Gratis | ∞ | Ollama local |
