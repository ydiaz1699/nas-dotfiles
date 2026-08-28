"""
project_index.py — Índice estructural del ecosistema nas-dotfiles + DebMenux.

El índice responde qué existe y dónde está conectado. No ejecuta Docker ni lee
los datos desplegados de $DOCKER_BASE. Se limita a los dos repositorios de código
para que el scanner pueda comparar la arquitectura real con contracts.json.

Uso:
    python3 agent/tools/project_index.py
    python3 agent/tools/project_index.py --check
    python3 agent/tools/project_index.py --output /tmp/project-index.json
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple


NAS_DOTFILES = Path(os.environ.get("NAS_DOTFILES", Path(__file__).resolve().parents[2]))
DEBMENUX_ENV = os.environ.get("DEBMENUX_DIR", "")
DEBMENUX_DIR = Path(DEBMENUX_ENV) if DEBMENUX_ENV else NAS_DOTFILES.parent / "DebMenux-"
CONTRACTS_FILE = NAS_DOTFILES / "agent" / "architecture" / "contracts.json"
DEFAULT_OUTPUT = NAS_DOTFILES / "agent" / "cache" / "project-index.json"

SKIP_DIRS = {
    ".git",
    "__pycache__",
    ".venv",
    "node_modules",
    "cache",
}
SKIP_FILES = {
    ".env",
    ".env.agent",
    "project-index.json",
    "project-snapshot.json",
}


# ---------------------------------------------------------------------------
# Filesystem discovery
# ---------------------------------------------------------------------------


def _relative(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def _iter_repo_files(root: Path) -> Iterable[Tuple[str, Path]]:
    """Yield (repo-relative path, absolute path), excluding runtime/secrets."""
    if not root.exists():
        return

    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        try:
            relative_parts = path.relative_to(root).parts
        except ValueError:
            continue
        if any(part in SKIP_DIRS for part in relative_parts):
            continue
        if path.name in SKIP_FILES:
            continue
        if path.name.endswith((".pyc", ".log")):
            continue
        yield _relative(path, root), path


def _classify_path(relative: str, repo: str) -> str:
    """Clasifica un path sin interpretar todavía su contenido."""
    if repo == "debmenux":
        if relative == "services.json":
            return "debmenux_registry"
        if relative.startswith("scripts/services/") and relative.endswith(".sh"):
            return "debmenux_service"
        if relative.startswith("lib/") and relative.endswith(".sh"):
            return "debmenux_library"
        if relative.startswith("templates/"):
            return "debmenux_template"
        if relative.endswith(".md"):
            return "documentation"
        return "other"

    if relative == "docker/cli/svc.sh":
        return "bash_cli"
    if relative.startswith("docker/cli/lib/") and relative.endswith(".sh"):
        return "bash_cli_library"
    if relative == "shell/lib/docker.sh":
        return "completion"
    if relative.startswith("shell/") and relative.endswith(".sh"):
        return "shell_module"
    if relative == "svc_py/app.py":
        return "python_cli"
    if relative.startswith("svc_py/") and relative.endswith(".py"):
        return "python_cli_module"
    if relative.startswith("agent/tools/") and relative.endswith(".py"):
        return "agent_tool"
    if relative.startswith("agent/capabilities/") and relative.endswith(".json"):
        return "capability_manifest"
    if relative == "agent/nas_agent.py":
        return "agent_prompt"
    if relative == "agent/lobehub_mcp.py":
        return "mcp_gateway"
    if relative.startswith("agent/mcp/"):
        return "mcp_gateway"
    if relative.startswith("systemd/lobehub-mcp"):
        return "mcp_gateway"
    if relative.startswith("agent/plugins/") and relative.endswith(".py"):
        return "agent_plugin"
    if relative.startswith("agent/catalog/services/") and relative.endswith("/compose.yml"):
        return "catalog_compose"
    if relative.startswith("agent/catalog/services/") and relative.endswith("/ficha.md"):
        return "catalog_ficha"
    if relative.startswith("docs/services/") and relative.endswith("-guide.md"):
        return "service_guide"
    if relative.startswith("docs/"):
        return "documentation"
    if relative.startswith(".kiro/hooks/"):
        return "hook"
    if relative.startswith("docker-nas/"):
        return "skill_reference"
    if relative.endswith(".yml") or relative.endswith(".yaml"):
        return "compose_or_yaml"
    if relative.endswith(".md"):
        return "documentation"
    return "other"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(65536), b""):
                digest.update(chunk)
    except OSError:
        return ""
    return digest.hexdigest()


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


def _file_records() -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    roots = (("nas_dotfiles", NAS_DOTFILES), ("debmenux", DEBMENUX_DIR))
    for repo, root in roots:
        for relative, path in _iter_repo_files(root):
            records.append(
                {
                    "repo": repo,
                    "path": relative,
                    "type": _classify_path(relative, repo),
                    "sha256": _sha256(path),
                    "size": path.stat().st_size,
                }
            )
    return records


# ---------------------------------------------------------------------------
# Source extraction
# ---------------------------------------------------------------------------


def _extract_bash_commands(path: Path) -> Set[str]:
    content = _read_text(path)
    return set(re.findall(r"^\s+([a-z][\w-]*)\)", content, re.MULTILINE))


def _extract_python_commands(path: Path) -> Set[str]:
    """Extrae app.command(...) y decoradores @app.command(...), sin importar Typer."""
    content = _read_text(path)
    if not content:
        return set()
    try:
        tree = ast.parse(content, filename=str(path))
    except SyntaxError:
        return set()

    commands: Set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if (
                isinstance(func, ast.Attribute)
                and isinstance(func.value, ast.Name)
                and func.value.id == "app"
                and func.attr == "command"
                and node.args
                and isinstance(node.args[0], ast.Constant)
                and isinstance(node.args[0].value, str)
            ):
                commands.add(node.args[0].value)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for decorator in node.decorator_list:
                if (
                    isinstance(decorator, ast.Call)
                    and isinstance(decorator.func, ast.Attribute)
                    and isinstance(decorator.func.value, ast.Name)
                    and decorator.func.value.id == "app"
                    and decorator.func.attr == "command"
                    and decorator.args
                    and isinstance(decorator.args[0], ast.Constant)
                    and isinstance(decorator.args[0].value, str)
                ):
                    commands.add(decorator.args[0].value)
    return commands


def _extract_completion_commands(path: Path) -> Dict[str, Set[str]]:
    content = _read_text(path)
    result: Dict[str, Set[str]] = {"global": set(), "service": set()}
    global_match = re.search(r"_SVC_GLOBAL_CMDS=\"([^\"]*)\"", content, re.DOTALL)
    service_match = re.search(r"_SVC_SERVICE_CMDS=\"([^\"]*)\"", content, re.DOTALL)
    if global_match:
        result["global"].update(global_match.group(1).split())
    if service_match:
        result["service"].update(service_match.group(1).split())
    return result


def _extract_prompt_commands(path: Path) -> Set[str]:
    content = _read_text(path)
    if not content:
        return set()
    return set(re.findall(r"`svc\s+([a-z][\w-]*)", content))


def _extract_registered_tools(path: Path) -> Set[str]:
    content = _read_text(path)
    if not content:
        return set()
    try:
        tree = ast.parse(content, filename=str(path))
    except SyntaxError:
        return set()

    tools: Set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        if not any(isinstance(target, ast.Name) and target.id == "ALL_TOOLS" for target in node.targets):
            continue
        if not isinstance(node.value, (ast.List, ast.Tuple)):
            continue
        for item in node.value.elts:
            if isinstance(item, ast.Name):
                tools.add(item.id)
    return tools


def _extract_capabilities() -> Dict[str, Any]:
    """Carga manifests versionados y verifica que cada entrypoint exista."""
    manifests: List[Dict[str, Any]] = []
    operations: List[Dict[str, Any]] = []
    capabilities_root = NAS_DOTFILES / "agent" / "capabilities"
    if not capabilities_root.exists():
        return {"manifests": [], "operations": []}

    for path in sorted(capabilities_root.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        source = str(data.get("source", ""))
        source_exists = bool(source) and (NAS_DOTFILES / source).exists()
        source_text = _read_text(NAS_DOTFILES / source) if source_exists else ""
        manifest = {
            "manifest": _relative(path, NAS_DOTFILES),
            "service": data.get("service", ""),
            "source": source,
            "source_exists": source_exists,
            "description": data.get("description", ""),
        }
        manifests.append(manifest)
        for operation in data.get("operations", []):
            item = dict(operation)
            operation_id = str(item.get("id", ""))
            action = operation_id.rsplit(".", 1)[-1]
            # Para entrypoints Bash, comprobar también el case dispatch y no
            # limitarse a que exista el archivo compartido.
            if source_exists and source.endswith(".sh"):
                dispatch_exists = bool(
                    re.search(
                        rf"^\s*(?:[\w-]+\|)*{re.escape(action)}(?:\|[\w-]+)*\)",
                        source_text,
                        re.MULTILINE,
                    )
                )
            else:
                dispatch_exists = source_exists
            mode = str(item.get("mode", ""))
            declared_confirm = bool(item.get("confirm"))
            command_has_confirm = "--confirm" in str(item.get("command", ""))
            guard_valid = (
                (mode == "mutating" and declared_confirm and command_has_confirm)
                or (mode in {"read_only", "backup"} and not declared_confirm and not command_has_confirm)
            )
            item.update({
                "service": data.get("service", ""),
                "manifest": manifest["manifest"],
                "source_exists": source_exists,
                "dispatch_exists": dispatch_exists,
                "guard_valid": guard_valid,
            })
            operations.append(item)

    return {"manifests": manifests, "operations": operations}


def _extract_service_ids() -> Dict[str, Dict[str, Any]]:
    catalog: Dict[str, Dict[str, Any]] = {}
    catalog_root = NAS_DOTFILES / "agent" / "catalog" / "services"
    guides_root = NAS_DOTFILES / "docs" / "services"
    scripts_root = DEBMENUX_DIR / "scripts" / "services"

    if catalog_root.exists():
        for service_dir in sorted(catalog_root.iterdir()):
            if not service_dir.is_dir() or service_dir.name.startswith("."):
                continue
            entry = catalog.setdefault(service_dir.name, {"id": service_dir.name})
            entry["catalog"] = True
            entry["catalog_ficha"] = (service_dir / "ficha.md").exists()
            entry["catalog_compose"] = (service_dir / "compose.yml").exists()
            entry["catalog_env_example"] = (service_dir / ".env.example").exists()

    if guides_root.exists():
        for guide in guides_root.glob("*-guide.md"):
            service_id = guide.name[: -len("-guide.md")]
            catalog.setdefault(service_id, {"id": service_id})["guide"] = True

    if scripts_root.exists():
        for script in scripts_root.glob("*.sh"):
            if script.name == "_template.sh":
                continue
            service_id = script.stem
            catalog.setdefault(service_id, {"id": service_id})["debmenux_script"] = True

    registry_path = DEBMENUX_DIR / "services.json"
    registry_ids: Set[str] = set()
    registry_valid = False
    if registry_path.exists():
        try:
            data = json.loads(_read_text(registry_path))
            registry_ids = {
                str(item.get("id"))
                for item in data.get("services", [])
                if isinstance(item, dict) and item.get("id")
            }
            registry_valid = True
        except (json.JSONDecodeError, TypeError):
            registry_valid = False

    for service_id in registry_ids:
        catalog.setdefault(service_id, {"id": service_id})["debmenux_registry"] = True

    for entry in catalog.values():
        entry.setdefault("catalog", False)
        entry.setdefault("catalog_ficha", False)
        entry.setdefault("catalog_compose", False)
        entry.setdefault("catalog_env_example", False)
        entry.setdefault("guide", False)
        entry.setdefault("debmenux_script", False)
        entry.setdefault("debmenux_registry", False)

    return {
        "services": sorted(catalog.values(), key=lambda item: item["id"]),
        "registry": {
            "path": _relative(registry_path, NAS_DOTFILES.parent) if registry_path.exists() else "../DebMenux-/services.json",
            "valid_json": registry_valid,
            "ids": sorted(registry_ids),
        },
    }


# ---------------------------------------------------------------------------
# Contract resolution
# ---------------------------------------------------------------------------


def _load_contracts() -> Dict[str, Any]:
    try:
        return json.loads(CONTRACTS_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _resolve_contract_path(relative: str) -> Path:
    if relative.startswith("../DebMenux-"):
        return NAS_DOTFILES.parent / relative.removeprefix("../")
    return NAS_DOTFILES / relative


def _contract_connections(contracts: Dict[str, Any]) -> List[Dict[str, Any]]:
    connections: List[Dict[str, Any]] = []
    for contract in contracts.get("connection_contracts", []):
        required = contract.get("required", [])
        statuses = []
        for relative in required:
            path = _resolve_contract_path(relative)
            statuses.append(
                {
                    "path": relative,
                    "exists": path.exists(),
                    "type": _classify_path(relative, "debmenux" if relative.startswith("../DebMenux-") else "nas_dotfiles"),
                }
            )
        connections.append(
            {
                "id": contract.get("id", "unknown"),
                "entity": contract.get("entity", "unknown"),
                "name": contract.get("name", ""),
                "level": contract.get("level", "documentation"),
                "required": statuses,
                "complete": all(item["exists"] for item in statuses),
            }
        )
    return connections


def _cli_index() -> Dict[str, Any]:
    bash_path = NAS_DOTFILES / "docker" / "cli" / "svc.sh"
    python_path = NAS_DOTFILES / "svc_py" / "app.py"
    completion_path = NAS_DOTFILES / "shell" / "lib" / "docker.sh"
    prompt_path = NAS_DOTFILES / "agent" / "nas_agent.py"
    tools_path = NAS_DOTFILES / "agent" / "tools" / "__init__.py"

    bash_commands = _extract_bash_commands(bash_path) if bash_path.exists() else set()
    python_commands = _extract_python_commands(python_path) if python_path.exists() else set()
    completion = _extract_completion_commands(completion_path) if completion_path.exists() else {"global": set(), "service": set()}
    prompt_commands = _extract_prompt_commands(prompt_path) if prompt_path.exists() else set()
    registered_tools = _extract_registered_tools(tools_path) if tools_path.exists() else set()

    return {
        "bash": {
            "path": "docker/cli/svc.sh",
            "commands": sorted(bash_commands),
        },
        "python": {
            "path": "svc_py/app.py",
            "commands": sorted(python_commands),
        },
        "completion": {
            "path": "shell/lib/docker.sh",
            "global_commands": sorted(completion["global"]),
            "service_commands": sorted(completion["service"]),
        },
        "agent_prompt": {
            "path": "agent/nas_agent.py",
            "commands": sorted(prompt_commands),
        },
        "registered_tools": {
            "path": "agent/tools/__init__.py",
            "tools": sorted(registered_tools),
        },
        "parity": {
            "bash_only": sorted(bash_commands - python_commands),
            "python_only": sorted(python_commands - bash_commands),
            "bash_and_python": sorted(bash_commands & python_commands),
            "bash_missing_completion": sorted(bash_commands - completion["global"] - completion["service"]),
            "bash_missing_agent_prompt": sorted(bash_commands - prompt_commands),
        },
    }


def build_index() -> Dict[str, Any]:
    contracts = _load_contracts()
    files = _file_records()
    service_data = _extract_service_ids()
    capabilities = _extract_capabilities()
    cli = _cli_index()
    connections = _contract_connections(contracts)

    return {
        "schema_version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "roots": {
            "nas_dotfiles": str(NAS_DOTFILES),
            "debmenux": str(DEBMENUX_DIR),
        },
        "contracts_file": "agent/architecture/contracts.json",
        "summary": {
            "files": len(files),
            "nas_dotfiles_files": sum(1 for item in files if item["repo"] == "nas_dotfiles"),
            "debmenux_files": sum(1 for item in files if item["repo"] == "debmenux"),
            "services": len(service_data["services"]),
            "capabilities": len(capabilities["operations"]),
            "contract_connections": len(connections),
            "broken_contract_connections": sum(1 for item in connections if not item["complete"]),
        },
        "files": files,
        "cli": cli,
        "services": service_data["services"],
        "capabilities": capabilities,
        "debmenux_registry": service_data["registry"],
        "connections": connections,
    }


def write_index(index: Dict[str, Any], output: Path = DEFAULT_OUTPUT) -> Path:
    """Escribe un índice ya construido y retorna su ruta."""
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(index, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description="Genera el índice estructural de nas-dotfiles + DebMenux")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Ruta del índice JSON generado")
    parser.add_argument("--check", action="store_true", help="Generar en memoria y mostrar resumen sin escribir")
    parser.add_argument("--json", action="store_true", help="Imprimir el índice completo en stdout")
    args = parser.parse_args()

    index = build_index()

    if args.json:
        print(json.dumps(index, indent=2, ensure_ascii=False))

    if args.check:
        print(
            "Project index: "
            f"{index['summary']['files']} archivos, "
            f"{index['summary']['services']} servicios, "
            f"{index['summary']['broken_contract_connections']} conexiones rotas"
        )
        return 0

    write_index(index, args.output)
    print(f"✅ Índice estructural generado: {args.output}")
    print(f"   Archivos: {index['summary']['files']}")
    print(f"   Servicios: {index['summary']['services']}")
    print(f"   Conexiones rotas: {index['summary']['broken_contract_connections']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
