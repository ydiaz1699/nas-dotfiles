"""
nas-agent — Agente inteligente para administración de NAS/Homelab

Basado en Strands Agents SDK. Usa auto-detección de servicios Docker,
catálogo local de configuraciones y web search como fallback para
crear, diagnosticar y administrar servicios en el NAS.

Uso:
    python -m agent.nas_agent "¿Qué servicios están caídos?"
    python -m agent.nas_agent "Quiero instalar Vaultwarden"
"""

__version__ = "1.0.0"
