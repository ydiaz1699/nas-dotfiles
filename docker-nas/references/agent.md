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

| Provider | Default model | Variable | Costo |
|----------|---------------|----------|-------|
| Gemini (default) | gemini-3.1-flash-lite | `GOOGLE_API_KEY` | ~$0.15/1M tokens |
| Bedrock | Claude Sonnet 4 | `AWS_REGION` | ~$3/1M + thinking |
| Ollama (local) | llama3.1 | `OLLAMA_HOST` | Gratis |

### Modelos disponibles (via `agent --model`)

1. gemini-2.5-flash (mejor razonamiento)
2. gemini-3.5-flash-lite (más requests/día)
3. gemini-3.5-flash (balance)
4. gemini-3.1-flash-lite (default actual)
5. gemini-3.6-flash (más nuevo)
6. Claude Sonnet 4 (Bedrock)
7. Ollama llama3.1 (local)

---

## Arquitectura del prompt

El agente NO usa un prompt monolítico. Python pre-clasifica la query y
selecciona **bloques** relevantes:

```
Query → _classify_query() → lista de bloques → _assemble_prompt()
```

Bloques disponibles: identidad, reglas_core, seguridad, herramientas,
formato, contexto_nas, diagnostico, creacion, backup, admin, memoria.

---

## Tools disponibles (28 total)

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
| `create_service(name, image, port, ...)` | Crear nuevo |
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

### Memoria persistente
| Tool | Acción |
|------|--------|
| `remember(fact, category)` | Guardar hecho/lección |
| `recall(query)` | Buscar en memoria |
| `learn_skill(name, procedure, trigger)` | Crear skill |
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

---

## Sesiones

- Persistencia via `FileSessionManager` (Strands SDK)
- Storage: `~/.nas-agent/sessions/`
- Timeout: 30 min de inactividad → auto-reset
- `agent --new` fuerza sesión limpia
- `agent --clear` elimina todo

---

## Plugins

Sistema modular en `$NAS_DOTFILES/agent/plugins/`:

| Plugin | Qué hace |
|--------|----------|
| `docker_plugin.py` | Health checks cada 5 min, eventos unhealthy |
| `backup_plugin.py` | Programar backups automáticos |
| `network_plugin.py` | Monitoreo de red |
| `ha_discovery_plugin.py` | Integración Home Assistant |
| `memory_plugin.py` | Curación de memoria (24h) |

Cada plugin registra: tools, event handlers, scheduled tasks.
Config en `agent/config/defaults.yml`:
```yaml
plugins:
  enabled: [docker, backup, network]
```

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
