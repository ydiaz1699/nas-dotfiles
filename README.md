# nas-dotfiles

Shell framework, Docker CLI y agente inteligente para administrar un NAS Debian/Ubuntu con Docker.

## Filosofía

**Todo el código vive exclusivamente dentro de `nas-dotfiles/`.** No se crean symlinks de `shell/` ni `docker/cli/` hacia rutas del sistema. El único rastro fuera del repo son 2 líneas en `~/.bashrc`.

Borrar el proyecto = `./uninstall.sh && rm -rf ~/nas-dotfiles/`

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
git clone git@github.com:ydiaz1699/nas-dotfiles.git ~/nas-dotfiles
cd ~/nas-dotfiles
./install.sh
source ~/.bashrc
```

El instalador agrega a `~/.bashrc`:
```bash
# nas-dotfiles shell framework
export NAS_DOTFILES="$HOME/nas-dotfiles"
source "$NAS_DOTFILES/shell/init.sh"
```

**No se crean symlinks.** El comando `svc` se define como alias dentro de `init.sh`.

### Para root

Si querés que root también use el framework:
```bash
# En /root/.bashrc
export NAS_DOTFILES="/home/aadm/nas-dotfiles"
source "$NAS_DOTFILES/shell/init.sh"
```

## Desinstalación

```bash
cd ~/nas-dotfiles
./uninstall.sh
rm -rf ~/nas-dotfiles
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

# Agente (requiere Strands SDK + credenciales)
cd ~/nas-dotfiles
python -m agent.nas_agent "¿Qué servicios están caídos?"
python -m agent.nas_agent "Quiero instalar Vaultwarden"
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

Proveedores soportados:
- Amazon Bedrock (default) — Claude Sonnet
- Ollama (local) — llama3.1

## Configuración

Variable principal en `~/.bashrc`:
- `NAS_DOTFILES` — ruta absoluta al repo (única fuente de verdad)

Variables derivadas (definidas en `shell/init.sh`):
- `SHELL_DIR` — `$NAS_DOTFILES/shell`
- `aadm` — home del usuario
- `dkco` — directorio base de servicios Docker (`/docker`)
- `DOCKER_BASE` — igual que `dkco`, usado por el CLI y agente

## Portabilidad

Si movés el repo a otra ruta, solo cambiás una línea en `~/.bashrc`:
```bash
export NAS_DOTFILES="/nueva/ruta/nas-dotfiles"
```

Todo lo demás se adapta automáticamente.

## Licencia

MIT
