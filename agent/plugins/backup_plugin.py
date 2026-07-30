"""
backup_plugin.py — Plugin de backup automático.

Registra tools de backup y programa backups periódicos
de servicios marcados como backup_critical en el catálogo.
"""

from agent.plugins.base import BasePlugin, PluginMeta, ScheduleConfig, EventHandler


class BackupPlugin(BasePlugin):
    """Plugin de gestión de backups."""

    meta = PluginMeta(
        name="backup",
        version="1.0.0",
        description="Backup automático y restore de servicios Docker",
    )

    def setup(self):
        from agent.tools.backup_tools import (
            backup_service, restore_service, list_backups,
        )

        self.register_tool(backup_service)
        self.register_tool(restore_service)
        self.register_tool(list_backups)

        # Backup diario (cada 24h = 1440 min)
        self.register_schedule(ScheduleConfig(
            name="daily-backup",
            handler=self._daily_backup,
            interval_minutes=1440,
        ))

        # Reaccionar a evento de backup solicitado via MQTT
        self.register_event(EventHandler(
            event_type="agent.command.backup",
            handler=self._on_backup_command,
            description="Backup solicitado via MQTT (nas-agent/command/backup)",
        ))

    def _daily_backup(self):
        """Backup de servicios críticos del catálogo."""
        try:
            from agent.catalog._index import load_index
            index = load_index()

            for svc_id, meta in index.get("services", {}).items():
                if meta.get("backup_critical", False):
                    from agent.core.backup_manager import BackupManager
                    BackupManager.backup(svc_id)

        except Exception:
            import logging
            logging.getLogger(__name__).error(
                "Error en backup diario", exc_info=True
            )

    def _on_backup_command(self, event):
        """Handler: backup solicitado via MQTT."""
        payload = event.data.get("payload", {})
        service = payload.get("service")
        if service:
            from agent.core.backup_manager import BackupManager
            BackupManager.backup(service)
