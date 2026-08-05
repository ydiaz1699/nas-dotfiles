"""
docker.py — Docker SDK nativo + compose subprocess.

Usa Docker SDK (python-docker) para inspección directa de contenedores
(más rápido, sin parsear strings). Usa subprocess solo para docker compose
(el SDK no tiene soporte completo para compose).

Fallback: si docker SDK no está instalado, usa subprocess para todo.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ── Docker SDK (opcional pero recomendado) ─────────────────────────────────

_docker_client = None
_sdk_available = False

try:
    import docker as docker_sdk
    _sdk_available = True
except ImportError:
    _sdk_available = False


def _get_client():
    """Obtiene o crea el cliente Docker SDK (singleton)."""
    global _docker_client
    if _docker_client is None and _sdk_available:
        try:
            _docker_client = docker_sdk.from_env()
        except Exception:
            pass
    return _docker_client


# ── Docker Compose (siempre subprocess — SDK no lo soporta) ───────────────


def compose_run(
    compose_file: Path,
    args: List[str],
    capture: bool = False,
    check: bool = True,
) -> subprocess.CompletedProcess:
    """Ejecuta docker compose con un compose file específico."""
    cmd = ["docker", "compose", "-f", str(compose_file)] + args

    if capture:
        return subprocess.run(cmd, capture_output=True, text=True, check=check)
    else:
        return subprocess.run(cmd, check=check)


def compose_output(compose_file: Path, args: List[str]) -> Tuple[str, int]:
    """Ejecuta docker compose y retorna (stdout, exit_code)."""
    result = compose_run(compose_file, args, capture=True, check=False)
    return result.stdout.strip(), result.returncode


def compose_passthrough(compose_file: Path, args: List[str]) -> int:
    """Ejecuta docker compose con herencia de terminal (streaming)."""
    cmd = ["docker", "compose", "-f", str(compose_file)] + args
    result = subprocess.run(cmd, check=False)
    return result.returncode


# ── Docker directo (SDK nativo cuando disponible) ─────────────────────────


def docker_run(
    args: List[str], capture: bool = True, check: bool = False
) -> subprocess.CompletedProcess:
    """Ejecuta un comando docker (fallback para cuando SDK no aplica)."""
    cmd = ["docker"] + args
    if capture:
        return subprocess.run(cmd, capture_output=True, text=True, check=check)
    else:
        return subprocess.run(cmd, check=check)


def is_service_running(compose_file: Path) -> bool:
    """Verifica si al menos un contenedor del servicio está corriendo."""
    output, rc = compose_output(compose_file, ["ps", "-q"])
    return rc == 0 and bool(output.strip())


def get_container_ids(compose_file: Path) -> List[str]:
    """Retorna IDs de contenedores activos del servicio."""
    output, rc = compose_output(compose_file, ["ps", "-q"])
    if rc != 0 or not output:
        return []
    return [cid for cid in output.splitlines() if cid.strip()]


def container_inspect(container_id: str, fmt: str) -> str:
    """Docker inspect con formato Go template (fallback subprocess)."""
    # Si el SDK está disponible, intentar con él para ciertos formatos comunes
    client = _get_client()
    if client and container_id:
        try:
            container = client.containers.get(container_id)
            # Mapear formatos Go template comunes a atributos del SDK
            if "RestartCount" in fmt:
                return str(container.attrs.get("RestartCount", 0))
            elif "State.StartedAt" in fmt:
                return container.attrs.get("State", {}).get("StartedAt", "")
            elif "State.Health" in fmt and "Status" in fmt:
                health = container.attrs.get("State", {}).get("Health", {})
                return health.get("Status", "--") if health else "--"
            elif "Name" in fmt and "State" not in fmt:
                return container.name
        except Exception:
            pass

    # Fallback: subprocess
    result = docker_run(["inspect", "--format", fmt, container_id])
    return result.stdout.strip() if result.returncode == 0 else ""


# ── Funciones SDK nativas (solo disponibles con docker SDK) ────────────────


def get_container_stats(container_id: str) -> Optional[Dict[str, Any]]:
    """Obtiene stats de un contenedor via SDK (una lectura, no stream)."""
    client = _get_client()
    if not client:
        return None
    try:
        container = client.containers.get(container_id)
        return container.stats(stream=False)
    except Exception:
        return None


def get_container_info(container_id: str) -> Optional[Dict[str, Any]]:
    """Obtiene info completa de un contenedor via SDK."""
    client = _get_client()
    if not client:
        return None
    try:
        container = client.containers.get(container_id)
        return {
            "name": container.name,
            "status": container.status,
            "image": container.image.tags[0] if container.image.tags else "?",
            "ports": container.ports,
            "restart_count": container.attrs.get("RestartCount", 0),
            "started_at": container.attrs.get("State", {}).get("StartedAt", ""),
            "health": (container.attrs.get("State", {}).get("Health", {}) or {}).get("Status", "--"),
        }
    except Exception:
        return None


def list_all_containers(running_only: bool = True) -> List[Dict[str, Any]]:
    """Lista todos los contenedores via SDK."""
    client = _get_client()
    if not client:
        return []
    try:
        filters = {"status": "running"} if running_only else {}
        containers = client.containers.list(filters=filters)
        return [
            {
                "id": c.short_id,
                "name": c.name,
                "status": c.status,
                "image": c.image.tags[0] if c.image.tags else "?",
            }
            for c in containers
        ]
    except Exception:
        return []


def get_networks() -> List[Dict[str, Any]]:
    """Lista redes Docker via SDK."""
    client = _get_client()
    if not client:
        return []
    try:
        networks = client.networks.list()
        result = []
        for net in networks:
            if net.name in ("bridge", "host", "none"):
                continue
            containers = []
            net.reload()
            for cid, info in (net.attrs.get("Containers") or {}).items():
                containers.append({
                    "name": info.get("Name", "?"),
                    "ip": info.get("IPv4Address", "").split("/")[0],
                })
            result.append({
                "name": net.name,
                "driver": net.attrs.get("Driver", "?"),
                "containers": containers,
            })
        return result
    except Exception:
        return []


def sdk_available() -> bool:
    """Retorna True si Docker SDK está disponible y conectado."""
    client = _get_client()
    if not client:
        return False
    try:
        client.ping()
        return True
    except Exception:
        return False
