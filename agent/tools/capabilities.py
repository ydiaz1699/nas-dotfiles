"""Consulta el inventario dinámico de capacidades del NAS.

No ejecuta operaciones de servicio. Lee manifests versionados y el índice
estructural; los comandos mutantes solo se muestran con sus guards.
"""
from __future__ import annotations

import argparse
import json
import importlib.util
from pathlib import Path
from typing import Any, Dict, Iterable, List

HERE = Path(__file__).resolve()
NAS_DOTFILES = HERE.parents[2]
CAPABILITIES_DIR = NAS_DOTFILES / "agent" / "capabilities"
INDEX_FILE = NAS_DOTFILES / "agent" / "cache" / "project-index.json"


def _manifests() -> Iterable[Dict[str, Any]]:
    for path in sorted(CAPABILITIES_DIR.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        data["manifest"] = str(path.relative_to(NAS_DOTFILES))
        yield data


def _index() -> Dict[str, Any]:
    """Construye el índice actual para no servir dispatch obsoleto desde cache."""
    index_path = NAS_DOTFILES / "agent" / "tools" / "project_index.py"
    try:
        spec = importlib.util.spec_from_file_location("project_index", index_path)
        if spec is None or spec.loader is None:
            raise ImportError("No se pudo cargar project_index.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.build_index()
    except (ImportError, OSError, AttributeError, TypeError, ValueError):
        # El cache solo es fallback cuando el índice no puede regenerarse; así
        # una modificación local no queda oculta por un JSON antiguo.
        if INDEX_FILE.exists():
            try:
                return json.loads(INDEX_FILE.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                pass
        return {}


def _operations() -> List[Dict[str, Any]]:
    result: List[Dict[str, Any]] = []
    index = _index()
    indexed = index.get("capabilities", {})
    index_available = bool(indexed)
    indexed_manifests = {item.get("manifest") for item in indexed.get("manifests", [])}
    indexed_operations = {
        (item.get("manifest"), item.get("id")): item
        for item in indexed.get("operations", [])
    }
    for manifest in _manifests():
        source = manifest.get("source", "")
        source_exists = (NAS_DOTFILES / source).exists()
        for operation in manifest.get("operations", []):
            item = dict(operation)
            item["service"] = manifest.get("service", "")
            item["source"] = source
            item["source_exists"] = source_exists
            item["manifest"] = manifest["manifest"]
            item["indexed"] = index_available and manifest["manifest"] in indexed_manifests
            indexed_item = indexed_operations.get((manifest["manifest"], item.get("id")))
            if indexed_item is not None:
                item["dispatch_exists"] = indexed_item.get("dispatch_exists", False)
                item["guard_valid"] = indexed_item.get("guard_valid", False)
            else:
                # Fail closed: sin índice fresco no se afirma que el dispatch
                # o el guard estén conectados, aunque el manifest exista.
                item["dispatch_exists"] = False
                item["guard_valid"] = False
            result.append(item)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Descubre comandos y capacidades reales del proyecto")
    parser.add_argument("query", nargs="?", help="Filtrar por comando, servicio, id o descripción")
    parser.add_argument("--service", help="Filtrar por servicio")
    parser.add_argument("--json", action="store_true", help="Emitir JSON estructurado")
    args = parser.parse_args()

    query = (args.query or "").lower()
    operations = []
    for item in _operations():
        haystack = " ".join(str(item.get(key, "")) for key in ("id", "command", "service", "description"))
        if args.service and item.get("service") != args.service:
            continue
        if query and query not in haystack.lower():
            continue
        operations.append(item)

    if args.json:
        print(json.dumps({"capabilities": operations}, indent=2, ensure_ascii=False))
        return 0

    if not operations:
        print("No se encontraron capacidades.")
        return 1
    print("Capacidades descubiertas desde manifests e índice estructural:")
    for item in operations:
        guard = "requiere --confirm" if item.get("confirm") else "solo lectura/backup"
        state = (
            "conectada"
            if item.get("source_exists")
            and item.get("dispatch_exists", True)
            and item.get("guard_valid", True)
            else "sin entrypoint/dispatch/guard"
        )
        print(f"  - {item['command']:<44} [{guard}] [{state}]")
        print(f"    {item.get('description', '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
