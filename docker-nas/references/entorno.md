# Entorno Shell — referencia completa

## Arquitectura

```
$NAS_DOTFILES/shell/
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
| `~` | cd ~ |

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
| `dps` | docker ps formateado (nombre/estado/puertos) |
| `dpa` | docker ps -a formateado (incluye detenidos) |
| `dim` | docker images formateado (repo/tag/size) |
| `dnet` | docker network ls |
| `dvol` | docker volume ls |
| `dprune` | docker system prune -f + docker volume prune -f |

## Alias — Archivos (TTY-safe)

`rm`, `cp`, `mv` son funciones que aplican `-iv` SOLO en terminal interactiva.
En pipes/scripts se comportan sin confirmación (no rompen automatización).

| Alias/Función | Flags | Comportamiento |
|---------------|-------|----------------|
| `rm` | -iv (solo en TTY) | Pide confirmación en terminal, normal en pipes |
| `cp` | -iv (solo en TTY) | Pide confirmación en terminal, normal en pipes |
| `mv` | -iv (solo en TTY) | Pide confirmación en terminal, normal en pipes |
| `mkdir` | -pv | Crea padres + verbose |
| `df` | -h | Formato legible |
| `dus` | du -sh | Tamaño total del directorio (summary) |
| `free` | -h | Formato legible |
| `bat` | batcat --style=header,grid --paging=never | Ver archivos con colores |
| `nano` | -i | Autoindent activado |

## Alias — Grep

| Alias | Acción |
|-------|--------|
| `grep` | grep --color=auto |
| `egrep` | egrep --color=auto |
| `fgrep` | fgrep --color=auto |

---

## Navegación

### up [n]
Sube n niveles desde PWD (default 1). Usa `dirname` internamente.
```bash
up       # sube 1 nivel
up 3     # sube 3 niveles
```

### adm (o NAV_CMD configurado) → home del usuario

| Comando | Acción |
|---------|--------|
| `adm` | cd $HOME |
| `adm <dir>` | cd $HOME/<dir> |
| `adm <dir> <cmd>` | ejecuta cmd en $HOME/<dir> |
| `adm <cmd>` | ejecuta cmd en contexto $HOME |
| `adm ..` / `adm .. 3` | sube niveles |
| `admf` | fuzzy finder con fzf (profundidad 4) |
| TAB | autocompleta solo directorios |

### dk → /docker (misma lógica que adm)

| Comando | Acción |
|---------|--------|
| `dk` | cd /docker |
| `dk <svc>` | cd /docker/<svc> |
| `dk <svc> <cmd>` | ejecuta cmd en /docker/<svc> |
| `dk <cmd>` | ejecuta cmd en contexto /docker |
| `dk ..` / `dk .. 3` | sube niveles |
| `dkf` | fuzzy finder con fzf (profundidad 4) |
| TAB | autocompleta solo directorios |

---

## Funciones de sistema

### nas
Dashboard completo del servidor:
- uptime + load average
- memoria usada/total con % y color (verde <60%, amarillo <80%, rojo ≥80%)
- discos: uso por mount con % y color (verde <75%, amarillo <90%, rojo ≥90%)
- red: interfaces activas con IP
- docker: contenedores corriendo vs detenidos
- temperatura (si `lm-sensors` está instalado)

### disk
Uso de discos montados, filtra tmpfs/loop/overlay.
```bash
disk    # df -h filtrado
```

### netinfo
Interfaces activas con IP + puertos TCP en escucha.
```bash
netinfo    # interfaces + ss -tulnp filtrado
```

### logs
```bash
logs              # journald, últimas 50 líneas (sin follow)
logs -f           # journald follow
logs syslog       # /var/log/syslog (últimas 50)
logs -f syslog    # follow de syslog
logs auth         # /var/log/auth.log
logs -f auth      # follow de auth.log
logs kern         # /var/log/kern.log
logs <nombre>     # /var/log/<nombre> o /var/log/<nombre>.log
```

---

## instal — apt inteligente

```bash
instal pkg1 pkg2    # instala con verificación previa
instal -y pkg       # auto-yes (ya incluido por defecto, no se duplica)
```

Features:
- Detecta `apt-fast` (fallback: `apt-get`)
- Verifica si ya instalado → skip con mensaje "Ya instalado: pkg"
- Verifica si existe en apt-cache → error limpio "No encontrado: pkg"
- Auto-actualiza cache si tiene >6 horas
- Log en `$NAS_DOTFILES/logs/packages.txt` (evita duplicados)
- Resumen final: instalados / ya tenías / no existe

---

## pipins — pip inteligente

```bash
pipins rich typer     # instala paquetes Python
pipins -u rich        # upgrade (--upgrade)
```

Features:
- Detecta pip3/pip
- Verifica si ya instalado → skip con versión
- Soporta `--break-system-packages` (PEP 668, Debian/Python 3.12+)
- Log en `$NAS_DOTFILES/logs/pip_packages.txt` (evita duplicados)
- Resumen final: instalados / ya tenías / errores

---

## Git aliases

| Alias | Acción |
|-------|--------|
| `gs` | git status -sb |
| `ga` | git add |
| `gc` | git commit |
| `gcm` | git commit -m |
| `gca` | git commit --amend |
| `gp` | git push |
| `gpl` | git pull |
| `gl` | git log --oneline -20 |
| `glg` | git log --oneline --graph --decorate -20 |
| `gd` | git diff |
| `gds` | git diff --staged |
| `gb` | git branch |
| `gco` | git checkout |
| `gsw` | git switch |
| `gsc` | git switch -c (crear rama) |
| `gst` | git stash |
| `gstp` | git stash pop |
| `gf` | git fetch --all --prune |

### Funciones git

```bash
git-clean-branches    # elimina ramas mergeadas locales (con confirmación)
git-quick "msg"       # add -A + commit + push en un solo comando
```

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
| `(main*)` | magenta | rama git + dirty (`*` si hay cambios) |
| `4↑` | verde (gris si 0) | contenedores corriendo (cache 5s) |
| `71%` | verde/amarillo/rojo | disco raíz (cache 10s) |
| `$`/`#` | verde/rojo | éxito/error del último comando |

