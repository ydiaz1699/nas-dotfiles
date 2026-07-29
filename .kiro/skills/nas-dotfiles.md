# Skill: nas-dotfiles — NAS Administration Framework

## Descripción

`nas-dotfiles` es un framework completo para administrar un NAS (Network Attached Storage) con Debian/Ubuntu y Docker. Tiene 3 componentes: un shell framework, un CLI para Docker (`svc`), y un agente de IA con herramientas. Todo vive en `/nas-dotfiles/` (ruta fija en la raíz del sistema, independiente del usuario).

## Cuándo usar esta skill

- Cuando necesites entender qué hace este proyecto antes de modificarlo
- Cuando quieras agregar un comando nuevo al CLI (`svc`)
- Cuando quieras agregar una tool nueva al agente Python
- Cuando necesites diagnosticar o administrar servicios Docker del NAS
- Cuando te pasen este archivo como contexto en un chat sin historial previo

---

## Arquitectura general

```
/nas-dotfiles/          ← TODO el código (ruta fija, nunca en home de usuario)
    ├── shell/          ← Shell framework (aliases, prompt, navegación)
    ├── docker/cli/     ← CLI bash para Docker (comando `svc`)
    └── agent/          ← Agente IA con tools (Python, Strands SDK)

/docker/                ← SOLO datos de servicios Docker (no código)
    ├── nextcloud/compose.yml
    ├── plex/compose.yml
    ├── backups/
    └── ...
```

**Principio:** El código vive en `/nas-dotfiles/`. Los datos de servicios viven en `/docker/`. No se mezclan. No hay symlinks.

---

## Componente 1: Shell Framework (`/nas-dotfiles/shell/`)

Se carga via `~/.bashrc`:
```bash
export NAS_DOTFILES="/nas-dotfiles"
source "$NAS_DOTFILES/shell/init.sh"
```

### Qué provee

| Comando/Función | Qué hace |
|-----------------|----------|
| `adm` / `adm carpeta` | Navegar a $HOME o subcarpeta |
| `dk traefik` | Navegar a /docker/traefik |
| `nas` | Dashboard del NAS (uptime, memoria, disco, docker, temperatura) |
| `disk` | Uso de disco rápido |
| `netinfo` | Interfaces + puertos en uso |
| `instal paquete` | apt-fast con verificación previa + log |
| `up 3` | Subir 3 niveles de directorio |
| `svc` | Alias al CLI Docker (ver componente 2) |
| Prompt | Muestra: usuario@host directorio contenedores↑ disco% |

### Archivos

| Archivo | Contenido |
|---------|-----------|
| `shell/init.sh` | Loader principal, define NAS_DOTFILES, alias svc, carga módulos |
| `shell/lib/aliases.sh` | Aliases de sistema (ls→eza, docker, archivos) |
| `shell/lib/nav.sh` | Navegación rápida con fzf (adm, dk, up) |
| `shell/lib/docker.sh` | Autocompletado de `svc` |
| `shell/lib/system.sh` | nas(), disk(), netinfo(), logs() |
| `shell/lib/instal.sh` | Wrapper inteligente de apt-fast |
| `shell/lib/prompt.sh` | Prompt con docker + disco + exit code |
| `shell/lib/git.sh` | Aliases de git |
| `shell/lib/completions.sh` | Completions adicionales |

---

## Componente 2: CLI Docker (`/nas-dotfiles/docker/cli/`)

Comando principal: `svc` (definido como alias en init.sh).

### Comandos globales (no requieren servicio)

| Comando | Qué hace |
|---------|----------|
| `svc lista` | Lista servicios con estado (activo/detenido) |
| `svc health` | Dashboard de salud de todos los servicios |
| `svc doctor` | Chequeo de 6 puntos: disco, memoria, servicios, puertos, restarts, docker storage |
| `svc update-all` | Pull + recrear todos los servicios |
| `svc port-map` | Mapa global de puertos asignados |
| `svc size` | Consumo de disco por servicio |
| `svc net` | Mapa de redes Docker con contenedores |
| `svc watch` | Monitoreo continuo (refresh cada 5s) |
| `svc create nombre` | Scaffolding de nuevo servicio |
| `svc menu` | TUI interactivo con fzf |

