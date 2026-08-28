"""
project_scanner.py — Detecta lagunas e inconsistencias en el ecosistema nas-dotfiles.

Escanea progresivamente (sin cargar todo en memoria) y verifica:
1. Servicios: compose ↔ ficha ↔ guía ↔ script DebMenux ↔ labels Homepage
2. CLI: comandos bash vs python (dual CLI parity)
3. Agente: tools registradas vs documentadas en prompt
4. Docs: guías referenciadas vs existentes
5. Config: IP hardcodeada, TZ duplicado, env_file faltante

Modos de ejecución:
- Full scan: verifica todo el proyecto (primera ejecución o --full)
- Incremental: usa git diff para solo procesar archivos que cambiaron

Uso como tool del agente:
    from agent.tools.project_scanner import project_scan
    result = project_scan()

Uso como CLI:
    python -m agent.tools.project_scanner [--verbose] [--json] [--full] [--changed]

Uso integrado en svc:
    svc scan              # incremental (si hay snapshot) o full (si no hay)
    svc scan --full       # forzar scan completo
    svc scan --changed    # solo mostrar qué cambió desde último scan
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURACIÓN
# ─────────────────────────────────────────────────────────────────────────────

NAS_DOTFILES = Path(os.environ.get("NAS_DOTFILES", "/nas-dotfiles"))
DOCKER_BASE = Path(os.environ.get("DOCKER_BASE", "/docker"))
DEBMENUX_DIR = Path(os.environ.get("DEBMENUX_DIR", "/debmenux"))

# Directorios del ecosistema
CATALOG_DIR = NAS_DOTFILES / "agent" / "catalog" / "services"
DOCS_DIR = NAS_DOTFILES / "docs" / "services"
SVC_SH = NAS_DOTFILES / "docker" / "cli" / "svc.sh"
SVC_PY_DIR = NAS_DOTFILES / "svc_py"
AGENT_FILE = NAS_DOTFILES / "agent" / "nas_agent.py"
TOOLS_INIT = NAS_DOTFILES / "agent" / "tools" / "__init__.py"
SKILL_FILE = NAS_DOTFILES / ".kiro" / "skills" / "dotfile-skill" / "SKILL.md"
DEBMENUX_SCRIPTS = DEBMENUX_DIR / "scripts" / "services"

# Alternativa: DebMenux como subdirectorio del workspace (para Kiro Web)
DEBMENUX_ALT = NAS_DOTFILES.parent / "DebMenux-" / "scripts" / "services"

# Snapshot para modo incremental
SNAPSHOT_FILE = NAS_DOTFILES / "agent" / "cache" / "project-snapshot.json"

# El índice arquitectónico es independiente del snapshot incremental.
try:
    _index_path = NAS_DOTFILES / "agent" / "tools" / "project_index.py"
    _index_spec = importlib.util.spec_from_file_location("nas_project_index", _index_path)
    if _index_spec is None or _index_spec.loader is None:
        raise ImportError(f"No se pudo cargar {_index_path}")
    _index_module = importlib.util.module_from_spec(_index_spec)
    _index_spec.loader.exec_module(_index_module)
    build_index = _index_module.build_index
    write_index = _index_module.write_index
except (ImportError, OSError, AttributeError):
    build_index = None
    write_index = None


# ─────────────────────────────────────────────────────────────────────────────
# SNAPSHOT & INCREMENTAL
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class Snapshot:
    """Estado guardado del último scan completo."""

    last_scan: str = ""
    last_commit: str = ""
    services: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    file_hashes: Dict[str, str] = field(default_factory=dict)

    def save(self, path: Path = SNAPSHOT_FILE) -> None:
        """Persiste el snapshot a disco."""
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "last_scan": self.last_scan,
            "last_commit": self.last_commit,
            "services": self.services,
            "file_hashes": self.file_hashes,
        }
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    @classmethod
    def load(cls, path: Path = SNAPSHOT_FILE) -> Optional["Snapshot"]:
        """Carga el snapshot previo si existe."""
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            snap = cls(
                last_scan=data.get("last_scan", ""),
                last_commit=data.get("last_commit", ""),
                services=data.get("services", {}),
                file_hashes=data.get("file_hashes", {}),
            )
            return snap
        except (json.JSONDecodeError, OSError):
            return None


def _get_current_commit() -> str:
    """Obtiene el hash del commit actual (HEAD)."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, timeout=5,
            cwd=str(NAS_DOTFILES),
        )
        return result.stdout.strip() if result.returncode == 0 else ""
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return ""


