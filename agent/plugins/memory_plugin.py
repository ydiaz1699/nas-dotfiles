"""
agent/plugins/memory_plugin.py — Plugin de memoria persistente y auto-mejora.

Registra:
- Tools: remember, recall, learn_skill, update_user_model, memory_stats
- Events (Capa B): task.completed, user.correction
- Schedule (Capa C): curación diaria de memoria

Las 3 capas del Learning Loop:
    A) System prompt → el modelo PUEDE recordar por iniciativa propia
    B) Event-driven → GARANTIZA que soluciones complejas se persistan
    C) Schedule → MANTIENE la calidad (limpia, consolida, verifica cada 24h)
"""

from agent.plugins.base import BasePlugin, EventHandler, PluginMeta, ScheduleConfig


class MemoryPlugin(BasePlugin):
    """Plugin de memoria persistente (Learning Loop)."""

    meta = PluginMeta(
        name="memory",
        version="1.0.0",
        description=(
            "Memoria persistente y auto-mejora: "
            "MEMORY.md, USER.md, SKILLS.md, sessions/"
        ),
        dependencies=[],  # Sin dependencias — se carga primero
    )

    def setup(self):
        from agent.tools.memory_tools import (
            learn_skill,
            memory_stats,
            recall,
            remember,
            update_user_model,
        )

        # ── Tools ──────────────────────────────────────────────
        self.register_tool(remember)
        self.register_tool(recall)
        self.register_tool(learn_skill)
        self.register_tool(update_user_model)
        self.register_tool(memory_stats)

        # ── Capa B: Event-driven ───────────────────────────────
        self.register_event(EventHandler(
            event_type="task.completed",
            handler=self._on_task_completed,
            description=(
                "Evaluar si la tarea completada merece "
                "persistirse en memoria o generar un skill"
            ),
        ))
        self.register_event(EventHandler(
            event_type="user.correction",
            handler=self._on_user_correction,
            description=(
                "Actualizar USER.md cuando el usuario "
                "corrige una decisión o preferencia"
            ),
        ))

        # ── Capa C: Curación periódica ────────────────────────
        self.register_schedule(ScheduleConfig(
            name="curate_memory",
            handler=self._curate_memory,
            interval_minutes=1440,  # 24h
            enabled=True,
            run_on_start=False,
        ))

    # ── Capa B: handlers ───────────────────────────────────────

    def _on_task_completed(self, event: dict) -> None:
        """Evalúa si una tarea merece ser recordada.

        Criterios de significancia:
        - tool_calls > 3 (tarea compleja)
        - errors_encountered = True (troubleshooting exitoso)
        - duration_seconds > 300 (más de 5 min investigando)
        """
        from agent.core.memory import MemoryManager

        data = event if isinstance(event, dict) else getattr(event, "data", {})

        tool_calls = data.get("tool_calls", 0)
        had_errors = data.get("errors_encountered", False)
        duration = data.get("duration_seconds", 0)

        is_significant = (
            tool_calls > 3
            or had_errors
            or duration > 300
        )

        if not is_significant:
            return

        # Guardar resumen de sesión
        summary = data.get("summary", "Tarea compleja completada")
        title = summary[:60]
        session_content = (
            f"# Sesión: {title}\n"
            f"> Tools: {tool_calls} | "
            f"Errores: {'sí' if had_errors else 'no'} | "
            f"Duración: {duration}s\n\n"
            f"## Resumen\n{summary}\n"
        )

        # Agregar detalle de tools usadas si disponible
        tools_used = data.get("tools_used", [])
        if tools_used:
            session_content += f"\n## Tools usadas\n"
            for t in tools_used[:10]:
                session_content += f"- {t}\n"

        # Agregar solución si hubo error
        solution = data.get("solution", "")
        if solution:
            session_content += f"\n## Solución\n{solution}\n"

        MemoryManager.save_session(title, session_content)

    def _on_user_correction(self, event: dict) -> None:
        """Persiste correcciones del usuario en USER.md."""
        from agent.core.memory import MemoryManager

        data = event if isinstance(event, dict) else getattr(event, "data", {})
        key = data.get("key", "correccion_reciente")
        value = data.get("value", data.get("correction", ""))

        if value:
            MemoryManager.update_user_model(key, value[:100])

    # ── Capa C: curación ───────────────────────────────────────

    def _curate_memory(self) -> None:
        """Curación diaria: limpiar sessions viejas y entradas obsoletas."""
        from agent.core.memory import MemoryManager

        stats = MemoryManager.get_memory_stats()

        # 1. Trim sessions > 90 días
        MemoryManager.trim_sessions(max_age_days=90)

        # 2. Si MEMORY.md > 80% del límite, podar entradas viejas
        if stats["memory_kb"] > 40:  # 80% de 50 KB
            MemoryManager.prune_old_entries(max_age_days=90)

        # 3. Log de curación (futuro: auditar)
        # logger.info(f"Curación completada: {stats}")
