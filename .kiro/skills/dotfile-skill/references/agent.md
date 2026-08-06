# Agente IA — referencia completa

## Ejecución

```bash
agent "query"          # query directa (Gemini default)
agent chat             # REPL interactivo
agent --new "query"    # nueva sesión limpia
agent --status         # info sesión actual
agent --clear          # borrar sesión
agent --model          # ver modelo activo

NAS_AGENT_MODEL=bedrock agent "query"   # usar Claude
NAS_AGENT_MODEL=ollama agent "query"    # usar Ollama local
```

## Providers

| Provider | Modelo | Variable requerida |
|----------|--------|--------------------|
| Gemini (default) | gemini-3.1-flash-lite | `GOOGLE_API_KEY` |
| Bedrock | Claude Sonnet 4 + thinking | `AWS_REGION` |
| Ollama | llama3.1 (configurable) | `OLLAMA_HOST` |

## Arquitectura del prompt

El agente NO usa un system prompt monolítico. Python pre-clasifica la query
y ensambla solo los bloques relevantes:

```
Thinking Prompt → Identidad → Reglas Core → [Bloque específico] → Formato
```

Bloques: identidad, reglas_core, seguridad, herramientas, formato,
contexto_nas, diagnostico, creacion, backup, admin, memoria.

## Tools (28 herramientas)

| Módulo | Tools |
|--------|-------|
| `discovery_tools` | list_services, scan_compose, auto_catalog, bulk_discover, export_service |
| `system_tools` | scan_ports, disk_usage, memory_info, network_info, list_files, read_file_content |
| `docker_tools` | service_start, service_stop, service_restart, service_update, service_logs |
| `compose_tools` | create_service, validate_compose, read_compose |
| `backup_tools` | backup_service, restore_service, list_backups |
| `diagnostic_tools` | service_health, port_conflicts, troubleshoot |
| `search_tools` | search_service_info (web fallback) |
| `memory_tools` | remember, recall, learn_skill, update_user_model, memory_stats |

## Reglas de ejecución del agente

- **Lectura/seguras**: ejecutar SIN preguntar (logs, health, restart, update)
- **Destructivas**: explicar + confirmar (stop, restore)
- Nunca mostrar docker commands crudos — usar tools
- Nunca inventar config sin buscar en catálogo o internet

## Memoria persistente

Archivos en `agent/memory/`:

| Archivo | Contenido |
|---------|-----------|
| `MEMORY.md` | Hechos, lecciones, patrones, pendientes (por categoría) |
| `USER.md` | Preferencias del usuario |
| `SKILLS.md` | Procedimientos reutilizables con triggers |
| `sessions/` | Resúmenes de sesiones |

Tools de memoria: `remember()`, `recall()`, `learn_skill()`, `update_user_model()`, `memory_stats()`

## Plugins (agent/plugins/)

| Plugin | Función |
|--------|---------|
| `docker_plugin` | Health checks periódicos |
| `backup_plugin` | Auto-backup diario |
| `network_plugin` | Escaneo de puertos |
| `memory_plugin` | Learning loop |
| `ha_discovery_plugin` | Descubrimiento Home Assistant |

Base: heredar de `BasePlugin`, implementar `setup()` con
`register_tool()`, `register_event()`, `register_schedule()`.

## Daemon (systemd)

`agent/daemon.py` → servicio `nas-agent.service`
- Ejecuta scheduler + plugins 24/7
- Heartbeat logging
- SIGTERM graceful shutdown

## Sesiones

- `FileSessionManager` con timeout configurable (default 30 min)
- Auto-reset si expira
- Directorio: `~/.nas-agent/sessions/`

## Catálogo de servicios

En `agent/catalog/`:
- `_rules.md` — reglas de formato
- `_template.md` — template fichas
- `catalog.json` — índice
- `services/<svc>/ficha.md` — fichas con frontmatter YAML