def _get_changed_files(since_commit: str) -> List[str]:
    """Obtiene archivos modificados desde un commit usando git diff."""
    if not since_commit:
        return []
    try:
        changed: List[str] = []
        commands: List[List[str]] = []
        if since_commit:
            # Comparar contra el commit del snapshot incluyendo el working tree;
            # usar ``... HEAD`` omitía modificaciones staged/unstaged no commit.
            commands.append(["git", "diff", "--name-only", since_commit])
        # Cubrir explícitamente cambios del índice y del árbol de trabajo cuando
        # el snapshot fue creado antes de un rebase o el commit ya no existe.
        commands.extend([
            ["git", "diff", "--name-only"],
            ["git", "diff", "--cached", "--name-only"],
        ])
        for command in commands:
            result = subprocess.run(
                command,
                capture_output=True, text=True, timeout=10,
                cwd=str(NAS_DOTFILES),
            )
            if result.returncode == 0:
                changed.extend(
                    line.strip()
                    for line in result.stdout.splitlines()
                    if line.strip()
                )

        # Archivos sin trackear (nuevos).
        result = subprocess.run(
            ["git", "ls-files", "--others", "--exclude-standard"],
            capture_output=True, text=True, timeout=10,
            cwd=str(NAS_DOTFILES),
        )
        if result.returncode == 0:
            changed.extend(
                line.strip()
                for line in result.stdout.splitlines()
                if line.strip()
            )

        # El mismo archivo puede aparecer en commit, índice y working tree.
        return list(dict.fromkeys(changed))
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return []


def _hash_file(path: Path) -> str:
    """Hash rápido del contenido de un archivo."""
    try:
        content = path.read_bytes()
        return hashlib.md5(content).hexdigest()[:12]
    except (OSError, IOError):
        return ""


def _classify_changed_file(filepath: str) -> Tuple[str, str]:
    """Clasifica un archivo modificado.

    Returns:
        Tuple (tipo, servicio_o_contexto)
        tipo: "compose", "script_svc", "shell_lib", "plugin", "tool",
              "capability", "guide", "ficha", "debmenux", "config", "other"
    """
    # Compose de servicio (en catálogo o $dkco)
    m = re.match(r"(?:agent/catalog/services|docker)/([^/]+)/compose\.yml", filepath)
    if m:
        return ("compose", m.group(1))

    # Ficha de catálogo
    m = re.match(r"agent/catalog/services/([^/]+)/ficha\.md", filepath)
    if m:
        return ("ficha", m.group(1))

    # Guía de servicio
    m = re.match(r"docs/services/([^/]+)-guide\.md", filepath)
    if m:
        return ("guide", m.group(1))

    # Script CLI bash
    m = re.match(r"docker/cli/(?:svc\.sh|lib/[\w-]+\.sh)", filepath)
    if m:
        return ("script_svc", "cli")

    # Shell lib
    m = re.match(r"shell/lib/(\w+)\.sh", filepath)
    if m:
        return ("shell_lib", m.group(1))

    # Manifest de capacidades por servicio
    m = re.match(r"agent/capabilities/([^/]+)\.json", filepath)
    if m:
        return ("capability", m.group(1))

    # Plugin agente
    m = re.match(r"agent/plugins/(\w+)\.py", filepath)
    if m:
        return ("plugin", m.group(1))

    # Tool agente
    m = re.match(r"agent/tools/(\w+)\.py", filepath)
    if m:
        return ("tool", m.group(1))

    # Script DebMenux
    m = re.match(r"(?:.*DebMenux.*/)?scripts/services/([^/]+)\.sh", filepath)
    if m:
        return ("debmenux", m.group(1))

    # Python CLI
    m = re.match(r"svc_py/", filepath)
    if m:
        return ("python_cli", "cli")

    # Archivos de configuración
    if filepath.endswith((".env", ".env.example", ".env.global.example")):
        return ("config", "env")

    # AGENTS.md, SKILL.md, etc.
    if filepath in ("AGENTS.md",) or "SKILL.md" in filepath or "nas-context.md" in filepath:
        return ("meta", "docs")

    return ("other", "")


def _build_snapshot_from_scan(result: ScanResult) -> Snapshot:
    """Construye un snapshot a partir del resultado de un full scan."""
    snap = Snapshot(
        last_scan=datetime.now(timezone.utc).isoformat(),
        last_commit=_get_current_commit(),
    )

    # Guardar estado de servicios
    for svc, status in result.services_status.items():
        snap.services[svc] = status

    # Guardar hashes de archivos clave
    key_patterns = [
        CATALOG_DIR.glob("*/compose.yml"),
        CATALOG_DIR.glob("*/ficha.md"),
        DOCS_DIR.glob("*-guide.md"),
    ]
    for pattern in key_patterns:
        for path in pattern:
            rel = str(path.relative_to(NAS_DOTFILES))
            snap.file_hashes[rel] = _hash_file(path)

    # svc.sh
    if SVC_SH.exists():
        snap.file_hashes["docker/cli/svc.sh"] = _hash_file(SVC_SH)

    # AGENTS.md
    agents_md = NAS_DOTFILES / "AGENTS.md"
    if agents_md.exists():
        snap.file_hashes["AGENTS.md"] = _hash_file(agents_md)

    return snap


