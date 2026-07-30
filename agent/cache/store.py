"""
store.py — Cache key-value en memoria con TTL.

Thread-safe, con persistencia opcional a disco (JSON).
"""

from __future__ import annotations

import json
import threading
import time
from pathlib import Path
from typing import Any, Dict, Optional


class Cache:
    """Cache en memoria con TTL y persistencia opcional.

    Uso:
        cache = Cache(ttl_seconds=300)
        cache.set("ports.used", [1883, 8083, 18083])
        cache.get("ports.used")  # Lista o None si expiró
        cache.invalidate("ports.used")
    """

    def __init__(
        self,
        ttl_seconds: int = 300,
        persist_path: Optional[Path] = None,
    ):
        """
        Args:
            ttl_seconds: Tiempo de vida por defecto (5 min).
            persist_path: Si se pasa, guarda cache en JSON.
        """
        self._store: Dict[str, Dict[str, Any]] = {}
        self._ttl = ttl_seconds
        self._persist_path = persist_path
        self._lock = threading.Lock()
        self._hits = 0
        self._misses = 0

        if persist_path and persist_path.exists():
            self._load_from_disk()

    def get(self, key: str) -> Optional[Any]:
        """Obtiene un valor. Retorna None si no existe o expiró."""
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                self._misses += 1
                return None
            if time.time() >= entry["expires"]:
                del self._store[key]
                self._misses += 1
                return None
            self._hits += 1
            return entry["value"]

    def set(
        self, key: str, value: Any, ttl: Optional[int] = None
    ) -> None:
        """Guarda un valor con TTL opcional."""
        with self._lock:
            self._store[key] = {
                "value": value,
                "expires": time.time() + (ttl or self._ttl),
                "created": time.time(),
            }
        if self._persist_path:
            self._save_to_disk()

    def invalidate(self, key: str) -> bool:
        """Invalida una entrada. Retorna True si existía."""
        with self._lock:
            if key in self._store:
                del self._store[key]
                return True
            return False

    def invalidate_prefix(self, prefix: str) -> int:
        """Invalida todas las claves con un prefijo."""
        with self._lock:
            keys = [k for k in self._store if k.startswith(prefix)]
            for k in keys:
                del self._store[k]
            return len(keys)

    def clear(self) -> None:
        """Limpia todo el cache."""
        with self._lock:
            self._store.clear()
            self._hits = 0
            self._misses = 0

    def keys(self) -> list:
        """Retorna claves no expiradas."""
        now = time.time()
        with self._lock:
            return [
                k for k, v in self._store.items()
                if now <= v["expires"]
            ]

    @property
    def stats(self) -> Dict[str, Any]:
        """Estadísticas del cache."""
        with self._lock:
            now = time.time()
            valid = sum(
                1 for v in self._store.values()
                if now <= v["expires"]
            )
            return {
                "entries": len(self._store),
                "valid": valid,
                "expired": len(self._store) - valid,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": (
                    f"{self._hits / (self._hits + self._misses) * 100:.0f}%"
                    if (self._hits + self._misses) > 0 else "N/A"
                ),
            }

    def _save_to_disk(self) -> None:
        """Persiste cache a JSON."""
        if not self._persist_path:
            return
        try:
            self._persist_path.parent.mkdir(parents=True, exist_ok=True)
            data = json.dumps(self._store, default=str)
            self._persist_path.write_text(data, encoding="utf-8")
        except Exception:
            pass

    def _load_from_disk(self) -> None:
        """Carga cache desde JSON."""
        if not self._persist_path or not self._persist_path.exists():
            return
        try:
            data = json.loads(
                self._persist_path.read_text(encoding="utf-8")
            )
            self._store = data
        except Exception:
            pass
