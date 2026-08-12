---
name: docker-nas
description: >
  Skill para NAS/Homelab Debian con Docker, administrado por tres capas:
  (1) Shell personalizado (aliases, navegación, prompt con eza/fzf),
  (2) CLI Docker `svc` (bash o Python), y (3) Agente IA Python (Strands SDK,
  28 tools, 3 providers, memoria persistente, plugins, daemon systemd).
  Activar cuando el usuario mencione: NAS, homelab, contenedor, servicio,
  compose, dk, adm, svc, agent, plugin, Docker, o cualquier comando del
  entorno bash personalizado del servidor.
---

# docker-nas skill

Framework completo de administración para NAS Debian con Docker.
Tres capas: **Shell** · **CLI Docker (svc)** · **Agente IA**.

---

## Servidor

| Campo | Valor |
|-------|-------|
| `$NAS_DOTFILES` | `/nas-dotfiles` (código, ruta fija) |
| `$<NAV_VAR>` | Configurable: home del usuario (ej: `$aadm` → `/home/aadm`) |
| `$dkco` | `/docker` (datos de servicios) |
| `$DOCKER_BASE` | `/docker` (alias de $dkco para scripts) |
| Shell | Bash 4.2+ con eza, fzf, batcat |
| Docker | Docker Engine + Compose v2 |
| Agente | Python 3.10+, Strands Agents SDK |

Código (`/nas-dotfiles/`) y datos (`/docker/`) NUNCA se mezclan.

---

## Reglas estrictas

Estas reglas son de libertad baja: no hay alternativa válida.

```
NUNCA:                              SIEMPRE:
  /docker/...                   →   $dkco/...
  /nas-dotfiles/...             →   $NAS_DOTFILES/...
  /home/aadm/...                →   $aadm/... (o la variable NAV_VAR configurada)
  /path/to/...                  →   deducir del contexto o preguntar
  cd /docker/<svc>              →   dk <svc>
  cd /home/aadm/<dir>           →   adm <dir>
  docker compose <cmd>          →   svc <cmd> <svc>
  docker restart/logs/exec      →   svc restart/logs/exec <svc>
  apt install                   →   instal
  pip install                   →   pipins
  cat archivo                   →   bat archivo
  docker-compose.yml            →   compose.yml
  subprocess.run(...)           →   safe_run() de _shell.py
```

- Si el prompt muestra la ruta → usar rutas relativas.
- Responder en el idioma del usuario.
- Nunca sugerir rutas genéricas como `/path/to/...` — deducir o preguntar.

---

## Nuevo servicio Docker

Entrega siempre en este orden exacto:

1. Árbol Unicode de directorios
2. `mkdir -p $dkco/<svc>/{carpetas}`
3. `compose.yml` completo (con anchors base obligatorios)
4. `dk <svc> && svc up <svc>`

Restricciones: `compose.yml` (nombre preferido) · `.env` solo secretos ·
variables triviales inline · `unless-stopped` · puertos 8100-8999 ·
nunca 22/53/80/443 · nombres `^[a-z0-9][a-z0-9._-]{0,63}$`

Para plantillas con anchors, redes compartidas y estructura de carpetas,
ver `references/svc.md`.

---

## Comandos esenciales

```bash
# Navegación
dk <svc>             # ir a /docker/<svc>
adm <dir>            # ir a $HOME/<dir>
up [n]               # subir n niveles
dkf / admf           # fuzzy finder con fzf

# Docker (siempre vía svc)
svc lista            # servicios con estado ●/○
svc up/down/restart/logs/update <svc>
svc health           # dashboard (health, uptime, restarts)
svc doctor           # chequeo 6 puntos del NAS
svc backup <svc>     # exportar volúmenes + bind mounts
svc restore <svc>    # restaurar desde backup
svc update-all       # actualizar todos los servicios
svc port-map         # mapa de puertos + conflictos
svc menu             # TUI interactivo con fzf

# Sistema
nas                  # dashboard (uptime, RAM, disco, red, Docker, temp)
disk / netinfo       # uso de disco / interfaces + puertos
logs [-f] [target]   # journald o /var/log/<target>
instal pkg           # apt + log en logs/packages.txt
pipins pkg           # pip + log en logs/pip_packages.txt

# Git
gs / ga / gc / gp    # status/add/commit/push
git-quick "msg"      # add -A + commit + push en un paso

# Agente IA
agent "query"        # consulta puntual
agent chat           # modo REPL conversacional
agent --new "q"      # nueva sesión limpia
agent --model        # cambiar modelo (menú interactivo)
agent --status       # info de sesión actual
```

