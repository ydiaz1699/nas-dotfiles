"""
notification_plugin.py — Plugin de notificaciones via ntfy para el agente NAS.

Envía alertas push cuando ocurren eventos relevantes:
- Servicio Docker caído (health check fallido)
- Backup completado/fallido
- Actualización de servicios
- Eventos del sistema (disco, SSH, etc.)

Configuración:
    ntfy_url: URL del servidor ntfy (default: http://localhost:8090)
    enabled_topics: Lista de topics habilitados
    min_priority: Prioridad mínima para enviar (default: "default")
"""

from __future__ import annotations

import subprocess
from typing import Any, Dict, Optional

from agent.plugins.base import (
    BasePlugin,
    EventHandler,
    PluginMeta,
    ScheduleConfig,
)


class NotificationPlugin(BasePlugin):
    """Plugin de notificaciones push via ntfy."""

    meta = PluginMeta(
        name="notification",
        version="1.0.0",
        description="Envía notificaciones push via ntfy al detectar eventos",
        author="ydiaz1699",
        dependencies=[],
    )

    # Configuración por defecto
    DEFAULT_NTFY_URL = "http://localhost:8090"
    DEFAULT_TOPICS = ["docker", "backups", "system", "usb", "nas-alerts"]
    TIMEOUT_SECONDS = 5

    def __init__(self):
        super().__init__()
        self._ntfy_url: str = self.DEFAULT_NTFY_URL
        self._enabled_topics: list = self.DEFAULT_TOPICS.copy()

    def setup(self) -> None:
        """Registrar event handlers y schedules."""
        # Events
        self.register_event(EventHandler(
            event_type="docker.unhealthy",
            handler=self.on_service_unhealthy,
            description="Notificar cuando un servicio Docker falla el healthcheck",
        ))
        self.register_event(EventHandler(
            event_type="docker.down",
            handler=self.on_service_down,
            description="Notificar cuando un servicio Docker se detiene inesperadamente",
        ))
        self.register_event(EventHandler(
            event_type="backup.complete",
            handler=self.on_backup_complete,
            description="Notificar cuando un backup se completa exitosamente",
        ))
        self.register_event(EventHandler(
            event_type="backup.failed",
            handler=self.on_backup_failed,
            description="Notificar cuando un backup falla",
        ))
        self.register_event(EventHandler(
            event_type="docker.updated",
            handler=self.on_service_updated,
            description="Notificar cuando un servicio es actualizado",
        ))
        self.register_event(EventHandler(
            event_type="system.alert",
            handler=self.on_system_alert,
            description="Reenviar alertas del sistema a ntfy",
        ))

        # Tools (invocables por el agente)
        self.register_tool(self.send_notification)
        self.register_tool(self.test_connection)

    def configure(self, config: Dict[str, Any]) -> None:
        """Configurar el plugin con valores del usuario.

        Args:
            config: Dict con claves opcionales:
                - ntfy_url: URL del servidor ntfy
                - enabled_topics: Lista de topics habilitados
        """
        self._ntfy_url = config.get("ntfy_url", self.DEFAULT_NTFY_URL)
        self._enabled_topics = config.get("enabled_topics", self.DEFAULT_TOPICS.copy())

    # ══════════════════════════════════════════════════════════════
    # FUNCIÓN PRINCIPAL DE ENVÍO
    # ══════════════════════════════════════════════════════════════

    def ntfy_send(
        self,
        topic: str = "nas-alerts",
        title: str = "",
        message: str = "",
        priority: str = "default",
        tags: str = "",
    ) -> bool:
        """Enviar notificación via ntfy.

        Args:
            topic: Topic/canal de la notificación
            title: Título de la notificación
            message: Cuerpo del mensaje
            priority: min|low|default|high|urgent
            tags: Tags separados por coma (se muestran como emojis)

        Returns:
            True si se envió correctamente, False si falló
        """
        if not message:
            return False

        if topic not in self._enabled_topics and topic != "nas-alerts":
            return False

        cmd = ["curl", "-s", "--max-time", str(self.TIMEOUT_SECONDS)]

        if title:
            cmd += ["-H", f"Title: {title}"]
        if priority and priority != "default":
            cmd += ["-H", f"Priority: {priority}"]
        if tags:
            cmd += ["-H", f"Tags: {tags}"]

        cmd += ["-d", message, f"{self._ntfy_url}/{topic}"]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.TIMEOUT_SECONDS + 2,
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            return False

    # ══════════════════════════════════════════════════════════════
    # EVENT HANDLERS
    # ══════════════════════════════════════════════════════════════

    def on_service_unhealthy(self, event: Dict[str, Any]) -> None:
        """Handler: servicio reporta healthcheck unhealthy."""
        service = event.get("service_name", "unknown")
        details = event.get("details", "no responde al healthcheck")
        self.ntfy_send(
            topic="docker",
            title=f"🏥 Health check fallido: {service}",
            message=f"El servicio {service} está unhealthy: {details}",
            priority="high",
            tags="warning,hospital",
        )

    def on_service_down(self, event: Dict[str, Any]) -> None:
        """Handler: servicio Docker detectado como caído."""
        service = event.get("service_name", "unknown")
        since = event.get("since", "")
        self.ntfy_send(
            topic="docker",
            title=f"⚠️ {service} DOWN",
            message=f"El servicio {service} no responde{f' desde {since}' if since else ''}",
            priority="high",
            tags="warning,whale",
        )

    def on_backup_complete(self, event: Dict[str, Any]) -> None:
        """Handler: backup completado exitosamente."""
        service = event.get("service_name", "unknown")
        size_mb = event.get("size_mb", "")
        duration = event.get("duration", "")
        msg = f"Backup de {service} completado"
        if size_mb:
            msg += f" ({size_mb}MB)"
        if duration:
            msg += f" en {duration}"
        self.ntfy_send(
            topic="backups",
            title=f"✅ Backup {service}",
            message=msg,
            priority="default",
            tags="floppy_disk,white_check_mark",
        )

    def on_backup_failed(self, event: Dict[str, Any]) -> None:
        """Handler: backup fallido."""
        service = event.get("service_name", "unknown")
        error = event.get("error", "error desconocido")
        self.ntfy_send(
            topic="backups",
            title=f"❌ Backup fallido: {service}",
            message=f"Error: {error}",
            priority="high",
            tags="x,floppy_disk",
        )

    def on_service_updated(self, event: Dict[str, Any]) -> None:
        """Handler: servicio actualizado exitosamente."""
        service = event.get("service_name", "unknown")
        old_version = event.get("old_version", "")
        new_version = event.get("new_version", "")
        msg = f"{service} actualizado"
        if old_version and new_version:
            msg += f" ({old_version} → {new_version})"
        self.ntfy_send(
            topic="docker",
            title=f"🆙 {service} actualizado",
            message=msg,
            priority="default",
            tags="whale,up",
        )

    def on_system_alert(self, event: Dict[str, Any]) -> None:
        """Handler: alerta del sistema (SMART, SSH, disco)."""
        title = event.get("title", "Alerta del sistema")
        message = event.get("message", "")
        priority = event.get("priority", "high")
        self.ntfy_send(
            topic="system",
            title=title,
            message=message,
            priority=priority,
            tags="rotating_light",
        )

    # ══════════════════════════════════════════════════════════════
    # TOOLS (invocables por el agente)
    # ══════════════════════════════════════════════════════════════

    def send_notification(
        self,
        topic: str = "nas-alerts",
        title: str = "",
        message: str = "",
        priority: str = "default",
        tags: str = "",
    ) -> Dict[str, Any]:
        """Tool: enviar notificación manual via ntfy.

        Uso del agente: send_notification(topic="docker", title="Test", message="OK")
        """
        success = self.ntfy_send(topic, title, message, priority, tags)
        return {
            "success": success,
            "topic": topic,
            "ntfy_url": self._ntfy_url,
        }

    def test_connection(self) -> Dict[str, Any]:
        """Tool: verificar conexión con el servidor ntfy.

        Envía un mensaje de prueba al topic nas-alerts.
        """
        success = self.ntfy_send(
            topic="nas-alerts",
            title="🧪 Test de conexión",
            message="El agente NAS puede enviar notificaciones correctamente.",
            priority="min",
            tags="test_tube",
        )
        return {
            "connected": success,
            "ntfy_url": self._ntfy_url,
            "message": "Conexión OK" if success else "No se pudo conectar a ntfy",
        }