### Cache del prompt
- Docker count: se refresca cada 5 segundos (`$_PROMPT_DK_TS`)
- Disk usage: se refresca cada 10 segundos (`$_PROMPT_DISK_TS`)
- Git: se evalúa en cada prompt (rápido, local)

---

## Autocompletado TAB

| Contexto | Completa con |
|----------|-------------|
| `svc <TAB>` | Todos los comandos svc (globales + servicio) |
| `svc up <TAB>` | Servicios detectados en /docker/ |
| `svc logs <TAB>` | Servicios detectados en /docker/ |
| `dk <TAB>` | Directorios en /docker/ |
| `adm <TAB>` | Directorios en $HOME |
| `instal <TAB>` | Paquetes apt (después de 2+ chars) |
| `logs <TAB>` | syslog, auth, kern, archivos en /var/log, flags (-f) |

---

## Dependencias opcionales

| Herramienta | Para qué | Instalar |
|-------------|----------|----------|
| `eza` | Aliases de listado (ls, ll, la, lt, lsd) | `instal eza` |
| `fzf` | admf, dkf, svc menu | `instal fzf` |
| `bash-completion` | Autocompletado TAB | `instal bash-completion` |
| `lm-sensors` | Temperatura en `nas` | `instal lm-sensors` |
| `apt-fast` | instal más rápido (descarga paralela) | `instal apt-fast` |
| `batcat` | Ver archivos con syntax highlight | `instal bat` |
| `qrencode` | QR code en `svc open` | `instal qrencode` |

---

## Extender con nuevo destino de navegación

```bash
# En shell/lib/nav.sh o un archivo nuevo:
sc()  { _nav "/mi/ruta" "$@"; }
scf() { _nav_fzf "/mi/ruta" "sc>"; }
_sc_completions() { _nav_complete "/mi/ruta"; }
complete -F _sc_completions sc
```

Patrón: `_nav()` maneja toda la lógica (cd, subir, ejecutar cmd, fallback).
Solo necesitas definir la función wrapper + completions.