### Comandos con servicio

| Comando | Qué hace |
|---------|----------|
| `svc up/down/restart/stop/start servicio` | Control de ciclo de vida |
| `svc logs servicio` | Ver logs (follow, tail 200) |
| `svc update servicio` | Pull + recrear |
| `svc backup servicio` | Exportar volúmenes a tar.gz |
| `svc diff servicio` | Comparar compose en disco vs config resuelta |
| `svc depends servicio` | Ver servicios y dependencias |
| `svc open servicio` | Abrir URL del servicio |
| `svc env servicio` | Ver/editar variables de entorno |

### Detección de servicios

Busca en `/docker/*/` archivos: `compose.yml`, `compose.yaml`, `docker-compose.yml`, `docker-compose.yaml`. Cada directorio con un compose file es un "servicio".

### Archivos del CLI

| Archivo | Contenido |
|---------|-----------|
| `docker/cli/svc.sh` | Entry point, auto-detecta CLI_DIR via BASH_SOURCE |
| `docker/cli/lib/discovery.sh` | svc_list(), svc_compose_file() |
| `docker/cli/lib/docker.sh` | svc_update_all() |
| `docker/cli/lib/health.sh` | svc_health(), svc_lista() |
| `docker/cli/lib/backup.sh` | svc_backup(), svc_restore() |
| `docker/cli/lib/extras.sh` | port-map, size, net, env, create, watch, doctor, diff |
| `docker/cli/lib/menu.sh` | TUI interactivo con fzf |
| `docker/cli/lib/help.sh` | _svc_ayuda() |

---

## Componente 3: Agente IA (`/nas-dotfiles/agent/`)

Agente Python basado en Strands Agents SDK. Administra el NAS con lenguaje natural.

### Ejecución

```bash
cd /nas-dotfiles
python -m agent.nas_agent "¿Qué servicios están caídos?"
python -m agent.nas_agent "Quiero instalar Vaultwarden"
python -m agent.nas_agent "Diagnostica nextcloud"
```

### Providers

| Provider | Variable | Modelo | Costo |
|----------|----------|--------|-------|
| Gemini (default) | `GOOGLE_API_KEY` | gemini-2.5-flash | ~$0.15/1M tokens |
| Bedrock (Claude) | `NAS_AGENT_MODEL=bedrock` | Claude Sonnet 4 | ~$3/1M + extended thinking |
| Ollama (local) | `NAS_AGENT_MODEL=ollama` | llama3.1 | Gratis |

### Tools disponibles (agent/tools/)

| Módulo | Tools |
|--------|-------|
| `discovery_tools.py` | list_services, scan_compose, auto_catalog |
| `system_tools.py` | scan_ports, disk_usage, memory_info, network_info |
| `docker_tools.py` | service_start, service_stop, service_restart, service_update, service_logs |
| `compose_tools.py` | create_service, validate_compose, read_compose |
| `backup_tools.py` | backup_service, restore_service, list_backups |
| `diagnostic_tools.py` | service_health, port_conflicts, troubleshoot |
| `search_tools.py` | search_service_info (web fallback) |

### Módulos internos

| Módulo | Función |
|--------|---------|
| `_shell.py` | safe_run (shell=False), validate_service_name, readonly_guard, is_dryrun |
| `_audit.py` | Audit log en JSON Lines, decorador audited(), get_session_summary() |

### Modos de seguridad

| Variable | Efecto |
|----------|--------|
| `NAS_AGENT_READONLY=1` | Bloquea tools destructivas (hard guard en código) |
| `NAS_AGENT_DRYRUN=1` | No ejecuta nada (soft: prompt + hard: safe_run intercepta) |
| `NAS_AGENT_AUDIT=0` | Deshabilita audit log |

### Catálogo de servicios

