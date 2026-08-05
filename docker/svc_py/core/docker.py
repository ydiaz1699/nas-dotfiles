"""
docker.py — Wrapper para ejecutar comandos docker compose.

Provee una interfaz unificada para invocar docker compose
con output capturado o en streaming.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Tuple


def compose_run(
    compose_file: Path,
    args: List[str],
    capture: bool = False,
    check: bool = True,
) -> subprocess.CompletedProcess:
    """Ejecuta docker compose con un compose file específico.

    Args:
        compose_file: Path al docker-compose.yml.
        args: Argumentos para docker compose (ej: ["up", "-d"]).
        capture: Si True, captura stdout/stderr. Si False, hereda terminal.
        check: Si True, lanza CalledProcessError en errores.

    Returns:
        CompletedProcess con el resultado.
    """
    cmd = ["docker", "compose", "-f", str(compose_file)] + args

    if capture:
        return subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=check,
        )
    else:
        return subprocess.run(
            cmd,
            check=check,
        )


def compose_output(
    compose_file: Path,
    args: List[str],
) -> Tuple[str, int]:
    """Ejecuta docker compose y retorna (stdout, exit_code).

    Siempre captura output. No lanza excepciones.
    """
    result = compose_run(compose_file, args, capture=True, check=False)
    return result.stdout.strip(), result.returncode


def compose_passthrough(compose_file: Path, args: List[str]) -> int:
    """Ejecuta docker compose con herencia de terminal (streaming).

    Para comandos como logs, exec, stats que necesitan TTY.

    Returns:
        Exit code del proceso.
    """
    cmd = ["docker", "compose", "-f", str(compose_file)] + args
    result = subprocess.run(cmd, check=False)
    return result.returncode


def docker_run(args: List[str], capture: bool = True, check: bool = False) -> subprocess.CompletedProcess:
    """Ejecuta un comando docker (no compose)."""
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
    """Docker inspect con formato Go template."""
    result = docker_run(["inspect", "--format", fmt, container_id])
    return result.stdout.strip() if result.returncode == 0 else ""
