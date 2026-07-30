"""
base.py — Clase base para plugins del agente NAS.

Cada plugin hereda de BasePlugin y define:
- metadata (nombre, versión, descripción)
- tools (funciones que el agente puede invocar)
- event_handlers (callbacks para eventos del bus)
- schedules (tareas periódicas)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


@dataclass
class ScheduleConfig:
    """Configuración de una tarea programada.

    Attributes:
        name: Nombre único de la tarea.
        handler: Función a ejecutar.
        interval_minutes: Intervalo en minutos entre ejecuciones.
        enabled: Si la tarea está activa.
        run_on_start: Si debe ejecutarse inmediatamente al cargar el plugin.
    """
    name: str
    handler: Callable[[], Any]
    interval_minutes: int = 60
    enabled: bool = True
    run_on_start: bool = False


@dataclass
class EventHandler:
    """Handler de un evento del bus.

    Attributes:
        event_type: Tipo de evento que maneja (ej. "mqtt.message", "docker.health").
        handler: Función callback. Recibe el evento como dict.
        topic_filter: Filtro MQTT opcional (ej. "homeassistant/+/status").
        description: Descripción del handler.
    """
    event_type: str
    handler: Callable[[Dict[str, Any]], Any]
    topic_filter: Optional[str] = None
    description: str = ""


@dataclass
class PluginMeta:
    """Metadata de un plugin.

    Attributes:
        name: Nombre corto del plugin (ej. "docker", "mqtt", "backup").
        version: Versión del plugin.
        description: Descripción de qué hace.
        author: Autor (opcional).
        dependencies: Plugins requeridos (por nombre).
    """
    name: str
    version: str = "1.0.0"
    description: str = ""
    author: str = ""
    dependencies: List[str] = field(default_factory=list)


class BasePlugin:
    """Clase base para plugins del agente NAS.

    Subclases deben:
    1. Definir `meta` con PluginMeta
    2. Implementar `setup()` para registrar tools/events/schedules
    3. Opcionalmente implementar `teardown()` para limpieza

    Ejemplo:
        class DockerPlugin(BasePlugin):
            meta = PluginMeta(name="docker", description="Control Docker")

            def setup(self):
                self.register_tool(service_restart)
                self.register_event(EventHandler(
                    event_type="docker.unhealthy",
                    handler=self.on_unhealthy,
                ))
                self.register_schedule(ScheduleConfig(
                    name="health-check",
                    handler=self.check_health,
                    interval_minutes=5,
                ))

            def on_unhealthy(self, event):
                ...

            def check_health(self):
                ...
    """

    meta: PluginMeta = PluginMeta(name="unnamed")

    def __init__(self):
        self._tools: List[Callable] = []
        self._event_handlers: List[EventHandler] = []
        self._schedules: List[ScheduleConfig] = []
        self._enabled: bool = True

    @property
    def name(self) -> str:
        return self.meta.name

    @property
    def enabled(self) -> bool:
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool):
        self._enabled = value

    @property
    def tools(self) -> List[Callable]:
        """Tools registradas por este plugin."""
        return self._tools

    @property
    def event_handlers(self) -> List[EventHandler]:
        """Event handlers registrados."""
        return self._event_handlers

    @property
    def schedules(self) -> List[ScheduleConfig]:
        """Tareas programadas registradas."""
        return self._schedules

    def register_tool(self, tool_fn: Callable) -> None:
        """Registra una tool para el agente."""
        self._tools.append(tool_fn)

    def register_event(self, handler: EventHandler) -> None:
        """Registra un handler de evento."""
        self._event_handlers.append(handler)

    def register_schedule(self, config: ScheduleConfig) -> None:
        """Registra una tarea programada."""
        self._schedules.append(config)

    def setup(self) -> None:
        """Inicializa el plugin. Subclases deben override."""
        pass

    def teardown(self) -> None:
        """Limpieza al descargar el plugin. Override opcional."""
        pass

    def __repr__(self) -> str:
        return (
            f"<Plugin:{self.name} v{self.meta.version} "
            f"tools={len(self._tools)} events={len(self._event_handlers)} "
            f"schedules={len(self._schedules)}>"
        )
