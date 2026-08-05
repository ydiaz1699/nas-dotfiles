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

Importar la tool y agregarla a `ALL_TOOLS`:

```python
from agent.tools.mi_modulo import mi_tool

ALL_TOOLS = [
    ...,
    mi_tool,
]
```

> **Nota:** Las tools se pasan directamente al agente sin wrapper.
> La auditoría se integra vía plugin/hooks, no por decorador,
> porque wrappear funciones `@tool` rompe su registro en Strands SDK.

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

## 3. Nuevo plugin

Los plugins extienden el agente con tools, eventos y tareas periódicas.

### Paso 1 — Crear el archivo

En `agent/plugins/mi_plugin.py`:

```python
from agent.plugins.base import BasePlugin, PluginMeta, ScheduleConfig, EventHandler

class MiPlugin(BasePlugin):
    meta = PluginMeta(
        name="mi-plugin",
        version="1.0.0",
        description="Qué hace este plugin",
    )

    def setup(self):
        """Registrar tools, eventos y tareas."""
        # Tool que el agente puede invocar
        self.register_tool(mi_tool_function)

        # Reaccionar a eventos del bus
        self.register_event(EventHandler(
            event_type="docker.unhealthy",
            handler=self._on_unhealthy,
            description="Reacciona cuando un contenedor está unhealthy",
        ))

        # Tarea periódica
        self.register_schedule(ScheduleConfig(
            name="mi-check",
            handler=self._check_periodico,
            interval_minutes=10,
            run_on_start=False,
        ))

    def teardown(self):
        """Limpieza al descargar (opcional)."""
        pass

    def _on_unhealthy(self, event):
        service = event.data.get("service", "?")
        # ... lógica de reacción

    def _check_periodico(self):
        # ... lógica que corre cada 10 min
        pass
```

### Paso 2 — Registrar en config

Agregar el nombre del plugin en `agent/config/defaults.yml`:

```yaml
plugins:
  enabled:
    - docker
    - backup
    - network
    - mi-plugin    # ← nuevo
```

### Paso 3 — Documentar

Agregar una fila en la tabla de plugins de `agent/README.md`.

### Anatomía de un plugin

| Componente | Método | Descripción |
|------------|--------|-------------|
| Tools | `register_tool(fn)` | Funciones @tool que el LLM puede invocar |
| Eventos | `register_event(EventHandler)` | Callbacks para eventos del bus |
| Tareas | `register_schedule(ScheduleConfig)` | Jobs periódicos (cron-like) |
| Metadata | `meta = PluginMeta(...)` | Nombre, versión, dependencias |

---

## 4. Nuevo evento en el bus

### Emitir un evento

```python
from agent.events.bus import EventBus

bus = EventBus()
bus.emit(
    "docker.unhealthy",
    data={"service": "emqx", "reason": "OOM"},
    source="docker_plugin",
)
```

### Suscribirse a eventos

```python
# Exacto
bus.on("docker.unhealthy", my_handler)

# Wildcard (cualquier docker.*)
bus.on("docker.*", my_wildcard_handler)

# Global (todos los eventos)
bus.on("*", audit_handler)
```

### Convenciones de nombres de eventos

| Prefijo | Origen | Ejemplo |
|---------|--------|---------|
| `agent.command.*` | MQTT (nas-agent/command/X) | `agent.command.backup` |
| `docker.*` | Docker plugin | `docker.unhealthy`, `docker.restart` |
| `schedule.*` | Scheduler | `schedule.run`, `schedule.error` |
| `mqtt.*` | MQTT listener | `mqtt.connected`, `mqtt.message` |
| `ha.*` | Home Assistant via MQTT | `ha.status` |
| `system.*` | System checks | `system.disk_warning` |

---

## 5. MQTT → Agente (eventos externos)

### Agregar un nuevo topic MQTT

1. Agregar el topic en `agent/config/defaults.yml`:
```yaml
mqtt:
  topics:
    - "nas-agent/#"
    - "homeassistant/+/status"
    - "mi-servicio/events/#"     # ← nuevo
```

2. Si necesitas mapeo custom de topic → event_type, agregar un mapper:
```python
def mi_mapper(topic: str, payload: dict) -> str | None:
    if topic.startswith("mi-servicio/"):
        return f"mi-servicio.{topic.split('/')[-1]}"
    return None

mqtt_listener.add_mapper(mi_mapper)
```

