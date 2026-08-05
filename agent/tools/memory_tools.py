"""
agent/tools/memory_tools.py — Tools de memoria persistente para el agente.

Thin wrappers que delegan a agent.core.memory.MemoryManager.
Patrón: @tool con docstring (Args/Returns) → Strands entiende qué hace.
"""

from datetime import datetime

from strands.tools import tool


def _mgr():
    """Lazy import para evitar ciclos."""
    from agent.core.memory import MemoryManager
    return MemoryManager


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


@tool
def remember(fact: str, category: str = "leccion") -> str:
    """Persiste un hecho o aprendizaje en la memoria del agente.
    Usar después de resolver un problema o descubrir algo nuevo.

    Categorías válidas: "entorno", "leccion", "patron", "pendiente"
    NO guardar: cosas triviales, info duplicada, datos sensibles (passwords).

    Args:
        fact: Lo aprendido. Conciso y accionable. Máx 200 chars.
        category: Sección destino (entorno|leccion|patron|pendiente). Default: leccion.

    Returns:
        Confirmación de lo guardado o error si categoría inválida.
    """
    return str(_mgr().add_to_memory(fact, category, _now()))


@tool
def recall(query: str) -> str:
    """Busca en la memoria del agente información relevante para la consulta.
    Busca en orden de prioridad: SKILLS (trigger) → MEMORY (keywords) → sessions.

    USAR SIEMPRE ANTES de resolver un problema — quizá ya lo resolviste antes.

    Args:
        query: Qué buscar, ej. "emqx no arranca", "backup falla", "puerto 8080"

    Returns:
        Resultados encontrados (skills, lecciones, sesiones) o indicación de problema nuevo.
    """
    return str(_mgr().recall(query))


@tool
def learn_skill(skill_name: str, procedure: str, trigger: str) -> str:
    """Crea un skill reutilizable basado en una solución exitosa.
    Usar cuando resolviste algo que tomó >3 pasos o fue complejo.

    Args:
        skill_name: Nombre corto descriptivo, ej. "diagnosticar-emqx-oom"
        procedure: Pasos del procedimiento en markdown (qué hacer, en qué orden)
        trigger: Cuándo aplicar este skill, ej. "emqx se reinicia por OOM"

    Returns:
        Confirmación de skill creado o warning si ya existe.
    """
    return str(_mgr().add_skill(skill_name, procedure, trigger))


@tool
def update_user_model(key: str, value: str) -> str:
    """Actualiza el perfil del usuario con una preferencia observada.
    Solo hechos OBSERVADOS en la interacción, nunca suposiciones.

    Args:
        key: Qué actualizar, ej. "estilo", "nivel_tecnico", "decision_cifrado"
        value: Valor observado, ej. "prefiere respuestas cortas", "avanzado"

    Returns:
        Confirmación de actualización en USER.md.
    """
    return str(_mgr().update_user_model(key, value))


@tool
def memory_stats() -> str:
    """Estadísticas del sistema de memoria: tamaño de cada archivo,
    número de skills, sesiones guardadas, y espacio usado vs límites.

    Returns:
        Resumen formateado del estado de la memoria.
    """
    stats = _mgr().get_memory_stats()
    return (
        f"=== MEMORIA DEL AGENTE ===\n\n"
        f"MEMORY.md: {stats['memory_kb']:.1f} KB / 50 KB\n"
        f"USER.md: {stats['user_kb']:.1f} KB / 10 KB\n"
        f"SKILLS.md: {stats['skills_kb']:.1f} KB / 100 KB"
        f" ({stats['skill_count']} skills)\n"
        f"Sessions: {stats['sessions_count']} archivos"
        f" ({stats['sessions_kb']:.1f} KB / 500 KB)\n"
        f"───────────────────────────\n"
        f"Total: {stats['total_kb']:.1f} KB"
    )
