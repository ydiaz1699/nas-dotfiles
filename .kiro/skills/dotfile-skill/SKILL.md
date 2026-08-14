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
| `$NAS_DOTFILES` | `/nas-dotfiles` (código del framework) |
| `$dkco` / `$DOCKER_BASE` | `/docker` (datos de servicios) |
| `$aadm` | `/home/aadm` (home del usuario, configurable en `user.conf`) |

Código (`$NAS_DOTFILES`) y datos (`$dkco`) nunca se mezclan.

> Los nombres `adm`/`$aadm` se configuran en `.config/user.conf` durante la instalación.
> El comando `adm` navega a `/home/aadm` y `$aadm` refiere esa ruta en scripts.

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
dk <svc>             # ir a $dkco/<svc>
adm <dir>            # ir a $aadm/<dir>
nasfk <dir>          # ir a $NAS_DOTFILES/<dir>
up [n]               # subir n niveles

# Variables para rutas
# $dkco = /docker    $aadm = /home/aadm    $NAS_DOTFILES = /nas-dotfiles

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

---

## _drafts/ — bandeja de entrada

Carpeta `$NAS_DOTFILES/_drafts/` es para subir fragmentos, ideas, notas,
diagnósticos o cualquier documento que el agente debe procesar.

```
_drafts/
├── filebrowser.md        ← fragmentos para guía de filebrowser
├── datasql/              ← notas dispersas por tema
├── idea-backup-remoto.md ← idea suelta
└── ...
```

**Convención:**
- El usuario sube lo que quiera (archivos sueltos, carpetas por tema)
- El agente los lee, unifica en el lugar correcto del repo, y los borra
- Es temporal — nada se queda ahí permanentemente
- Destinos típicos: `docs/services/<svc>-guide.md`, `docs/troubleshooting.md`

**Herramienta de unificación:**
Al procesar drafts, seguir las reglas de `$NAS_DOTFILES/docs/meta-prompt-unificar.md`:
- NO resumir — código/configs van ÍNTEGROS
- NO inventar — solo información de los fragmentos
- Detectar contradicciones → marcar como "DECISIÓN PENDIENTE"
- Orden de ejecución real: mkdir → archivos → permisos → levantar
- Guía autocontenida (no referenciar los fragmentos originales)