### Mapper por defecto

| Topic MQTT | Event type |
|------------|-----------|
| `nas-agent/command/X` | `agent.command.X` |
| `homeassistant/+/status` | `ha.status` |
| `docker/events/X` | `docker.X` |
| Cualquier otro | `mqtt.message` |

---

## 6. Módulos de seguridad (`agent/tools/_shell.py`)

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

## 7. Auditoría (`agent/tools/_audit.py`)

- `log_tool_call()`: registra en JSON Lines (timestamp, tool, args, resultado, duración)
- `get_session_summary()`: lee las últimas N entradas del log
- `_sanitize_args()`: oculta valores sensibles (password, token, secret)

### Configuración

| Variable | Default | Descripción |
|----------|---------|-------------|
| `NAS_AGENT_AUDIT` | `1` | Habilitar/deshabilitar (`0` para off) |
| `NAS_AGENT_AUDIT_LOG` | `/docker/backups/agent_audit.log` | Ruta del archivo |

---

## 8. Variables de entorno del agente

| Variable | Default | Descripción |
|----------|---------|-------------|
| `NAS_AGENT_MODEL` | `gemini` | Provider: `gemini`, `bedrock`, `ollama` |
| `NAS_AGENT_MODEL_ID` | `gemini-3.1-flash-lite` | Override del modelo |
| `GOOGLE_API_KEY` | — | API key para Gemini |
| `AWS_REGION` | `us-east-1` | Región para Bedrock |
| `NAS_AGENT_THINKING_BUDGET` | `10000` | Tokens de razonamiento (solo Bedrock) |
| `OLLAMA_HOST` | `http://localhost:11434` | Host de Ollama |
| `NAS_AGENT_READONLY` | `0` | Bloquear acciones destructivas |
| `NAS_AGENT_DRYRUN` | `0` | No ejecutar nada (dual: prompt + hard guard) |
| `NAS_AGENT_AUDIT` | `1` | Habilitar audit log |
| `NAS_AGENT_AUDIT_LOG` | `/docker/backups/agent_audit.log` | Ruta del audit log |
| `NAS_AGENT_SESSION_TIMEOUT` | `30` | Minutos antes de auto-reset de sesión |
| `NAS_AGENT_MEMORY_DIR` | `agent/memory` | Directorio de memoria persistente |
| `NAS_MQTT_HOST` | `localhost` | Host broker MQTT |
| `NAS_MQTT_PORT` | `1883` | Puerto broker MQTT |
| `NAS_MQTT_USER` | — | Usuario MQTT (opcional) |
| `NAS_MQTT_PASS` | — | Password MQTT (opcional) |
| `NAS_MQTT_TOPICS` | `nas-agent/#` | Topics separados por `;` |
| `NAS_CLI` | `bash` | CLI dual: `bash` o `python` |
| `NAS_AGENT_LOG_LEVEL` | `INFO` | Log level del daemon (DEBUG/INFO/WARNING/ERROR) |

---

## 9. Estructura del proyecto

