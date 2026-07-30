"""
network_plugin.py — Plugin de monitoreo de red.

Registra tools de red y programa escaneos periódicos de puertos.
"""

from agent.plugins.base import BasePlugin, PluginMeta, ScheduleConfig


class NetworkPlugin(BasePlugin):
    """Plugin de monitoreo y diagnóstico de red."""

    meta = PluginMeta(
        name="network",
        version="1.0.0",
        description="Monitoreo de red, puertos y conflictos",
    )

    def setup(self):
        from agent.tools.system_tools import scan_ports, network_info
        from agent.tools.diagnostic_tools import port_conflicts

        self.register_tool(scan_ports)
        self.register_tool(network_info)
        self.register_tool(port_conflicts)

        # Escaneo de puertos cada 15 minutos
        self.register_schedule(ScheduleConfig(
            name="port-scan",
            handler=self._scan_ports,
            interval_minutes=15,
        ))

    def _scan_ports(self):
        """Escanea puertos y actualiza cache."""
        from agent.tools._shell import safe_run

        output = safe_run(["ss", "-tnlp"], timeout=10)
        # En el futuro: parsear y guardar en cache
        # cache.set("ports.tcp", parsed_ports)
