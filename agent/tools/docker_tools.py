"""
Herramientas para control de servicios Docker.

Permiten al agente iniciar, detener, reiniciar, actualizar
y ver logs de servicios. Las acciones destructivas requieren
confirmación del usuario.
"""

from strands.tools import tool

from agent.tools._shell import (
    safe_run,
    find_compose,
    service_exists_or_error,
    readonly_guard,
)


@tool
def service_start(service_name: str) -> str:
    """Levanta (up -d) un servicio Docker.

    Ejecuta docker compose up -d para iniciar los contenedores del servicio.
    Seguro de ejecutar sin confirmación.

    Args:
        service_name: Nombre del servicio a iniciar.
                      Ejemplos: nextcloud, plex, grafana
    """
    error = service_exists_or_error(service_name)
    if error:
        return error

    compose = find_compose(service_name)
    output = safe_run(
        ["docker", "compose", "-f", str(compose), "up", "-d"],
        timeout=120,
    )
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
    # Read-only guard
    blocked = readonly_guard("service_stop")
    if blocked:
        return blocked

    error = service_exists_or_error(service_name)
    if error:
        return error

    compose = find_compose(service_name)

    if confirm.lower() not in ("si", "sí", "yes"):
        # Modo dry-run
        running = safe_run(
            ["docker", "compose", "-f", str(compose), "ps", "--format", "{{.Names}}"],
            timeout=15,
        )
        return (
            f"⚠️ ACCIÓN DESTRUCTIVA: Detener '{service_name}'\n\n"
            f"Contenedores que se detendrían:\n{running or '  (ninguno corriendo)'}\n\n"
            f"Para ejecutar, llama service_stop('{service_name}', confirm='si')"
        )

    output = safe_run(
        ["docker", "compose", "-f", str(compose), "down"],
        timeout=120,
    )
    return f"🛑 Servicio '{service_name}' detenido.\n\n{output}"


@tool
def service_restart(service_name: str) -> str:
    """Reinicia un servicio Docker (restart).

    Reinicia los contenedores sin destruirlos. Seguro de ejecutar.

    Args:
        service_name: Nombre del servicio a reiniciar.
    """
    error = service_exists_or_error(service_name)
    if error:
        return error

    compose = find_compose(service_name)
    output = safe_run(
        ["docker", "compose", "-f", str(compose), "restart"],
        timeout=120,
    )
    return f"🔄 Servicio '{service_name}' reiniciado.\n\n{output}"


@tool
def service_update(service_name: str) -> str:
    """Actualiza un servicio: pull de nueva imagen + recrear contenedores.

    Ejecuta pull + up -d --remove-orphans. Seguro de ejecutar
    (no pierde datos, solo actualiza la imagen).

    Args:
        service_name: Nombre del servicio a actualizar.
    """
    # Read-only guard
    blocked = readonly_guard("service_update")
    if blocked:
        return blocked

    error = service_exists_or_error(service_name)
    if error:
        return error

    compose = find_compose(service_name)

    # Pull
    pull_output = safe_run(
        ["docker", "compose", "-f", str(compose), "pull"],
        timeout=300,
    )

    # Recrear
    up_output = safe_run(
        ["docker", "compose", "-f", str(compose), "up", "-d", "--remove-orphans"],
        timeout=120,
    )

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
    error = service_exists_or_error(service_name)
    if error:
        return error

    compose = find_compose(service_name)
    lines = min(max(lines, 1), 500)  # Limitar rango

    output = safe_run(
        ["docker", "compose", "-f", str(compose), "logs",
         f"--tail={lines}", "--no-color"],
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
