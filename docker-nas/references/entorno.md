# Entorno Shell — referencia completa

## Arquitectura

```
$nas-dotfiles/shell/
├── init.sh              ← loader principal (sourced por ~/.bashrc)
└── lib/
    ├── aliases.sh       ← aliases del sistema (eza, docker, archivos)
    ├── nav.sh           ← navegación: adm, dk, up, fzf
    ├── docker.sh        ← autocompletado TAB para svc
    ├── system.sh        ← nas, disk, netinfo, logs
    ├── instal.sh        ← wrapper apt install + log
    ├── pipins.sh        ← wrapper pip install + log
    ├── git.sh           ← aliases git + helpers
    ├── completions.sh   ← completions adicionales
    └── prompt.sh        ← prompt dinámico con cache
```

**Carga:** `~/.bashrc` → `export NAS_DOTFILES="/nas-dotfiles"` → `source "$NAS_DOTFILES/shell/init.sh"`

Anti-doble-carga: `$_SHELL_INIT_LOADED` previene re-source en subshells.
Recargar: `reload` (o `_SHELL_RELOAD=1 && source ~/.bashrc`).

---

## Variables exportadas por init.sh

| Variable | Valor | Origen |
|----------|-------|--------|
| `$NAS_DOTFILES` | `/nas-dotfiles` | ~/.bashrc |
| `$<NAV_VAR>` | Ruta home (ej: `/home/aadm`) | `.config/user.conf` |
| `$dkco` | `/docker` | init.sh |
| `$DOCKER_BASE` | `/docker` | init.sh |

Configuración de navegación en `$NAS_DOTFILES/.config/user.conf`:
```bash
NAV_HOME="/home/aadm"   # destino del comando
NAV_VAR="aadm"          # nombre de la variable exportada
NAV_CMD="adm"           # nombre del comando
```

---

## Funciones definidas en init.sh

| Función | Qué hace |
|---------|----------|
| `path_add "/ruta"` | Agrega a $PATH si no existe |
| `svc <args>` | Wrapper: bash CLI o Python CLI (según `$NAS_CLI`) |
| `agent <args>` | Ejecuta `python3 -m agent.nas_agent` desde $NAS_DOTFILES |

---

## Alias — Listado (eza)

| Alias | Equivale a | Descripción |
|-------|-----------|-------------|
| `ls` | `eza` | Listado básico |
| `ll` | `eza -lah` | Detallado con ocultos |
| `la` | `eza -a` | Todos los archivos |
| `lt` | `eza -lah --sort=modified` | Por fecha, reciente abajo |
| `lsd` | `eza -lD` | Solo directorios |

## Alias — Navegación

| Alias | Acción |
|-------|--------|
| `..` | cd .. |
| `...` | cd ../.. |
| `....` | cd ../../.. |

## Alias — Sistema

| Alias | Acción |
|-------|--------|
| `cls` | clear |
| `h` | history |
| `ports` | ss -tulnp |
| `reload` | source ~/.bashrc (con _SHELL_RELOAD) |
| `myip` | IP pública via ifconfig.me |

## Alias — Docker rápido

| Alias | Acción |
|-------|--------|
| `dps` | docker ps formateado |
| `dpa` | docker ps -a formateado |
| `dim` | docker images formateado |
| `dnet` | docker network ls |
| `dvol` | docker volume ls |
| `dprune` | docker system prune + volume prune |

## Alias — Archivos (TTY-safe)

`rm`, `cp`, `mv` son funciones que aplican `-iv` SOLO en terminal interactiva.
En pipes/scripts se comportan sin confirmación (no rompen automatización).

| Alias | Flags |
|-------|-------|
| `mkdir` | -pv |
| `df` | -h |
| `dus` | du -sh (summary) |
| `free` | -h |
| `bat` | batcat --style=header,grid --paging=never |
| `nano` | -i (autoindent) |
| `grep/egrep/fgrep` | --color=auto |

---

## Navegación

### up [n]
Sube n niveles desde PWD (default 1).

### adm (o NAV_CMD configurado) → home del usuario

