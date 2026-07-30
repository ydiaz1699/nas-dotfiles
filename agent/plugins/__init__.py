"""
agent/plugins/ — Sistema de plugins dinámicos.

Cada plugin es un módulo Python que hereda de BasePlugin y registra:
- tools: funciones @tool que el agente puede invocar
- events: handlers que responden a eventos del event bus
- schedules: tareas periódicas (cron-like)

El PluginLoader descubre y carga plugins automáticamente al iniciar.

Uso:
    from agent.plugins import PluginLoader

    loader = PluginLoader()
    loader.discover()       # Escanea agent/plugins/*.py
    tools = loader.tools()  # Retorna todas las tools registradas
"""

from agent.plugins.base import BasePlugin, PluginMeta
from agent.plugins.loader import PluginLoader

__all__ = ["BasePlugin", "PluginMeta", "PluginLoader"]
