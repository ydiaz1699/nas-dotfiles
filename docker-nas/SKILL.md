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
  REGLAS ESTRICTAS: rutas con $dkco/$NAS_DOTFILES/variable de nav, navegación
  con dk/adm, operaciones Docker con svc, paquetes con instal/pipins.
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

**Principio:** Código (`/nas-dotfiles/`) y datos (`/docker/`) NUNCA se mezclan.

---

## Reglas estrictas — APLICAR SIEMPRE

```
NUNCA uses:                         USA en su lugar:
  /docker/...                    →  $dkco/...
  /nas-dotfiles/...              →  $NAS_DOTFILES/...
  /home/<usuario>/...            →  $<NAV_VAR>/... (ej: $aadm/...)
  /path/to/...                   →  DEDUCE del contexto o pregunta
  cd /docker/<svc>               →  dk <svc>
  cd /home/<user>/<dir>          →  adm <dir>  (o el NAV_CMD configurado)
  docker compose <cmd>           →  svc <cmd> <svc>
  docker restart/logs/exec       →  svc restart/logs/exec <svc>
  apt install                    →  instal
  pip install                    →  pipins
  docker-compose.yml             →  compose.yml (nombre preferido)
  subprocess.run(...)            →  safe_run() de _shell.py (en Python)
```

- Si el prompt muestra la ruta → usar rutas relativas.
- Responder en el idioma del usuario.
- Nunca sugerir rutas genéricas como `/path/to/...` — deducir o preguntar.

---

## Nuevo servicio Docker — entrega requerida

Para cada nuevo servicio entregar SIEMPRE en este orden:

1. **Árbol** Unicode de directorios
2. **`mkdir -p $dkco/<svc>/{carpetas}`** en una línea
3. **`compose.yml`** completo
4. **`dk <svc> && svc up <svc>`** para navegar y levantar

### Restricciones de configuración

| Regla | Valor |
|-------|-------|
| Compose file | `compose.yml` (preferido) |
| .env | SOLO para secretos reales (tokens, passwords, API keys) |
| Variables triviales | inline en compose (TZ, puertos, nombres) |
| Restart policy | `unless-stopped` siempre |
| Puertos nuevos | Rango 8100-8999 |
| Puertos reservados | 22, 53, 80, 443 — NUNCA asignar |
| Nombres servicio | `^[a-z0-9][a-z0-9._-]{0,63}$` |
| Healthcheck | Agregar si expone HTTP |
| Network | Bridge dedicada si interactúa con otros |

---

## Comandos esenciales

```bash
# ── Navegación ─────────────────────────────────────────────────────
dk <svc>             # ir a $dkco/<svc>
adm <dir>            # ir a $HOME/<dir> (o NAV_CMD configurado)
up [n]               # subir n niveles
dkf / admf           # fuzzy finder con fzf

# ── Docker (siempre vía svc) ──────────────────────────────────────
svc lista            # servicios con estado ●/○
svc up/down/restart/logs/update <svc>
svc health           # dashboard (health, uptime, restarts)
svc doctor           # chequeo 6 puntos del NAS
svc backup <svc>     # exportar volúmenes + bind mounts
svc restore <svc>    # restaurar desde backup
svc update-all       # actualizar todos los servicios
svc port-map         # mapa de puertos + conflictos
svc menu             # TUI interactivo con fzf

# ── Sistema ────────────────────────────────────────────────────────
nas                  # dashboard (uptime, RAM, disco, red, Docker, temp)
disk / netinfo       # uso de disco / interfaces + puertos
logs [-f] [target]   # journald o /var/log/<target>
instal pkg           # apt + log en logs/packages.txt
pipins pkg           # pip + log en logs/pip_packages.txt

# ── Git ────────────────────────────────────────────────────────────
gs / ga / gc / gp    # status/add/commit/push
git-quick "msg"      # add -A + commit + push en un paso

# ── Agente IA ──────────────────────────────────────────────────────
agent "query"        # consulta puntual
agent chat           # modo REPL conversacional
agent --new "q"      # nueva sesión limpia
agent --model        # cambiar modelo (menú interactivo)
agent --status       # info de sesión actual
```

