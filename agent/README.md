# nas-agent — Administrador inteligente de NAS

Agente basado en [Strands Agents SDK](https://strandsagents.com/) que
administra servicios Docker en tu NAS con lenguaje natural.

## Requisitos

```bash
pip install -r requirements.txt
```

### Proveedor de modelo

**Google Gemini (default — rápido y barato):**
```bash
export NAS_AGENT_MODEL=gemini
export GOOGLE_API_KEY=tu-api-key     # https://aistudio.google.com/apikey
# Modelo: gemini-3.1-flash-lite (override con NAS_AGENT_MODEL_ID)
```

**Amazon Bedrock (Claude — mejor tool-use):**
```bash
export NAS_AGENT_MODEL=bedrock
export AWS_REGION=us-east-1
export AWS_PROFILE=default
# Modelo: Claude Sonnet 4 con extended thinking
```

**Ollama (local, gratis, privado):**
```bash
export NAS_AGENT_MODEL=ollama
export OLLAMA_HOST=http://localhost:11434
# Requiere: ollama serve + ollama pull llama3.1
```


## Uso

```bash
cd ~/nas-dotfiles

# Modo interactivo
python -m agent.nas_agent

# Con query directa
python -m agent.nas_agent "¿Qué servicios están caídos?"
python -m agent.nas_agent "Quiero instalar Vaultwarden"
python -m agent.nas_agent "Diagnostica nextcloud"
python -m agent.nas_agent "¿Hay conflictos de puertos?"
python -m agent.nas_agent "Hazme backup de grafana"

# Gestión de sesión
python -m agent.nas_agent --new "crear servicio X"   # Nueva sesión limpia
python -m agent.nas_agent --status                   # Ver sesión actual
python -m agent.nas_agent --clear                    # Borrar sesión
```

### Alias (desde terminal):

```bash
agent "revisar emqx"          # Equivale a python -m agent.nas_agent
agent --status                 # Info de sesión
agent --new "instalar X"       # Forzar nueva sesión
agent --model                  # Cambiar modelo (menú interactivo)
agent --model gemini-2.5-flash # Cambio directo
```

### Importar en tu código:

```python
from agent.nas_agent import create_nas_agent

agent = create_nas_agent()
result = agent("¿Qué servicios están corriendo?")
```

## Arquitectura

```
agent/
├── __init__.py
├── nas_agent.py                ← Entry point + system prompt + sesión + Rich UI
├── README.md                   ← Este archivo
├── config/
│   └── defaults.yml            ← Configuración centralizada (plugins, MQTT, cache, etc.)
├── core/                       ← Lógica de negocio (managers)
│   ├── _result.py              ← ToolResult dataclass
│   ├── memory.py               ← MemoryManager (Learning Loop)
│   ├── service_manager.py      ← start/stop/restart/update/logs
│   ├── compose_manager.py      ← create/validate/read
│   └── backup_manager.py       ← backup/restore/list
├── tools/                      ← Thin wrappers (@tool → core managers)
│   ├── __init__.py             ← Exporta ALL_TOOLS (28 herramientas)
│   ├── _shell.py               ← safe_run, validate, readonly, dryrun
│   ├── _audit.py               ← Audit log JSON Lines
│   ├── _result.py              ← ToolResult helpers
│   ├── discovery_tools.py      ← list_services, scan_compose, auto_catalog, bulk_discover, export_service
│   ├── system_tools.py         ← scan_ports, disk_usage, memory_info, network_info, list_files, read_file_content
│   ├── docker_tools.py         ← service_start/stop/restart/update/logs
│   ├── compose_tools.py        ← create_service, validate_compose, read_compose
│   ├── backup_tools.py         ← backup_service, restore_service, list_backups
│   ├── search_tools.py         ← search_service_info (web fallback)
│   ├── diagnostic_tools.py     ← service_health, port_conflicts, troubleshoot
│   └── memory_tools.py         ← remember, recall, learn_skill, update_user_model, memory_stats
├── plugins/                    ← Sistema de plugins dinámicos
│   ├── base.py                 ← BasePlugin + PluginMeta + ScheduleConfig + EventHandler
│   ├── loader.py               ← Auto-discovery + load/unload
│   ├── docker_plugin.py        ← Health check cada 5 min
│   ├── backup_plugin.py        ← Backup diario automático
│   ├── network_plugin.py       ← Escaneo puertos cada 15 min
│   ├── memory_plugin.py        ← Learning Loop (curación + consolidación)
│   └── ha_discovery_plugin.py  ← HA MQTT Discovery (auto-discovery en Home Assistant)
├── events/                     ← Event bus pub/sub
│   ├── bus.py                  ← EventBus (exact/wildcard/global, thread-safe)
│   └── mqtt_listener.py        ← MQTT → EventBus pipeline
├── scheduler/                  ← Tareas periódicas
│   └── runner.py               ← Threaded task runner (cron-like)
├── cache/                      ← Cache KV con TTL
│   └── store.py                ← Thread-safe + persistencia a disco
├── memory/                     ← Datos persistentes de memoria
│   ├── MEMORY.md               ← Hechos, lecciones, patrones
│   ├── USER.md                 ← Perfil del usuario
│   ├── SKILLS.md               ← Procedimientos reutilizables
│   └── sessions/               ← Historial resumido
└── catalog/                    ← Catálogo de servicios (portable)
    ├── _rules.md               ← Reglas de generación
    ├── _compose_base.md        ← Template base (anchors YAML)
    ├── _template.md            ← Template de fichas
    ├── _index.py               ← Generador de catalog.json
    ├── .env.global.example     ← Variables globales compartidas
    ├── catalog.json            ← Índice auto-generado
    └── services/               ← Servicios exportados
        ├── datasql/            ← Stack PostgreSQL + pgAdmin + Redis
        └── emqx/              ← Broker MQTT
```


## Herramientas (28 tools)

| Herramienta | Qué hace | Segura |
|-------------|----------|--------|
| `list_services()` | Lista servicios con estado | ✅ |
| `scan_compose(svc)` | Analiza compose de un servicio | ✅ |
| `auto_catalog(svc)` | Genera ficha de catálogo | ✅ |
| `bulk_discover()` | Descubrir y catalogar todos los servicios | ✅ |
| `export_service(svc)` | Exportar config real al catálogo | ✅ |
| `scan_ports()` | Puertos en uso + libres | ✅ |
| `disk_usage()` | Uso de disco con alertas | ✅ |
| `memory_info()` | RAM/Swap + top procesos | ✅ |
| `network_info()` | IPs, interfaces, redes Docker | ✅ |
| `list_files(path)` | Listar archivos en ruta del NAS | ✅ |
| `read_file_content(path)` | Leer archivo de texto | ✅ |
| `service_start(svc)` | Levantar servicio | ✅ |
| `service_stop(svc, confirm)` | Detener servicio | ⚠️ |
| `service_restart(svc)` | Reiniciar servicio | ✅ |
| `service_update(svc)` | Pull + recrear | ✅ |
| `service_logs(svc, lines)` | Ver logs | ✅ |
| `create_service(...)` | Crear servicio nuevo | ✅ |
| `validate_compose(svc)` | Validar contra _rules.md | ✅ |
| `read_compose(svc)` | Leer compose actual | ✅ |
| `backup_service(svc)` | Crear backup | ✅ |
| `restore_service(svc, confirm)` | Restaurar backup | ⚠️ |
| `list_backups()` | Listar backups | ✅ |
| `search_service_info(name)` | Buscar en internet | ✅ |
| `service_health()` | Dashboard de salud | ✅ |
| `port_conflicts()` | Detectar conflictos | ✅ |
| `troubleshoot(svc)` | Diagnóstico completo | ✅ |
| `remember(fact)` | Guardar hecho en memoria persistente | ✅ |
| `recall(query)` | Buscar en memoria persistente | ✅ |
| `learn_skill(name, steps)` | Guardar procedimiento reutilizable | ✅ |
| `update_user_model(info)` | Actualizar perfil del usuario | ✅ |
| `memory_stats()` | Estadísticas de memoria | ✅ |

⚠️ = Requiere `confirm="si"` para ejecutarse


## Sesión persistente

El agente recuerda el contexto entre invocaciones. Usa `FileSessionManager` de Strands SDK.

```bash
agent "revisar tasmoadmin"        # Diagnostica con troubleshoot + logs
agent "si reiniciar"              # Recuerda el contexto → reinicia tasmoadmin
agent --status                    # Ver sesión actual (turnos, última actividad)
agent --new "instalar X"          # Forzar sesión nueva
agent --clear                     # Borrar memoria completamente
agent --model                     # Cambiar modelo interactivamente
agent --model gemini-2.5-flash    # Cambio directo (se guarda en .env.agent)
```

Auto-reset tras 30 min de inactividad (configurable con `NAS_AGENT_SESSION_TIMEOUT`).


## Interfaz Rich

El agente usa la librería [Rich](https://github.com/Textualize/rich) para output formateado:

- **Header**: Panel cyan con título y subtítulo
- **Query**: Texto destacado con colores por categoría
- **Resultado**: Panel verde con Markdown renderizado
- **Errores**: Paneles amarillos/rojos según severidad
- **Modos**: Indicadores coloridos para dry-run/read-only

Si Rich no está instalado, degrada a texto plano automáticamente.


## Arquitectura del Prompt: Thinking + Bloques Dinámicos

El system prompt NO es monolítico. Se ensambla dinámicamente por query:

```
agent "revisar emqx"
        │
        ▼
┌─ Python: _classify_query("revisar emqx") ────────────┐
│  Detecta keywords → tipo: diagnóstico                  │
│  Selecciona: [identidad, reglas_core, herramientas,   │
│               diagnostico, formato]                    │
└────────────────────────────────────────────────────────┘
        │
        ▼
┌─ _assemble_prompt(bloques) ───────────────────────────┐
│  THINKING_PROMPT (razonar antes de actuar)             │
│  + BLOCK_IDENTIDAD (modelo, provider)                  │
│  + BLOCK_REGLAS_CORE (actuar sin preguntar)            │
│  + BLOCK_HERRAMIENTAS (23 tools)                       │
│  + BLOCK_DIAGNOSTICO (cadena, patrones error)          │
│  + BLOCK_FORMATO (español, conciso)                    │
└────────────────────────────────────────────────────────┘
```

### Bloques disponibles (10):

| Bloque | Contenido |
|--------|-----------|
| `identidad` | Modelo, provider, nombre |
| `reglas_core` | Actuar sin preguntar, mapeo acción→tool |
| `seguridad` | Puertos reservados, credenciales, modos |
| `herramientas` | Lista de 23 tools con descripción |
| `formato` | Español, conciso, emojis, markdown |
| `contexto_nas` | Memoria sesión, comandos del usuario |
| `diagnostico` | Cadena diagnóstica, patrones de error |
| `creacion` | Flujo creación, deps, puertos 8100-8999 |
| `backup` | Backup/restore, confirmación |
| `admin` | Acciones seguras vs destructivas |

### Qué recibe cada tipo de query:

| Query | Bloques |
|-------|---------|
| "revisar emqx" | identidad + reglas + tools + **diagnostico** + formato |
| "instalar X" | identidad + reglas + tools + seguridad + **creacion** + formato |
| "backup plex" | identidad + reglas + tools + **backup** + formato |
| "reiniciar Y" | identidad + reglas + tools + **admin** + formato |
| "qué modelo eres" | **identidad** (solo) |
| "hola" | identidad + reglas + contexto_nas + formato |


## Cambio de modelo

Cambiar el modelo del agente desde la terminal:

```bash
# Menú interactivo con 7 opciones
agent --model

# Cambio directo (se guarda automáticamente en .env.agent)
agent --model gemini-2.5-flash
```

Modelos disponibles en el menú:
1. Gemini 2.5 Flash (mejor razonamiento)
2. Gemini 3.5 Flash Lite (más requests/día)
3. Gemini 3.5 Flash (balance)
4. Gemini 3.1 Flash Lite (default actual)
5. Gemini 3.6 Flash (más nuevo)
6. Claude Sonnet 4 (Bedrock)
7. Ollama llama3.1 (local, gratis)


## Sistema de Plugins

Plugins se cargan dinámicamente y registran tools, eventos y tareas periódicas.

```python
class DockerPlugin(BasePlugin):
    meta = PluginMeta(name="docker", description="Control Docker")

    def setup(self):
        self.register_tool(service_restart)
        self.register_schedule(ScheduleConfig(
            name="health-check",
            handler=self.check_health,
            interval_minutes=5,
        ))
        self.register_event(EventHandler(
            event_type="docker.unhealthy",
            handler=self.on_unhealthy,
        ))
```

Plugins incluidos:
| Plugin | Función |
|--------|---------|
| `docker_plugin` | Health check cada 5 min |
| `backup_plugin` | Backup diario automático |
| `network_plugin` | Escaneo de puertos cada 15 min |
| `memory_plugin` | Learning Loop (curación + consolidación 24h) |
| `ha_discovery_plugin` | HA MQTT Discovery (auto-discovery en Home Assistant) |


## Event Bus + MQTT

El bus interno soporta pub/sub con matching exacto, wildcard (`prefix.*`) y global (`*`).

```python
bus = EventBus()
bus.on("docker.unhealthy", my_handler)   # Exacto
bus.on("docker.*", wildcard_handler)     # Wildcard
bus.on("*", audit_all_events)            # Global
bus.emit("docker.unhealthy", {"service": "emqx"})
```

### MQTT → Agente

Home Assistant, Node-RED o cualquier servicio puede disparar acciones via MQTT:

```bash
# Trigger backup via MQTT
mosquitto_pub -t "nas-agent/command/backup" -m '{"service":"emqx"}'
```

Pipeline:
```
MQTT topic (nas-agent/command/backup)
       ↓
MQTTListener (traduce topic → event_type)
       ↓
EventBus.emit("agent.command.backup", {service: "emqx"})
       ↓
BackupPlugin._on_backup_command()
       ↓
BackupManager.backup("emqx")
```


## Scheduler

Tareas periódicas estilo cron, ejecutadas en hilos separados:

```python
scheduler = Scheduler(event_bus=bus)
scheduler.add(ScheduleConfig(
    name="health-check",
    handler=check_all_services,
    interval_minutes=5,
    run_on_start=True,
))
scheduler.start()
```

Emite eventos al bus: `schedule.run`, `schedule.complete`, `schedule.error`.


## Cache

Cache key-value en memoria con TTL, thread-safe:

```python
cache = Cache(ttl_seconds=300, persist_path=Path("~/.nas-agent/cache.json"))
cache.set("ports.used", [1883, 8083])
cache.get("ports.used")       # Lista o None si expiró
cache.invalidate("ports.used")
cache.stats                   # {"hits": 42, "misses": 3, "hit_rate": "93%"}
```


## Catálogo: local + web search

### Flujo al crear un servicio:

```
1. ¿Está en catalog/services/?
   → SÍ: Usa la ficha local (configuración verificada)
   → NO: Busca en Docker Hub + GitHub

2. Aplica _rules.md SIEMPRE:
   - Puerto en rango 8100-8999 (verifica disponibilidad)
   - Formato estándar de compose
   - Variables sensibles en .env
   - Healthcheck si expone HTTP

3. Genera: docker-compose.yml + .env + README.md

4. Ofrece guardar ficha en catálogo (auto_catalog)
```

### Agregar fichas manualmente:

```bash
cp agent/catalog/_template.md agent/catalog/services/mi-servicio/ficha.md
nano agent/catalog/services/mi-servicio/ficha.md
```


## Variables de entorno

| Variable | Default | Descripción |
|----------|---------|-------------|
| `NAS_AGENT_MODEL` | `gemini` | Proveedor: gemini, bedrock, ollama |
| `NAS_AGENT_MODEL_ID` | `gemini-3.1-flash-lite` | Override del model ID |
| `GOOGLE_API_KEY` | — | API key para Gemini |
| `AWS_REGION` | `us-east-1` | Región para Bedrock |
| `NAS_AGENT_THINKING_BUDGET` | `10000` | Tokens de razonamiento (Bedrock) |
| `OLLAMA_HOST` | `http://localhost:11434` | Host de Ollama |
| `NAS_AGENT_READONLY` | `0` | Bloquear acciones destructivas |
| `NAS_AGENT_DRYRUN` | `0` | No ejecutar nada (dual: prompt + hard) |
| `NAS_AGENT_AUDIT` | `1` | Habilitar audit log |
| `NAS_AGENT_AUDIT_LOG` | `/docker/backups/agent_audit.log` | Ruta del audit log |
| `NAS_AGENT_SESSION_TIMEOUT` | `30` | Minutos de inactividad antes de auto-reset |
| `NAS_MQTT_HOST` | `localhost` | Host del broker MQTT |
| `NAS_MQTT_PORT` | `1883` | Puerto del broker MQTT |
| `NAS_MQTT_TOPICS` | `nas-agent/#` | Topics MQTT (separados por `;`) |

## Seguridad

- Acciones destructivas (stop, restore) requieren confirmación
- Servicios protegidos no se tocan sin confirmación explícita
- Credenciales NUNCA se muestran en claro en respuestas
- Los composes generados ponen credenciales en .env (no inline)
- Puertos reservados (22, 53, 80, 443) nunca se asignan
- Audit log registra todas las invocaciones de tools
- Modo read-only/dry-run para entornos sensibles
