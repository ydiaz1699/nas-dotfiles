"""
runner.py — Scheduler de tareas periódicas.

Ejecuta tareas en intervalos configurados. Cada tarea corre en su propio
hilo para no bloquear el scheduler. Emite eventos al bus cuando una tarea
se ejecuta o falla.
"""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from agent.plugins.base import ScheduleConfig

logger = logging.getLogger(__name__)


@dataclass
class TaskState:
    """Estado de una tarea programada."""
    config: ScheduleConfig
    last_run: float = 0.0
    run_count: int = 0
    error_count: int = 0
    last_error: Optional[str] = None
    running: bool = False


class Scheduler:
    """Scheduler de tareas periódicas.

    Ejecuta tareas a intervalos definidos. Thread-safe.
    Emite eventos al bus: schedule.run, schedule.error, schedule.complete.

    Uso:
        scheduler = Scheduler(event_bus=bus)
        scheduler.add(ScheduleConfig(...))
        scheduler.start()
        # ...
        scheduler.stop()
    """

    def __init__(self, event_bus: Optional[Any] = None, tick_interval: float = 30.0):
        """
        Args:
            event_bus: EventBus para emitir eventos (opcional).
            tick_interval: Segundos entre cada revisión de tareas pendientes.
        """
        self._tasks: Dict[str, TaskState] = {}
        self._bus = event_bus
        self._tick_interval = tick_interval
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self._lock = threading.Lock()

    def add(self, config: ScheduleConfig) -> None:
        """Agrega una tarea al scheduler.

        Args:
            config: Configuración de la tarea.
        """
        with self._lock:
            self._tasks[config.name] = TaskState(config=config)
            logger.info(
                f"Tarea '{config.name}' registrada "
                f"(cada {config.interval_minutes} min)"
            )

    def remove(self, name: str) -> bool:
        """Elimina una tarea por nombre."""
        with self._lock:
            if name in self._tasks:
                del self._tasks[name]
                return True
            return False

    def start(self) -> None:
        """Inicia el scheduler en un hilo background."""
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(
            target=self._run_loop,
            name="scheduler",
            daemon=True,
        )
        self._thread.start()
        logger.info(
            f"Scheduler iniciado ({len(self._tasks)} tareas, "
            f"tick={self._tick_interval}s)"
        )

        # Ejecutar tareas con run_on_start
        for state in self._tasks.values():
            if state.config.run_on_start and state.config.enabled:
                self._execute_task(state)

    def stop(self) -> None:
        """Detiene el scheduler."""
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=10)
        logger.info("Scheduler detenido.")

    @property
    def running(self) -> bool:
        return self._running

    def status(self) -> str:
        """Resumen del estado del scheduler."""
        with self._lock:
            if not self._tasks:
                return "Scheduler: sin tareas registradas."

            lines = [f"=== SCHEDULER ({len(self._tasks)} tareas) ===\n"]
            for name, state in sorted(self._tasks.items()):
                cfg = state.config
                status_icon = "✅" if cfg.enabled else "⏸️"
                if state.running:
                    status_icon = "🔄"
                elif state.last_error:
                    status_icon = "❌"

                elapsed = ""
                if state.last_run:
                    minutes_ago = (time.time() - state.last_run) / 60
                    elapsed = f" (hace {minutes_ago:.0f}m)"

                lines.append(
                    f"  {status_icon} {name}: cada {cfg.interval_minutes}m "
                    f"| runs: {state.run_count} | errors: {state.error_count}"
                    f"{elapsed}"
                )
                if state.last_error:
                    lines.append(f"      └─ Error: {state.last_error[:80]}")

            return "\n".join(lines)

    def _run_loop(self) -> None:
        """Loop principal del scheduler."""
        while self._running:
            now = time.time()

            with self._lock:
                pending = [
                    state for state in self._tasks.values()
                    if (
                        state.config.enabled
                        and not state.running
                        and (now - state.last_run) >= state.config.interval_minutes * 60
                    )
                ]

            for state in pending:
                self._execute_task(state)

            time.sleep(self._tick_interval)

    def _execute_task(self, state: TaskState) -> None:
        """Ejecuta una tarea en un hilo separado."""
        def _run():
            state.running = True
            task_name = state.config.name

            if self._bus:
                self._bus.emit(
                    "schedule.run",
                    {"task": task_name},
                    source="scheduler",
                )

            try:
                state.config.handler()
                state.run_count += 1
                state.last_error = None
                logger.debug(f"Tarea '{task_name}' completada.")

                if self._bus:
                    self._bus.emit(
                        "schedule.complete",
                        {"task": task_name, "run_count": state.run_count},
                        source="scheduler",
                    )

            except Exception as e:
                state.error_count += 1
                state.last_error = str(e)
                logger.error(f"Error en tarea '{task_name}': {e}")

                if self._bus:
                    self._bus.emit(
                        "schedule.error",
                        {"task": task_name, "error": str(e)},
                        source="scheduler",
                    )
            finally:
                state.last_run = time.time()
                state.running = False

        thread = threading.Thread(
            target=_run,
            name=f"task-{state.config.name}",
            daemon=True,
        )
        thread.start()