```
nas-dotfiles/
├── agent/
│   ├── nas_agent.py          # Entry point + system prompt + sesión + Rich UI + REPL
│   ├── daemon.py             # Daemon systemd (scheduler + plugins 24/7)
│   ├── config/
│   │   └── defaults.yml      # Configuración centralizada
│   ├── core/                 # Lógica de negocio (managers)
│   │   ├── _result.py
│   │   ├── memory.py         # MemoryManager (Learning Loop)
│   │   ├── service_manager.py
│   │   ├── compose_manager.py
│   │   └── backup_manager.py
│   ├── tools/                # Thin wrappers (@tool → core)
│   │   ├── __init__.py       # Exporta ALL_TOOLS (28 tools)
│   │   ├── _shell.py         # safe_run, validación, readonly, dryrun
│   │   ├── _audit.py         # Sistema de auditoría
│   │   ├── docker_tools.py
│   │   ├── discovery_tools.py
│   │   ├── system_tools.py
│   │   ├── compose_tools.py
│   │   ├── backup_tools.py
│   │   ├── diagnostic_tools.py
│   │   ├── search_tools.py
│   │   └── memory_tools.py   # remember, recall, learn_skill, update_user_model, memory_stats
│   ├── plugins/              # Sistema de plugins dinámicos
│   │   ├── base.py           # BasePlugin + PluginMeta + dataclasses
│   │   ├── loader.py         # Auto-discovery + load/unload
│   │   ├── docker_plugin.py
│   │   ├── backup_plugin.py
│   │   ├── network_plugin.py
│   │   └── memory_plugin.py  # Learning Loop (capas B + C)
│   ├── memory/               # Datos persistentes de memoria
│   │   ├── MEMORY.md         # Hechos, lecciones, patrones
│   │   ├── USER.md           # Perfil del usuario
│   │   ├── SKILLS.md         # Procedimientos reutilizables
│   │   └── sessions/         # Historial resumido
│   ├── events/               # Event bus pub/sub
│   │   ├── bus.py
│   │   └── mqtt_listener.py
│   ├── scheduler/
│   │   └── runner.py
│   ├── cache/
│   │   └── store.py
│   └── catalog/
│       └── services/
├── svc_py/                   # Python CLI (alternativa a svc.sh)
│   ├── __main__.py           # Entry point: python -m svc_py
│   ├── app.py                # Typer app (30+ comandos)
│   ├── config.py             # DOCKER_BASE, BACKUP_DIR, etc.
│   ├── ui.py                 # Rich helpers
│   ├── commands/
│   │   ├── health.py         # health, doctor, watch (Rich Live)
│   │   ├── docker.py         # update-all (InquirerPy checkboxes)
│   │   ├── backup.py         # backup (progress), restore (selector)
│   │   ├── info.py           # port-map, size, net, depends, env, open
│   │   ├── compose.py        # create (wizard), diff (syntax)
│   │   └── menu.py           # Menú interactivo + multi-select
│   └── core/
│       ├── discovery.py      # svc_list, svc_compose_file
│       └── docker.py         # Docker SDK + subprocess fallback
├── docker/cli/
│   ├── svc.sh               # Entry point del CLI bash
│   └── lib/
│       ├── discovery.sh
│       ├── docker.sh
│       ├── health.sh
│       ├── backup.sh
│       ├── extras.sh
│       ├── menu.sh
│       └── help.sh
├── shell/
│   ├── init.sh              # Loader + selector dual svc() + agent()
│   └── lib/
│       ├── aliases.sh
│       ├── nav.sh
│       ├── docker.sh
│       ├── system.sh
│       ├── instal.sh        # APT installer
│       ├── pipins.sh        # pip installer
│       ├── prompt.sh
│       ├── git.sh
│       └── completions.sh
├── systemd/
│   ├── nas-agent.service    # Unit file del daemon
│   └── README.md
├── tests/                   # Tests (pytest, 75+)
│   ├── conftest.py          # Mocks de Strands SDK + fixtures
│   ├── test_memory.py       # 24 tests (MemoryManager)
│   ├── test_classify.py     # 21 tests (clasificación queries)
│   ├── test_validation.py   # 12 tests (seguridad inputs)
│   ├── test_daemon.py       # 4 tests (Scheduler)
│   ├── test_tool_result.py  # 10 tests (ToolResult)
│   ├── test_result.py
│   ├── test_compose_generation.py
│   └── test_phase3.py
├── pyproject.toml
└── requirements.txt
```

---

## 10. Convenciones

- **Idioma**: Código en inglés, UI/mensajes en español
- **Nombres de servicio**: solo `[a-z0-9._-]`, máx 64 chars
- **Puertos**: rango 8100-8999 para servicios nuevos, reservados: 22/53/80/443
- **Restart policy**: siempre `unless-stopped`
- **Secrets**: nunca inline en compose, siempre en `.env` + referencia `${VAR}`
- **Commits**: convención conventional commits (`feat:`, `fix:`, `security:`, `docs:`)
- **Ramas**: push directo a `main` (repo personal), o PR para cambios grandes
- **Python**: >=3.9, formato con ruff, type hints en todas las funciones públicas
- **Plugins**: un archivo por plugin, hereda `BasePlugin`, define `meta` y `setup()`
- **Eventos**: nombres con punto como separador (`dominio.accion`)
