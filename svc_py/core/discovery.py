"""
discovery.py — Detección de servicios Docker Compose.

Equivale a docker/cli/lib/discovery.sh pero en Python.
"""

from pathlib import Path
from typing import List, Optional

from svc_py.config import COMPOSE_FILENAMES, DOCKER_BASE


def svc_list() -> List[str]:
    """Lista todos los servicios detectados (tienen compose file).

    Returns:
        Lista ordenada de nombres de servicio.
    """
    services = set()
    if not DOCKER_BASE.exists():
        return []

    for item in sorted(DOCKER_BASE.iterdir()):
        if not item.is_dir():
            continue
        # Skip hidden dirs y backups
        if item.name.startswith(".") or item.name == "backups":
            continue
        for name in COMPOSE_FILENAMES:
            if (item / name).exists():
                services.add(item.name)
                break

    return sorted(services)


def svc_compose_file(service: str) -> Optional[Path]:
    """Retorna la ruta al compose file de un servicio.

    Args:
        service: Nombre del servicio.

    Returns:
        Path al compose file, o None si no existe.
    """
    svc_dir = DOCKER_BASE / service
    if not svc_dir.is_dir():
        return None

    for name in COMPOSE_FILENAMES:
        candidate = svc_dir / name
        if candidate.exists():
            return candidate

    return None


def svc_dir(service: str) -> Optional[Path]:
    """Retorna la ruta al directorio del servicio."""
    d = DOCKER_BASE / service
    return d if d.is_dir() else None


def service_exists(service: str) -> bool:
    """Verifica si un servicio existe (tiene compose file)."""
    return svc_compose_file(service) is not None
