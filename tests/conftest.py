"""
conftest.py — Configuración de pytest.

Mocks strands SDK para poder correr tests sin tener strands instalado.
En el NAS con strands instalado, estos mocks no se aplican.
"""

import sys
from unittest.mock import MagicMock
from types import ModuleType


def _mock_strands():
    """Instala módulos mock de strands si no están disponibles."""
    try:
        import strands  # noqa: F401
        return  # Ya está instalado, no hacer nada
    except ImportError:
        pass

    # Crear módulos mock
    strands_mod = MagicMock()
    strands_tools_mod = MagicMock()

    # Mock del decorador @tool: simplemente retorna la función sin modificar
    def tool_decorator(fn):
        return fn

    strands_tools_mod.tool = tool_decorator

    # Registrar en sys.modules
    sys.modules["strands"] = strands_mod
    sys.modules["strands.tools"] = strands_tools_mod
    sys.modules["strands.Agent"] = MagicMock()
    sys.modules["strands.session"] = MagicMock()
    sys.modules["strands.session.file_session_manager"] = MagicMock()


# Ejecutar antes de cualquier import
_mock_strands()