def incremental_scan(verbose: bool = False) -> Tuple[ScanResult, List[str]]:
    """Ejecuta un scan incremental basado en git diff.

    Returns:
        Tuple de (ScanResult con solo issues de archivos modificados,
                  Lista de archivos modificados clasificados)
    """
    prev_snapshot = Snapshot.load()

    if prev_snapshot is None:
        # No hay snapshot previo → hacer full scan
        result = scan(verbose=verbose)
        snapshot = _build_snapshot_from_scan(result)
        snapshot.save()
        return result, ["(full scan — no había snapshot previo)"]

    # Obtener archivos modificados desde el último commit escaneado
    changed_files = _get_changed_files(prev_snapshot.last_commit)

    if not changed_files:
        # Nada cambió → retornar resultado vacío
        result = ScanResult()
        result.services_scanned = len(prev_snapshot.services)
        result.services_complete = sum(
            1 for s in prev_snapshot.services.values()
            if all(s.get(k, False) for k in ("ficha", "guide", "debmenux_script"))
            and (s.get("homepage_labels", False))
        )
        return result, []

    # Clasificar archivos modificados
    affected_services: Set[str] = set()
    classifications: List[str] = []

    for filepath in changed_files:
        file_type, context = _classify_changed_file(filepath)
        classifications.append(f"  {filepath} → [{file_type}] {context}")

        # Determinar servicios afectados
        if file_type in ("compose", "ficha", "guide", "debmenux", "capability") and context:
            affected_services.add(context)
        elif file_type in ("script_svc", "python_cli", "shell_lib"):
            # Cambios globales de CLI afectan la verificación de paridad
            affected_services.add("__cli__")
        elif file_type == "meta":
            affected_services.add("__meta__")

    # Hacer full scan pero filtrar issues solo a servicios afectados
    full_result = scan(verbose=verbose)

    # Si solo cambiaron archivos de servicios específicos, filtrar
    if "__cli__" not in affected_services and "__meta__" not in affected_services:
        filtered_issues = [
            i for i in full_result.issues
            if i.service in affected_services or i.service == "global"
        ]
        full_result.issues = filtered_issues

    # Guardar nuevo snapshot
    snapshot = _build_snapshot_from_scan(full_result)
    snapshot.save()

    return full_result, classifications


# ─────────────────────────────────────────────────────────────────────────────
# DATACLASSES
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class Issue:
    """Una inconsistencia detectada."""

    severity: str  # "error", "warning", "info"
    category: str  # "service", "cli", "agent", "docs", "config"
    service: str  # servicio afectado (o "global")
    message: str
    fix_hint: str = ""

    def __str__(self) -> str:
        icons = {"error": "🔴", "warning": "⚠️", "info": "ℹ️"}
        icon = icons.get(self.severity, "?")
        hint = f" → {self.fix_hint}" if self.fix_hint else ""
        return f"{icon} [{self.category}] {self.service}: {self.message}{hint}"


@dataclass
class ScanResult:
    """Resultado completo del scan."""

    services_scanned: int = 0
    services_complete: int = 0
    issues: List[Issue] = field(default_factory=list)
    services_status: Dict[str, Dict[str, bool]] = field(default_factory=dict)
    architecture: Dict[str, Any] = field(default_factory=dict)

    @property
    def errors(self) -> List[Issue]:
        return [i for i in self.issues if i.severity == "error"]

    @property
    def warnings(self) -> List[Issue]:
        return [i for i in self.issues if i.severity == "warning"]

    def summary(self) -> str:
        lines = [
            f"📊 Scan completado: {self.services_scanned} servicios",
            f"   ✅ Completos: {self.services_complete}",
            f"   🔴 Errores: {len(self.errors)}",
            f"   ⚠️  Warnings: {len(self.warnings)}",
        ]
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "services_scanned": self.services_scanned,
            "services_complete": self.services_complete,
            "issues": [
                {
                    "severity": i.severity,
                    "category": i.category,
                    "service": i.service,
                    "message": i.message,
                    "fix_hint": i.fix_hint,
                }
                for i in self.issues
            ],
            "services_status": self.services_status,
            "architecture": self.architecture,
        }


# ─────────────────────────────────────────────────────────────────────────────
# DETECTORES
# ─────────────────────────────────────────────────────────────────────────────


def _detect_services() -> Set[str]:
    """Detecta todos los servicios con compose.yml en $DOCKER_BASE o catálogo."""
    services = set()

    # Desde $DOCKER_BASE (servicios activos en el NAS)
    if DOCKER_BASE.exists():
        for item in DOCKER_BASE.iterdir():
            if not item.is_dir() or item.name.startswith("."):
                continue
            if item.name in ("backups", "cli"):
                continue
            for name in ("compose.yml", "compose.yaml", "docker-compose.yml"):
                if (item / name).exists():
                    services.add(item.name)
                    break

    # Desde catálogo (puede tener servicios no desplegados aún)
    if CATALOG_DIR.exists():
        for item in CATALOG_DIR.iterdir():
            if item.is_dir() and (item / "compose.yml").exists():
                services.add(item.name)

    return services


def _get_debmenux_scripts_dir() -> Optional[Path]:
    """Retorna el directorio de scripts DebMenux (ubicación real o alternativa)."""
    if DEBMENUX_SCRIPTS.exists():
        return DEBMENUX_SCRIPTS
    if DEBMENUX_ALT.exists():
        return DEBMENUX_ALT
    return None


