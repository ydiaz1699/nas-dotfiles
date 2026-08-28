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
    export_service,
)
from agent.tools.system_tools import (
    scan_ports,
    disk_usage,
    memory_info,
    network_info,
    list_files,
    read_file_content,
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
from agent.tools.project_scanner import project_scan
from agent.tools.capability_tools import discover_capabilities
from agent.tools.compare_tools import compare_catalog
from agent.tools.memory_tools import (
    remember,
    recall,
    learn_skill,
    update_user_model,
    memory_stats,
)

# Lista de tools para el agente — SIN wrapper (Strands necesita @tool puro)
ALL_TOOLS = [
    # Descubrimiento
    list_services,
    scan_compose,
    auto_catalog,
    bulk_discover,
    export_service,
    # Sistema
    scan_ports,
    disk_usage,
    memory_info,
    network_info,
    list_files,
    read_file_content,
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
    # Scanner de proyecto
    project_scan,
    # Descubrimiento dinámico de capacidades (no ejecuta mutaciones)
    discover_capabilities,
    # Comparador catálogo vs real
    compare_catalog,
    # Memoria persistente (Learning Loop)
    remember,
    recall,
    learn_skill,
    update_user_model,
    memory_stats,
]
