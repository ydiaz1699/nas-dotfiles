# nas-dotfiles

Shell framework y Docker CLI para administrar un NAS Debian/Ubuntu con Docker.

## Estructura

```
nas-dotfiles/
├── install.sh              # Instalador: crea symlinks en el sistema
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
└── scripts/                # Scripts sueltos (opcional)
```

## Instalacion

```bash
git clone git@github.com:ydiaz1699/nas-dotfiles.git ~/nas-dotfiles
cd ~/nas-dotfiles
./install.sh
```

El instalador crea symlinks:
- `~/shell` → `~/nas-dotfiles/shell`
- `/docker/cli` → `~/nas-dotfiles/docker/cli`
- `/docker/cli/svc.sh` → `/usr/local/bin/svc`

Luego anade a `~/.bashrc` (si no esta ya):
```bash
source ~/shell/init.sh
```

## Uso rapido

```bash
# Shell
adm           # cd /home/aadm
dk traefik    # cd /docker/traefik
nas           # dashboard del NAS
instal htop   # instalar paquete con log

# Docker
svc lista              # ver servicios con estado
svc up nextcloud       # levantar servicio
svc logs grafana       # ver logs
svc health             # dashboard de salud
svc port-map           # mapa de puertos
svc size               # consumo de disco
svc backup plex        # backup de volumenes
svc restore plex       # restaurar backup
svc create mi-app      # scaffolding de nuevo servicio
svc watch              # monitoreo continuo
svc menu               # TUI interactivo
```

## Requisitos

- Bash 4.2+
- Docker + Docker Compose v2
- `eza` (reemplazo de ls)
- Opcional: `fzf`, `qrencode`, `apt-fast`

## Configuracion

Variables en `shell/init.sh`:
- `SHELL_DIR` — ruta al directorio shell
- `aadm` — home del usuario principal
- `dkco` — directorio base de docker (/docker)

## Licencia

MIT