---

## Cuándo usar svc vs agent

| Situación | Usar |
|-----------|------|
| Acción puntual y clara (restart, logs, update, backup) | `svc` directo |
| Operación batch conocida (update-all, backup-all) | `svc` directo |
| Diagnóstico que requiere interpretar logs + contexto | `agent` |
| Crear servicio nuevo (buscar config, generar compose) | `agent` |
| Pregunta abierta ("¿qué está fallando?", "¿cómo optimizo X?") | `agent` |
| Operación multi-paso con dependencias | `agent` |

**Regla simple:** Si sabes exactamente qué comando → `svc`. Si necesitas razonamiento → `agent`.

---

## Prompt del servidor

```
aadm@Nas ~/docker/cli (main*) 4↑ 71% #
```

| Elemento | Significado |
|----------|-------------|
| `(main*)` | rama git + dirty flag (magenta) |
| `4↑` | contenedores corriendo (verde >0, gris =0) |
| `71%` | disco raíz (verde <75%, amarillo <90%, rojo ≥90%) |
| `$` / `#` | rojo si último comando falló |

---

## Diagnóstico — cadena de investigación

Cuando algo falla, seguir este orden:

1. `svc health` → estado global
2. `svc logs <svc>` → errores recientes
3. `svc ps <svc>` → contenedores + health status
4. `svc stats <svc>` → CPU/RAM en tiempo real
5. Si necesita razonamiento profundo → `agent "diagnosticar <svc>"`

Para recetas completas de diagnóstico, ver `references/svc.md`.

---

## Seguridad

- `safe_run(list, shell=False)` obligatorio en Python
- `validate_service_name()` previene path traversal
- `readonly_guard()` bloquea tools destructivas
- Audit log JSON Lines en `/docker/backups/agent_audit.log`
- Dual dry-run: `NAS_AGENT_DRYRUN=1` y `NAS_AGENT_READONLY=1`

Para mecanismos completos, ver `references/seguridad.md`.

---

## Agente IA — resumen

28 tools · 3 providers (Gemini default, Bedrock, Ollama) · memoria
persistente (MEMORY/USER/SKILLS) · plugins dinámicos · daemon systemd ·
prompt modular por bloques.

Para referencia completa, ver `references/agent.md`.

---

## Extender el sistema

### Nuevo comando svc (bash)
1. Función `svc_nombre()` en `docker/cli/lib/`
2. Case en `svc.sh`
3. Completar en `shell/lib/docker.sh`
4. Documentar en `docker/cli/lib/help.sh`

### Nueva tool del agente (Python)
1. Función `@tool` en `agent/tools/`
2. Usar `safe_run()` (nunca subprocess directo)
3. Exportar en `agent/tools/__init__.py` → `ALL_TOOLS`
4. Si destructiva: agregar a `_DESTRUCTIVE_TOOLS` en `_shell.py`

### Nuevo destino de navegación (bash)
```bash
sc()  { _nav "/ruta/destino" "$@"; }
scf() { _nav_fzf "/ruta/destino" "sc>"; }
_sc_completions() { _nav_complete "/ruta/destino"; }
complete -F _sc_completions sc
```

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
| Python 3.10+ | Agente IA | pre-instalado |

---

## Referencias adicionales

Leer cuando se necesite detalle completo de un componente:

- `references/entorno.md` — Shell framework: módulos, aliases, funciones, prompt
- `references/estructura.md` — Guía de estructura Docker con plantillas
- `references/svc.md` — CLI svc: todos los comandos con flujos típicos
- `references/agent.md` — Agente IA: providers, tools, memoria, plugins, daemon
- `references/seguridad.md` — Mecanismos de seguridad y auditoría
