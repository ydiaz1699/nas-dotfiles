# Agente IA — referencia completa

## Invocación

```bash
agent "query"                    # Consulta puntual (Gemini default)
agent chat                       # Modo REPL conversacional
agent --new "query"              # Nueva sesión limpia
agent --model                    # Menú para cambiar modelo
agent --model gemini-2.5-flash   # Cambiar directamente
agent --status                   # Info de sesión actual
agent --clear                    # Borrar sesión

# Override de provider por variable:
NAS_AGENT_MODEL=bedrock agent "query"
NAS_AGENT_MODEL=ollama agent "query"
```

---

## Providers

| Provider | Modelo default | Variable requerida | Costo |
|----------|----------------|--------------------|-------|
| Gemini (default) | gemini-3.1-flash-lite | `GOOGLE_API_KEY` | ~$0.15/1M tokens |
| Bedrock | Claude Sonnet 4 + thinking | `AWS_REGION` | ~$3/1M + thinking |
| Ollama (local) | llama3.1 (configurable) | `OLLAMA_HOST` | Gratis |

### Modelos disponibles (via `agent --model`)

1. gemini-2.5-flash (mejor razonamiento)
2. gemini-3.5-flash-lite (más requests/día)
3. gemini-3.5-flash (balance)
4. gemini-3.1-flash-lite (default actual)
5. gemini-3.6-flash (más nuevo)
6. Claude Sonnet 4 (Bedrock, con interleaved thinking)
7. Ollama llama3.1 (local, gratis)

Cambio persistente: se guarda en `.env.agent` (NAS_AGENT_MODEL + NAS_AGENT_MODEL_ID).

---

## Arquitectura del prompt

El agente NO usa un prompt monolítico. Python pre-clasifica la query y
selecciona **bloques** relevantes:

```
Query → _classify_query() → lista de bloques → _assemble_prompt()
```

```
Thinking Prompt → Identidad → Reglas Core → [Bloque específico] → Formato
```

Bloques disponibles: identidad, reglas_core, seguridad, herramientas,
formato, contexto_nas, diagnostico, creacion, backup, admin, memoria.

Clasificación por keywords:
- Diagnóstico: "revisar", "error", "falla", "caído", "unhealthy", "log"
- Creación: "instalar", "crear", "nuevo servicio", "montar", "configurar"
- Backup: "backup", "respaldo", "restaurar", "restore"
- Admin: "start", "stop", "restart", "update", "detener", "levantar"
- Memoria: "recuerda", "recordar", "skill", "qué sabes"
- General: todo lo demás → reglas_core + contexto_nas + memoria

---

## Reglas de ejecución del agente

- **Lectura/seguras**: ejecutar SIN preguntar (logs, health, restart, update)
- **Destructivas**: explicar + confirmar (stop, restore)
- Nunca mostrar docker commands crudos — usar tools
- Nunca inventar config sin buscar en catálogo o internet

### Mapeo acción → herramienta

| Acción | Tool |
|--------|------|
| Detener | `service_stop(svc, confirm="si")` |
| Levantar | `service_start(svc)` |
| Reiniciar | `service_restart(svc)` |
| Actualizar | `service_update(svc)` |
| Logs | `service_logs(svc, 50)` |
| Diagnóstico | `troubleshoot(svc)` |
| Compose | `read_compose(svc)` |
| Backup | `backup_service(svc)` |
| Restaurar | `restore_service(svc, confirm="si")` |

---

## Tools disponibles (31 total)

### Descubrimiento
| Tool | Acción |
|------|--------|
| `list_services()` | Servicios Docker con estado |
| `scan_compose(service)` | Analizar compose |
| `auto_catalog(service)` | Generar ficha de catálogo |
| `bulk_discover()` | Descubrir y catalogar todos |
| `export_service(service)` | Exportar config al catálogo |

### Sistema
| Tool | Acción |
|------|--------|
| `scan_ports()` | Puertos en uso + disponibles |
| `disk_usage()` | Uso de disco con alertas |
| `memory_info()` | RAM/Swap con top procesos |
| `network_info()` | Interfaces, IPs, redes Docker |
| `list_files(path, max_depth)` | Listar archivos (rutas permitidas) |
| `read_file_content(path, lines)` | Leer archivo (sanitiza .env) |

