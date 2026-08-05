"""
agent/daemon.py — Entry point para modo daemon (systemd).

Mantiene vivos en background:
- Scheduler: tareas periódicas (curación de memoria 24h, health checks, etc.)
- MQTT Listener: recibe comandos de Home Assistant / Node-RED
- EventBus: pub/sub interno para comunicación entre componentes

El agente CLI (python -m agent.nas_agent) sigue funcionando igual por separado.
Este daemon es para los componentes que necesitan correr 24/7.

Uso:
    # Directo (foreground, para debug)
    python -m agent.daemon

    # Via systemd (producción)
    sudo systemctl start nas-agent

    # Ver logs
    journalctl -u nas-agent -f
"""

from __future__ import annotations

import logging
import os
import signal
import sys
import threading
import time
from pathlib import Path

# ─── Cargar .env.agent ───────────────────────────────────────────────────────

def _load_env_agent():
    """Carga variables de entorno desde .env.agent si existe."""
    env_file = Path(__file__).resolve().parent.parent / ".env.agent"
    if not env_file.exists():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip()
            if key and key not in os.environ:
                os.environ[key] = value

_load_env_agent()

# ─── Logging ─────────────────────────────────────────────────────────────────

LOG_LEVEL = os.environ.get("NAS_AGENT_LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("nas-agent.daemon")

# ─── Scheduler ───────────────────────────────────────────────────────────────


class Scheduler:
    """Ejecutor de tareas periódicas basado en threads.

    Cada ScheduleConfig registrada se ejecuta en su intervalo.
    Thread-safe, graceful shutdown via stop().
    """

    def __init__(self):
        self._tasks: list = []
        self._stop_event = threading.Event()
        self._threads: list[threading.Thread] = []

    def add_task(self, name: str, handler, interval_minutes: int, run_on_start: bool = False):
        """Registra una tarea periódica."""
        self._tasks.append({
            "name": name,
            "handler": handler,
            "interval": interval_minutes * 60,  # a segundos
            "run_on_start": run_on_start,
        })

    def start(self):
        """Inicia todos los schedulers en threads separados."""
        for task in self._tasks:
            t = threading.Thread(
                target=self._run_task,
                args=(task,),
                name=f"sched-{task['name']}",
                daemon=True,
            )
            self._threads.append(t)
            t.start()
            logger.info(f"Scheduler: '{task['name']}' cada {task['interval'] // 60} min")

    def _run_task(self, task: dict):
        """Loop de una tarea individual."""
        if task["run_on_start"]:
            self._execute(task)

        while not self._stop_event.is_set():
            # Dormir en intervalos cortos para responder rápido al stop
            slept = 0
            while slept < task["interval"] and not self._stop_event.is_set():
                time.sleep(min(10, task["interval"] - slept))
                slept += 10

            if not self._stop_event.is_set():
                self._execute(task)

    def _execute(self, task: dict):
        """Ejecuta una tarea con manejo de errores."""
        try:
            logger.debug(f"Ejecutando tarea: {task['name']}")
            result = task["handler"]()
            if result:
                logger.info(f"Tarea '{task['name']}' completada: {result}")
        except Exception as e:
            logger.error(f"Error en tarea '{task['name']}': {e}", exc_info=True)

    def stop(self):
        """Detiene todos los schedulers."""
        self._stop_event.set()
        for t in self._threads:
            t.join(timeout=5)
        logger.info("Scheduler detenido.")


# ─── Daemon principal ────────────────────────────────────────────────────────


class NASAgentDaemon:
    """Daemon principal que orquesta scheduler + plugins."""

    def __init__(self):
        self._running = False
        self._scheduler = Scheduler()
        self._stop_event = threading.Event()

    def setup(self):
        """Inicializa plugins y registra sus schedules."""
        from agent.plugins import PluginLoader

        logger.info("Cargando plugins...")
        loader = PluginLoader()
        loaded = loader.discover()
        logger.info(f"Plugins cargados: {loaded}")

        # Registrar schedules de todos los plugins
        for schedule in loader.all_schedules():
            if schedule.enabled:
                self._scheduler.add_task(
                    name=schedule.name,
                    handler=schedule.handler,
                    interval_minutes=schedule.interval_minutes,
                    run_on_start=schedule.run_on_start,
                )

        # Registrar health check propio del daemon
        self._scheduler.add_task(
            name="daemon_heartbeat",
            handler=self._heartbeat,
            interval_minutes=60,
            run_on_start=True,
        )

    def _heartbeat(self):
        """Heartbeat del daemon — log de que sigue vivo."""
        from agent.core.memory import MemoryManager
        stats = MemoryManager.get_memory_stats()
        logger.info(
            f"Heartbeat OK | Memoria: {stats['total_kb']:.1f} KB | "
            f"Skills: {stats['skill_count']} | "
            f"Sessions: {stats['sessions_count']}"
        )

    def start(self):
        """Arranca el daemon."""
        self._running = True
        logger.info("=" * 60)
        logger.info("NAS Agent Daemon iniciando...")
        logger.info(f"PID: {os.getpid()}")
        logger.info(f"Log level: {LOG_LEVEL}")
        logger.info("=" * 60)

        self.setup()
        self._scheduler.start()

        logger.info("Daemon activo. Ctrl+C o SIGTERM para detener.")

        # Loop principal — espera señal de stop
        try:
            while not self._stop_event.is_set():
                self._stop_event.wait(timeout=1)
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()

    def stop(self):
        """Shutdown graceful."""
        if not self._running:
            return
        self._running = False
        logger.info("Deteniendo daemon...")
        self._scheduler.stop()
        logger.info("NAS Agent Daemon detenido.")

    def signal_stop(self):
        """Señala al daemon que debe detenerse."""
        self._stop_event.set()


# ─── Signal handlers ─────────────────────────────────────────────────────────

_daemon: NASAgentDaemon | None = None


def _signal_handler(signum, frame):
    """Maneja SIGTERM/SIGINT para shutdown graceful."""
    sig_name = signal.Signals(signum).name
    logger.info(f"Señal recibida: {sig_name}")
    if _daemon:
        _daemon.signal_stop()


# ─── Entry point ─────────────────────────────────────────────────────────────


def main():
    """Punto de entrada del daemon."""
    global _daemon

    # Registrar signal handlers
    signal.signal(signal.SIGTERM, _signal_handler)
    signal.signal(signal.SIGINT, _signal_handler)

    _daemon = NASAgentDaemon()
    _daemon.start()


if __name__ == "__main__":
    main()
