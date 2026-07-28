# Guía de desarrollo — nas-dotfiles

Patrones y convenciones para agregar funcionalidad al proyecto.

---

## 1. Nuevo comando `svc` (bash)

### Paso 1 — Escribir la función

En el archivo correspondiente de `docker/cli/lib/` (o crear uno nuevo si es una categoría distinta). Convención de nombres: `svc_<nombre>`.

```bash
# en docker/cli/lib/extras.sh (o el archivo que corresponda)
svc_miComando() {
  local svc="$1"   # si necesita un servicio como argumento
  echo "Haciendo algo con $svc..."
}
```

### Paso 2 — Source (si es archivo nuevo)

Si el archivo no existe todavía, agregar el `source` en `docker/cli/svc.sh`:

```bash
source "$CLI_DIR/lib/mi_nuevo_archivo.sh"
```

### Paso 3 — Registrar en `svc.sh`

- Si **no** necesita servicio (como `doctor`, `health`): agregarlo al primer `case` (comandos globales).
- Si **sí** necesita servicio (como `backup`, `logs`): agregarlo al segundo `case`, después de que `COMPOSE_FILE` ya se resolvió.

```bash
# comando global (primer case)
mi-comando) svc_miComando "$@" ; exit 0 ;;

# comando con servicio (segundo case)
mi-comando)
  svc_miComando "$servicio" "$@"
  ;;
```

### Paso 4 — Autocompletado

Agregar a `shell/lib/docker.sh`:
- `_SVC_GLOBAL_CMDS` si es global
- `_SVC_SERVICE_CMDS` si requiere servicio

### Paso 5 — Documentar

Agregar entrada en `_svc_ayuda()` dentro de `docker/cli/lib/help.sh`.

### Cuidados

- Usar `while read ... done < <(comando)` en vez de `comando | while read` si necesitás que contadores/variables sobrevivan al loop (bash crea subshell en pipes).
- `DOCKER_BASE` es la carpeta de datos (`/docker`), no del código.
- `CLI_DIR` se auto-detecta via `BASH_SOURCE` en `svc.sh`.

---

## 2. Nueva tool para el agente Python

### Paso 1 — Escribir la función

En el archivo temático correspondiente de `agent/tools/` (o crear uno nuevo). Usar siempre `_shell.py` — nunca `subprocess` directo.

```python
from strands.tools import tool
from agent.tools._shell import (
    safe_run, find_compose, service_exists_or_error, readonly_guard,
)

@tool
def mi_tool(service_name: str) -> str:
    """Descripción clara — el LLM la usa para decidir cuándo llamarla.

    Args:
        service_name: Nombre del servicio (ej: nextcloud, plex).
    """
    # Si es destructiva:
    blocked = readonly_guard("mi_tool")
    if blocked:
        return blocked

    error = service_exists_or_error(service_name)
    if error:
        return error

    compose = find_compose(service_name)
    output = safe_run(["docker", "compose", "-f", str(compose), "algo"], timeout=60)
    return f"Resultado:\n\n{output}"
```

### Paso 2 — Exportar en `__init__.py`

Importar la tool y agregarla a `_RAW_TOOLS`. Se audita y expone automáticamente vía `ALL_TOOLS = [audited(t) for t in _RAW_TOOLS]`.

```python
from agent.tools.mi_modulo import mi_tool

_RAW_TOOLS = [
    ...,
    mi_tool,
]
```

### Paso 3 — Si es destructiva

Agregarla a `_DESTRUCTIVE_TOOLS` en `agent/tools/_shell.py`:

```python
_DESTRUCTIVE_TOOLS = frozenset({
    ...,
    "mi_tool",
})
```

Esto la bloquea en modo `NAS_AGENT_READONLY=1`.

### Paso 4 — Documentar en system prompt

Mencionar en `SYSTEM_PROMPT` dentro de `agent/nas_agent.py`, en la sección de herramientas correspondiente, para que el agente sepa cuándo usarla.

### Reglas para @tool

1. El **docstring** se convierte en la descripción (el modelo lo lee para decidir cuándo llamarla)
2. Los **type hints** definen el schema de parámetros
3. El **return** debe ser `str`
4. Errores se manejan devolviendo `"ERROR: ..."` (no lanzar excepciones)
5. Nunca usar `shell=True` ni f-strings en subprocess — siempre `safe_run(list)`
6. Validar `service_name` con `service_exists_or_error()` o `validate_service_name()`

---

## 3. Módulos de seguridad (`agent/tools/_shell.py`)

### safe_run()
- Ejecuta comandos con `shell=False` (lista de args)
- En modo dry-run retorna `[DRY-RUN] Se ejecutaría: ...` sin ejecutar
- Timeout configurable, manejo de errores integrado