En `agent/catalog/`:
- `_rules.md` — Reglas de formato (puertos, restart policy, naming)
- `_template.md` — Template para fichas
- `services/*.md` — Fichas individuales con frontmatter YAML

### System Prompt

El agente incluye instrucciones de razonamiento paso a paso:
1. Entender la petición
2. Planificar qué herramientas usar
3. Verificar estado actual antes de actuar
4. Evaluar riesgo
5. Ejecutar solo después de tener toda la info
6. Confirmar resultado

---

## Seguridad

| Mecanismo | Qué protege |
|-----------|-------------|
| `validate_service_name()` | Path traversal, inyección de comandos |
| `safe_run(list, shell=False)` | Inyección shell via f-strings |
| `validated_service_path()` | Escape de DOCKER_BASE |
| `readonly_guard()` | LLM ejecutando acciones destructivas |
| Dual dry-run (prompt + código) | Ejecución accidental |
| Audit log | Trazabilidad de todas las acciones |
| Backup de .bashrc antes de sed | Pérdida de configuración |
| Sanitización de YAML en create_service | Inyección de contenido |

---

## Variables de entorno (referencia completa)

| Variable | Default | Descripción |
|----------|---------|-------------|
| `NAS_DOTFILES` | `/nas-dotfiles` | Ruta fija al proyecto |
| `DOCKER_BASE` | `/docker` | Ruta a datos de servicios Docker |
| `NAS_AGENT_MODEL` | `gemini` | Provider del agente |
| `NAS_AGENT_MODEL_ID` | (auto) | Override de modelo |
| `GOOGLE_API_KEY` | — | API key Gemini |
| `AWS_REGION` | `us-east-1` | Región para Bedrock |
| `NAS_AGENT_THINKING_BUDGET` | `10000` | Tokens de razonamiento (Bedrock) |
| `OLLAMA_HOST` | `http://localhost:11434` | Host Ollama |
| `NAS_AGENT_READONLY` | `0` | Modo solo lectura |
| `NAS_AGENT_DRYRUN` | `0` | Modo plan sin ejecutar |
| `NAS_AGENT_AUDIT` | `1` | Habilitar audit log |
| `NAS_AGENT_AUDIT_LOG` | `/docker/backups/agent_audit.log` | Ruta audit log |

---

## Convenciones

- **Ruta del proyecto**: siempre `/nas-dotfiles/` (fija, raíz del sistema)
- **Datos Docker**: siempre `/docker/` (no mezclar con código)
- **Idioma del código**: inglés
- **Idioma de la UI/mensajes**: español
- **Nombres de servicio**: `^[a-z0-9][a-z0-9._-]{0,63}$`
- **Puertos nuevos**: rango 8100-8999
- **Puertos reservados**: 22, 53, 80, 443 (nunca asignar)
- **Restart policy**: `unless-stopped` siempre
- **Secrets**: en `.env`, nunca inline en compose
- **Commits**: conventional commits (feat:, fix:, security:, docs:)

---

## Cómo agregar funcionalidad

### Nuevo comando svc (bash)
1. Función `svc_nombre()` en `docker/cli/lib/`
2. Registrar en `svc.sh` (case statement)
3. Agregar a autocompletado en `shell/lib/docker.sh`
4. Documentar en `docker/cli/lib/help.sh`

### Nueva tool del agente (Python)
1. Función `@tool` en `agent/tools/`
2. Usar `safe_run()` de `_shell.py` (nunca subprocess directo)
3. Exportar en `agent/tools/__init__.py` → `_RAW_TOOLS`
4. Si destructiva: agregar a `_DESTRUCTIVE_TOOLS` en `_shell.py`
5. Documentar en SYSTEM_PROMPT de `nas_agent.py`

---

## Requisitos del sistema

- Debian/Ubuntu (o derivado) en el NAS
- Bash 4.2+
- Docker + Docker Compose v2
- `eza` (reemplazo de ls)
- Python 3.10+ (solo para el agente)
- Opcionales: `fzf`, `qrencode`, `apt-fast`, `lm-sensors`
