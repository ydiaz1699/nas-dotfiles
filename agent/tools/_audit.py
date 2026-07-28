"""
_audit.py — Sistema de auditoría para el agente NAS.

Registra cada invocación de herramientas con:
- Timestamp
- Nombre de la tool
- Argumentos recibidos
- Resultado (truncado)
- Duración

El log se escribe en: /docker/backups/agent_audit.log (o configurable)
Formato: JSON Lines (una entrada JSON por línea, fácil de parsear)

Variables de entorno:
- NAS_AGENT_AUDIT_LOG: ruta al archivo de log (default: /docker/backups/agent_audit.log)
- NAS_AGENT_AUDIT: "1" para habilitar (default), "0" para deshabilitar
"""

import json
import os
import time
import functools
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


# ─────────────────────────────────────────────────────────────────────────────
# Configuración
# ─────────────────────────────────────────────────────────────────────────────

_DEFAULT_LOG_PATH = "/docker/backups/agent_audit.log"
_MAX_RESULT_LENGTH = 500  # Truncar resultados largos en el log


def _get_log_path() -> Path:
    """Retorna la ruta al archivo de auditoría."""
    return Path(os.environ.get("NAS_AGENT_AUDIT_LOG", _DEFAULT_LOG_PATH))


def _is_audit_enabled() -> bool:
    """Retorna True si la auditoría está habilitada."""
    return os.environ.get("NAS_AGENT_AUDIT", "1").strip() not in ("0", "false", "no")


# ─────────────────────────────────────────────────────────────────────────────
# Logger
# ─────────────────────────────────────────────────────────────────────────────


def log_tool_call(
    tool_name: str,
    args: dict[str, Any],
    result: str,
    duration_ms: float,
    error: str | None = None,
) -> None:
    """Registra una invocación de herramienta en el audit log.

    Args:
        tool_name: Nombre de la herramienta invocada.
        args: Diccionario de argumentos recibidos.
        result: Resultado retornado (se trunca a _MAX_RESULT_LENGTH).
        duration_ms: Duración en milisegundos.
        error: Mensaje de error si falló (opcional).
    """
    if not _is_audit_enabled():
        return

    log_path = _get_log_path()

    # Crear directorio si no existe
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        # Si no podemos escribir en /docker/backups, usar fallback local
        log_path = Path.home() / ".nas-agent-audit.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)

    # Truncar resultado para no inflar el log
    result_truncated = result[:_MAX_RESULT_LENGTH]
    if len(result) > _MAX_RESULT_LENGTH:
        result_truncated += f"... [truncado, {len(result)} chars total]"

    # Sanitizar args (ocultar valores sensibles)
    safe_args = _sanitize_args(args)

    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "tool": tool_name,
        "args": safe_args,
        "result_preview": result_truncated,
        "duration_ms": round(duration_ms, 1),
        "success": error is None,
    }

    if error:
        entry["error"] = error[:200]

    # Escribir como JSON Line
    try:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        # Auditoría nunca debe romper el agente
        pass


def _sanitize_args(args: dict[str, Any]) -> dict[str, Any]:
    """Oculta valores sensibles en los argumentos."""
    sensitive_keys = {"password", "token", "secret", "api_key", "key"}
    safe = {}
    for k, v in args.items():
        if any(s in k.lower() for s in sensitive_keys):
            safe[k] = "***"
        else:
            safe[k] = str(v)[:200] if isinstance(v, str) else v
    return safe


# ─────────────────────────────────────────────────────────────────────────────
# Decorador para wrappear tools con auditoría automática
# ─────────────────────────────────────────────────────────────────────────────


def audited(func: Callable) -> Callable:
    """Decorador que agrega auditoría automática a una función @tool.

    Uso:
        @tool
        @audited
        def my_tool(arg1: str) -> str:
            ...

    O aplicado programáticamente:
        tools = [audited(t) for t in ALL_TOOLS]
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        tool_name = getattr(func, "tool_name", None) or func.__name__
        start = time.perf_counter()
        error = None
        result = ""

        try:
            result = func(*args, **kwargs)
            return result
        except Exception as e:
            error = f"{type(e).__name__}: {e}"
            raise
        finally:
            duration_ms = (time.perf_counter() - start) * 1000
            # Construir dict de args
            call_args = {}
            if args:
                import inspect
                sig = inspect.signature(func)
                params = list(sig.parameters.keys())
                for i, a in enumerate(args):
                    key = params[i] if i < len(params) else f"arg{i}"
                    call_args[key] = a
            call_args.update(kwargs)

            log_tool_call(
                tool_name=tool_name,
                args=call_args,
                result=str(result) if result else "",
                duration_ms=duration_ms,
                error=error,
            )

    return wrapper


# ─────────────────────────────────────────────────────────────────────────────
# Utilidades para consultar el log
# ─────────────────────────────────────────────────────────────────────────────


def get_session_summary(last_n: int = 50) -> str:
    """Lee las últimas N entradas del audit log y genera un resumen.

    Returns:
        str: Resumen legible de las últimas acciones del agente.
    """
    log_path = _get_log_path()
    if not log_path.exists():
        return "No hay audit log disponible."

    try:
        lines = log_path.read_text(encoding="utf-8").strip().splitlines()
        recent = lines[-last_n:] if len(lines) > last_n else lines
    except Exception as e:
        return f"Error leyendo audit log: {e}"

    entries = []
    for line in recent:
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue

    if not entries:
        return "Audit log vacío."

    # Generar resumen
    summary_parts = [
        f"=== AUDIT LOG (últimas {len(entries)} acciones) ===\n"
    ]

    for e in entries:
        ts = e.get("ts", "?")[:19].replace("T", " ")
        tool = e.get("tool", "?")
        args = e.get("args", {})
        success = "✅" if e.get("success") else "❌"
        duration = e.get("duration_ms", 0)

        args_short = ", ".join(f"{k}={v}" for k, v in list(args.items())[:3])
        summary_parts.append(
            f"  {ts} {success} {tool}({args_short}) [{duration:.0f}ms]"
        )

    return "\n".join(summary_parts)
