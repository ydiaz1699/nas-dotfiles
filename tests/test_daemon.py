"""
test_daemon.py — Tests para el daemon (scheduler).
"""

import threading
import time

from agent.daemon import Scheduler


class TestScheduler:
    def test_task_executes(self):
        """Una tarea con run_on_start=True se ejecuta inmediatamente."""
        results = []

        def task_fn():
            results.append("executed")

        sched = Scheduler()
        sched.add_task("test-task", task_fn, interval_minutes=60, run_on_start=True)
        sched.start()

        # Esperar un poco para que la tarea se ejecute
        time.sleep(0.3)
        sched.stop()

        assert "executed" in results

    def test_stop_is_graceful(self):
        """stop() detiene los threads sin bloquear indefinidamente."""
        sched = Scheduler()
        sched.add_task("dummy", lambda: None, interval_minutes=1)
        sched.start()

        start = time.time()
        sched.stop()
        elapsed = time.time() - start

        # Stop debe completar en menos de 6 segundos
        assert elapsed < 6

    def test_error_in_task_doesnt_crash(self):
        """Un error en una tarea no mata al scheduler."""
        call_count = []

        def failing_task():
            call_count.append(1)
            raise RuntimeError("boom")

        sched = Scheduler()
        sched.add_task("fail-task", failing_task, interval_minutes=60, run_on_start=True)
        sched.start()

        time.sleep(0.3)
        sched.stop()

        # La tarea se ejecutó (y falló) pero el scheduler no crasheó
        assert len(call_count) >= 1

    def test_multiple_tasks(self):
        """Múltiples tareas se ejecutan independientemente."""
        results_a = []
        results_b = []

        sched = Scheduler()
        sched.add_task("task-a", lambda: results_a.append("a"), interval_minutes=60, run_on_start=True)
        sched.add_task("task-b", lambda: results_b.append("b"), interval_minutes=60, run_on_start=True)
        sched.start()

        time.sleep(0.3)
        sched.stop()

        assert "a" in results_a
        assert "b" in results_b
