"""
Herramientas para control de servicios Docker.

Thin wrappers que delegan a agent.core.service_manager.
"""

from strands.tools import tool


def _get_service_manager():
    """Lazy import para evitar circular dependency."""
    from agent.core.service_manager import ServiceManager
    return ServiceManager


@tool
def service_start(service_name: str) -> str:
    """Levanta (up -d) un servicio Docker.

    Ejecuta docker compose up -d para iniciar los contenedores del servicio.
    Seguro de ejecutar sin confirmación.

    Args:
        service_name: Nombre del servicio a iniciar.
                      Ejemplos: nextcloud, plex, grafana
    """
    return str(_get_service_manager().start(service_name))


@tool
def service_stop(service_name: str, confirm: str = "no") -> str:
    """Detiene (down) un servicio Docker.

    ⚠️ ACCIÓN DESTRUCTIVA: Requiere confirm="si" para ejecutarse.
    Sin confirmación solo muestra qué haría.

    Args:
        service_name: Nombre del servicio a detener.
        confirm: Debe ser "si" para ejecutar. Cualquier otro valor
                 solo muestra la acción sin ejecutarla.
    """
    return str(_get_service_manager().stop(service_name, confirm))


@tool
def service_restart(service_name: str) -> str:
    """Reinicia un servicio Docker (restart).

    Reinicia los contenedores sin destruirlos. Seguro de ejecutar.

    Args:
        service_name: Nombre del servicio a reiniciar.
    """
    return str(_get_service_manager().restart(service_name))


@tool
def service_update(service_name: str) -> str:
    """Actualiza un servicio: pull de nueva imagen + recrear contenedores.

    Ejecuta pull + up -d --remove-orphans. Seguro de ejecutar
    (no pierde datos, solo actualiza la imagen).

    Args:
        service_name: Nombre del servicio a actualizar.
    """
    return str(_get_service_manager().update(service_name))


@tool
def service_logs(service_name: str, lines: int = 100) -> str:
    """Muestra las últimas líneas de logs de un servicio.

    No hace follow (no se queda esperando). Muestra las últimas N líneas.

    Args:
        service_name: Nombre del servicio.
        lines: Número de líneas a mostrar (default: 100, máximo: 500).
    """
    return str(_get_service_manager().logs(service_name, lines))
