"""
loader.py — Descubrimiento y carga dinámica de plugins.

Escanea agent/plugins/ buscando clases que hereden de BasePlugin,
las instancia y ejecuta setup(). Proporciona acceso unificado a
todas las tools, event_handlers y schedules registrados.
"""

from __future__ import annotations

import importlib
import inspect
import logging
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Type

from agent.plugins.base import BasePlugin, EventHandler, ScheduleConfig

logger = logging.getLogger(__name__)

PLUGINS_DIR = Path(__file__).resolve().parent


class PluginLoader:
    """Carga y gestiona plugins dinámicamente.

    Uso:
        loader = PluginLoader()
        loader.discover()                    # Auto-descubre plugins
        loader.load_plugin(MyPlugin)         # O carga manualmente

        all_tools = loader.all_tools()       # Todas las tools combinadas
        all_handlers = loader.all_events()   # Todos los event handlers
        all_schedules = loader.all_schedules()  # Todas las tareas
    """

    def __init__(self):
        self._plugins: Dict[str, BasePlugin] = {}
        self._load_order: List[str] = []

    @property
    def plugins(self) -> Dict[str, BasePlugin]:
        """Plugins cargados por nombre."""
        return dict(self._plugins)

    def discover(self, plugins_dir: Optional[Path] = None) -> List[str]:
        """Auto-descubre y carga plugins desde el directorio.

        Busca archivos .py que contengan clases heredando de BasePlugin.
        Excluye: __init__.py, base.py, loader.py, archivos con _ prefix.

        Args:
            plugins_dir: Directorio a escanear. Default: agent/plugins/

        Returns:
            Lista de nombres de plugins cargados.
        """
        search_dir = plugins_dir or PLUGINS_DIR
        loaded = []

        for py_file in sorted(search_dir.glob("*.py")):
            # Skip internos
            if py_file.name.startswith("_") or py_file.name in (
                "__init__.py", "base.py", "loader.py"
            ):
                continue

            try:
                module_name = f"agent.plugins.{py_file.stem}"
                module = importlib.import_module(module_name)

                # Buscar clases que hereden de BasePlugin
                for _, obj in inspect.getmembers(module, inspect.isclass):
                    if (
                        issubclass(obj, BasePlugin)
                        and obj is not BasePlugin
                        and obj.meta.name != "unnamed"
                    ):
                        self.load_plugin(obj)
                        loaded.append(obj.meta.name)

            except Exception as e:
                logger.warning(f"Error cargando plugin {py_file.name}: {e}")

        return loaded

    def load_plugin(self, plugin_class: Type[BasePlugin]) -> Optional[BasePlugin]:
        """Instancia y configura un plugin.

        Args:
            plugin_class: Clase del plugin a cargar.

        Returns:
            Instancia del plugin, o None si falla.
        """
        try:
            instance = plugin_class()
            name = instance.name

            # Verificar dependencias
            for dep in instance.meta.dependencies:
                if dep not in self._plugins:
                    logger.warning(
                        f"Plugin '{name}' requiere '{dep}' que no está cargado"
                    )
                    return None

            # Setup
            instance.setup()
            self._plugins[name] = instance
            self._load_order.append(name)

            logger.info(
                f"Plugin '{name}' v{instance.meta.version} cargado "
                f"({len(instance.tools)} tools, "
                f"{len(instance.event_handlers)} events, "
                f"{len(instance.schedules)} schedules)"
            )
            return instance

        except Exception as e:
            logger.error(f"Error inicializando plugin {plugin_class}: {e}")
            return None

    def unload_plugin(self, name: str) -> bool:
        """Descarga un plugin y ejecuta su teardown.

        Args:
            name: Nombre del plugin a descargar.

        Returns:
            True si se descargó correctamente.
        """
        plugin = self._plugins.get(name)
        if not plugin:
            return False

        try:
            plugin.teardown()
        except Exception as e:
            logger.warning(f"Error en teardown de '{name}': {e}")

        del self._plugins[name]
        if name in self._load_order:
            self._load_order.remove(name)
        return True

    def get_plugin(self, name: str) -> Optional[BasePlugin]:
        """Obtiene un plugin por nombre."""
        return self._plugins.get(name)

    def all_tools(self) -> List[Callable]:
        """Retorna todas las tools de todos los plugins activos."""
        tools = []
        for plugin in self._plugins.values():
            if plugin.enabled:
                tools.extend(plugin.tools)
        return tools

    def all_events(self) -> List[EventHandler]:
        """Retorna todos los event handlers de plugins activos."""
        handlers = []
        for plugin in self._plugins.values():
            if plugin.enabled:
                handlers.extend(plugin.event_handlers)
        return handlers

    def all_schedules(self) -> List[ScheduleConfig]:
        """Retorna todas las tareas programadas de plugins activos."""
        schedules = []
        for plugin in self._plugins.values():
            if plugin.enabled:
                schedules.extend(plugin.schedules)
        return schedules

    def events_for_type(self, event_type: str) -> List[EventHandler]:
        """Retorna handlers que manejan un tipo de evento específico."""
        return [
            h for h in self.all_events()
            if h.event_type == event_type
        ]

    def summary(self) -> str:
        """Resumen de plugins cargados."""
        if not self._plugins:
            return "No hay plugins cargados."

        lines = [f"=== PLUGINS ({len(self._plugins)}) ===\n"]
        for name in self._load_order:
            p = self._plugins[name]
            status = "✅" if p.enabled else "⏸️"
            lines.append(
                f"  {status} {name} v{p.meta.version} — "
                f"{p.meta.description or '(sin descripción)'}"
            )
            if p.tools:
                tool_names = [t.__name__ for t in p.tools]
                lines.append(f"      Tools: {', '.join(tool_names)}")
            if p.event_handlers:
                lines.append(f"      Events: {len(p.event_handlers)} handler(s)")
            if p.schedules:
                sched_names = [s.name for s in p.schedules]
                lines.append(f"      Schedules: {', '.join(sched_names)}")

        return "\n".join(lines)
