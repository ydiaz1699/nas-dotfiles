"""
agent/cache/ — Cache ligero en memoria con persistencia opcional.

Key-value store para lookups frecuentes: estados de servicios,
mapas de puertos, resultados de scans recientes.

Evita llamar a Docker/ss/df en cada invocación del agente.

Uso:
    from agent.cache import Cache

    cache = Cache(ttl_seconds=300)  # 5 min TTL
    cache.set("services.list", [...])
    cache.get("services.list")      # None si expiró
"""

from agent.cache.store import Cache

__all__ = ["Cache"]
