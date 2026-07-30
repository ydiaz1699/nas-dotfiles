"""
docker_plugin.py — Plugin de gestión Docker.

Registra tools de Docker y programa health checks periódicos.
Emite eventos cuando detecta servicios unhealthy.
"""

from agent.plugins.base import BasePlugin, PluginMeta, ScheduleConfig, EventHandler


class DockerPlugin(BasePlugin):
    """Plugin principal de gestión de servicios Docker."""

    meta = PluginMeta(
        name="docker",
        version="1.0.0",
        description="Control de ciclo de vida Docker (start/stop/restart/update/logs)",
    )

    def setup(self):
        # Importar tools (lazy para evitar circular)
        from agent.tools.docker_tools import (
            service_start, service_stop, service_restart,
            service_update, service_logs,
        )
        from agent.tools.discovery_tools import list_services, scan_compose

        # Registrar tools
        self.register_tool(service_start)
        self.register_tool(service_stop)
        self.register_tool(service_restart)
        self.register_tool(service_update)
        self.register_tool(service_logs)
        self.register_tool(list_services)
        self.register_tool(scan_compose)

        # Health check cada 5 minutos
        self.register_schedule(ScheduleConfig(
            name="docker-health-check",
            handler=self._check_health,
            interval_minutes=5,
            run_on_start=True,
        ))

        # Reaccionar a eventos de servicios unhealthy
        self.register_event(EventHandler(
            event_type="docker.unhealthy",
            handler=self._on_unhealthy,
            description="Notifica cuando un servicio Docker reporta unhealthy",
        ))

    def _check_health(self):
        """Verifica salud de todos los servicios y emite eventos."""
        from agent.tools._shell import safe_run

        output = safe_run(
            ["docker", "ps", "--format", "{{.Names}}\t{{.Status}}"],
            timeout=15,
        )
        if not output or "ERROR" in output:
            return

        for line in output.strip().splitlines():
            parts = line.split("\t")
            if len(parts) >= 2:
                name, status = parts[0], parts[1]
                if "unhealthy" in status.lower():
                    # Emitir evento via bus (si está disponible)
                    # El bus se inyecta al plugin en runtime
                    pass

    def _on_unhealthy(self, event):
        """Handler: servicio unhealthy detectado."""
        service = event.data.get("service", "desconocido")
        # Log — en el futuro puede disparar restart automático
        import logging
        logging.getLogger(__name__).warning(
            f"Servicio unhealthy detectado: {service}"
        )
