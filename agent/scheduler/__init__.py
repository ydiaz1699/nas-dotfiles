"""
agent/scheduler/ — Ejecutor de tareas periódicas (cron-like).

Ejecuta tareas definidas por plugins a intervalos configurados.
Thread-safe, corre en background.

Uso:
    from agent.scheduler import Scheduler
    from agent.plugins.base import ScheduleConfig

    scheduler = Scheduler(event_bus=bus)
    scheduler.add(ScheduleConfig(
        name="health-check",
        handler=check_all_services,
        interval_minutes=5,
    ))
    scheduler.start()
"""

from agent.scheduler.runner import Scheduler

__all__ = ["Scheduler"]