Para referencia completa del shell, ver `references/entorno.md`.
Para referencia completa de svc, ver `references/svc.md`.

---

## Cuándo usar svc vs agent

| Situación | Usar |
|-----------|------|
| Acción puntual y clara (restart, logs, update, backup) | `svc` directo |
| Operación batch ya conocida (update-all, backup-all) | `svc` directo |
| Diagnóstico que requiere interpretar logs + contexto | `agent` |
| Crear servicio nuevo (buscar config, generar compose) | `agent` |
| Pregunta abierta ("¿qué está fallando?", "¿cómo optimizo X?") | `agent` |
| Operación multi-paso con dependencias | `agent` |

Regla simple: si sabes exactamente qué comando correr → `svc`.
Si necesitas razonamiento, búsqueda o decisión → `agent`.

---

## Diagnóstico

Cuando algo falla, seguir un orden de investigación estructurado:

1. `svc health` → estado global
2. `svc logs <svc>` → errores recientes
3. `svc ps <svc>` → contenedores + health status
4. `svc stats <svc>` → CPU/RAM en tiempo real
5. Si necesita razonamiento profundo → `agent "diagnosticar <svc>"`

Para recetas completas (OOM, crash loop, conflicto de puerto, servicio
lento, healthcheck, red), ver `references/diagnostic.md`.

---

## Agente IA

28 tools · 3 providers (Gemini default, Bedrock, Ollama) · memoria
persistente · plugins dinámicos · daemon systemd · prompt modular por bloques.

Para tools, memoria, plugins y configuración, ver `references/agent.md`.

---

## Seguridad

`safe_run(list, shell=False)` obligatorio · `validate_service_name()` ·
`readonly_guard()` · audit log JSON Lines · dual dry-run.

Para mecanismos completos y variables de entorno, ver `references/seguridad.md`.

---

## Extender

Para agregar comandos svc, tools del agente, plugins, o módulos shell,
ver `references/extend.md`.

---

## Prompt del servidor

```
aadm@Nas ~/docker/cli (main*) 4↑ 71% #
```

| Elemento | Significado |
|----------|-------------|
| `(main*)` | rama git + dirty flag (magenta) |
| `4↑` | contenedores corriendo (verde >0, gris =0) — cache 5s |
| `71%` | disco raíz (verde <75%, amarillo <90%, rojo ≥90%) — cache 10s |
| `$` / `#` | rojo si último comando falló |

---

## Dependencias del sistema

| Herramienta | Para qué | Instalar |
|-------------|----------|----------|
| `eza` | Reemplazo de ls (aliases) | `instal eza` |
| `fzf` | Menú, admf, dkf, svc menu | `instal fzf` |
| `batcat` | cat con syntax highlighting | `instal bat` |
| `bash-completion` | Autocompletado TAB | `instal bash-completion` |
| `lm-sensors` | Temperatura en `nas` | `instal lm-sensors` |
| `qrencode` | QR en `svc open` | `instal qrencode` |
| `apt-fast` | instal más rápido | `instal apt-fast` |
| Python 3.10+ | Agente IA | pre-instalado |

---

## Referencias adicionales

Leer cuando se necesite detalle completo de un componente:

- `references/entorno.md` — Shell framework: módulos, aliases, funciones, prompt
- `references/svc.md` — CLI svc: comandos, anchors, redes compartidas, plantillas
- `references/agent.md` — Agente IA: providers, tools, memoria, plugins, daemon
- `references/seguridad.md` — Mecanismos de seguridad, variables, convenciones
- `references/diagnostic.md` — Recetas de diagnóstico paso a paso
- `references/extend.md` — Cómo agregar comandos, tools, plugins, módulos shell
