# Índice de Herramientas — nas-dotfiles

> **Propósito:** permitir consultar **UNA** herramienta/alias/comando/skill/tool del
> framework sin leer todo el proyecto ni cargar una skill entera. Un LLM (o tú)
> busca la fila por nombre y obtiene: **qué es, qué hace, su definición y dónde vive**.
>
> **Regla enlazar-no-duplicar:** este índice da la definición mínima + el puntero a la
> fuente dueña. Para el detalle completo, ir a la columna *Fuente*.
>
> **Granularidad:** aquí viven herramientas atómicas (un alias, una función, un
> subcomando). Para el mapa de archivos/componentes por capa → `docs/framework-audit.md`.
> Para operar paso a paso → `docs/cheatsheet.md`.

Variables base: `$NAS_DOTFILES` = `/nas-dotfiles` · `$dkco` = `/docker` · `$aadm` = `/home/aadm`

---

## Cómo consultar (para un LLM sin el repo cargado)

1. El usuario pregunta por una herramienta (ej. "¿qué es `bat` en mi framework?").
2. Busca el nombre exacto en las tablas de abajo (están agrupadas por tipo).
3. Responde con las columnas *Qué hace* + *Definición/Equivale a*.
4. Si piden más detalle del que hay aquí, apunta a la columna *Fuente* en el repo.

---

## 1. Aliases de archivos y visualización

| Herramienta | Tipo | Qué hace | Definición / Equivale a | Fuente |
|---|---|---|---|---|
| `bat` | alias | Ver archivos con **syntax highlight** (solo lectura). En Debian el binario es `batcat`, no `bat` | `batcat --style=header,grid --paging=never` | `shell/lib/aliases.sh` · doc `docker-nas/references/entorno.md` |
| `nano` | alias | Editar con autoindent | `nano -i` | `shell/lib/aliases.sh` |
| `rm` | función | Borrar; pide confirmación **solo en terminal interactiva** (no rompe scripts/pipes) | `rm -iv` en TTY | `shell/lib/aliases.sh` |
| `cp` | función | Copiar; confirmación solo en TTY | `cp -iv` en TTY | `shell/lib/aliases.sh` |
| `mv` | función | Mover; confirmación solo en TTY | `mv -iv` en TTY | `shell/lib/aliases.sh` |
| `mkdir` | alias | Crear carpetas con padres + verbose | `mkdir -pv` | `shell/lib/aliases.sh` |
| `df` | alias | Discos en formato legible | `df -h` | `shell/lib/aliases.sh` |
| `free` | alias | RAM en formato legible | `free -h` | `shell/lib/aliases.sh` |
| `dus` | alias | Tamaño total del directorio actual | `du -sh` | `shell/lib/aliases.sh` |
| `grep` / `egrep` / `fgrep` | alias | Búsqueda con color | `… --color=auto` | `shell/lib/aliases.sh` |

## 2. Aliases de listado (requieren `eza`)

| Herramienta | Tipo | Qué hace | Definición / Equivale a | Fuente |
|---|---|---|---|---|
| `ls` | alias | Listado básico con colores | `eza` | `shell/lib/aliases.sh` |
| `ll` | alias | Detallado con ocultos | `eza -lah` | `shell/lib/aliases.sh` |
| `la` | alias | Todos (sin `.`/`..`) | `eza -a` | `shell/lib/aliases.sh` |
| `lt` | alias | Por fecha, reciente abajo | `eza -lah --sort=modified` | `shell/lib/aliases.sh` |
| `lsd` | alias | Solo directorios | `eza -lD` | `shell/lib/aliases.sh` |

## 3. Docker rápido (sin `svc`)

| Herramienta | Tipo | Qué hace | Definición / Equivale a | Fuente |
|---|---|---|---|---|
| `dps` | alias | `docker ps` formateado (nombre/estado/puertos) | — | `shell/lib/aliases.sh` |
| `dpa` | alias | `docker ps -a` formateado (incluye detenidos) | — | `shell/lib/aliases.sh` |
| `dim` | alias | `docker images` formateado | — | `shell/lib/aliases.sh` |
| `dnet` | alias | `docker network ls` | — | `shell/lib/aliases.sh` |
| `dvol` | alias | `docker volume ls` | — | `shell/lib/aliases.sh` |
| `dprune` | alias | Limpiar: `docker system prune -f` + `docker volume prune -f` | — | `shell/lib/aliases.sh` |