| Comando | Acción |
|---------|--------|
| `adm` | cd $HOME |
| `adm <dir>` | cd $HOME/<dir> |
| `adm <dir> <cmd>` | ejecuta cmd en $HOME/<dir> |
| `adm ..` / `adm .. 3` | sube niveles |
| `admf` | fuzzy finder con fzf |
| TAB | autocompleta directorios |

### dk → /docker (misma lógica)

| Comando | Acción |
|---------|--------|
| `dk` | cd /docker |
| `dk <svc>` | cd /docker/<svc> |
| `dk <svc> <cmd>` | ejecuta cmd en /docker/<svc> |
| `dkf` | fuzzy finder (fzf, profundidad 4) |

---

## Funciones de sistema

### nas
Dashboard: uptime, load, memoria (con %), discos (con color según %),
interfaces de red con IP, contenedores Docker (corriendo/detenidos),
temperatura (si lm-sensors instalado).

### disk
`df -h` filtrado (sin tmpfs/loop/overlay).

### netinfo
Interfaces activas con IP + puertos TCP en escucha.

### logs [-f] [target]
```bash
logs              # journald, últimas 50 (sin follow)
logs -f           # journald follow
logs syslog       # /var/log/syslog (últimas 50)
logs -f auth      # follow de /var/log/auth.log
logs kern         # /var/log/kern.log
```

---

## instal — apt inteligente

```bash
instal pkg1 pkg2    # instala con verificación previa
instal -y pkg       # auto-yes (ya incluido, no duplica)
```

Features:
- Detecta `apt-fast` (fallback: `apt-get`)
- Verifica si ya instalado → skip
- Verifica si existe en cache → error limpio
- Auto-actualiza cache si tiene >6 horas
- Log en `$NAS_DOTFILES/logs/packages.txt`

---

## pipins — pip inteligente

```bash
pipins rich typer     # instala paquetes Python
pipins -u rich        # upgrade
```

Features:
- Detecta pip3/pip
- Verifica si ya instalado → skip
- Soporta `--break-system-packages` (PEP 668)
- Log en `$NAS_DOTFILES/logs/pip_packages.txt`

---

## Git aliases

| Alias | Acción |
|-------|--------|
| `gs` | git status -sb |
| `ga` | git add |
| `gc` / `gcm` | commit / commit -m |
| `gp` / `gpl` | push / pull |
| `gl` / `glg` | log --oneline / log --graph |
| `gd` / `gds` | diff / diff --staged |
| `gb` / `gco` / `gsw` | branch / checkout / switch |
| `gst` / `gstp` | stash / stash pop |
| `gf` | fetch --all --prune |

Funciones:
- `git-clean-branches` — elimina ramas mergeadas locales
- `git-quick "msg"` — add -A + commit + push

---

## Prompt dinámico

```
aadm@Nas ~/docker/cli (main*) 4↑ 71% $
root@Nas /docker/cli (main*) 4↑ 71% #
```

| Elemento | Color | Significado |
|----------|-------|-------------|
| usuario | azul (rojo si root) | quien eres |
| host | cyan | hostname |
| path | bold | directorio actual |
| `(main*)` | magenta | rama git + dirty |
| `4↑` | verde (gris si 0) | contenedores corriendo (cache 5s) |
| `71%` | verde/amarillo/rojo | disco raíz (cache 10s) |
| `$`/`#` | verde/rojo | éxito/error del último comando |

---

## Autocompletado TAB

| Contexto | Completa con |
|----------|-------------|
| `svc <TAB>` | Todos los comandos svc |
| `svc up <TAB>` | Servicios en /docker/ |
| `instal <TAB>` | Paquetes apt (>2 chars) |
| `logs <TAB>` | syslog, auth, kern, archivos en /var/log |
| `dk <TAB>` | Directorios en /docker/ |
| `adm <TAB>` | Directorios en $HOME |

---

## Extender con nuevo destino de navegación

```bash
# En shell/lib/nav.sh o un archivo nuevo:
sc()  { _nav "/mi/ruta" "$@"; }
scf() { _nav_fzf "/mi/ruta" "sc>"; }
_sc_completions() { _nav_complete "/mi/ruta"; }
complete -F _sc_completions sc
```
