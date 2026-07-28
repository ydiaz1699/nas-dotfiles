"""
_shell.py — Módulo común de ejecución segura de comandos.

Centraliza la ejecución de subprocesos con:
- shell=False (previene inyección de comandos)
- Validación de nombres de servicio (previene path traversal)
- Modo read-only (bloquea acciones destructivas)

Todos los agent/tools/*.py deben usar safe_run() y validate_service_name()
de este módulo en vez de implementar su propio _run() con shell=True.
"""

import os
import re
import subprocess
from pathlib import Path
from typing import Optional

# ─────────────────────────────────────────────────────────────────────────────
# Constantes
# ─────────────────────────────────────────────────────────────────────────────

DOCKER_BASE = Path("/docker")
BACKUP_DIR = Path("/docker/backups")

# Regex para nombres de servicio válidos: letras, números, guión, punto, guión bajo
# Mínimo 1 carácter, máximo 64, debe empezar con alfanumérico
_SERVICE_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")

# Nombres reservados que no pueden ser servicios
_RESERVED_NAMES = frozenset({
    ".", "..", "cli", "backups", "lost+found",
    "proc", "sys", "dev", "tmp", "etc", "root",
})


# ─────────────────────────────────────────────────────────────────────────────
# Validación de service_name
# ─────────────────────────────────────────────────────────────────────────────


class InvalidServiceName(ValueError):
    """Nombre de servicio no válido o potencialmente peligroso."""
    pass


def validate_service_name(name: str) -> str:
    """Valida que un nombre de servicio sea seguro.

    Reglas:
    - Solo letras minúsculas, números, guión (-), punto (.), guión bajo (_)
    - Debe empezar con letra o número
    - Máximo 64 caracteres
    - No puede contener '..' (path traversal)
    - No puede contener '/' ni '\\'
    - No puede ser un nombre reservado

    Args:
        name: Nombre del servicio a validar.

    Returns:
        str: El nombre validado (strip aplicado).

    Raises:
        InvalidServiceName: Si el nombre no cumple las reglas.
    """
    if not name or not isinstance(name, str):
        raise InvalidServiceName("Nombre de servicio vacío o inválido")

    name = name.strip()

    # Bloquear path traversal explícito
    if ".." in name or "/" in name or "\\" in name:
        raise InvalidServiceName(
            f"Nombre '{name}' contiene caracteres de path traversal (../ o \\)"
        )

    # Bloquear nombres reservados
    if name.lower() in _RESERVED_NAMES:
        raise InvalidServiceName(
            f"Nombre '{name}' es reservado y no puede usarse como servicio"
        )

    # Validar contra regex
    if not _SERVICE_NAME_RE.match(name.lower()):
        raise InvalidServiceName(
            f"Nombre '{name}' no es válido. "
            f"Solo se permiten: letras minúsculas, números, guión (-), "
            f"punto (.) y guión bajo (_). Debe empezar con alfanumérico. "
            f"Máximo 64 caracteres."
        )

    return name


def validated_service_path(name: str) -> Path:
    """Valida el nombre y retorna la ruta completa al directorio del servicio.

    Args:
        name: Nombre del servicio.

    Returns:
        Path: DOCKER_BASE / name (validado y resuelto).

    Raises:
        InvalidServiceName: Si el nombre no es válido o la ruta resultante
                           escapa de DOCKER_BASE.
    """
    name = validate_service_name(name)
    svc_path = (DOCKER_BASE / name).resolve()

    # Verificación final: la ruta resuelta debe estar dentro de DOCKER_BASE
    try:
        svc_path.relative_to(DOCKER_BASE.resolve())
    except ValueError:
        raise InvalidServiceName(
            f"La ruta resuelta '{svc_path}' escapa de {DOCKER_BASE}. "
            f"Posible path traversal."
        )

    return svc_path


# ─────────────────────────────────────────────────────────────────────────────
# Ejecución segura de comandos (shell=False)
# ─────────────────────────────────────────────────────────────────────────────


