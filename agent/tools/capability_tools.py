"""Tools de descubrimiento de capacidades sin ejecutar mutaciones."""
from __future__ import annotations

import json
from typing import Optional

from strands.tools import tool

from agent.tools.capabilities import _operations


@tool
def discover_capabilities(query: str = "", service: Optional[str] = None) -> str:
    """Descubre comandos reales y sus restricciones desde manifests versionados.

    Esta tool solo consulta el índice; nunca ejecuta el comando encontrado.
    Para operaciones mutantes devuelve el guard `--confirm` y las evidencias que
    deben leerse antes de actuar.
    """
    needle = query.lower().strip()
    matches = []
    for item in _operations():
        if service and item.get("service") != service:
            continue
        haystack = " ".join(
            str(item.get(key, ""))
            for key in ("id", "command", "service", "description")
        ).lower()
        if needle and needle not in haystack:
            continue
        matches.append(
            {
                "id": item.get("id"),
                "service": item.get("service"),
                "command": item.get("command"),
                "mode": item.get("mode"),
                "requires_confirmation": item.get("confirm", False),
                "description": item.get("description", ""),
                "evidence": item.get("evidence", []),
                "entrypoint_connected": item.get("source_exists", False)
                and item.get("dispatch_exists", False)
                and item.get("guard_valid", False),
                "dispatch_exists": item.get("dispatch_exists", False),
                "guard_valid": item.get("guard_valid", False),
            }
        )
    return json.dumps({"capabilities": matches}, ensure_ascii=False, indent=2)
