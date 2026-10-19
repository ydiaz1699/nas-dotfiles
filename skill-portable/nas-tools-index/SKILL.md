---
name: nas-tools-index
description: >
  Índice consultable de las herramientas personalizadas del framework nas-dotfiles
  de ydiaz1699 (aliases de shell, funciones, comandos `svc`, skills y tools del
  agente). Úsala cuando el usuario pregunte "¿qué es X en mi framework?",
  "¿tengo una herramienta para Y?", "¿qué hace el alias/comando Z?" o
  "¿cómo le explico a otro LLM qué es <herramienta>?" — ej. bat, dk, svc doctor,
  instal, ntfy_send. Es AUTOCONTENIDA: responde sin necesitar el repo clonado.
  NO cubre: operar un servicio concreto paso a paso (usar la guía del servicio),
  ni el mapa de archivos por capa (usar framework-audit).
license: MIT
metadata:
  author: ydiaz1699
  version: "1.0"
  scope: [docs]
  auto_invoke:
    - "El usuario pregunta qué es o qué hace una herramienta/alias/comando del framework (ej. bat, dk, svc doctor, instal)"
    - "El usuario quiere pasar a otro LLM el conocimiento de UNA herramienta sin volcar todo el framework"
---

# Skill `nas-tools-index`

Índice granular de las herramientas del framework **nas-dotfiles**. Resuelve la
pregunta "¿qué es/qué hace <herramienta> en mi framework?" sin cargar todo el repo.

- **Fuente viva** (si tienes el repo): `docs/tools-index.md`.
- Esta skill es la copia **portable autocontenida** (lleva el conocimiento dentro,
  para Claude / Kiro Web / otro LLM sin el repo).

## Cómo responder

1. Busca el nombre exacto que preguntó el usuario en las tablas de abajo.
2. Responde con *Qué hace* + *Definición / Equivale a*.
3. Si no está en el índice, dilo claramente (no inventes): sugiere `docs/tools-index.md`
   o `docker-nas/references/entorno.md` / `svc.md` del repo.

## Frontera (qué NO cubre)

- Operar un servicio Docker concreto paso a paso → su guía `docs/services/<svc>-guide.md`.
- Mapa de archivos/componentes por capa → `docs/framework-audit.md`.
- Recetas de operación manual → `docs/cheatsheet.md`.

---

## Gotcha de aliases (importante)

Los **alias** (`bat`, `ls`, `ll`, `grep`…) solo se expanden al escribirlos
**directamente en la terminal**. NO funcionan dentro de `find -exec`, `xargs`,
scripts ni `sudo`. Ahí usa el binario real: `bat` → `batcat`. Para ver carpetas
recursivo usa la función `batr` (no es alias) o `find … -exec batcat {} +`.

Ver varios archivos de golpe (el glob `*`/`**` lo expande bash, el alias `bat`
sí aplica porque se escribe en la terminal):
`bat secrets.yaml common/*.yaml` · `shopt -s globstar; bat **/*.yaml` (recursivo).

## Datos clave del entorno

Rutas base: `$NAS_DOTFILES` = `/nas-dotfiles` · `$dkco` = `/docker` · `$aadm` = `/home/aadm`.
Reglas de oro del framework: usar `dk`/`adm`/`nasfk` (no `cd`), `svc` (no `docker compose`),
`instal` (no `apt install`), `pipins` (no `pip install`), `bat` (no `cat`), `compose.yml`
(no `docker-compose.yml`).

## Aliases de archivos / visualización

