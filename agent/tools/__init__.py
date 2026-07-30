"""
Herramientas (tools) del nas-agent.

Cada módulo expone funciones con @tool que el agente invoca
autónomamente para administrar el NAS.

Nota: Las tools se pasan directamente al agente (sin wrapper).
La auditoría se integra via plugin/hooks del agente, no por decorador,
porque wrappear funciones @tool rompe su registro en Strands SDK.
"""

from agent.tools.discovery_tools import (
    list_services,
    scan_compose,
    auto_catalog,
    bulk_discover,
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

# Lista de tools para el agente — SIN wrapper (Strands necesita @tool puro)
ALL_TOOLS = [
    # Descubrimiento
    list_services,
    scan_compose,
    auto_catalog,
    bulk_discover,
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