### Docker
| Tool | Acción |
|------|--------|
| `service_start(service)` | Levantar (seguro) |
| `service_stop(service, confirm)` | Detener (requiere confirm="si") |
| `service_restart(service)` | Reiniciar (seguro) |
| `service_update(service)` | Pull + recrear (seguro) |
| `service_logs(service, lines)` | Ver logs |

### Compose
| Tool | Acción |
|------|--------|
| `create_service(name, image, port, ...)` | Crear servicio nuevo |
| `validate_compose(service)` | Validar contra reglas |
| `read_compose(service)` | Leer compose actual |

### Backup
| Tool | Acción |
|------|--------|
| `backup_service(service)` | Crear backup |
| `restore_service(service, confirm)` | Restaurar (destructivo) |
| `list_backups()` | Listar backups disponibles |

### Búsqueda y Diagnóstico
| Tool | Acción |
|------|--------|
| `search_service_info(name)` | Buscar en internet |
| `service_health()` | Dashboard de salud |
| `port_conflicts()` | Detectar conflictos |
| `troubleshoot(service)` | Diagnóstico completo |
| `project_scan()` | Detectar lagunas y conexiones faltantes del proyecto |
| `discover_capabilities(query, service)` | Descubrir operaciones y guards desde manifests |
| `compare_catalog(service)` | Detectar drift entre compose real y catálogo |

### Índice estructural

`agent/tools/project_index.py` genera `agent/cache/project-index.json` sin
necesitar Docker. Inventaría por separado archivos, comandos Bash/Python,
servicios, capacidades y gateways MCP. La superficie MCP se publica en las
claves `mcp` y `mcp_tools`; no se mezcla con `ALL_TOOLS` ni con
`agent/capabilities/*.json`. `project-snapshot.json` es el baseline incremental
del scanner y no debe confundirse con el índice.

### Gateways MCP

| Gateway | Función | Estado |
|---------|---------|--------|
| `agent/lobehub_mcp.py` | Gateway histórico read-only específico de LobeHub | Conservado por compatibilidad |
| `agent/mcp/nas_mcp_gateway/` | Gateway NAS independiente con manifest, front-door lazy, worker y helper host | Preparado, no desplegado |

El gateway NAS publica únicamente `nas_services`, `nas_health`,
`nas_capabilities` y `nas_diagnostics`, recomienda `stdio` y deja HTTP como
transporte interno autenticado. No activar el helper ni el compose durante una
actualización del framework.

| Tool | Acción |
|------|--------|
| `remember(fact, category)` | Guardar hecho/lección |
| `recall(query)` | Buscar en memoria |
| `learn_skill(name, procedure, trigger)` | Crear skill reutilizable |
| `update_user_model(key, value)` | Actualizar perfil |
| `memory_stats()` | Estado de la memoria |

---

## Sistema de memoria

Archivos en `$NAS_DOTFILES/agent/memory/`:

| Archivo | Qué guarda | Límite |
|---------|------------|--------|
| `MEMORY.md` | Hechos, lecciones, patrones, pendientes | 50 KB |
| `USER.md` | Preferencias del usuario, decisiones | 10 KB |
| `SKILLS.md` | Procedimientos reutilizables con trigger | 100 KB |
| `sessions/` | Resúmenes de sesiones pasadas | 500 KB |

Categorías válidas para `remember()`: `entorno`, `leccion`, `patron`, `pendiente`.

### Flujo de memoria

- Antes de actuar → `recall("descripción del problema")` busca si ya lo resolvió
- Si encuentra un SKILL → aplicar directamente (no re-investigar)
- Después de resolver algo complejo → `remember()` o `learn_skill()`
- Observaciones sobre el usuario → `update_user_model()`
- NO guardar: cosas triviales, info duplicada, datos sensibles

### Búsqueda (recall)

Orden de prioridad: SKILLS (trigger) → MEMORY (keywords) → sessions.
Keywords de >2 chars se buscan como substring en todos los archivos.

---

## Sesiones

- Persistencia via `FileSessionManager` (Strands SDK)
- Storage: `~/.nas-agent/sessions/`
- Timeout: 30 min de inactividad → auto-reset
- `agent --new` fuerza sesión limpia
- `agent --clear` elimina todo
- Mensajes cortos sin contexto = continuación de sesión previa

