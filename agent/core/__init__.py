"""
agent/core/ — Capa de lógica de negocio del agente NAS.

Los tools (@tool) son wrappers delgados que delegan a estos managers.
Esto permite:
- Reutilizar lógica sin duplicar código
- Testear sin depender de Strands SDK
- Desacoplar la interfaz (tools) de la implementación (core)

Importar directamente desde los módulos:
    from agent.core.service_manager import ServiceManager
    from agent.core.compose_manager import ComposeManager
    from agent.core.backup_manager import BackupManager
"""
