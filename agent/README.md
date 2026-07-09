# nas-agent — Administrador inteligente de NAS

Agente basado en [Strands Agents SDK](https://strandsagents.com/) que
administra servicios Docker en tu NAS con lenguaje natural.

## Requisitos

```bash
pip install strands-agents strands-agents-tools python-frontmatter pyyaml
```

### Proveedor de modelo

**Amazon Bedrock (default — más inteligente):**
```bash
export NAS_AGENT_MODEL=bedrock
export AWS_REGION=us-east-1
export AWS_PROFILE=default
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
├── nas_agent.py             ← Agente principal (entry point)
├── README.md                ← Este archivo
├── catalog/
│   ├── _rules.md            ← Reglas del NAS (SIEMPRE se aplican)
│   ├── _template.md         ← Template para fichas nuevas
│   └── services/            ← Fichas de servicios (auto + manuales)
│       └── .gitkeep
└── tools/
    ├── __init__.py           ← Exporta ALL_TOOLS (20 herramientas)
    ├── discovery_tools.py    ← list_services, scan_compose, auto_catalog
    ├── system_tools.py       ← scan_ports, disk_usage, memory_info, network_info
    ├── docker_tools.py       ← service_start/stop/restart/update/logs
    ├── compose_tools.py      ← create_service, validate_compose, read_compose
    ├── backup_tools.py       ← backup_service, restore_service, list_backups
    ├── search_tools.py       ← search_service_info (web fallback)
    └── diagnostic_tools.py   ← service_health, port_conflicts, troubleshoot
```


## Herramientas (20 tools)

| Herramienta | Qué hace | Segura |
|-------------|----------|--------|
| `list_services()` | Lista servicios con estado | ✅ |
| `scan_compose(svc)` | Analiza compose de un servicio | ✅ |
| `auto_catalog(svc)` | Genera ficha de catálogo | ✅ |
| `scan_ports()` | Puertos en uso + libres | ✅ |
| `disk_usage()` | Uso de disco con alertas | ✅ |
| `memory_info()` | RAM/Swap + top procesos | ✅ |
| `network_info()` | IPs, interfaces, redes Docker | ✅ |
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

⚠️ = Requiere `confirm="si"` para ejecutarse

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
cp agent/catalog/_template.md agent/catalog/services/mi-servicio.md
nano agent/catalog/services/mi-servicio.md
```

## Variables de entorno

| Variable | Default | Descripción |
|----------|---------|-------------|
| `NAS_AGENT_MODEL` | `bedrock` | Proveedor: bedrock, ollama |
| `NAS_AGENT_MODEL_ID` | (auto) | Override del model ID |
| `AWS_REGION` | `us-east-1` | Región para Bedrock |
| `OLLAMA_HOST` | `http://localhost:11434` | Host de Ollama |

## Seguridad

- Acciones destructivas (stop, restore) requieren confirmación
- Servicios protegidos no se tocan sin confirmación explícita
- Credenciales NUNCA se muestran en claro en respuestas
- Los composes generados ponen credenciales en .env (no inline)
- Puertos reservados (22, 53, 80, 443) nunca se asignan
