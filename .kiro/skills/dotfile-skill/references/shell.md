# Shell Framework — referencia completa

## Loader

`shell/init.sh` sourced por `~/.bashrc`. Carga módulos en orden:
aliases → nav → docker → system → instal → pipins → git → completions → prompt

Anti-doble-carga: `$_SHELL_INIT_LOADED`. Reload: `reload` (alias).

## Navegación

```bash
up [n]                # sube n niveles (default 1)

# adm → home del usuario (NAV_HOME, default /home/aadm)
adm                   # cd al home configurado
adm <dir>             # cd al home/<dir>
adm <dir> <cmd>       # ejecuta cmd en contexto
adm .. [n]            # sube n niveles
admf                  # fuzzy finder (fzf)

# dk → carpeta de datos Docker (DOCKER_BASE, default /docker)
dk                    # cd a la carpeta Docker
dk <dir>              # cd a Docker/<dir>
dk <dir> <cmd>        # ejecuta cmd en contexto
dk .. [n]             # sube n niveles
dkf                   # fuzzy finder (fzf)

# nasfk → carpeta del framework (NAS_DOTFILES, default /nas-dotfiles)
nasfk                 # cd al código del framework
nasfk agent           # cd al código/agent
nasfk shell ll        # cd al código/shell + listar
nasfkf                # fuzzy finder (fzf)
```

### Variables vs Comandos

| Variable | Para qué | Nota |
|----------|----------|------|
| `$dkco` | Referir rutas de servicios (`$dkco/emqx/compose.yml`) | Siempre `/docker` |
| `$NAS_DOTFILES` | Referir rutas del código (`$NAS_DOTFILES/shell/init.sh`) | Siempre disponible |
| `$<NAV_VAR>` | Referir rutas del home (ej: `$aadm/scripts/x.sh`) | Solo si configuraste `user.conf` |

| Comando | Para qué | Funciona siempre |
|---------|----------|:----------------:|
| `dk emqx` | **Navegar** a un servicio | ✅ |
| `nasfk agent` | **Navegar** al código | ✅ |
| `adm scripts` | **Navegar** al home del usuario | ✅ |

**Regla:** Para navegar usa el comando. Para referir una ruta usa la variable.

> **Importante:** `$aadm` solo existe si configuraste `NAV_VAR=aadm` en `.config/user.conf`.
> Sin user.conf, el default es `NAV_VAR=adm` → la variable se llama `$adm` y vale `$HOME`.
> El comando `adm` funciona siempre (usa el valor configurado internamente).

## Alias — listado (usa eza)

| Alias | Acción |
|-------|--------|
| `ll` | eza -lah (detallado + colores) |
| `la` | eza -A |
| `lt` | eza -lah --sort=modified |
| `lsd` | solo directorios |

## Alias — sistema

| Alias | Acción |
|-------|--------|
| `cls` | clear |
| `h` | history |
| `ports` | ss -tulnp |
| `reload` | source ~/.bashrc |
| `myip` | IP pública |

## Alias — archivos (confirmación en TTY)

| Alias | Flags |
|-------|-------|
| `cp/mv/rm` | -iv |
| `mkdir` | -pv |
| `df/free` | -h |
| `du` | -sh |
| `nano` | -i |

## Alias — Docker rápido

| Alias | Acción |
|-------|--------|
| `dps` | docker ps formateado |
| `dpa` | docker ps -a formateado |
| `dim` | docker images formateado |
| `dnet` | docker network ls |
| `dvol` | docker volume ls |
| `dprune` | prune sistema + volúmenes |

## Alias — Git

| Alias | Acción |
|-------|--------|
| `gs` | git status |
| `ga` | git add |
| `gc` | git commit |
| `gp` | git push |
| `gl` | git log --oneline --graph |
| `gd` | git diff |

## Funciones de sistema

```bash
nas                     # dashboard: uptime/load/RAM/disco/red/Docker/temp
disk                    # discos montados (sin tmpfs/loop)
netinfo                 # interfaces + puertos TCP activos
logs                    # journald últimas 50 líneas
logs syslog|auth|kern   # tail de archivo específico
instal pkg1 pkg2        # apt-fast + skip-installed + log (logs/packages.txt)
pipins pkg1 pkg2        # pip + skip-installed + log (--break-system-packages)
```

## Prompt dinámico

```
aadm@Nas /docker/emqx (main*) 12↑ 71% $
```

| Elemento | Significado |
|----------|-------------|
| `12↑` | contenedores corriendo (verde >0, gris =0) — caché 5s |
| `71%` | disco raíz (verde <75%, amarillo <90%, rojo ≥90%) — caché 10s |
| `(main*)` | rama git + dirty |
| `$`/`#` | rojo si último comando falló |

## Dependencias opcionales

| Herramienta | Para qué |
|-------------|----------|
| `eza` | aliases de listado |
| `fzf` | admf, dkf, svc menu |
| `bash-completion` | TAB |
| `lm-sensors` | temperatura en `nas` |
| `apt-fast` | instal más rápido |
| `bat` | pager con colores |
