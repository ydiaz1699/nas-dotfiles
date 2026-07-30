"""
bus.py — Event bus interno del agente.

Patrón pub/sub en memoria: los productores emiten eventos,
los consumers (plugins, handlers) reaccionan.

Thread-safe para uso con el scheduler y MQTT listener.
"""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class Event:
    """Evento emitido en el bus.

    Attributes:
        type: Tipo de evento (ej. "mqtt.message", "docker.unhealthy",
              "schedule.backup", "system.disk_warning").
        data: Payload del evento (dict libre).
        source: Origen del evento (ej. "mqtt", "scheduler", "cli").
        timestamp: Unix timestamp de cuándo se emitió.
    """
    type: str
    data: Dict[str, Any] = field(default_factory=dict)
    source: str = ""
    timestamp: float = field(default_factory=time.time)

    def __repr__(self) -> str:
        return f"<Event:{self.type} from={self.source} keys={list(self.data.keys())}>"


# Type alias para handlers
EventCallback = Callable[[Event], Any]


class EventBus:
    """Bus de eventos pub/sub en memoria.

    Thread-safe. Soporta:
    - Subscripción por tipo exacto ("docker.unhealthy")
    - Subscripción con wildcard ("docker.*")
    - Subscripción global ("*")
    - Historial de últimos N eventos
    - Emisión síncrona (handlers se ejecutan en el hilo del emisor)

    Uso:
        bus = EventBus()
        bus.on("docker.unhealthy", my_handler)
        bus.on("docker.*", my_wildcard_handler)
        bus.emit("docker.unhealthy", {"service": "emqx"})
    """

    def __init__(self, history_size: int = 100):
        self._handlers: Dict[str, List[EventCallback]] = {}
        self._history: List[Event] = []
        self._history_size = history_size
        self._lock = threading.Lock()
        self._event_count = 0

    def on(self, event_type: str, handler: EventCallback) -> None:
        """Registra un handler para un tipo de evento.

        Args:
            event_type: Tipo de evento. Soporta "*" para todos,
                       o "prefix.*" para wildcard por prefijo.
            handler: Función que recibe un Event.
        """
        with self._lock:
            if event_type not in self._handlers:
                self._handlers[event_type] = []
            self._handlers[event_type].append(handler)

    def off(self, event_type: str, handler: EventCallback) -> bool:
        """Desregistra un handler.

        Returns:
            True si se encontró y eliminó.
        """
        with self._lock:
            handlers = self._handlers.get(event_type, [])
            if handler in handlers:
                handlers.remove(handler)
                return True
            return False

    def emit(self, event_type: str, data: Optional[Dict[str, Any]] = None,
             source: str = "") -> Event:
        """Emite un evento y ejecuta todos los handlers matching.

        Args:
            event_type: Tipo del evento.
            data: Payload opcional.
            source: Origen del evento.

        Returns:
            El Event emitido.
        """
        event = Event(type=event_type, data=data or {}, source=source)

        with self._lock:
            self._event_count += 1
            self._history.append(event)
            if len(self._history) > self._history_size:
                self._history = self._history[-self._history_size:]

            # Recolectar handlers que matchean
            matching: List[EventCallback] = []

            # Handlers exactos
            matching.extend(self._handlers.get(event_type, []))

            # Handlers wildcard (prefix.*)
            prefix = event_type.rsplit(".", 1)[0] if "." in event_type else ""
            if prefix:
                matching.extend(self._handlers.get(f"{prefix}.*", []))

            # Handler global
            matching.extend(self._handlers.get("*", []))

        # Ejecutar handlers fuera del lock
        for handler in matching:
            try:
                handler(event)
            except Exception as e:
                logger.error(
                    f"Error en handler para '{event_type}': {e}",
                    exc_info=True,
                )

        return event

    @property
    def event_count(self) -> int:
        """Total de eventos emitidos."""
        return self._event_count

    @property
    def history(self) -> List[Event]:
        """Últimos N eventos emitidos."""
        with self._lock:
            return list(self._history)

    def last_events(self, n: int = 10, event_type: Optional[str] = None) -> List[Event]:
        """Retorna los últimos N eventos, opcionalmente filtrados por tipo."""
        with self._lock:
            if event_type:
                filtered = [e for e in self._history if e.type == event_type]
                return filtered[-n:]
            return self._history[-n:]

    def registered_types(self) -> List[str]:
        """Lista tipos de eventos con handlers registrados."""
        with self._lock:
            return list(self._handlers.keys())

    def clear(self) -> None:
        """Limpia todos los handlers y historial."""
        with self._lock:
            self._handlers.clear()
            self._history.clear()
            self._event_count = 0