def safe_run(
    args: list[str],
    timeout: int = 120,
    check: bool = False,
    cwd: Optional[Path] = None,
) -> str:
    """Ejecuta un comando de forma segura SIN shell=True.

    En modo dry-run (NAS_AGENT_DRYRUN=1), NO ejecuta el comando —
    solo retorna una descripción de lo que se habría ejecutado.

    Args:
        args: Lista de argumentos del comando.
              Ejemplo: ["docker", "compose", "-f", "/docker/svc/compose.yml", "ps"]
        timeout: Timeout en segundos (default: 120).
        check: Si True, lanza excepción en returncode != 0.
        cwd: Directorio de trabajo (opcional).

    Returns:
        str: stdout + stderr combinados (stderr solo si hay error).
             En dry-run: "[DRY-RUN] ..." con el comando que se habría ejecutado.
    """
    # Hard dry-run guard: interceptar ANTES de ejecutar
    if is_dryrun():
        cmd_str = " ".join(args)
        cwd_info = f" (en {cwd})" if cwd else ""
        return f"[DRY-RUN] Se ejecutaría:{cwd_info}\n  $ {cmd_str}"

    try:
        result = subprocess.run(
            args,
            shell=False,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd,
        )
        output = result.stdout.strip()
        if result.returncode != 0 and result.stderr:
            output += f"\n⚠️ {result.stderr.strip()}"
        if check and result.returncode != 0:
            raise subprocess.CalledProcessError(
                result.returncode, args, result.stdout, result.stderr
            )
        return output
    except subprocess.TimeoutExpired:
        return f"ERROR: Comando excedió el timeout de {timeout}s"
    except subprocess.CalledProcessError:
        raise
    except Exception as e:
        return f"ERROR: {e}"


# ─────────────────────────────────────────────────────────────────────────────
# Helpers comunes
# ─────────────────────────────────────────────────────────────────────────────


def find_compose(service: str) -> Optional[Path]:
    """Busca el archivo compose de un servicio (validando el nombre).

    Args:
        service: Nombre del servicio.

    Returns:
        Path al archivo compose, o None si no se encuentra.

    Raises:
        InvalidServiceName: Si el nombre no es válido.
    """
    svc_path = validated_service_path(service)

    for name in [
        "compose.yml", "compose.yaml",
        "docker-compose.yml", "docker-compose.yaml",
    ]:
        path = svc_path / name
        if path.exists():
            return path
    return None


def service_exists_or_error(service: str) -> Optional[str]:
    """Verifica que un servicio exista. Retorna error string o None.

    Args:
        service: Nombre del servicio.

    Returns:
        None si existe, string con error si no.
    """
    try:
        validate_service_name(service)
    except InvalidServiceName as e:
        return f"ERROR: {e}"

    if not find_compose(service):
        try:
            disponibles = sorted(
                d.name for d in DOCKER_BASE.iterdir()
                if d.is_dir() and not d.name.startswith(".")
                and d.name not in _RESERVED_NAMES
                and find_compose(d.name) is not None
            )
        except Exception:
            disponibles = []

        return (
            f"ERROR: Servicio '{service}' no encontrado en {DOCKER_BASE}/\n"
            f"Disponibles: {', '.join(disponibles[:20])}"
        )
    return None


# ─────────────────────────────────────────────────────────────────────────────
# Read-only mode
# ─────────────────────────────────────────────────────────────────────────────

# Tools marcadas como destructivas (requieren que readonly esté OFF)
_DESTRUCTIVE_TOOLS = frozenset({
    "service_stop",
    "service_update",
    "create_service",
    "restore_service",
    "backup_service",
})


def is_readonly() -> bool:
    """Retorna True si el agente está en modo read-only.

    Se activa con: export NAS_AGENT_READONLY=1
    """
    return os.environ.get("NAS_AGENT_READONLY", "0").strip() in ("1", "true", "yes")


def is_dryrun() -> bool:
    """Retorna True si el agente está en modo dry-run.

    Se activa con: export NAS_AGENT_DRYRUN=1
    En este modo, safe_run() NO ejecuta comandos — solo describe qué haría.
    """
    return os.environ.get("NAS_AGENT_DRYRUN", "0").strip() in ("1", "true", "yes")


def readonly_guard(tool_name: str) -> Optional[str]:
    """Si estamos en modo readonly y la tool es destructiva, bloquea.

    Args:
        tool_name: Nombre de la tool que se intenta ejecutar.

    Returns:
        None si está permitido, string con error si está bloqueado.
    """
    if is_readonly() and tool_name in _DESTRUCTIVE_TOOLS:
        return (
            f"🔒 BLOQUEADO: '{tool_name}' no se puede ejecutar en modo read-only.\n\n"
            f"El agente está en modo solo lectura (NAS_AGENT_READONLY=1).\n"
            f"Para permitir acciones destructivas:\n"
            f"  export NAS_AGENT_READONLY=0\n"
            f"  # o simplemente: unset NAS_AGENT_READONLY"
        )
    return None
