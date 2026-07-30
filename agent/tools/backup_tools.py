"""
Herramientas de backup y restore para servicios Docker.

Thin wrappers que delegan a agent.core.backup_manager.
"""

from strands.tools import tool


def _get_backup_manager():
    """Lazy import para evitar circular dependency."""
    from agent.core.backup_manager import BackupManager
    return BackupManager


@tool
def backup_service(service_name: str) -> str:
    """Crea un backup de los volúmenes y bind mounts de un servicio.

    Usa la lógica del CLI existente (svc backup). Comprime datos
    en /docker/backups/ con timestamp. Rotación automática (últimos 5).

    Args:
        service_name: Nombre del servicio a respaldar.
                      Ejemplos: nextcloud, vaultwarden, grafana
    """
    return str(_get_backup_manager().backup(service_name))


@tool
def restore_service(service_name: str, confirm: str = "no") -> str:
    """Lista backups disponibles o restaura un servicio desde backup.

    ACCION DESTRUCTIVA: Sin confirm="si" solo lista los backups.
    Con confirm="si" restaura el más reciente.

    Args:
        service_name: Nombre del servicio a restaurar.
        confirm: "si" para ejecutar restauración del más reciente.
                 Cualquier otro valor solo lista backups disponibles.
    """
    return str(_get_backup_manager().restore(service_name, confirm))


@tool
def list_backups() -> str:
    """Lista todos los backups existentes en /docker/backups/.

    Muestra: servicio, archivo, tamaño y fecha de cada backup.
    Agrupa por servicio.

    No requiere argumentos.
    """
    return str(_get_backup_manager().list_all())