## 4. Navegación

| Herramienta | Tipo | Qué hace | Definición / Equivale a | Fuente |
|---|---|---|---|---|
| `dk` | función | Ir a `/docker` (`dk <svc>` entra al servicio; `dk <svc> <cmd>` ejecuta ahí) | `cd /docker[/…]` | `shell/lib/nav.sh` |
| `adm` | función | Ir a `/home/aadm` (misma lógica que `dk`) | `cd /home/aadm[/…]` | `shell/lib/nav.sh` |
| `nasfk` | función | Ir a `/nas-dotfiles` (código del framework) | `cd /nas-dotfiles[/…]` | `shell/lib/nav.sh` |
| `dkf` / `admf` / `nasfkf` | función | Fuzzy finder (fzf) en cada ruta base | `fzf` (profundidad 4) | `shell/lib/nav.sh` |
| `up [n]` | función | Subir n niveles desde PWD (default 1) | `cd` + `dirname` | `shell/lib/nav.sh` |
| `..` / `...` / `....` | alias | Subir 1/2/3 niveles | `cd ..[/..]` | `shell/lib/aliases.sh` |
| `~` | alias | Ir a home | `cd ~` | `shell/lib/aliases.sh` |

## 5. Sistema e info

| Herramienta | Tipo | Qué hace | Definición / Equivale a | Fuente |
|---|---|---|---|---|
| `nas` | función | Dashboard: uptime, load, RAM, disco, red, Docker, temp (con color por umbral) | — | `shell/lib/system.sh` |
| `disk` | función | Discos montados (filtra tmpfs/loop/overlay) | `df -h` filtrado | `shell/lib/system.sh` |
| `netinfo` | función | Interfaces activas + puertos TCP en escucha | + `ss -tulnp` | `shell/lib/system.sh` |
| `logs` | función | journald últimas 50 (`logs -f` follow; `logs syslog\|auth\|kern`) | `journalctl` / `tail` | `shell/lib/system.sh` |
| `ports` | alias | Puertos en escucha | `ss -tulnp` | `shell/lib/aliases.sh` |
| `myip` | alias | IP pública | `curl ifconfig.me` | `shell/lib/aliases.sh` |
| `cls` | alias | Limpiar pantalla | `clear` | `shell/lib/aliases.sh` |
| `h` | alias | Historial | `history` | `shell/lib/aliases.sh` |
| `reload` | alias | Recargar shell sin cerrar terminal | `source ~/.bashrc` (con `_SHELL_RELOAD`) | `shell/lib/aliases.sh` |

## 6. Instalación de paquetes (wrappers inteligentes)

| Herramienta | Tipo | Qué hace | Definición / Equivale a | Fuente |
|---|---|---|---|---|
| `instal` | función | `apt install` con verificación previa (skip si ya está), auto-cache, log en `logs/packages.txt` | reemplaza `apt install` | `shell/lib/instal.sh` |
| `pipins` | función | `pip install` con verificación, `--break-system-packages` (PEP 668), log en `logs/pip_packages.txt` | reemplaza `pip install` | `shell/lib/pipins.sh` |

## 7. Git (aliases + helpers)

| Herramienta | Tipo | Qué hace | Definición / Equivale a | Fuente |
|---|---|---|---|---|
| `gs` | alias | Estado corto | `git status -sb` | `shell/lib/git.sh` |
| `ga` | alias | Add | `git add` | `shell/lib/git.sh` |
| `gc` / `gcm` / `gca` | alias | Commit / commit -m / commit --amend | `git commit[…]` | `shell/lib/git.sh` |
| `gp` / `gpl` / `gf` | alias | Push / pull / fetch --all --prune | `git …` | `shell/lib/git.sh` |
| `gl` / `glg` | alias | Log oneline -20 / con grafo | `git log …` | `shell/lib/git.sh` |
| `gd` / `gds` | alias | Diff / diff --staged | `git diff[…]` | `shell/lib/git.sh` |
| `gb` / `gco` / `gsw` / `gsc` | alias | Branch / checkout / switch / switch -c | `git …` | `shell/lib/git.sh` |
| `gst` / `gstp` | alias | Stash / stash pop | `git stash[…]` | `shell/lib/git.sh` |
| `git-quick "msg"` | función | `add -A` + `commit -m` + `push` en uno | — | `shell/lib/git.sh` |
| `git-clean-branches` | función | Eliminar ramas mergeadas locales (con confirmación) | — | `shell/lib/git.sh` |

