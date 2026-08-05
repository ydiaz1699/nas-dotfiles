"""
agent/plugins/ha_discovery_plugin.py — MQTT Discovery para Home Assistant.

Publica auto-discovery configs + estados periódicos para que HA
detecte automáticamente todas las entidades del NAS bajo un device.

Entidades publicadas:
- binary_sensor: 1 por servicio Docker (on/off)
- sensor: restarts y uptime por servicio
- sensor: disco, RAM, CPU, servicios activos/total
- button: restart per-service + update_all

Device: "NASAgent" — todo agrupado bajo un device en HA.
Intervalo: 60 segundos (configurable via NAS_HA_INTERVAL).

Requisitos:
    pip install paho-mqtt

Configuración:
    NAS_MQTT_HOST: Host del broker (default: localhost)
    NAS_MQTT_PORT: Puerto (default: 1883)
    NAS_HA_INTERVAL: Segundos entre publicaciones (default: 60)
    NAS_HA_DEVICE_NAME: Nombre del device en HA (default: NASAgent)
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

from agent.plugins.base import BasePlugin, EventHandler, PluginMeta, ScheduleConfig

logger = logging.getLogger(__name__)

# ─── Configuración ───────────────────────────────────────────────────────────

MQTT_HOST = os.environ.get("NAS_MQTT_HOST", "localhost")
MQTT_PORT = int(os.environ.get("NAS_MQTT_PORT", "1883"))
MQTT_USER = os.environ.get("NAS_MQTT_USER", "")
MQTT_PASS = os.environ.get("NAS_MQTT_PASS", "")
HA_INTERVAL = int(os.environ.get("NAS_HA_INTERVAL", "60"))
DEVICE_NAME = os.environ.get("NAS_HA_DEVICE_NAME", "NASAgent")
DOCKER_BASE = Path(os.environ.get("DOCKER_BASE", "/docker"))

# Prefijo para topics de estado
STATE_PREFIX = "nas-agent"
# Prefijo para discovery de HA
DISCOVERY_PREFIX = "homeassistant"

# Device info (aparece en HA)
DEVICE_INFO = {
    "identifiers": ["nas_agent_homelab"],
    "name": DEVICE_NAME,
    "manufacturer": "nas-dotfiles",
    "model": "NAS Homelab Agent",
    "sw_version": "1.0",
}

# Compose filenames válidos
COMPOSE_NAMES = [
    "docker-compose.yml",
    "docker-compose.yaml",
    "compose.yml",
    "compose.yaml",
]


class HADiscoveryPlugin(BasePlugin):
    """Plugin de MQTT Discovery para Home Assistant."""

    meta = PluginMeta(
        name="ha_discovery",
        version="1.0.0",
        description="MQTT Discovery para Home Assistant — auto-descubrimiento de servicios y sistema",
        dependencies=[],
    )

    def __init__(self):
        super().__init__()
        self._mqtt_client = None
        self._connected = False
        self._discovered_services: List[str] = []

    def setup(self):
        """Registra schedules para discovery + publicación de estados."""
        # Publicar discovery configs al arrancar
        self.register_schedule(ScheduleConfig(
            name="ha_discovery_publish",
            handler=self._publish_discovery,
            interval_minutes=60,  # Re-publicar cada hora (por si HA se reinicia)
            enabled=True,
            run_on_start=True,
        ))

        # Publicar estados cada 60 segundos
        interval_min = max(1, HA_INTERVAL // 60) if HA_INTERVAL >= 60 else 1
        self.register_schedule(ScheduleConfig(
            name="ha_state_update",
            handler=self._publish_states,
            interval_minutes=interval_min,
            enabled=True,
            run_on_start=True,
        ))

        # Escuchar comandos de HA (buttons)
        self.register_event(EventHandler(
            event_type="agent.command.restart",
            handler=self._on_restart_command,
            description="HA button restart → ejecutar restart del servicio",
        ))
        self.register_event(EventHandler(
            event_type="agent.command.update_all",
            handler=self._on_update_all_command,
            description="HA button update_all → ejecutar update de todos",
        ))

    def teardown(self):
        """Publica offline y desconecta."""
        if self._mqtt_client and self._connected:
            # Publicar availability offline
            self._mqtt_publish(
                f"{STATE_PREFIX}/availability",
                "offline",
                retain=True,
            )
            self._mqtt_client.disconnect()

    # ─── MQTT Connection ───────────────────────────────────────────────────

    def _ensure_mqtt(self) -> bool:
        """Asegura conexión MQTT. Retorna True si conectado."""
        if self._connected and self._mqtt_client:
            return True

        try:
            import paho.mqtt.client as mqtt
        except ImportError:
            logger.warning("paho-mqtt no instalado. HA Discovery desactivado.")
            return False

        try:
            self._mqtt_client = mqtt.Client(
                client_id="nas-agent-ha-discovery",
                protocol=mqtt.MQTTv311,
            )
            if MQTT_USER:
                self._mqtt_client.username_pw_set(MQTT_USER, MQTT_PASS)

            # Last Will: si el daemon muere, HA marca offline
            self._mqtt_client.will_set(
                f"{STATE_PREFIX}/availability",
                "offline",
                qos=1,
                retain=True,
            )

            self._mqtt_client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
            self._mqtt_client.loop_start()
            self._connected = True

            # Publicar online
            self._mqtt_publish(f"{STATE_PREFIX}/availability", "online", retain=True)
            logger.info(f"HA Discovery: conectado a MQTT {MQTT_HOST}:{MQTT_PORT}")
            return True

        except Exception as e:
            logger.error(f"HA Discovery: error conectando MQTT: {e}")
            self._connected = False
            return False

    def _mqtt_publish(self, topic: str, payload: Any, retain: bool = False) -> None:
        """Publica un mensaje MQTT."""
        if not self._mqtt_client:
            return
        if isinstance(payload, dict):
            payload = json.dumps(payload)
        self._mqtt_client.publish(topic, payload, qos=1, retain=retain)

    # ─── Service Discovery ─────────────────────────────────────────────────

    def _get_services(self) -> List[str]:
        """Detecta servicios Docker con compose file."""
        services = []
        if not DOCKER_BASE.exists():
            return services
        for item in sorted(DOCKER_BASE.iterdir()):
            if not item.is_dir() or item.name.startswith(".") or item.name == "backups":
                continue
            for name in COMPOSE_NAMES:
                if (item / name).exists():
                    services.append(item.name)
                    break
        return services

    def _is_running(self, service: str) -> bool:
        """Verifica si un servicio está corriendo."""
        compose = self._get_compose_file(service)
        if not compose:
            return False
        result = subprocess.run(
            ["docker", "compose", "-f", str(compose), "ps", "-q"],
            capture_output=True, text=True, check=False,
        )
        return result.returncode == 0 and bool(result.stdout.strip())

    def _get_compose_file(self, service: str) -> Optional[Path]:
        """Obtiene compose file de un servicio."""
        svc_dir = DOCKER_BASE / service
        for name in COMPOSE_NAMES:
            candidate = svc_dir / name
            if candidate.exists():
                return candidate
        return None

    def _get_container_id(self, service: str) -> Optional[str]:
        """Obtiene el ID del primer contenedor activo."""
        compose = self._get_compose_file(service)
        if not compose:
            return None
        result = subprocess.run(
            ["docker", "compose", "-f", str(compose), "ps", "-q"],
            capture_output=True, text=True, check=False,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip().splitlines()[0]
        return None

    def _inspect(self, container_id: str, fmt: str) -> str:
        """Docker inspect con formato."""
        result = subprocess.run(
            ["docker", "inspect", "--format", fmt, container_id],
            capture_output=True, text=True, check=False,
        )
        return result.stdout.strip() if result.returncode == 0 else ""

    # ─── System Metrics ────────────────────────────────────────────────────

    def _get_system_metrics(self) -> Dict[str, Any]:
        """Obtiene métricas del sistema."""
        metrics = {}

        # Disco
        try:
            result = subprocess.run(
                ["df", "/docker", "--output=pcent"],
                capture_output=True, text=True, check=False,
            )
            if result.returncode == 0:
                lines = result.stdout.strip().splitlines()
                if len(lines) >= 2:
                    metrics["disk"] = int(lines[1].strip().rstrip("%"))
        except Exception:
            pass

        # Memoria
        try:
            result = subprocess.run(
                ["free"], capture_output=True, text=True, check=False,
            )
            for line in result.stdout.splitlines():
                if line.startswith("Mem:"):
                    parts = line.split()
                    total = int(parts[1])
                    used = int(parts[2])
                    metrics["memory"] = int(used / total * 100) if total > 0 else 0
                    break
        except Exception:
            pass

        # CPU
        try:
            with open("/proc/loadavg") as f:
                load = float(f.read().split()[0])
                # Número de CPUs
                cpu_count = os.cpu_count() or 1
                metrics["cpu"] = min(100, int(load / cpu_count * 100))
        except Exception:
            pass

        return metrics

    # ─── Publish Discovery Configs ─────────────────────────────────────────

    def _publish_discovery(self) -> None:
        """Publica configs de MQTT Discovery para HA."""
        if not self._ensure_mqtt():
            return

        services = self._get_services()
        self._discovered_services = services
        logger.info(f"HA Discovery: publicando configs para {len(services)} servicios")

        availability = {"topic": f"{STATE_PREFIX}/availability"}

        # ── Sensores de sistema ────────────────────────────────────────────
        system_sensors = [
            ("disk_usage", "Disk Usage", "%", "mdi:harddisk", "disk"),
            ("memory_usage", "Memory Usage", "%", "mdi:memory", "memory"),
            ("cpu_usage", "CPU Usage", "%", "mdi:cpu-64-bit", "cpu"),
            ("services_running", "Services Running", "", "mdi:docker", None),
            ("services_total", "Services Total", "", "mdi:docker", None),
        ]

        for sensor_id, name, unit, icon, dev_class in system_sensors:
            config = {
                "name": name,
                "unique_id": f"nasagent_{sensor_id}",
                "state_topic": f"{STATE_PREFIX}/system/state",
                "value_template": f"{{{{ value_json.{sensor_id} }}}}",
                "availability": availability,
                "device": DEVICE_INFO,
                "icon": icon,
            }
            if unit:
                config["unit_of_measurement"] = unit
            if dev_class:
                config["device_class"] = dev_class

            self._mqtt_publish(
                f"{DISCOVERY_PREFIX}/sensor/nasagent/{sensor_id}/config",
                config,
                retain=True,
            )

        # ── Entidades por servicio ─────────────────────────────────────────
        for svc in services:
            svc_id = svc.replace("-", "_").replace(".", "_")

            # binary_sensor: running/stopped
            self._mqtt_publish(
                f"{DISCOVERY_PREFIX}/binary_sensor/nasagent/{svc_id}/config",
                {
                    "name": f"{svc}",
                    "unique_id": f"nasagent_docker_{svc_id}",
                    "state_topic": f"{STATE_PREFIX}/docker/{svc}/state",
                    "value_template": "{{ value_json.state }}",
                    "payload_on": "on",
                    "payload_off": "off",
                    "device_class": "running",
                    "availability": availability,
                    "device": DEVICE_INFO,
                    "icon": "mdi:docker",
                },
                retain=True,
            )

            # sensor: restarts
            self._mqtt_publish(
                f"{DISCOVERY_PREFIX}/sensor/nasagent/{svc_id}_restarts/config",
                {
                    "name": f"{svc} Restarts",
                    "unique_id": f"nasagent_{svc_id}_restarts",
                    "state_topic": f"{STATE_PREFIX}/docker/{svc}/state",
                    "value_template": "{{ value_json.restarts }}",
                    "availability": availability,
                    "device": DEVICE_INFO,
                    "icon": "mdi:restart",
                },
                retain=True,
            )

            # sensor: uptime
            self._mqtt_publish(
                f"{DISCOVERY_PREFIX}/sensor/nasagent/{svc_id}_uptime/config",
                {
                    "name": f"{svc} Uptime",
                    "unique_id": f"nasagent_{svc_id}_uptime",
                    "state_topic": f"{STATE_PREFIX}/docker/{svc}/state",
                    "value_template": "{{ value_json.uptime }}",
                    "availability": availability,
                    "device": DEVICE_INFO,
                    "icon": "mdi:clock-outline",
                },
                retain=True,
            )

            # button: restart
            self._mqtt_publish(
                f"{DISCOVERY_PREFIX}/button/nasagent/{svc_id}_restart/config",
                {
                    "name": f"Restart {svc}",
                    "unique_id": f"nasagent_restart_{svc_id}",
                    "command_topic": f"{STATE_PREFIX}/command/restart",
                    "payload_press": json.dumps({"service": svc}),
                    "availability": availability,
                    "device": DEVICE_INFO,
                    "icon": "mdi:restart",
                    "device_class": "restart",
                },
                retain=True,
            )

        # ── Button: update all ─────────────────────────────────────────────
        self._mqtt_publish(
            f"{DISCOVERY_PREFIX}/button/nasagent/update_all/config",
            {
                "name": "Update All Services",
                "unique_id": "nasagent_update_all",
                "command_topic": f"{STATE_PREFIX}/command/update_all",
                "payload_press": json.dumps({"action": "update_all"}),
                "availability": availability,
                "device": DEVICE_INFO,
                "icon": "mdi:update",
                "device_class": "update",
            },
            retain=True,
        )

        logger.info(f"HA Discovery: {len(services)} servicios + sistema publicados")

    # ─── Publish States ────────────────────────────────────────────────────

    def _publish_states(self) -> None:
        """Publica estados actuales de servicios y sistema."""
        if not self._ensure_mqtt():
            return

        services = self._discovered_services or self._get_services()
        running_count = 0

        # ── Estados de cada servicio ───────────────────────────────────────
        for svc in services:
            is_running = self._is_running(svc)
            state_data = {
                "state": "on" if is_running else "off",
                "restarts": 0,
                "uptime": "offline",
            }

            if is_running:
                running_count += 1
                cid = self._get_container_id(svc)
                if cid:
                    # Restarts
                    rc = self._inspect(cid, "{{.RestartCount}}")
                    state_data["restarts"] = int(rc) if rc.isdigit() else 0

                    # Uptime
                    started = self._inspect(cid, "{{.State.StartedAt}}")
                    if started and not started.startswith("0001"):
                        try:
                            from datetime import datetime
                            clean = started.split(".")[0].replace("T", " ").replace("Z", "")
                            start_dt = datetime.strptime(clean, "%Y-%m-%d %H:%M:%S")
                            diff = datetime.now() - start_dt
                            seconds = int(diff.total_seconds())
                            if seconds < 3600:
                                state_data["uptime"] = f"{seconds // 60}m"
                            elif seconds < 86400:
                                state_data["uptime"] = f"{seconds // 3600}h"
                            else:
                                state_data["uptime"] = f"{seconds // 86400}d"
                        except (ValueError, TypeError):
                            state_data["uptime"] = "?"

            self._mqtt_publish(
                f"{STATE_PREFIX}/docker/{svc}/state",
                state_data,
            )

        # ── Estado del sistema ─────────────────────────────────────────────
        metrics = self._get_system_metrics()
        system_state = {
            "disk_usage": metrics.get("disk", 0),
            "memory_usage": metrics.get("memory", 0),
            "cpu_usage": metrics.get("cpu", 0),
            "services_running": running_count,
            "services_total": len(services),
        }

        self._mqtt_publish(f"{STATE_PREFIX}/system/state", system_state)

        logger.debug(
            f"HA States: {running_count}/{len(services)} running | "
            f"disk={system_state['disk_usage']}% "
            f"mem={system_state['memory_usage']}% "
            f"cpu={system_state['cpu_usage']}%"
        )

    # ─── Command Handlers ──────────────────────────────────────────────────

    def _on_restart_command(self, event: dict) -> None:
        """Maneja comando restart desde HA button."""
        data = event if isinstance(event, dict) else getattr(event, "data", {})
        payload = data.get("payload", {})
        service = payload.get("service", "")

        if not service:
            logger.warning("HA restart command sin servicio")
            return

        compose = self._get_compose_file(service)
        if not compose:
            logger.error(f"HA restart: servicio '{service}' no encontrado")
            return

        logger.info(f"HA command: restart {service}")
        subprocess.run(
            ["docker", "compose", "-f", str(compose), "restart"],
            capture_output=True, check=False,
        )

    def _on_update_all_command(self, event: dict) -> None:
        """Maneja comando update_all desde HA button."""
        logger.info("HA command: update_all")
        services = self._get_services()

        for svc in services:
            compose = self._get_compose_file(svc)
            if not compose:
                continue
            if not self._is_running(svc):
                continue

            logger.info(f"  Updating {svc}...")
            subprocess.run(
                ["docker", "compose", "-f", str(compose), "pull"],
                capture_output=True, check=False,
            )
            subprocess.run(
                ["docker", "compose", "-f", str(compose), "up", "-d", "--remove-orphans"],
                capture_output=True, check=False,
            )