| Herramienta | Qué hace | Equivale a |
|---|---|---|
| `bat` | Ver **un** archivo con syntax highlight (solo lectura). En Debian el binario es `batcat`, no `bat`. NO es recursivo | `batcat --style=header,grid --paging=never` |
| `batr [dir] [ext]` | Ver el contenido de **TODOS los archivos** de una carpeta y subcarpetas (bat recursivo). **Poda** `.esphome`/`.pioenvs`/`.git`/`node_modules`/`__pycache__`/`.cache`/`.venv`… (no las recorre → sin pico de CPU). Excluye `secrets.yaml`/`.env`/ocultos salvo `FORCE=1`. Ej: `batr`, `batr common`, `batr . yaml` | `find <dir> \( <prune> \) -prune -o \( -type f … -exec batcat {} + \)` |
| `nano` | Editar con autoindent | `nano -i` |
| `rm` / `cp` / `mv` | Confirmación solo en terminal interactiva (no rompe scripts) | `… -iv` en TTY |
| `mkdir` | Crear con padres + verbose | `mkdir -pv` |
| `df` / `free` / `dus` | Legible / legible / tamaño del dir actual | `df -h` · `free -h` · `du -sh` |
| `grep`/`egrep`/`fgrep` | Con color | `… --color=auto` |

## Listado (requiere `eza`)

| Herramienta | Qué hace | Equivale a |
|---|---|---|
| `ls` / `ll` / `la` / `lt` / `lsd` | básico / detallado+ocultos / todos / por fecha / solo dirs | `eza` · `eza -lah` · `eza -a` · `eza -lah --sort=modified` · `eza -lD` |

## Docker rápido (sin `svc`)

| Herramienta | Qué hace |
|---|---|
| `dps` / `dpa` | `docker ps` / `docker ps -a` formateados |
| `dim` / `dnet` / `dvol` | imágenes / redes / volúmenes |
| `dprune` | `docker system prune -f` + `volume prune -f` |

## Navegación

| Herramienta | Qué hace |
|---|---|
| `dk [svc] [cmd]` | Ir a `/docker` (o a un servicio; o ejecutar ahí) |
| `adm [dir] [cmd]` | Ir a `/home/aadm` (misma lógica) |
| `nasfk [dir] [cmd]` | Ir a `/nas-dotfiles` (código del framework) |
| `dkf` / `admf` / `nasfkf` | Fuzzy finder (fzf) en cada ruta base |
| `up [n]` | Subir n niveles (default 1) |
| `..` / `...` / `....` / `~` | Subir 1/2/3 niveles / home |

## Sistema e info

| Herramienta | Qué hace |
|---|---|
| `nas` | Dashboard: uptime, load, RAM, disco, red, Docker, temp (con color por umbral) |
| `disk` | Discos montados (sin tmpfs/loop) |
| `netinfo` | Interfaces activas + puertos TCP (`ss -tulnp`) |
| `logs [-f] [syslog\|auth\|kern]` | journald (default 50 líneas) o archivo de `/var/log` |
| `ports` | Puertos en escucha (`ss -tulnp`) |
| `myip` | IP pública |
| `cls` / `h` / `reload` | clear / history / recargar shell |

## Instalación (wrappers inteligentes)

| Herramienta | Qué hace |
|---|---|
| `instal <pkg>` | `apt install` con verificación previa (skip si ya está) + log. Reemplaza `apt install` |
| `pipins <pkg>` | `pip install` con verificación + `--break-system-packages` + log. Reemplaza `pip install` |

## Git (aliases + helpers)

| Herramienta | Qué hace |
|---|---|
| `gs` / `ga` / `gc` / `gcm` / `gca` | status -sb / add / commit / commit -m / commit --amend |
| `gp` / `gpl` / `gf` | push / pull / fetch --all --prune |
| `gl` / `glg` / `gd` / `gds` | log oneline / log con grafo / diff / diff --staged |
| `gb` / `gco` / `gsw` / `gsc` | branch / checkout / switch / switch -c |
| `gst` / `gstp` | stash / stash pop |
| `git-quick "msg"` | add -A + commit -m + push en uno |
| `git-clean-branches` | eliminar ramas mergeadas locales (con confirmación) |

## CLI `svc` — globales (propios del framework)

> Además, cualquier subcomando de `docker compose` funciona como passthrough (`svc build`, `svc pull`, etc.).

