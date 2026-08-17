"""
bash_bridge.py — Puente entre Python CLI y bash CLI (svc.sh).

Arquitectura definitiva (decisión #14 en ideas-decisions.md):
  - Bash CLI = fuente de verdad (toda la lógica)
  - Python CLI = interfaz bonita (Rich, InquirerPy)
  - bash_bridge = capa de comunicación entre ambos

Uso:
    from svc_py.core.bash_bridge import svc, svc_output, svc_passthrough

    # Ejecutar comando y dejar que el output vaya directo a terminal
    svc("up", "ntfy")

    # Ejecutar y capturar output (para parsear/embellecer)
    output = svc_output("health")

    # Passthrough completo (streaming, colores, interactivo)
    svc_passthrough("logs", "ntfy", "--tail=50")
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Tuple

from svc_py.config import DOCKER_BASE, NAS_DOTFILES

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURACIÓN
# ─────────────────────────────────────────────────────────────────────────────

# Ruta al script svc.sh (fuente de verdad)
SVC_SH = NAS_DOTFILES / "docker" / "cli" / "svc.sh"


def _svc_sh_path() -> Path:
    """Retorna la ruta a svc.sh, verificando que existe."""
    if SVC_SH.exists():
        return SVC_SH
    # Fallback: buscar en PATH
    from shutil import which
    found = which("svc")
    if found:
        return Path(found)
    # Último fallback: intentar ruta estándar del NAS
    default = Path("/nas-dotfiles/docker/cli/svc.sh")
    if default.exists():
        return default
    raise FileNotFoundError(
        f"No se encontró svc.sh en:\n"
        f"  - {SVC_SH}\n"
        f"  - PATH (svc)\n"
        f"  - /nas-dotfiles/docker/cli/svc.sh\n"
        f"Verificar que NAS_DOTFILES apunta al directorio correcto."
    )


def _build_env() -> dict:
    """Construye el entorno de ejecución para svc.sh."""
    env = os.environ.copy()
    env["DOCKER_BASE"] = str(DOCKER_BASE)
    env["NAS_DOTFILES"] = str(NAS_DOTFILES)
    # Forzar bash CLI (no recursión al Python CLI)
    env["NAS_CLI"] = "bash"
    return env


# ─────────────────────────────────────────────────────────────────────────────
# API PRINCIPAL
# ─────────────────────────────────────────────────────────────────────────────


def svc(command: str, *args: str, check: bool = False) -> subprocess.CompletedProcess:
    """Ejecuta un comando svc via bash (output directo a terminal).

    Equivale a: NAS_CLI=bash svc <command> [args...]

    Args:
        command: Comando svc (up, down, health, scan, etc.)
        *args: Argumentos adicionales (servicio, flags, etc.)
        check: Si True, lanza CalledProcessError si exit code != 0

    Returns:
        CompletedProcess con returncode (stdout/stderr van a terminal)

    Example:
        svc("up", "ntfy")
        svc("restart", "emqx")
        svc("catalog-sync", "--status")
    """
    cmd = ["bash", str(_svc_sh_path()), command] + list(args)
    return subprocess.run(cmd, env=_build_env(), check=check)


def svc_output(command: str, *args: str) -> Tuple[str, int]:
    """Ejecuta un comando svc y captura el output (para parsear/embellecer).

    Args:
        command: Comando svc
        *args: Argumentos adicionales

    Returns:
        Tupla (stdout_text, exit_code)

    Example:
        output, rc = svc_output("health")
        output, rc = svc_output("catalog-sync", "--status")
    """
    cmd = ["bash", str(_svc_sh_path()), command] + list(args)
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        env=_build_env(),
    )
    return result.stdout, result.returncode


def svc_passthrough(command: str, *args: str) -> int:
    """Ejecuta svc con herencia completa de terminal (streaming, colores).

    Usa execvp-like: el proceso hijo hereda stdin/stdout/stderr.
    Ideal para comandos que producen output continuo (logs, watch).

    Args:
        command: Comando svc
        *args: Argumentos adicionales

    Returns:
        Exit code del comando

    Example:
        svc_passthrough("logs", "ntfy", "--tail=50")
        svc_passthrough("watch")
    """
    cmd = ["bash", str(_svc_sh_path()), command] + list(args)
    result = subprocess.run(cmd, env=_build_env())
    return result.returncode


def svc_check(command: str, *args: str) -> bool:
    """Ejecuta svc y retorna True si exitoso (exit code 0).

    Útil para verificaciones rápidas sin necesitar el output.

    Example:
        if svc_check("health"):
            print("Todo healthy")
    """
    cmd = ["bash", str(_svc_sh_path()), command] + list(args)
    result = subprocess.run(
        cmd,
        capture_output=True,
        env=_build_env(),
    )
    return result.returncode == 0


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS DE CONVENIENCIA
# ─────────────────────────────────────────────────────────────────────────────


def svc_list_services() -> List[str]:
    """Retorna lista de servicios detectados por el bash CLI.

    Parsea output de `svc lista` (formato: estado + nombre).
    Fallback a discovery.py si svc.sh no está disponible.
    """
    try:
        output, rc = svc_output("lista")
        if rc != 0:
            return []
        # El output de svc lista tiene formato variable; extraer nombres
        services = []
        for line in output.splitlines():
            # Buscar nombres de servicio (después de emoji/indicador)
            line = line.strip()
            if not line or line.startswith("─") or line.startswith("━"):
                continue
            # Formato típico: "  🟢 ntfy" o "  🔴 emqx"
            parts = line.split()
            if len(parts) >= 2:
                # El último elemento suele ser el nombre
                candidate = parts[-1].strip()
                if candidate and not candidate.startswith(("(", "[", "─")):
                    services.append(candidate)
        return services
    except (FileNotFoundError, OSError):
        # Fallback: usar discovery de Python
        from svc_py.core.discovery import svc_list
        return svc_list()


def is_svc_sh_available() -> bool:
    """Verifica si svc.sh está disponible para ejecutar."""
    try:
        _svc_sh_path()
        return True
    except FileNotFoundError:
        return False