def _check_services(result: ScanResult) -> None:
    """Verifica completitud de documentación por servicio."""
    services = _detect_services()
    debmenux_dir = _get_debmenux_scripts_dir()

    for svc in sorted(services):
        status = {}

        # Compose en catálogo
        catalog_compose = CATALOG_DIR / svc / "compose.yml"
        status["catalog_compose"] = catalog_compose.exists()

        # Ficha
        ficha = CATALOG_DIR / svc / "ficha.md"
        status["ficha"] = ficha.exists()

        # Guía
        guide = DOCS_DIR / f"{svc}-guide.md"
        status["guide"] = guide.exists()

        # Script DebMenux
        has_debmenux = False
        if debmenux_dir:
            has_debmenux = (debmenux_dir / f"{svc}.sh").exists()
        status["debmenux_script"] = has_debmenux

        # Homepage labels
        has_labels = False
        compose_path = catalog_compose if catalog_compose.exists() else None
        if compose_path is None and DOCKER_BASE.exists():
            candidate = DOCKER_BASE / svc / "compose.yml"
            if candidate.exists():
                compose_path = candidate
        if compose_path and compose_path.exists():
            content = compose_path.read_text(encoding="utf-8")
            has_labels = "homepage." in content
        status["homepage_labels"] = has_labels

        result.services_status[svc] = status
        result.services_scanned += 1

        # Generar issues
        if not status["ficha"]:
            result.issues.append(Issue(
                severity="error",
                category="service",
                service=svc,
                message="Sin ficha en catálogo",
                fix_hint="svc catalog-sync " + svc,
            ))

        if not status["guide"]:
            result.issues.append(Issue(
                severity="warning",
                category="service",
                service=svc,
                message="Sin guía operativa",
                fix_hint=f"Crear docs/services/{svc}-guide.md",
            ))

        if not status["debmenux_script"]:
            result.issues.append(Issue(
                severity="info",
                category="service",
                service=svc,
                message="Sin script DebMenux",
                fix_hint=f"Crear scripts/services/{svc}.sh en DebMenux",
            ))

        if not has_labels and svc != "homepage":
            result.issues.append(Issue(
                severity="warning",
                category="service",
                service=svc,
                message="Sin labels Homepage en compose",
                fix_hint="Agregar labels homepage.* al compose",
            ))

        # Servicio completamente documentado
        checks = [status["ficha"], status["guide"], status["debmenux_script"], has_labels or svc == "homepage"]
        if all(checks):
            result.services_complete += 1


def _check_compose_hygiene(result: ScanResult) -> None:
    """Verifica reglas de compose (IP hardcodeada, TZ duplicado, env_file)."""
    dirs_to_check = []

    if CATALOG_DIR.exists():
        for item in CATALOG_DIR.iterdir():
            if item.is_dir() and (item / "compose.yml").exists():
                dirs_to_check.append((item.name, item / "compose.yml"))

    if DOCKER_BASE.exists():
        for item in DOCKER_BASE.iterdir():
            if not item.is_dir() or item.name in ("backups", "cli", ".env"):
                continue
            compose = item / "compose.yml"
            if compose.exists():
                dirs_to_check.append((item.name, compose))

    seen = set()
    for svc_name, compose_path in dirs_to_check:
        # Evitar duplicados (mismo servicio en catálogo y $dkco)
        key = f"{svc_name}:{compose_path}"
        if key in seen:
            continue
        seen.add(key)

        try:
            content = compose_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue

        # IP hardcodeada (192.168.x.x en labels o URLs)
        ip_matches = re.findall(r"192\.168\.\d+\.\d+", content)
        if ip_matches:
            # Filtrar: OK en comments, NOT OK in labels/hrefs
            for line in content.splitlines():
                stripped = line.strip()
                if stripped.startswith("#"):
                    continue
                if re.search(r"192\.168\.\d+\.\d+", stripped):
                    if "homepage." in stripped or "href" in stripped or "url" in stripped.lower():
                        result.issues.append(Issue(
                            severity="error",
                            category="config",
                            service=svc_name,
                            message=f"IP hardcodeada en: {stripped[:60]}",
                            fix_hint="Usar ${SERVER_IP} (requiere env_file: [../.env, .env])",
                        ))
                        break

        # TZ en environment: (debería heredarse del global)
        if re.search(r"^\s+TZ[:=]\s*(America|Europe|Asia)", content, re.MULTILINE):
            # Solo alertar si no es el .env global
            if "env_file:" not in content or "../.env" not in content:
                result.issues.append(Issue(
                    severity="warning",
                    category="config",
                    service=svc_name,
                    message="TZ definido inline en environment",
                    fix_hint="Heredar TZ de ../.env via env_file: [../.env, .env]",
                ))

        # env_file faltante (no tiene ../.env)
        if "env_file:" in content and "../.env" not in content:
            # Excepciones: network_mode: host no siempre necesita global
            if "network_mode:" not in content:
                result.issues.append(Issue(
                    severity="info",
                    category="config",
                    service=svc_name,
                    message="env_file no incluye ../.env (global)",
                    fix_hint="Agregar ../.env al env_file para heredar SERVER_IP y TZ",
                ))


