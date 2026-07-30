"""
_result.py — Resultado estructurado para tools del agente.

Todas las tools retornan un ToolResult en vez de strings crudos.
El agente recibe datos estructurados que puede formatear inteligentemente.

Backward compatible: ToolResult.__str__() retorna el texto formateado,
así Strands SDK sigue funcionando sin cambios.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class Status(str, Enum):
    """Estado del resultado de una tool."""
    OK = "ok"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class ToolResult:
    """Resultado estructurado de una herramienta del agente.

    Attributes:
        success: Si la operación fue exitosa.
        message: Mensaje principal para el usuario (texto formateado).
        status: Estado semántico (ok, warning, error).
        data: Datos estructurados opcionales (dict, list, etc.)
              que el agente puede usar para razonar sobre el resultado.
        suggestions: Lista de acciones sugeridas como siguiente paso.
        elapsed_ms: Tiempo de ejecución en milisegundos (opcional).
        tool_name: Nombre de la tool que generó el resultado.
    """
    success: bool
    message: str
    status: Status = Status.OK
    data: Dict[str, Any] = field(default_factory=dict)
    suggestions: List[str] = field(default_factory=list)
    elapsed_ms: Optional[float] = None
    tool_name: str = ""

    def __str__(self) -> str:
        """Formato string para backward compat con Strands SDK."""
        return self.message

    def __repr__(self) -> str:
        return (
            f"ToolResult(success={self.success}, status={self.status.value}, "
            f"tool={self.tool_name!r}, data_keys={list(self.data.keys())})"
        )

    @classmethod
    def ok(
        cls,
        message: str,
        data: Optional[Dict[str, Any]] = None,
        suggestions: Optional[List[str]] = None,
        tool_name: str = "",
        elapsed_ms: Optional[float] = None,
    ) -> "ToolResult":
        """Atajo para resultado exitoso."""
        return cls(
            success=True,
            message=message,
            status=Status.OK,
            data=data or {},
            suggestions=suggestions or [],
            elapsed_ms=elapsed_ms,
            tool_name=tool_name,
        )

    @classmethod
    def warn(
        cls,
        message: str,
        data: Optional[Dict[str, Any]] = None,
        suggestions: Optional[List[str]] = None,
        tool_name: str = "",
    ) -> "ToolResult":
        """Atajo para resultado con advertencia."""
        return cls(
            success=True,
            message=message,
            status=Status.WARNING,
            data=data or {},
            suggestions=suggestions or [],
            tool_name=tool_name,
        )

    @classmethod
    def error(
        cls,
        message: str,
        data: Optional[Dict[str, Any]] = None,
        suggestions: Optional[List[str]] = None,
        tool_name: str = "",
    ) -> "ToolResult":
        """Atajo para resultado de error."""
        return cls(
            success=False,
            message=message,
            status=Status.ERROR,
            data=data or {},
            suggestions=suggestions or [],
            tool_name=tool_name,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Serializa a dict (útil para logging/audit)."""
        return {
            "success": self.success,
            "status": self.status.value,
            "message": self.message,
            "data": self.data,
            "suggestions": self.suggestions,
            "elapsed_ms": self.elapsed_ms,
            "tool_name": self.tool_name,
        }


class Timer:
    """Context manager para medir tiempo de ejecución.

    Uso:
        with Timer() as t:
            # ... operación ...
        result = ToolResult.ok("Listo", elapsed_ms=t.elapsed_ms)
    """
    def __init__(self):
        self.start: float = 0
        self.end: float = 0

    def __enter__(self) -> Timer:
        self.start = time.perf_counter()
        return self

    def __exit__(self, *_):
        self.end = time.perf_counter()

    @property
    def elapsed_ms(self) -> float:
        """Tiempo transcurrido en milisegundos."""
        return (self.end - self.start) * 1000
