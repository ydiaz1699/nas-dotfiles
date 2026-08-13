---
name: dotfile-skill
description: >
  Administra un NAS/Homelab Debian con Docker mediante tres capas: shell
  personalizado (aliases, navegación, prompt), CLI Docker (comando svc), y
  agente IA Python (Strands SDK, 28 tools). Usar cuando el usuario mencione
  NAS, homelab, contenedor, servicio, compose, dk, adm, svc, agent, plugin,
  o cualquier comando del entorno bash personalizado del servidor.
---

# dotfile-skill

Framework de administración para NAS Debian con Docker.

## Servidor

| Campo | Valor |
|-------|-------|
| `$NAS_DOTFILES` | Ruta al código (default `/nas-dotfiles`, configurable) |
| `$aadm` | Home del usuario (default `/home/aadm`, configurable) |
| `$dkco` / `$DOCKER_BASE` | Datos de servicios Docker (default `/docker`) |

Código (`$NAS_DOTFILES`) y datos (`$dkco`) nunca se mezclan.

---

## Reglas estrictas

Estas reglas son de libertad baja: no hay alternativa válida.

```
NUNCA:                              SIEMPRE:
  /docker/...                   →   $dkco/...
  /nas-dotfiles/...             →   $NAS_DOTFILES/...
  /home/aadm/...                →   $aadm/...
  /path/to/...                  →   deducir del contexto o preguntar
  cd /docker/<svc>              →   dk <svc>
  cd /home/aadm/<dir>           →   adm <dir>
  cd /nas-dotfiles/<dir>        →   nasfk <dir>
  docker compose <cmd>          →   svc <cmd> <svc>
  docker restart/logs/exec      →   svc restart/logs/exec <svc>
  apt install                   →   instal
  pip install                   →   pipins
  docker-compose.yml            →   compose.yml
  subprocess.run(...)           →   safe_run() de _shell.py
```

- Si el prompt muestra la ruta → rutas relativas.
- Responder en el idioma del usuario.

---

## Nuevo servicio Docker

Entrega siempre en este orden exacto:

1. Árbol Unicode de directorios
2. `mkdir -p $dkco/<svc>/{carpetas}`
3. `compose.yml` completo
4. `dk <svc> && svc up <svc>`

Restricciones: `compose.yml` (nombre preferido) · `.env` solo secretos ·
variables triviales inline · `unless-stopped` · puertos 8100-8999 ·
nunca 22/53/80/443 · nombres `^[a-z0-9][a-z0-9._-]{0,63}$`

Para plantillas y estructura de carpetas, ver `references/svc.md`.

---

## Comandos esenciales

```bash
# Navegación
dk <svc>             # ir a /docker/<svc>
adm <dir>            # ir a $HOME/<dir>
nasfk <dir>          # ir a /nas-dotfiles/<dir>
up [n]               # subir n niveles

# Docker (siempre vía svc)
svc lista            # servicios con estado
svc up/down/restart/logs/update <svc>
svc recreate <svc>   # recrear sin pull (force-recreate)
svc health           # dashboard global
svc doctor           # chequeo 6 puntos
svc backup <svc>     # exportar volúmenes

# Sistema
nas                  # dashboard NAS
instal pkg           # apt con log
pipins pkg           # pip con log
agent "query"        # agente IA
agent chat           # REPL
```

Para referencia completa del shell, ver `references/shell.md`.
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

Cuando algo falla, seguir un orden de investigación estructurado.

Para recetas completas (OOM, crash loop, conflicto de puerto, servicio
lento, healthcheck, red), ver `references/diagnostic.md`.

---

## Agente IA

28 tools · 3 providers (Gemini default, Bedrock, Ollama) · memoria
persistente · plugins dinámicos · daemon systemd.

Para tools, memoria, plugins y configuración, ver `references/agent.md`.

---

## Seguridad

`safe_run(list, shell=False)` obligatorio · `validate_service_name()` ·
`readonly_guard()` · audit log JSON Lines · dual dry-run.

Para mecanismos completos y variables de entorno, ver `references/security.md`.

---

## Extender

Para agregar comandos svc, tools del agente, plugins, o módulos shell,
ver `references/extend.md`.
