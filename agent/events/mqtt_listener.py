"""
mqtt_listener.py — Listener MQTT que conecta el broker al event bus.

Se conecta al broker MQTT (EMQX por defecto), se suscribe a topics
configurados, y traduce mensajes MQTT a eventos del bus interno.

Pipeline:
    MQTT broker → MQTTListener → Event("mqtt.message", {...}) → EventBus → handlers

Requisitos:
    pip install paho-mqtt

Configuración via env vars o config:
    NAS_MQTT_HOST: Host del broker (default: localhost)
    NAS_MQTT_PORT: Puerto (default: 1883)
    NAS_MQTT_USER: Usuario (opcional)
    NAS_MQTT_PASS: Password (opcional)
    NAS_MQTT_TOPICS: Topics separados por ; (default: nas-agent/#)
"""

from __future__ import annotations

import json
import logging
import os
import threading
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class MQTTListener:
    """Listener MQTT que traduce mensajes a eventos del bus.

    Uso:
        from agent.events import EventBus, MQTTListener

        bus = EventBus()
        mqtt = MQTTListener(bus)
        mqtt.start()  # Conecta y escucha en background

        # O con config explícita:
        mqtt = MQTTListener(
            bus,
            host="emqx.local",
            port=1883,
            topics=["homeassistant/+/status", "nas-agent/#"],
        )
        mqtt.start()
    """

    def __init__(
        self,
        event_bus: Any,  # EventBus — Any para evitar circular import
        host: Optional[str] = None,
        port: Optional[int] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        topics: Optional[List[str]] = None,
        client_id: str = "nas-agent",
    ):
        self._bus = event_bus
        self._host = host or os.environ.get("NAS_MQTT_HOST", "localhost")
        self._port = port or int(os.environ.get("NAS_MQTT_PORT", "1883"))
        self._username = username or os.environ.get("NAS_MQTT_USER", "")
        self._password = password or os.environ.get("NAS_MQTT_PASS", "")
        self._client_id = client_id
        self._client = None
        self._thread: Optional[threading.Thread] = None
        self._running = False

        # Topics a suscribir
        topics_env = os.environ.get("NAS_MQTT_TOPICS", "nas-agent/#")
        self._topics = topics or [t.strip() for t in topics_env.split(";") if t.strip()]

        # Topic-to-event mappers
        self._mappers: List[Callable[[str, Dict[str, Any]], Optional[str]]] = [
            self._default_mapper
        ]

    def add_mapper(self, mapper: Callable[[str, Dict[str, Any]], Optional[str]]) -> None:
        """Agrega un mapper de topic→event_type.

        El mapper recibe (topic, payload) y retorna el event_type
        o None si no debe emitirse evento.
        """
        self._mappers.insert(0, mapper)  # Prioridad: últimos agregados primero

    def start(self) -> bool:
        """Inicia la conexión MQTT en un hilo background.

        Returns:
            True si se inició correctamente, False si paho-mqtt no está disponible.
        """
        try:
            import paho.mqtt.client as mqtt
        except ImportError:
            logger.warning(
                "paho-mqtt no instalado. MQTT listener desactivado. "
                "Instalar con: pip install paho-mqtt"
            )
            return False

        self._client = mqtt.Client(
            client_id=self._client_id,
            protocol=mqtt.MQTTv311,
        )

        if self._username:
            self._client.username_pw_set(self._username, self._password)

        self._client.on_connect = self._on_connect
        self._client.on_message = self._on_message
        self._client.on_disconnect = self._on_disconnect

        self._running = True
        self._thread = threading.Thread(
            target=self._run_loop,
            name="mqtt-listener",
            daemon=True,
        )
        self._thread.start()

        logger.info(
            f"MQTT Listener iniciado: {self._host}:{self._port} "
            f"topics={self._topics}"
        )
        return True

    def stop(self) -> None:
        """Detiene la conexión MQTT."""
        self._running = False
        if self._client:
            self._client.disconnect()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)
        logger.info("MQTT Listener detenido.")

    @property
    def connected(self) -> bool:
        """True si está conectado al broker."""
        return self._client is not None and self._client.is_connected()

    def _run_loop(self) -> None:
        """Loop principal del MQTT client (corre en hilo daemon)."""
        try:
            self._client.connect(self._host, self._port, keepalive=60)
            self._client.loop_forever()
        except Exception as e:
            if self._running:
                logger.error(f"Error en MQTT loop: {e}")
                self._bus.emit("mqtt.error", {"error": str(e)}, source="mqtt")

    def _on_connect(self, client, userdata, flags, rc) -> None:
        """Callback de conexión MQTT."""
        if rc == 0:
            logger.info(f"MQTT conectado a {self._host}:{self._port}")
            # Suscribir a todos los topics configurados
            for topic in self._topics:
                client.subscribe(topic, qos=1)
                logger.debug(f"  Suscrito a: {topic}")

            self._bus.emit(
                "mqtt.connected",
                {"host": self._host, "topics": self._topics},
                source="mqtt",
            )
        else:
            logger.error(f"MQTT conexión fallida (rc={rc})")
            self._bus.emit(
                "mqtt.error",
                {"error": f"Connection failed rc={rc}"},
                source="mqtt",
            )

    def _on_message(self, client, userdata, msg) -> None:
        """Callback de mensaje MQTT recibido."""
        topic = msg.topic
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            payload = {"raw": msg.payload.decode("utf-8", errors="replace")}

        # Determinar event_type usando mappers
        event_type = None
        for mapper in self._mappers:
            event_type = mapper(topic, payload)
            if event_type:
                break

        if event_type:
            self._bus.emit(
                event_type,
                {"topic": topic, "payload": payload},
                source="mqtt",
            )

    def _on_disconnect(self, client, userdata, rc) -> None:
        """Callback de desconexión MQTT."""
        if self._running:
            logger.warning(f"MQTT desconectado (rc={rc}). Reconectando...")
            self._bus.emit("mqtt.disconnected", {"rc": rc}, source="mqtt")

    @staticmethod
    def _default_mapper(topic: str, payload: Dict[str, Any]) -> Optional[str]:
        """Mapper por defecto: convierte MQTT topic a event type.

        Reglas:
        - nas-agent/command/X → agent.command.X
        - homeassistant/+/status → ha.status
        - docker/events/X → docker.X
        - Cualquier otro → mqtt.message
        """
        parts = topic.split("/")

        if parts[0] == "nas-agent" and len(parts) >= 3:
            # nas-agent/command/restart → agent.command.restart
            return f"agent.{'.'.join(parts[1:])}"

        if parts[0] == "homeassistant":
            # homeassistant/binary_sensor/status → ha.status
            return f"ha.{parts[-1]}" if len(parts) >= 2 else "ha.event"

        if parts[0] == "docker" and len(parts) >= 2:
            # docker/events/die → docker.die
            return f"docker.{'.'.join(parts[1:])}"

        # Default: emitir como mqtt.message
        return "mqtt.message"