| Herramienta | Qué hace |
|---|---|
| `svc lista` / `svc health` | servicios con estado ●/○ / tabla estado+uptime+restarts |
| `svc doctor` / `svc doctor-history` | chequeo 8 puntos / tendencia histórica (mem%, disk%) |
| `svc scan` | detectar lagunas (servicios, CLI, docs) |
| `svc catalog-sync [svc]` | generar docs en cascada (ficha, guía, .env.example, script DebMenux) |
| `svc code-map` | generar `docs/CODE-MAP.md` |
| `svc capabilities [q]` | descubrir capacidades desde manifests |
| `svc port-map` / `svc net` / `svc size` | puertos+conflictos / redes+IPs / disco por servicio |
| `svc watch [n]` | monitoreo continuo (refresh 5s/n) |
| `svc create <n>` / `svc clone <o> <n>` | scaffolding / duplicar servicio |
| `svc menu` | TUI con fzf |
| `svc diff <svc>` | compose en disco vs resuelta |
| `svc logs-grep <patrón>` | buscar en logs de todos los servicios |
| `svc cron` | agendar backups/updates via crontab |
| `svc lock/unlock <svc>` | proteger/desproteger (doble confirmación) |
| `svc no-boot/boot-enable <svc>` | excluir/reactivar del arranque escalonado |
| `svc boot-status` | estado del arranque escalonado |
| `svc snapshot/rollback <svc>` | guardar/restaurar compose+.env (rotación 10) |
| `svc backup-all` / `svc update-all [-y]` | backup de todos + ntfy / pull+recrear todos |

## CLI `svc` — con servicio

| Herramienta | Qué hace |
|---|---|
| `svc up/down/restart <svc>` | crear-iniciar / detener-eliminar / reiniciar |
| `svc start/stop/kill <svc>` | control básico |
| `svc update/recreate <svc>` | pull+recrear / recrear sin pull |
| `svc logs <svc> [-n N]` | logs en vivo (tail 200) |
| `svc ps/stats/top <svc>` | contenedores / CPU-RAM / procesos internos |
| `svc exec <svc> <cmd>` | ejecutar en el contenedor |
| `svc backup/restore <svc>` | volúmenes → tar.gz (rotación 5) / restaurar con fzf |
| `svc env <svc> [edit]` | ver/editar variables |
| `svc config <svc>` | configuración resuelta |
| `svc open <svc>` | abrir URL (auto-detecta puerto) + QR |
| `svc depends <svc>` | ver dependencias |

## Agente IA

| Herramienta | Qué hace |
|---|---|
| `agent "query"` | consulta puntual (Gemini default) |
| `agent chat` | REPL conversacional |
| `agent --new/--model/--status/--clear` | nueva sesión / cambiar modelo / info / borrar |

## Notificaciones

| Herramienta | Qué hace |
|---|---|
| `ntfy_send "topic" "título" "msg" "prioridad" "tags"` | notificación headless (topics: usb, docker, backups, system, alarma, nas-alerts; prioridad numérica 1-5). **Nunca** `notify-send` |

## Skills (Kiro) disponibles

`dotfile-skill` (router), `docker-boot-order`, `nas-diagnostics`, `datasql`,
`nas-runtime-secrets`, `nas-mcp-gateway`, `documentation-evolution`,
`dependency-cascade`, `skill-creator`. Cada una se activa según la tarea; el
router es `dotfile-skill`.

## Tools del agente (Python)

`project_scanner.py` (motor de `svc scan`), `compare_tools.py` (motor de `svc diff`),
`compose_tools.py` (`create_service()` + `validate_compose()`),
`discovery_tools.py` (`auto_catalog()`).

---

## Script de ayuda incluido

`scripts/tool-lookup.sh <nombre>` busca una herramienta por nombre dentro de este
SKILL.md y devuelve su fila. Útil para grep rápido. Uso:

```bash
bash scripts/tool-lookup.sh bat
```

## Nota: esto es un espejo portable

Si cambias `docs/tools-index.md` en el repo, regenera este SKILL.md, re-empaqueta
el `.zip` y vuelve a subirlo (Kiro: Settings → Skills → + Add skill · Claude: subir
como Agent Skill). No se sincroniza solo.
