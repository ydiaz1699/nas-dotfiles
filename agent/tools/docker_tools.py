"""
Herramientas para control de servicios Docker.

Permiten al agente iniciar, detener, reiniciar, actualizar
y ver logs de servicios. Las acciones destructivas requieren
confirmación del usuario.
"""

import subprocess
from pathlib import Path
from strands.tools import tool

DOCKER_BASE = Path("/docker")


def _run(cmd: str, timeout: int = 120) -> str:
    """Ejecuta un comando shell y retorna stdout + stderr."""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=timeout
        )
        output = result.stdout.strip()
        if result.returncode != 0 and result.stderr:
            output += f"\n⚠️ stderr: {result.stderr.strip()}"
        return output
    except subprocess.TimeoutExpired:
        return "ERROR: Comando excedió tiempo límite"
    except Exception as e:
        return f"ERROR: {e}"


def _find_compose(service: str) -> Path | None:
    """Busca el archivo compose de un servicio."""
    for name in [
        "docker-compose.yml", "docker-compose.yaml",
        "compose.yml", "compose.yaml",
    ]:
        path = DOCKER_BASE / service / name
        if path.exists():
            return path
    return None


def _service_exists(service: str) -> str | None:
    """Verifica que el servicio existe. Retorna error string o None."""
    if not _find_compose(service):
        disponibles = sorted(
            d.name for d in DOCKER_BASE.iterdir()
            if d.is_dir() and _find_compose(d.name)
        )
        return (
            f"ERROR: Servicio '{service}' no encontrado.\n"
            f"Disponibles: {', '.join(disponibles)}"
        )
    return None


@tool
def service_start(service_name: str) -> str:
    """Levanta (up -d) un servicio Docker.

    Ejecuta docker compose up -d para iniciar los contenedores del servicio.
    Seguro de ejecutar sin confirmación.

    Args:
        service_name: Nombre del servicio a iniciar.
                      Ejemplos: nextcloud, plex, grafana
    """
    error = _service_exists(service_name)
    if error:
        return error

    compose = _find_compose(service_name)
    output = _run(f"docker compose -f {compose} up -d")
    return f"✅ Servicio '{service_name}' iniciado.\n\n{output}"


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
    error = _service_exists(service_name)
    if error:
        return error

    compose = _find_compose(service_name)

    if confirm.lower() not in ("si", "sí", "yes"):
        # Modo dry-run
        running = _run(f"docker compose -f {compose} ps --format '{{{{.Names}}}}'")
        return (
            f"⚠️ ACCIÓN DESTRUCTIVA: Detener '{service_name}'\n\n"
            f"Contenedores que se detendrían:\n{running or '  (ninguno corriendo)'}\n\n"
            f"Para ejecutar, llama service_stop('{service_name}', confirm='si')"
        )

    output = _run(f"docker compose -f {compose} down")
    return f"🛑 Servicio '{service_name}' detenido.\n\n{output}"


@tool
def service_restart(service_name: str) -> str:
    """Reinicia un servicio Docker (restart).

    Reinicia los contenedores sin destruirlos. Seguro de ejecutar.

    Args:
        service_name: Nombre del servicio a reiniciar.
    """
    error = _service_exists(service_name)
    if error:
        return error

    compose = _find_compose(service_name)
    output = _run(f"docker compose -f {compose} restart")
    return f"🔄 Servicio '{service_name}' reiniciado.\n\n{output}"


@tool
def service_update(service_name: str) -> str:
    """Actualiza un servicio: pull de nueva imagen + recrear contenedores.

    Ejecuta pull + up -d --remove-orphans. Seguro de ejecutar
    (no pierde datos, solo actualiza la imagen).

    Args:
        service_name: Nombre del servicio a actualizar.
    """
    error = _service_exists(service_name)
    if error:
        return error

    compose = _find_compose(service_name)

    # Pull
    pull_output = _run(f"docker compose -f {compose} pull")

    # Recrear
    up_output = _run(f"docker compose -f {compose} up -d --remove-orphans")

    return (
        f"⬆️ Servicio '{service_name}' actualizado.\n\n"
        f"--- Pull ---\n{pull_output}\n\n"
        f"--- Up ---\n{up_output}"
    )


@tool
def service_logs(service_name: str, lines: int = 100) -> str:
    """Muestra las últimas líneas de logs de un servicio.

    No hace follow (no se queda esperando). Muestra las últimas N líneas.

    Args:
        service_name: Nombre del servicio.
        lines: Número de líneas a mostrar (default: 100, máximo: 500).
    """
    error = _service_exists(service_name)
    if error:
        return error

    compose = _find_compose(service_name)
    lines = min(lines, 500)  # Limitar para no desbordar

    output = _run(
        f"docker compose -f {compose} logs --tail={lines} --no-color 2>&1",
        timeout=30,
    )

    if not output:
        return f"No hay logs disponibles para '{service_name}'"

    # Truncar si es muy largo
    if len(output) > 8000:
        output = output[-8000:]
        output = "... (truncado) ...\n" + output

    return (
        f"=== LOGS: {service_name} (últimas {lines} líneas) ===\n\n"
        f"{output}"
    )
