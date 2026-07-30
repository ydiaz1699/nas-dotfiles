"""
service_manager.py — Operaciones de ciclo de vida de servicios Docker.

Centraliza: start, stop, restart, update, logs.
Los tools de docker_tools.py delegan aquí.
"""

from typing import Optional

from agent.core._result import ToolResult, Timer
from agent.tools._shell import (
    safe_run,
    find_compose,
    service_exists_or_error,
    readonly_guard,
)


class ServiceManager:
    """Gestor de ciclo de vida de servicios Docker Compose."""

    @staticmethod
    def start(service_name: str) -> ToolResult:
        """Levanta un servicio (docker compose up -d)."""
        error = service_exists_or_error(service_name)
        if error:
            return ToolResult.error(error, tool_name="service_start")

        compose = find_compose(service_name)
        with Timer() as t:
            output = safe_run(
                ["docker", "compose", "-f", str(compose), "up", "-d"],
                timeout=120,
            )

        return ToolResult.ok(
            f"✅ Servicio '{service_name}' iniciado.\n\n{output}",
            data={"service": service_name, "action": "start", "output": output},
            suggestions=[f"service_logs('{service_name}', lines=20)"],
            tool_name="service_start",
            elapsed_ms=t.elapsed_ms,
        )

    @staticmethod
    def stop(service_name: str, confirm: str = "no") -> ToolResult:
        """Detiene un servicio (docker compose down). Requiere confirmación."""
        blocked = readonly_guard("service_stop")
        if blocked:
            return ToolResult.error(blocked, tool_name="service_stop")

        error = service_exists_or_error(service_name)
        if error:
            return ToolResult.error(error, tool_name="service_stop")

        compose = find_compose(service_name)

        if confirm.lower() not in ("si", "sí", "yes"):
            running = safe_run(
                ["docker", "compose", "-f", str(compose), "ps",
                 "--format", "{{.Names}}"],
                timeout=15,
            )
            containers = running.strip().splitlines() if running.strip() else []
            return ToolResult.warn(
                f"⚠️ ACCIÓN DESTRUCTIVA: Detener '{service_name}'\n\n"
                f"Contenedores que se detendrían:\n"
                f"{running or '  (ninguno corriendo)'}\n\n"
                f"Para ejecutar, llama service_stop('{service_name}', confirm='si')",
                data={"service": service_name, "action": "stop",
                      "confirmed": False, "containers": containers},
                tool_name="service_stop",
            )

        with Timer() as t:
            output = safe_run(
                ["docker", "compose", "-f", str(compose), "down"],
                timeout=120,
            )

        return ToolResult.ok(
            f"🛑 Servicio '{service_name}' detenido.\n\n{output}",
            data={"service": service_name, "action": "stop",
                  "confirmed": True, "output": output},
            tool_name="service_stop",
            elapsed_ms=t.elapsed_ms,
        )

    @staticmethod
    def restart(service_name: str) -> ToolResult:
        """Reinicia un servicio (docker compose restart)."""
        error = service_exists_or_error(service_name)
        if error:
            return ToolResult.error(error, tool_name="service_restart")

        compose = find_compose(service_name)
        with Timer() as t:
            output = safe_run(
                ["docker", "compose", "-f", str(compose), "restart"],
                timeout=120,
            )

        return ToolResult.ok(
            f"🔄 Servicio '{service_name}' reiniciado.\n\n{output}",
            data={"service": service_name, "action": "restart", "output": output},
            suggestions=[f"service_logs('{service_name}', lines=20)",
                         f"troubleshoot('{service_name}')"],
            tool_name="service_restart",
            elapsed_ms=t.elapsed_ms,
        )

    @staticmethod
    def update(service_name: str) -> ToolResult:
        """Actualiza un servicio: pull + recrear."""
        blocked = readonly_guard("service_update")
        if blocked:
            return ToolResult.error(blocked, tool_name="service_update")

        error = service_exists_or_error(service_name)
        if error:
            return ToolResult.error(error, tool_name="service_update")

        compose = find_compose(service_name)

        with Timer() as t:
            pull_output = safe_run(
                ["docker", "compose", "-f", str(compose), "pull"],
                timeout=300,
            )
            up_output = safe_run(
                ["docker", "compose", "-f", str(compose),
                 "up", "-d", "--remove-orphans"],
                timeout=120,
            )

        return ToolResult.ok(
            f"⬆️ Servicio '{service_name}' actualizado.\n\n"
            f"--- Pull ---\n{pull_output}\n\n"
            f"--- Up ---\n{up_output}",
            data={"service": service_name, "action": "update",
                  "pull": pull_output, "up": up_output},
            suggestions=[f"service_logs('{service_name}', lines=20)"],
            tool_name="service_update",
            elapsed_ms=t.elapsed_ms,
        )

    @staticmethod
    def logs(service_name: str, lines: int = 100) -> ToolResult:
        """Muestra las últimas N líneas de logs."""
        error = service_exists_or_error(service_name)
        if error:
            return ToolResult.error(error, tool_name="service_logs")

        compose = find_compose(service_name)
        lines = min(max(lines, 1), 500)

        with Timer() as t:
            output = safe_run(
                ["docker", "compose", "-f", str(compose), "logs",
                 f"--tail={lines}", "--no-color"],
                timeout=30,
            )

        if not output:
            return ToolResult.warn(
                f"No hay logs disponibles para '{service_name}'",
                data={"service": service_name, "lines_requested": lines,
                      "lines_found": 0},
                tool_name="service_logs",
            )

        truncated = False
        if len(output) > 8000:
            output = output[-8000:]
            output = "... (truncado) ...\n" + output
            truncated = True

        return ToolResult.ok(
            f"=== LOGS: {service_name} (últimas {lines} líneas) ===\n\n{output}",
            data={"service": service_name, "lines_requested": lines,
                  "truncated": truncated, "log_size": len(output)},
            tool_name="service_logs",
            elapsed_ms=t.elapsed_ms,
        )
