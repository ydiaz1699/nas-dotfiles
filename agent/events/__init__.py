"""
agent/events/ — Event bus para comunicación asíncrona.

Permite que servicios externos (MQTT, Home Assistant, Node-RED) disparen
acciones en el agente sin pasar por el chat. Pipeline:

    MQTT topic → MQTTListener → EventBus.emit() → handlers (plugins)

Uso:
    from agent.events import EventBus, MQTTListener

    bus = EventBus()
    bus.on("docker.unhealthy", handler_fn)
    bus.emit("docker.unhealthy", {"service": "emqx"})
"""

from agent.events.bus import EventBus, Event
from agent.events.mqtt_listener import MQTTListener

__all__ = ["EventBus", "Event", "MQTTListener"]
