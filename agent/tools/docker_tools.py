"""
Herramientas para control de servicios Docker.

Permiten al agente iniciar, detener, reiniciar, actualizar
y ver logs de servicios. Las acciones destructivas requieren
confirmación del usuario.
"""

from strands.tools import tool

from agent.tools._result import ToolResult, Timer
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
        return str(ToolResult.error(error, tool_name="service_start"))

    compose = find_compose(service_name)
    with Timer() as t:
        output = safe_run(
            ["docker", "compose", "-f", str(compose), "up", "-d"],
            timeout=120,
        )

    return str(ToolResult.ok(
        f"✅ Servicio '{service_name}' iniciado.\n\n{output}",
        data={"service": service_name, "action": "start", "output": output},
        suggestions=[f"service_logs('{service_name}', lines=20)"],
        tool_name="service_start",
        elapsed_ms=t.elapsed_ms,
    ))


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
        return str(ToolResult.error(blocked, tool_name="service_stop"))

    error = service_exists_or_error(service_name)
    if error:
        return str(ToolResult.error(error, tool_name="service_stop"))

    compose = find_compose(service_name)

    if confirm.lower() not in ("si", "sí", "yes"):
        running = safe_run(
            ["docker", "compose", "-f", str(compose), "ps", "--format", "{{.Names}}"],
            timeout=15,
        )
        return str(ToolResult.warn(
            f"⚠️ ACCIÓN DESTRUCTIVA: Detener '{service_name}'\n\n"
            f"Contenedores que se detendrían:\n{running or '  (ninguno corriendo)'}\n\n"
            f"Para ejecutar, llama service_stop('{service_name}', confirm='si')",
            data={"service": service_name, "action": "stop", "confirmed": False,
                  "containers": running.strip().splitlines() if running.strip() else []},
            tool_name="service_stop",
        ))

    with Timer() as t:
        output = safe_run(
            ["docker", "compose", "-f", str(compose), "down"],
            timeout=120,
        )

    return str(ToolResult.ok(
        f"🛑 Servicio '{service_name}' detenido.\n\n{output}",
        data={"service": service_name, "action": "stop", "confirmed": True, "output": output},
        tool_name="service_stop",
        elapsed_ms=t.elapsed_ms,
    ))


@tool
def service_restart(service_name: str) -> str:
    """Reinicia un servicio Docker (restart).

    Reinicia los contenedores sin destruirlos. Seguro de ejecutar.

    Args:
        service_name: Nombre del servicio a reiniciar.
    """
    error = service_exists_or_error(service_name)
    if error:
        return str(ToolResult.error(error, tool_name="service_restart"))

    compose = find_compose(service_name)
    with Timer() as t:
        output = safe_run(
            ["docker", "compose", "-f", str(compose), "restart"],
            timeout=120,
        )

    return str(ToolResult.ok(
        f"🔄 Servicio '{service_name}' reiniciado.\n\n{output}",
        data={"service": service_name, "action": "restart", "output": output},
        suggestions=[f"service_logs('{service_name}', lines=20)",
                     f"troubleshoot('{service_name}')"],
        tool_name="service_restart",
        elapsed_ms=t.elapsed_ms,
    ))


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
        return str(ToolResult.error(blocked, tool_name="service_update"))

    error = service_exists_or_error(service_name)
    if error:
        return str(ToolResult.error(error, tool_name="service_update"))

    compose = find_compose(service_name)

    with Timer() as t:
        pull_output = safe_run(
            ["docker", "compose", "-f", str(compose), "pull"],
            timeout=300,
        )
        up_output = safe_run(
            ["docker", "compose", "-f", str(compose), "up", "-d", "--remove-orphans"],
            timeout=120,
        )

    return str(ToolResult.ok(
        f"⬆️ Servicio '{service_name}' actualizado.\n\n"
        f"--- Pull ---\n{pull_output}\n\n"
        f"--- Up ---\n{up_output}",
        data={"service": service_name, "action": "update",
              "pull": pull_output, "up": up_output},
        suggestions=[f"service_logs('{service_name}', lines=20)"],
        tool_name="service_update",
        elapsed_ms=t.elapsed_ms,
    ))


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
        return str(ToolResult.error(error, tool_name="service_logs"))

    compose = find_compose(service_name)
    lines = min(max(lines, 1), 500)

    with Timer() as t:
        output = safe_run(
            ["docker", "compose", "-f", str(compose), "logs",
             f"--tail={lines}", "--no-color"],
            timeout=30,
        )

    if not output:
        return str(ToolResult.warn(
            f"No hay logs disponibles para '{service_name}'",
            data={"service": service_name, "lines_requested": lines, "lines_found": 0},
            tool_name="service_logs",
        ))

    # Truncar si es muy largo
    truncated = False
    if len(output) > 8000:
        output = output[-8000:]
        output = "... (truncado) ...\n" + output
        truncated = True

    return str(ToolResult.ok(
        f"=== LOGS: {service_name} (últimas {lines} líneas) ===\n\n{output}",
        data={"service": service_name, "lines_requested": lines,
              "truncated": truncated, "log_size": len(output)},
        tool_name="service_logs",
        elapsed_ms=t.elapsed_ms,
    ))