## 8. CLI `svc` — globales (sin servicio)

> Hay un passthrough: cualquier subcomando válido de `docker compose` funciona con `svc`.
> Aquí están los **propios** del framework. Lista completa en `docker-nas/references/svc.md`.

| Herramienta | Tipo | Qué hace | Fuente |
|---|---|---|---|
| `svc lista` | svc-global | Servicios con estado ●/○ | `docker/cli/svc.sh` · `svc_py/` |
| `svc health` | svc-global | Tabla: estado, uptime, restarts | idem |
| `svc doctor` | svc-global | Chequeo 8 puntos (disco, memoria, puertos, restarts, storage, secretos, permisos .env) | idem |
| `svc doctor-history` | svc-global | Historial con tendencia (mem%, disk%, errores) | idem |
| `svc scan` | svc-global | Detectar lagunas (servicios, CLI, docs) vía git diff + snapshot | `agent/tools/project_scanner.py` |
| `svc catalog-sync [svc]` | svc-global | Generar docs en cascada (ficha, guía, .env.example, script DebMenux) | idem |
| `svc code-map` | svc-global | Generar `docs/CODE-MAP.md` (qué hace cada archivo + conexiones) | idem |
| `svc capabilities [q]` | svc-global | Descubrir capacidades reales desde manifests | idem |
| `svc port-map` | svc-global | Mapa global de puertos + conflictos | idem |
| `svc net` | svc-global | Redes Docker con contenedores e IPs | idem |
| `svc size` | svc-global | Disco por servicio | idem |
| `svc watch [n]` | svc-global | Monitoreo continuo (refresh 5s / n) | idem |
| `svc create <n>` | svc-global | Scaffolding de servicio nuevo | idem |
| `svc clone <o> <n>` | svc-global | Duplicar servicio (compose + .env sanitizado) | idem |
| `svc menu` | svc-global | TUI interactivo con fzf | idem |
| `svc diff <svc>` | svc-global | Compose en disco vs config resuelta | `agent/tools/compare_tools.py` |
| `svc logs-grep <patrón>` | svc-global | Buscar texto en logs de todos los servicios | idem |
| `svc cron` | svc-global | Agendar backups/updates via crontab (add/list/remove) | idem |
| `svc lock <svc>` / `svc unlock <svc>` | svc-global | Proteger/desproteger servicio (doble confirmación en stop/down/kill/restore) | idem |
| `svc no-boot <svc>` / `svc boot-enable <svc>` | svc-global | Excluir/reactivar servicio del arranque escalonado | `shell/scripts/boot-order.sh` |
| `svc boot-status` | svc-global | Estado del arranque escalonado (en proceso / terminado / falló) | idem |
| `svc snapshot <svc>` / `svc rollback <svc>` | svc-global | Guardar/restaurar compose+.env (liviano, rotación 10) | `svc_py/` + `bash_bridge.py` |
| `svc backup-all` | svc-global | Backup de todos + resumen + ntfy | idem |
| `svc update-all [-y]` | svc-global | Pull + recrear todos | idem |

## 9. CLI `svc` — con servicio

| Herramienta | Tipo | Qué hace | Fuente |
|---|---|---|---|
| `svc up/down/restart <svc>` | svc-svc | Crear-iniciar / detener-eliminar / reiniciar | `docker/cli/svc.sh` |
| `svc start/stop/kill <svc>` | svc-svc | Control básico del contenedor | idem |
| `svc update <svc>` / `svc recreate <svc>` | svc-svc | Pull+recrear / recrear sin pull (force-recreate) | idem |
| `svc logs <svc> [-n N]` | svc-svc | Logs en vivo (tail 200 por defecto) | idem |
| `svc ps/stats/top <svc>` | svc-svc | Contenedores / CPU-RAM / procesos internos | idem |
| `svc exec <svc> <cmd>` | svc-svc | Ejecutar comando en el contenedor | idem |
| `svc backup <svc>` / `svc restore <svc>` | svc-svc | Volúmenes → tar.gz (rotación 5) / restaurar con fzf | idem |
| `svc env <svc> [edit]` | svc-svc | Ver / editar variables del servicio | idem |
| `svc config <svc>` | svc-svc | Configuración resuelta (variables expandidas) | idem |
| `svc open <svc>` | svc-svc | Abrir URL (auto-detecta puerto) + QR + clipboard | idem |
| `svc depends <svc>` | svc-svc | Ver dependencias (depends_on) | idem |