### validate_service_name()
- Regex: `^[a-z0-9][a-z0-9._-]{0,63}$`
- Bloquea: `..`, `/`, `\`, nombres reservados
- Lanza `InvalidServiceName` si falla

### validated_service_path()
- Llama a `validate_service_name()` + resuelve la ruta
- Verifica que no escape de `DOCKER_BASE` (anti path-traversal)

### readonly_guard()
- Retorna error string si `NAS_AGENT_READONLY=1` y la tool es destructiva
- Retorna `None` si está permitido

### is_dryrun() / is_readonly()
- Helpers para chequear estado de los modos

---

## 4. Auditoría (`agent/tools/_audit.py`)

- `audited(func)`: decorador que wrappea tools con logging automático
- `log_tool_call()`: registra en JSON Lines (timestamp, tool, args, resultado, duración)
- `get_session_summary()`: lee las últimas N entradas del log
- `_sanitize_args()`: oculta valores sensibles (password, token, secret)

### Configuración

| Variable | Default | Descripción |
|----------|---------|-------------|
| `NAS_AGENT_AUDIT` | `1` | Habilitar/deshabilitar (`0` para off) |
| `NAS_AGENT_AUDIT_LOG` | `/docker/backups/agent_audit.log` | Ruta del archivo |

---

## 5. Variables de entorno del agente

| Variable | Default | Descripción |
|----------|---------|-------------|
| `NAS_AGENT_MODEL` | `gemini` | Provider: `gemini`, `bedrock`, `ollama` |
| `NAS_AGENT_MODEL_ID` | (auto) | Override del modelo |
| `GOOGLE_API_KEY` | — | API key para Gemini |
| `AWS_REGION` | `us-east-1` | Región para Bedrock |
| `NAS_AGENT_THINKING_BUDGET` | `10000` | Tokens de razonamiento (solo Bedrock) |
| `OLLAMA_HOST` | `http://localhost:11434` | Host de Ollama |
| `NAS_AGENT_READONLY` | `0` | Bloquear acciones destructivas |
| `NAS_AGENT_DRYRUN` | `0` | No ejecutar nada (dual: prompt + hard guard) |
| `NAS_AGENT_AUDIT` | `1` | Habilitar audit log |
| `NAS_AGENT_AUDIT_LOG` | `/docker/backups/agent_audit.log` | Ruta del audit log |

---

## 6. Estructura del proyecto

```
nas-dotfiles/
├── agent/
│   ├── nas_agent.py          # Entry point + system prompt + get_model()
│   ├── catalog/
│   │   ├── _rules.md         # Reglas de formato compose
│   │   ├── _template.md      # Template de ficha de servicio
│   │   └── services/         # Fichas .md de servicios catalogados
│   └── tools/
│       ├── __init__.py       # Exports ALL_TOOLS (con auditoría)
│       ├── _shell.py         # safe_run, validación, readonly, dryrun
│       ├── _audit.py         # Sistema de auditoría
│       ├── docker_tools.py   # start, stop, restart, update, logs
│       ├── discovery_tools.py # list_services, scan_compose, auto_catalog
│       ├── system_tools.py   # scan_ports, disk_usage, memory_info, network_info
│       ├── compose_tools.py  # create_service, validate_compose, read_compose
│       ├── backup_tools.py   # backup, restore, list_backups
│       ├── diagnostic_tools.py # health, port_conflicts, troubleshoot
│       └── search_tools.py   # search_service_info (web fallback)
├── docker/cli/
│   ├── svc.sh               # Entry point del CLI (BASH_SOURCE auto-detect)
│   └── lib/
│       ├── discovery.sh      # svc_list, svc_compose_file
│       ├── docker.sh         # svc_update_all
│       ├── health.sh         # svc_health, svc_lista
│       ├── backup.sh         # svc_backup, svc_restore
│       ├── extras.sh         # port-map, size, net, env, create, watch, doctor, diff
│       ├── menu.sh           # TUI interactivo con fzf
│       └── help.sh           # _svc_ayuda
├── shell/
│   ├── init.sh              # Loader (sourced por ~/.bashrc)
│   └── lib/
│       ├── docker.sh         # Autocompletado de svc
│       └── ...              # aliases, nav, system, etc.
├── install.sh               # Configura ~/.bashrc (sin symlinks)
├── uninstall.sh             # Revierte instalación
└── requirements.txt         # Deps Python del agente
```

---

## 7. Convenciones

- **Idioma**: Código en inglés, UI/mensajes en español
- **Nombres de servicio**: solo `[a-z0-9._-]`, máx 64 chars
- **Puertos**: rango 8100-8999 para servicios nuevos, reservados: 22/53/80/443
- **Restart policy**: siempre `unless-stopped`
- **Secrets**: nunca inline en compose, siempre en `.env` + referencia `${VAR}`
- **Commits**: convención conventional commits (`feat:`, `fix:`, `security:`, `docs:`)
- **Ramas**: push directo a `main` (repo personal), o PR para cambios grandes