def _check_cli_parity(result: ScanResult) -> None:
    """Verifica paridad entre bash CLI y Python CLI."""
    bash_commands = set()
    python_commands = set()

    # Extraer comandos del bash CLI (case statements en svc.sh)
    if SVC_SH.exists():
        content = SVC_SH.read_text(encoding="utf-8")
        # Buscar patrones como: comando) o "comando")
        for m in re.finditer(r"^\s+([a-z][\w-]*)\)", content, re.MULTILINE):
            cmd = m.group(1)
            if cmd not in ("esac", "in"):
                bash_commands.add(cmd)

    # Extraer comandos del Python CLI (app.command en app.py)
    app_py = SVC_PY_DIR / "app.py"
    if app_py.exists():
        content = app_py.read_text(encoding="utf-8")
        for m in re.finditer(r'app\.command\("([^"]+)"\)', content):
            python_commands.add(m.group(1))
        # También @app.command("...")
        for m in re.finditer(r'@app\.command\("([^"]+)"\)', content):
            python_commands.add(m.group(1))

    # Comandos solo en bash
    bash_only = bash_commands - python_commands
    # Filtrar los que son passthrough natural
    bash_passthrough = {"up", "down", "restart", "stop", "start", "kill", "logs",
                        "ps", "exec", "build", "pull", "images", "rm", "config",
                        "events", "volumes", "top", "stats", "update", "recreate"}
    bash_only_real = bash_only - bash_passthrough

    for cmd in sorted(bash_only_real):
        if cmd in ("", "-h", "--help"):
            continue
        result.issues.append(Issue(
            severity="info",
            category="cli",
            service="global",
            message=f"Comando '{cmd}' solo existe en bash CLI",
            fix_hint=f"Agregar a svc_py/ o documentar como bash-only",
        ))

    # Comandos solo en Python (que no están en bash)
    python_only = python_commands - bash_commands - bash_passthrough
    for cmd in sorted(python_only):
        result.issues.append(Issue(
            severity="info",
            category="cli",
            service="global",
            message=f"Comando '{cmd}' solo existe en Python CLI",
            fix_hint="Agregar a svc.sh o documentar como python-only",
        ))


def _check_agent_prompt(result: ScanResult) -> None:
    """Verifica que el prompt del agente conoce todos los comandos CLI."""
    if not AGENT_FILE.exists():
        return

    content = AGENT_FILE.read_text(encoding="utf-8")

    # Extraer comandos mencionados en BLOCK_CONTEXTO_NAS
    # El prompt usa formato: - `svc command <arg>` → descripción
    prompt_commands = set()
    in_block = False
    for line in content.splitlines():
        if "BLOCK_CONTEXTO_NAS" in line and "=" in line:
            in_block = True
            continue
        if in_block:
            if line.strip() == '"""' and in_block:
                break
            # Buscar patrones: `svc command` o `svc command <arg>`
            matches = re.findall(r"`svc\s+([\w-]+)", line)
            for cmd in matches:
                prompt_commands.add(cmd)

    # Comandos registrados en bash CLI (case statements globales)
    bash_commands = set()
    if SVC_SH.exists():
        svc_content = SVC_SH.read_text(encoding="utf-8")
        for m in re.finditer(r"^\s+([a-z][\w-]*)\)", svc_content, re.MULTILINE):
            cmd = m.group(1)
            if cmd not in ("esac", "in", "", "-h", "--help"):
                bash_commands.add(cmd)

    # Comandos que existen pero el agente no conoce
    unknown_to_agent = bash_commands - prompt_commands
    # Filtrar los que son passthrough natural (el agente no necesita listarlos)
    passthrough = {"up", "down", "restart", "stop", "start", "kill", "logs",
                   "update", "recreate", "ps", "exec", "build", "pull",
                   "images", "rm", "config", "events", "volumes", "top", "stats"}
    unknown_real = unknown_to_agent - passthrough

    for cmd in sorted(unknown_real):
        result.issues.append(Issue(
            severity="warning",
            category="agent",
            service="global",
            message=f"Comando 'svc {cmd}' no está en el prompt del agente",
            fix_hint="Agregar a BLOCK_CONTEXTO_NAS en nas_agent.py",
        ))