---

## Plugins

Sistema modular en `$NAS_DOTFILES/agent/plugins/`:

| Plugin | Función | Schedule |
|--------|---------|----------|
| `docker_plugin.py` | Health checks, eventos unhealthy | Cada 5 min |
| `backup_plugin.py` | Auto-backup programado | Configurable |
| `network_plugin.py` | Escaneo de puertos | Configurable |
| `ha_discovery_plugin.py` | Integración Home Assistant | — |
| `memory_plugin.py` | Curación de memoria | Cada 24h |

Cada plugin registra: tools, event handlers, scheduled tasks.
Config en `agent/config/defaults.yml`:
```yaml
plugins:
  enabled: [docker, backup, network]
  disabled: []
```

Base: heredar de `BasePlugin`, implementar `setup()` con
`register_tool()`, `register_event()`, `register_schedule()`.
Auto-descubrimiento por `loader.py` (escanea *.py en plugins/).

---

## Daemon (systemd)

```bash
# Foreground (debug)
python -m agent.daemon

# Producción
sudo systemctl start nas-agent
journalctl -u nas-agent -f
```

Mantiene vivos: Scheduler (tareas periódicas) + Plugin schedules.
Heartbeat cada 60 min con stats de memoria.
Graceful shutdown via SIGTERM/SIGINT.

---

## Catálogo de servicios

En `$NAS_DOTFILES/agent/catalog/`:

| Archivo | Contenido |
|---------|-----------|
| `_rules.md` | Reglas de formato (puertos, restart, naming) |
| `_template.md` | Template para fichas nuevas |
| `_compose_base.md` | Anchors YAML obligatorios |
| `catalog.json` | Índice de servicios catalogados |
| `services/<svc>/ficha.md` | Ficha individual con frontmatter YAML |

Flujo de creación:
1. `search_service_info()` busca en internet
2. `create_service()` genera compose con anchors
3. `validate_compose()` valida contra _rules.md
4. `auto_catalog()` genera ficha para futuras referencias

---

## Variables de entorno

| Variable | Default | Descripción |
|----------|---------|-------------|
| `NAS_AGENT_MODEL` | `gemini` | Provider |
| `NAS_AGENT_MODEL_ID` | (auto) | Override de modelo |
| `GOOGLE_API_KEY` | — | API key Gemini |
| `AWS_REGION` | `us-east-1` | Región Bedrock |
| `NAS_AGENT_THINKING_BUDGET` | `10000` | Tokens razonamiento (Bedrock) |
| `OLLAMA_HOST` | `http://localhost:11434` | Host Ollama |
| `NAS_AGENT_READONLY` | `0` | Bloquear tools destructivas |
| `NAS_AGENT_DRYRUN` | `0` | Solo mostrar plan |
| `NAS_AGENT_AUDIT` | `1` | Habilitar audit log |
| `NAS_AGENT_AUDIT_LOG` | `/docker/backups/agent_audit.log` | Ruta log |
| `NAS_AGENT_SESSION_TIMEOUT` | `30` | Minutos antes de auto-reset |
| `NAS_AGENT_SESSIONS_DIR` | `~/.nas-agent/sessions` | Dir sesiones |
| `NAS_AGENT_MEMORY_DIR` | `agent/memory/` | Dir memoria |
| `NAS_AGENT_LOG_LEVEL` | `INFO` | Nivel del daemon |

---

## Dependencias Python

```
strands-agents[gemini]>=1.0.0
strands-agents-tools>=0.1.0
python-frontmatter>=1.0.0
PyYAML>=6.0
rich>=13.0.0
paho-mqtt>=1.6.0  (opcional, para MQTT)
```

Instalar: `pip install -r $NAS_DOTFILES/requirements.txt`

---

## Configuración (defaults.yml)

```yaml
plugins:
  enabled: [docker, backup, network]
mqtt:
  enabled: false
  host: localhost
  port: 1883
  topics: ["nas-agent/#", "homeassistant/+/status", "docker/events/#"]
scheduler:
  enabled: true
  tick_interval_seconds: 30
cache:
  ttl_seconds: 300
  persist_path: "~/.nas-agent/cache.json"
session:
  timeout_minutes: 30
logging:
  level: "INFO"
```
