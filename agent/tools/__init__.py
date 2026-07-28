"""
Herramientas (tools) del nas-agent.

Cada módulo expone funciones con @tool que el agente invoca
autónomamente para administrar el NAS.

Auditoría: Todas las tools se wrappean con el decorador `audited()`
que registra cada invocación en el audit log (JSON Lines).
Deshabilitar con: export NAS_AGENT_AUDIT=0
"""

from agent.tools._audit import audited

from agent.tools.discovery_tools import (
    list_services,
    scan_compose,
    auto_catalog,
)
from agent.tools.system_tools import (
    scan_ports,
    disk_usage,
    memory_info,
    network_info,
)
from agent.tools.docker_tools import (
    service_start,
    service_stop,
    service_restart,
    service_update,
    service_logs,
)
from agent.tools.compose_tools import (
    create_service,
    validate_compose,
    read_compose,
)
from agent.tools.backup_tools import (
    backup_service,
    restore_service,
    list_backups,
)
from agent.tools.search_tools import (
    search_service_info,
)
from agent.tools.diagnostic_tools import (
    service_health,
    port_conflicts,
    troubleshoot,
)

# Lista de tools sin auditoría (referencia interna)
_RAW_TOOLS = [
    # Descubrimiento
    list_services,
    scan_compose,
    auto_catalog,
    # Sistema
    scan_ports,
    disk_usage,
    memory_info,
    network_info,
    # Docker
    service_start,
    service_stop,
    service_restart,
    service_update,
    service_logs,
    # Compose
    create_service,
    validate_compose,
    read_compose,
    # Backup
    backup_service,
    restore_service,
    list_backups,
    # Búsqueda web
    search_service_info,
    # Diagnóstico
    service_health,
    port_conflicts,
    troubleshoot,
]

# Lista completa de tools para el agente — CON auditoría
ALL_TOOLS = [audited(t) for t in _RAW_TOOLS]