def _check_architecture_contracts(result: ScanResult) -> None:
    """Compara el índice estructural contra contracts.json.

    Esta primera versión no intenta resolver semántica de Markdown. Verifica
    contratos de existencia, superficies CLI y relaciones explícitas entre
    ambos repositorios. Las diferencias de paridad se reportan; no se ocultan
    detrás de una lista de excepciones implícita.
    """
    if build_index is None:
        result.issues.append(Issue(
            severity="warning",
            category="architecture",
            service="global",
            message="No se pudo cargar project_index.py",
            fix_hint="Verificar agent/tools/project_index.py",
        ))
        return

    try:
        index = build_index()
    except Exception as exc:  # El scanner no debe caerse por un índice auxiliar.
        result.issues.append(Issue(
            severity="error",
            category="architecture",
            service="global",
            message=f"Falló la construcción del project index: {exc}",
            fix_hint="Ejecutar python3 agent/tools/project_index.py --check",
        ))
        return

    if write_index is not None:
        try:
            write_index(index)
        except OSError as exc:
            result.issues.append(Issue(
                severity="info",
                category="architecture",
                service="global",
                message=f"No se pudo guardar project-index.json: {exc}",
                fix_hint="Revisar permisos de agent/cache/",
            ))

    capabilities = index.get("capabilities", {})
    for manifest in capabilities.get("manifests", []):
        if not manifest.get("source_exists"):
            result.issues.append(Issue(
                severity="error",
                category="capability",
                service=manifest.get("service") or "global",
                message=f"Manifest de capacidades sin entrypoint: {manifest.get('source')}",
                fix_hint="Crear el entrypoint o corregir source en agent/capabilities/*.json",
            ))
    for operation in capabilities.get("operations", []):
        if not operation.get("source_exists"):
            result.issues.append(Issue(
                severity="error",
                category="capability",
                service=operation.get("service") or "global",
                message=f"Capacidad sin implementación: {operation.get('id')}",
                fix_hint="Conectar la operación al código antes de documentarla como disponible",
            ))
        elif not operation.get("dispatch_exists", True):
            result.issues.append(Issue(
                severity="error",
                category="capability",
                service=operation.get("service") or "global",
                message=f"Capacidad sin dispatch real: {operation.get('id')}",
                fix_hint="Agregar la subacción al entrypoint o retirarla del manifest",
            ))
        elif not operation.get("guard_valid", True):
            result.issues.append(Issue(
                severity="error",
                category="capability",
                service=operation.get("service") or "global",
                message=f"Guard inconsistente en capacidad: {operation.get('id')}",
                fix_hint="Alinear mode/confirm/--confirm en agent/capabilities/*.json",
            ))

    contracts_path = NAS_DOTFILES / "agent" / "architecture" / "contracts.json"
    try:
        contracts = json.loads(contracts_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        result.issues.append(Issue(
            severity="error",
            category="architecture",
            service="global",
            message="No existe o no es válido agent/architecture/contracts.json",
            fix_hint="Regenerar la especificación de contratos",
        ))
        return

    severity_by_level = {
        "functional": "error",
        "interface": "warning",
        "knowledge": "warning",
        "documentation": "info",
        "historical": "info",
    }

    # Conexiones explícitas del contrato.
    for connection in index.get("connections", []):
        if connection.get("complete"):
            continue
        severity = severity_by_level.get(connection.get("level"), "warning")
        missing = [
            item["path"]
            for item in connection.get("required", [])
            if not item.get("exists")
        ]
        result.issues.append(Issue(
            severity=severity,
            category="architecture",
            service=connection.get("name") or "global",
            message=(
                f"Contrato '{connection.get('id')}' incompleto; faltan: "
                + ", ".join(missing)
            ),
            fix_hint="Crear o conectar las superficies requeridas por contracts.json",
        ))

    cli = index.get("cli", {})
    bash = set(cli.get("bash", {}).get("commands", []))
    python = set(cli.get("python", {}).get("commands", []))
    completion = set(cli.get("completion", {}).get("global_commands", []))
    completion.update(cli.get("completion", {}).get("service_commands", []))
    prompt = set(cli.get("agent_prompt", {}).get("commands", []))
    cli_contract = contracts.get("cli_contract", {})

    # Comandos que el contrato declara como compartidos deben existir en ambos.
    for command in cli_contract.get("required_shared_commands", []):
        if command not in bash or command not in python:
            missing_in = []
            if command not in bash:
                missing_in.append("Bash")
            if command not in python:
                missing_in.append("Python")
            result.issues.append(Issue(
                severity="error",
                category="architecture",
                service="global",
                message=f"Comando compartido '{command}' falta en: {', '.join(missing_in)}",
                fix_hint="Registrar el comando en ambos lados del contrato CLI",
            ))
        if command not in completion:
            result.issues.append(Issue(
                severity="warning",
                category="architecture",
                service="global",
                message=f"Comando '{command}' no aparece en completions",
                fix_hint="Agregarlo a shell/lib/docker.sh",
            ))
        if command not in prompt:
            result.issues.append(Issue(
                severity="warning",
                category="architecture",
                service="global",
                message=f"Comando '{command}' no aparece en el conocimiento del agente",
                fix_hint="Agregarlo a BLOCK_CONTEXTO_NAS en agent/nas_agent.py",
            ))

    allowed_bash_only = set(cli_contract.get("allowed_bash_only_commands", []))
    allowed_python_only = set(cli_contract.get("allowed_python_only_commands", []))

    for command in sorted((bash - python) - allowed_bash_only):
        result.issues.append(Issue(
            severity="warning",
            category="architecture",
            service="global",
            message=f"Comando Bash-only no declarado en el contrato: svc {command}",
            fix_hint="Agregarlo a Python o declararlo explícitamente como Bash-only",
        ))

    for command in sorted((python - bash) - allowed_python_only):
        result.issues.append(Issue(
            severity="warning",
            category="architecture",
            service="global",
            message=f"Comando Python-only no declarado en el contrato: svc {command}",
            fix_hint="Agregarlo a Bash o declararlo explícitamente como Python-only",
        ))

    # Relación catálogo ↔ scripts ↔ services.json en el segundo repositorio.
    for service in index.get("services", []):
        service_id = service.get("id", "unknown")
        if service.get("debmenux_script") and not service.get("debmenux_registry"):
            result.issues.append(Issue(
                severity="warning",
                category="architecture",
                service=service_id,
                message="Existe script DebMenux pero falta en services.json",
                fix_hint="Agregar la entrada del servicio al registry de DebMenux",
            ))
        if service.get("debmenux_registry") and not service.get("debmenux_script"):
            result.issues.append(Issue(
                severity="warning",
                category="architecture",
                service=service_id,
                message="services.json declara el servicio pero falta su script DebMenux",
                fix_hint="Crear scripts/services/" + service_id + ".sh o retirar la entrada",
            ))

    result.architecture = {
        "files": index.get("summary", {}).get("files", 0),
        "services": index.get("summary", {}).get("services", 0),
        "connections": index.get("summary", {}).get("contract_connections", 0),
        "capabilities": index.get("summary", {}).get("capabilities", 0),
        "broken_connections": index.get("summary", {}).get("broken_contract_connections", 0),
        "cli_parity": index.get("cli", {}).get("parity", {}),
    }


# ─────────────────────────────────────────────────────────────────────────────
# DOCS REFERENCES
# ─────────────────────────────────────────────────────────────────────────────


def _check_docs_references(result: ScanResult) -> None:
    """Verifica que docs_url en fichas apuntan a archivos que existen."""
    if not CATALOG_DIR.exists():
        return

    for svc_dir in sorted(CATALOG_DIR.iterdir()):
        if not svc_dir.is_dir():
            continue
        ficha = svc_dir / "ficha.md"
        if not ficha.exists():
            continue

        content = ficha.read_text(encoding="utf-8")
        # Buscar docs_url
        m = re.search(r'docs_url:\s*["\']?([^"\'#\n]+)', content)
        if not m:
            continue

        docs_url = m.group(1).strip()
        # Solo verificar paths locales (no URLs http)
        if docs_url.startswith("http"):
            continue

        target = NAS_DOTFILES / docs_url
        if not target.exists():
            result.issues.append(Issue(
                severity="warning",
                category="docs",
                service=svc_dir.name,
                message=f"docs_url apunta a archivo inexistente: {docs_url}",
                fix_hint=f"Crear {docs_url} o corregir docs_url en ficha.md",
            ))


# ─────────────────────────────────────────────────────────────────────────────
# SCANNER PRINCIPAL
# ─────────────────────────────────────────────────────────────────────────────


def scan(verbose: bool = False) -> ScanResult:
    """Ejecuta todos los checks y retorna el resultado completo."""
    result = ScanResult()

    _check_services(result)
    _check_compose_hygiene(result)
    _check_cli_parity(result)
    _check_agent_prompt(result)
    _check_docs_references(result)
    _check_architecture_contracts(result)

    return result


def format_report(result: ScanResult, verbose: bool = False) -> str:
    """Formatea el resultado como reporte legible."""
    lines = []
    lines.append("")
    lines.append("  ━━━ 🔍 Project Scanner — Reporte de Inconsistencias ━━━")
    lines.append("")

    # Tabla de servicios
    lines.append("  Servicios:")
    lines.append("  ┌────────────────┬─────────┬───────┬───────┬─────────┬──────────┐")
    lines.append("  │ Servicio       │ Compose │ Ficha │ Guía  │ DebMenu │ Homepage │")
    lines.append("  ├────────────────┼─────────┼───────┼───────┼─────────┼──────────┤")

    for svc, status in sorted(result.services_status.items()):
        c = "✅" if status.get("catalog_compose") else "❌"
        f = "✅" if status.get("ficha") else "❌"
        g = "✅" if status.get("guide") else "❌"
        d = "✅" if status.get("debmenux_script") else "❌"
        h = "✅" if status.get("homepage_labels") else ("—" if svc == "homepage" else "❌")
        lines.append(f"  │ {svc:<14} │   {c}   │  {f}  │  {g}  │   {d}   │    {h}    │")

    lines.append("  └────────────────┴─────────┴───────┴───────┴─────────┴──────────┘")
    lines.append("")

    # Mapa arquitectónico y paridad CLI
    if result.architecture:
        parity = result.architecture.get("cli_parity", {})
        lines.append("  Arquitectura:")
        lines.append(
            "     Índice: "
            f"{result.architecture.get('files', 0)} archivos, "
            f"{result.architecture.get('services', 0)} servicios, "
            f"{result.architecture.get('capabilities', 0)} capacidades, "
            f"{result.architecture.get('connections', 0)} contratos"
        )
        lines.append(
            "     Conexiones rotas: "
            f"{result.architecture.get('broken_connections', 0)}"
        )
        bash_only = parity.get("bash_only", [])
        python_only = parity.get("python_only", [])
        lines.append(f"     Bash-only: {', '.join(bash_only) if bash_only else 'ninguno'}")
        lines.append(f"     Python-only: {', '.join(python_only) if python_only else 'ninguno'}")
        lines.append("")

    # Issues por categoría
    if result.issues:
        # Errores
        errors = result.errors
        if errors:
            lines.append("  🔴 Errores (corregir):")
            for issue in errors:
                lines.append(f"     {issue}")
            lines.append("")

        # Warnings
        warnings = result.warnings
        if warnings:
            lines.append("  ⚠️  Warnings (recomendado):")
            for issue in warnings:
                lines.append(f"     {issue}")
            lines.append("")

        # Info (solo en verbose)
        if verbose:
            infos = [i for i in result.issues if i.severity == "info"]
            if infos:
                lines.append("  ℹ️  Info (opcional):")
                for issue in infos:
                    lines.append(f"     {issue}")
                lines.append("")
    else:
        lines.append("  ✅ Sin inconsistencias detectadas")
        lines.append("")

    # Resumen
    lines.append(result.summary())
    lines.append("")

    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# TOOL DEL AGENTE (compatible con Strands @tool)
# ─────────────────────────────────────────────────────────────────────────────

try:
    from strands.tools import tool

    @tool
    def project_scan(verbose: bool = False, full: bool = False) -> str:
        """Escanea el proyecto y detecta lagunas/inconsistencias.

        Verifica: servicios sin docs, IP hardcodeada, CLI sin paridad,
        prompt del agente desactualizado, docs_url rotos.

        Modo inteligente: si hay snapshot previo, hace scan incremental
        (solo archivos que cambiaron). Usar full=True para forzar scan completo.

        Args:
            verbose: Si True, incluye issues de severidad 'info'.
            full: Si True, fuerza un scan completo (ignora snapshot).

        Returns:
            Reporte formateado con tabla de servicios e issues encontrados.
        """
        if full or not Snapshot.load():
            result = scan(verbose=verbose)
            snapshot = _build_snapshot_from_scan(result)
            snapshot.save()
            return format_report(result, verbose=verbose)
        else:
            result, classifications = incremental_scan(verbose=verbose)
            report = format_report(result, verbose=verbose)
            if classifications and classifications[0] != "(full scan — no había snapshot previo)":
                header = f"📝 Incremental: {len(classifications)} archivos cambiaron\n"
                report = header + report
            return report

except ImportError:
    # Si strands no está disponible (uso standalone o en tests)
    def project_scan(verbose: bool = False, full: bool = False) -> str:
        """Escanea el proyecto (versión sin @tool decorator)."""
        if full or not Snapshot.load():
            result = scan(verbose=verbose)
            snapshot = _build_snapshot_from_scan(result)
            snapshot.save()
            return format_report(result, verbose=verbose)
        else:
            result, classifications = incremental_scan(verbose=verbose)
            report = format_report(result, verbose=verbose)
            if classifications and classifications[0] != "(full scan — no había snapshot previo)":
                header = f"📝 Incremental: {len(classifications)} archivos cambiaron\n"
                report = header + report
            return report


# ─────────────────────────────────────────────────────────────────────────────
# CLI ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

def main():
    """Punto de entrada CLI."""
    verbose = "--verbose" in sys.argv or "-v" in sys.argv
    as_json = "--json" in sys.argv
    force_full = "--full" in sys.argv
    changes_only = "--changed" in sys.argv

    # Modo --changed: solo mostrar qué cambió (sin verificar conexiones)
    if changes_only:
        prev = Snapshot.load()
        if prev is None:
            print("  ⚠️  No hay snapshot previo. Ejecuta primero: svc scan --full")
            sys.exit(0)
        changed = _get_changed_files(prev.last_commit)
        if not changed:
            print(f"  ✅ Nada cambió desde {prev.last_commit} ({prev.last_scan[:10]})")
            sys.exit(0)
        print(f"\n  📝 {len(changed)} archivos modificados desde {prev.last_commit}:\n")
        for f in changed:
            ftype, ctx = _classify_changed_file(f)
            print(f"    {f}  → [{ftype}] {ctx}")
        print()
        sys.exit(0)

    # Modo full o incremental
    if force_full or not Snapshot.load():
        # Full scan
        result = scan(verbose=verbose)
        # Guardar snapshot
        snapshot = _build_snapshot_from_scan(result)
        snapshot.save()
        classifications = None
    else:
        # Incremental scan
        result, classifications = incremental_scan(verbose=verbose)

    if as_json:
        output = result.to_dict()
        if classifications:
            output["changed_files"] = classifications
        print(json.dumps(output, indent=2, ensure_ascii=False))
    else:
        report = format_report(result, verbose=verbose)
        if classifications and classifications[0] != "(full scan — no había snapshot previo)":
            header = f"\n  📝 Scan incremental ({len(classifications)} archivos cambiaron):\n"
            for c in classifications[:15]:  # Limitar output
                header += f"  {c}\n"
            if len(classifications) > 15:
                header += f"    ... y {len(classifications) - 15} más\n"
            header += "\n  ─── Verificación de conexiones ───\n"
            report = header + report
        print(report)

    # Exit code: 1 si hay errores, 0 si solo warnings/info
    sys.exit(1 if result.errors else 0)


if __name__ == "__main__":
    main()
