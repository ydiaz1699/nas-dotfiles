"""
_index.py — Generador de índice del catálogo de servicios.

Lee todas las fichas .md en agent/catalog/services/, extrae el
frontmatter YAML de cada una, y genera un catalog.json indexado
que el agente puede consultar rápidamente sin parsear markdown.

Uso:
    python -m agent.catalog._index              # genera catalog.json
    python -m agent.catalog._index --check      # verifica sin escribir

También se puede importar y usar programáticamente:
    from agent.catalog._index import build_index, load_index
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import frontmatter
except ImportError:
    frontmatter = None

try:
    import yaml
except ImportError:
    yaml = None

# ─────────────────────────────────────────────────────────────────────────────

CATALOG_DIR = Path(__file__).resolve().parent
SERVICES_DIR = CATALOG_DIR / "services"
INDEX_FILE = CATALOG_DIR / "catalog.json"


def _parse_frontmatter(filepath: Path) -> Optional[Dict[str, Any]]:
    """Extrae frontmatter YAML de un archivo .md.

    Intenta usar python-frontmatter si está disponible,
    si no hace un parse manual del bloque entre ---.
    """
    content = filepath.read_text(encoding="utf-8")

    if frontmatter:
        post = frontmatter.loads(content)
        return dict(post.metadata) if post.metadata else None

    # Fallback: parse manual
    if not content.startswith("---"):
        return None

    parts = content.split("---", 2)
    if len(parts) < 3:
        return None

    if yaml:
        try:
            return yaml.safe_load(parts[1])
        except Exception:
            return None

    # Sin yaml ni frontmatter — no podemos parsear
    return None


def build_index() -> Dict[str, Any]:
    """Construye el índice del catálogo leyendo todas las fichas de servicios.

    Returns:
        dict con estructura:
        {
            "version": "1.0",
            "services_count": N,
            "services": {
                "emqx": { ...frontmatter... },
                "adguard": { ...frontmatter... },
            },
            "by_category": {
                "domótica": ["emqx", "homeassistant"],
                "red": ["adguard"],
            },
            "by_network": {
                "iot_net": ["emqx", "homeassistant"],
                "db_net": ["emqx", "datasql"],
            }
        }
    """
    services: Dict[str, Any] = {}
    by_category: Dict[str, List[str]] = {}
    by_network: Dict[str, List[str]] = {}

    if not SERVICES_DIR.exists():
        return {
            "version": "1.0",
            "services_count": 0,
            "services": {},
            "by_category": {},
            "by_network": {},
        }

    for md_file in sorted(SERVICES_DIR.glob("*.md")):
        if md_file.name.startswith(".") or md_file.name.startswith("_"):
            continue

        meta = _parse_frontmatter(md_file)
        if not meta or "id" not in meta:
            continue

        svc_id = meta["id"]
        services[svc_id] = meta

        # Indexar por categoría
        cat = meta.get("category", "otro")
        by_category.setdefault(cat, []).append(svc_id)

        # Indexar por red
        nets = meta.get("networks", [])
        if isinstance(nets, list):
            for net in nets:
                by_network.setdefault(net, []).append(svc_id)

    return {
        "version": "1.0",
        "services_count": len(services),
        "services": services,
        "by_category": by_category,
        "by_network": by_network,
    }


def write_index(index: Optional[Dict[str, Any]] = None) -> Path:
    """Genera catalog.json en disco.

    Args:
        index: Índice pre-construido. Si None, llama a build_index().

    Returns:
        Path al archivo generado.
    """
    if index is None:
        index = build_index()

    INDEX_FILE.write_text(
        json.dumps(index, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return INDEX_FILE


def load_index() -> Dict[str, Any]:
    """Carga el catalog.json desde disco.

    Si no existe, lo genera primero.

    Returns:
        dict con el índice del catálogo.
    """
    if not INDEX_FILE.exists():
        write_index()

    try:
        return json.loads(INDEX_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        # Regenerar si está corrupto
        index = build_index()
        write_index(index)
        return index


def lookup_service(service_id: str) -> Optional[Dict[str, Any]]:
    """Busca un servicio en el índice por su ID.

    Args:
        service_id: ID del servicio (ej. "emqx", "adguard").

    Returns:
        dict con la metadata del servicio, o None si no existe.
    """
    index = load_index()
    return index.get("services", {}).get(service_id)


def services_by_category(category: str) -> List[str]:
    """Lista servicios de una categoría.

    Args:
        category: Categoría a buscar (ej. "domótica", "red").

    Returns:
        Lista de IDs de servicios en esa categoría.
    """
    index = load_index()
    return index.get("by_category", {}).get(category, [])


def services_by_network(network: str) -> List[str]:
    """Lista servicios conectados a una red.

    Args:
        network: Red Docker (ej. "iot_net", "db_net").

    Returns:
        Lista de IDs de servicios en esa red.
    """
    index = load_index()
    return index.get("by_network", {}).get(network, [])


# ─────────────────────────────────────────────────────────────────────────────
# CLI entry point
# ─────────────────────────────────────────────────────────────────────────────

def main():
    """Punto de entrada CLI para generar el catálogo."""
    check_only = "--check" in sys.argv

    index = build_index()
    count = index["services_count"]

    if check_only:
        print(f"✓ Catálogo: {count} servicio(s) indexado(s)")
        for svc_id, meta in index["services"].items():
            cat = meta.get("category", "?")
            img = meta.get("image", "?")
            print(f"  • {svc_id} [{cat}] — {img}")
        if count == 0:
            print("  (vacío — agrega fichas en agent/catalog/services/)")
        return

    path = write_index(index)
    print(f"✅ catalog.json generado: {path}")
    print(f"   {count} servicio(s) indexado(s)")

    categories = index.get("by_category", {})
    if categories:
        print(f"   Categorías: {', '.join(sorted(categories.keys()))}")

    networks = index.get("by_network", {})
    if networks:
        print(f"   Redes: {', '.join(sorted(networks.keys()))}")


if __name__ == "__main__":
    main()