## 10. Agente IA

| Herramienta | Tipo | Qué hace | Fuente |
|---|---|---|---|
| `agent "query"` | comando | Consulta puntual al agente (Gemini default) | `agent/nas_agent.py` |
| `agent chat` | comando | Modo REPL conversacional | idem |
| `agent --new / --model / --status / --clear` | comando | Nueva sesión / cambiar modelo / info sesión / borrar sesión | idem |

## 11. Notificaciones

| Herramienta | Tipo | Qué hace | Fuente |
|---|---|---|---|
| `ntfy_send "topic" "título" "msg" "prioridad" "tags"` | función | Enviar notificación headless (topics: usb, docker, backups, system, alarma, nas-alerts). Prioridad numérica 1-5. **Nunca** `notify-send` | `docker/cli/lib/notifications.sh` |

## 12. Skills (Kiro) — artefactos de contexto

| Herramienta | Tipo | Cuándo se usa | Fuente |
|---|---|---|---|
| `dotfile-skill` | skill | Router de entrada: cualquier tarea del NAS enruta desde aquí a la específica | `.kiro/skills/dotfile-skill/SKILL.md` |
| `docker-boot-order` | skill | Crear/eliminar/detener/reordenar servicio; `layers.conf`; restart policy; arranque escalonado | `.kiro/skills/docker-boot-order/SKILL.md` |
| `nas-diagnostics` | skill | Servicio existente falla/unhealthy/lento/crash loop; conflicto de puerto; OOM; red | `.kiro/skills/nas-diagnostics/SKILL.md` |
| `datasql` | skill | Crear base/rol PostgreSQL o configurar Redis; conectar consumidor en db_net | `.kiro/skills/datasql/SKILL.md` |
| `nas-runtime-secrets` | skill | Leer/transportar secretos sin exponerlos; sincronizar credencial `.env` | `.kiro/skills/nas-runtime-secrets/SKILL.md` |
| `nas-mcp-gateway` | skill | Decidir si activar el gateway MCP read-only del NAS | `.kiro/skills/nas-mcp-gateway/SKILL.md` |
| `documentation-evolution` | skill | Unificar drafts/fragmentos; cerrar huecos de docs/herramientas | `.kiro/skills/documentation-evolution/SKILL.md` |
| `dependency-cascade` | skill | Tras editar un archivo del framework: completar la cascada de derivados | `.kiro/skills/dependency-cascade/SKILL.md` |
| `skill-creator` | skill | Crear una skill nueva o estandarizar una existente | `.kiro/skills/skill-creator/SKILL.md` |

## 13. Tools del agente (Python)

| Herramienta | Tipo | Qué hace | Fuente |
|---|---|---|---|
| `project_scanner.py` | tool | Detecta lagunas estructurales (motor de `svc scan`) | `agent/tools/project_scanner.py` |
| `compare_tools.py` | tool | Detecta drift compose real ↔ catálogo (motor de `svc diff`) | `agent/tools/compare_tools.py` |
| `compose_tools.py` | tool | `create_service()` (servicios nuevos, impone anchors base) y `validate_compose()` | `agent/tools/compose_tools.py` |
| `discovery_tools.py` | tool | `auto_catalog()` — autogenera metadatos de ficha desde el compose | `agent/tools/discovery_tools.py` |

---

## Mantenimiento

- Este índice se mantiene **a mano** (no hay auto-sync). Al añadir un alias/función/comando
  nuevo al shell o a `svc`, añade su fila aquí.
- Fuentes dueñas (no duplicar su contenido, solo apuntar):
  - Aliases/funciones del shell → `docker-nas/references/entorno.md`
  - Comandos `svc` → `docker-nas/references/svc.md`
  - Operación paso a paso → `docs/cheatsheet.md`
  - Mapa de archivos/componentes por capa → `docs/framework-audit.md`
- Versión **portable** (para pegar a otro LLM/Claude sin el repo): `skill-portable/nas-tools-index/`.
  Es un **espejo**: si cambias este índice, regenera el `.zip` y vuelve a subirlo.
