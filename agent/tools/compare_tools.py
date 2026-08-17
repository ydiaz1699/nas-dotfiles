"""
compare_tools.py — Detecta drift entre el compose real y el catálogo.

Compara la config REAL de un servicio en $DOCKER_BASE contra:
1. El compose del catálogo (agent/catalog/services/<svc>/compose.yml)
2. Los metadatos de la ficha (puertos, redes, volúmenes, env_required)

Útil para detectar cuando alguien modificó el compose en producción
sin actualizar la documentación, o viceversa.

Uso como tool del agente:
    compare_catalog("emqx")  → reporte de diferencias

Uso standalone:
    python -m agent.tools.compare_tools emqx
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURACIÓN
# ─────────────────────────────────────────────────────────────────────────────

NAS_DOTFILES = Path(os.environ.get("NAS_DOTFILES", "/nas-dotfiles"))
DOCKER_BASE = Path(os.environ.get("DOCKER_BASE", "/docker"))
CATALOG_DIR = NAS_DOTFILES / "agent" / "catalog" / "services"


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────


def _extract_ports(content: str) -> Set[str]:
    """Extrae puertos publicados (host:container) de un compose."""
    ports = set()
    in_ports = False
    for line in content.splitlines():
        stripped = line.strip()
        if stripped == "ports:" or stripped.startswith("ports:"):
            in_ports = True
            continue
        if in_ports:
            if stripped.startswith("- "):
                # Extraer puerto: "8090:80", "${VAR}:80", etc.
                port_match = re.search(r'["\']?([^"\']+)["\']?', stripped[2:])
                if port_match:
                    ports.add(port_match.group(1).strip())
            elif not stripped.startswith("#") and stripped and not stripped.startswith("-"):
                in_ports = False
    return ports


def _extract_networks(content: str) -> Set[str]:
    """Extrae redes de un servicio compose (del bloque services.X.networks)."""
    networks = set()
    in_service_networks = False
    indent_level = 0

    for line in content.splitlines():
        stripped = line.strip()
        # Detectar bloque networks: dentro de un servicio
        if stripped == "networks:" and len(line) - len(line.lstrip()) > 2:
            in_service_networks = True
            indent_level = len(line) - len(line.lstrip())
            continue
        if in_service_networks:
            current_indent = len(line) - len(line.lstrip()) if line.strip() else 0
            if current_indent <= indent_level and stripped and not stripped.startswith("#"):
                in_service_networks = False
                continue
            if stripped.startswith("- "):
                net_name = stripped[2:].strip()
                if net_name and not net_name.startswith("#"):
                    networks.add(net_name)

    return networks


def _extract_volumes(content: str) -> Set[str]:
    """Extrae bind mounts de un compose."""
    volumes = set()
    in_volumes = False
    for line in content.splitlines():
        stripped = line.strip()
        if stripped == "volumes:" and len(line) - len(line.lstrip()) > 2:
            in_volumes = True
            continue
        if in_volumes:
            if stripped.startswith("- "):
                vol = stripped[2:].strip().strip('"').strip("'")
                if ":" in vol:
                    volumes.add(vol)
            elif stripped and not stripped.startswith("#") and not stripped.startswith("-"):
                in_volumes = False
    return volumes


def _extract_env_vars(content: str) -> Set[str]:
    """Extrae variables ${VAR} interpoladas en todo el compose."""
    return set(re.findall(r'\$\{([A-Z_][A-Z0-9_]*)', content))


def _extract_image(content: str) -> str:
    """Extrae la imagen principal del compose."""
    match = re.search(r'^\s+image:\s*["\']?([^\s"\'#]+)', content, re.MULTILINE)
    return match.group(1) if match else ""


def _has_env_file_global(content: str) -> bool:
    """Verifica si el compose tiene env_file con ../.env (global)."""
    return "../.env" in content


def _has_healthcheck(content: str) -> bool:
    """Verifica si el compose define un healthcheck."""
    return "healthcheck:" in content


def _has_security_opt(content: str) -> bool:
    """Verifica si tiene security_opt."""
    return "security_opt:" in content or "no-new-privileges" in content


def _has_resource_limits(content: str) -> bool:
    """Verifica si tiene deploy.resources.limits."""
    return "limits:" in content and ("memory:" in content or "cpus:" in content)


def _parse_ficha_frontmatter(ficha_path: Path) -> Dict[str, str]:
    """Parsea el frontmatter YAML de una ficha."""
    meta = {}
    if not ficha_path.exists():
        return meta

    content = ficha_path.read_text(encoding="utf-8")
    in_front = False
    for line in content.splitlines():
        if line.strip() == "---":
            if not in_front:
                in_front = True
                continue
            else:
                break
        if in_front and ":" in line:
            key, _, val = line.partition(":")
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            meta[key] = val
    return meta


# ─────────────────────────────────────────────────────────────────────────────
# COMPARADOR PRINCIPAL
# ─────────────────────────────────────────────────────────────────────────────


def _compare(service: str) -> str:
    """Compara compose real vs catálogo y genera reporte de drift."""
    lines: List[str] = []

    # Localizar archivos
    real_compose = DOCKER_BASE / service / "compose.yml"
    catalog_compose = CATALOG_DIR / service / "compose.yml"
    ficha_path = CATALOG_DIR / service / "ficha.md"

    if not catalog_compose.exists() and not ficha_path.exists():
        return f"❌ Servicio '{service}' no tiene entrada en el catálogo.\n   Crear con: svc catalog-sync {service}"

    # Leer archivos
    real_content = ""
    catalog_content = ""

    if real_compose.exists():
        real_content = real_compose.read_text(encoding="utf-8")
    if catalog_compose.exists():
        catalog_content = catalog_compose.read_text(encoding="utf-8")

    ficha = _parse_ficha_frontmatter(ficha_path)

    lines.append(f"\n  ━━━ 🔍 Comparación: {service} ━━━\n")

    has_drift = False

    # ── Si tenemos ambos composes, comparar ────────────────────────────────
    if real_content and catalog_content:
        lines.append("  📁 Real: $DOCKER_BASE/{}/compose.yml".format(service))
        lines.append("  📋 Catálogo: agent/catalog/services/{}/compose.yml\n".format(service))

        # Imagen
        real_img = _extract_image(real_content)
        cat_img = _extract_image(catalog_content)
        if real_img and cat_img and real_img != cat_img:
            lines.append(f"  ⚠️  Imagen diferente:")
            lines.append(f"       Real:     {real_img}")
            lines.append(f"       Catálogo: {cat_img}")
            has_drift = True

        # Puertos
        real_ports = _extract_ports(real_content)
        cat_ports = _extract_ports(catalog_content)
        if real_ports != cat_ports:
            only_real = real_ports - cat_ports
            only_cat = cat_ports - real_ports
            if only_real:
                lines.append(f"  ⚠️  Puertos solo en real: {', '.join(sorted(only_real))}")
                has_drift = True
            if only_cat:
                lines.append(f"  ⚠️  Puertos solo en catálogo: {', '.join(sorted(only_cat))}")
                has_drift = True

        # Redes
        real_nets = _extract_networks(real_content)
        cat_nets = _extract_networks(catalog_content)
        if real_nets != cat_nets:
            only_real = real_nets - cat_nets
            only_cat = cat_nets - real_nets
            if only_real:
                lines.append(f"  ⚠️  Redes solo en real: {', '.join(sorted(only_real))}")
                has_drift = True
            if only_cat:
                lines.append(f"  ⚠️  Redes solo en catálogo: {', '.join(sorted(only_cat))}")
                has_drift = True

        # Volúmenes
        real_vols = _extract_volumes(real_content)
        cat_vols = _extract_volumes(catalog_content)
        if real_vols != cat_vols:
            only_real = real_vols - cat_vols
            only_cat = cat_vols - real_vols
            if only_real:
                lines.append(f"  ⚠️  Volúmenes solo en real: {', '.join(sorted(only_real))}")
                has_drift = True
            if only_cat:
                lines.append(f"  ⚠️  Volúmenes solo en catálogo: {', '.join(sorted(only_cat))}")
                has_drift = True

        # env_file global
        real_has_global = _has_env_file_global(real_content)
        cat_has_global = _has_env_file_global(catalog_content)
        if not real_has_global and cat_has_global:
            lines.append("  🔴 Real no tiene env_file: [../.env] (catálogo sí)")
            has_drift = True
        elif real_has_global and not cat_has_global:
            lines.append("  ℹ️  Real tiene env_file global pero catálogo no (actualizar catálogo)")
            has_drift = True

    elif real_content and not catalog_content:
        lines.append("  ⚠️  Existe en $DOCKER_BASE pero NO en el catálogo")
        lines.append("     → Ejecutar: svc catalog-sync {}".format(service))
        has_drift = True

    elif catalog_content and not real_content:
        lines.append("  ℹ️  Solo existe en catálogo (no desplegado en $DOCKER_BASE)")

    # ── Verificar convenciones contra el real ──────────────────────────────
    source = real_content or catalog_content
    if source:
        lines.append("")
        lines.append("  📋 Convenciones:")

        checks = [
            (_has_healthcheck(source), "healthcheck"),
            (_has_security_opt(source), "security_opt"),
            (_has_resource_limits(source), "resource_limits"),
            (_has_env_file_global(source), "env_file ../.env"),
        ]
        for ok, name in checks:
            icon = "✅" if ok else "❌"
            lines.append(f"     {icon} {name}")
            if not ok:
                has_drift = True

    # ── Resumen ────────────────────────────────────────────────────────────
    lines.append("")
    if has_drift:
        lines.append("  🔶 Drift detectado — sincronizar con: svc catalog-sync {}".format(service))
    else:
        lines.append("  ✅ Sin drift — real y catálogo están sincronizados")
    lines.append("")

    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# TOOL DEL AGENTE
# ─────────────────────────────────────────────────────────────────────────────

try:
    from strands.tools import tool

    @tool
    def compare_catalog(service: str) -> str:
        """Compara la config real de un servicio contra su entrada en el catálogo.

        Detecta drift: diferencias en imagen, puertos, redes, volúmenes,
        env_file, healthcheck, security_opt, y resource_limits.

        Args:
            service: Nombre del servicio a comparar (ej: "emqx", "ntfy").

        Returns:
            Reporte de diferencias o confirmación de sincronización.
        """
        return _compare(service)

except ImportError:
    def compare_catalog(service: str) -> str:
        """Compara config real vs catálogo (versión sin @tool)."""
        return _compare(service)


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python -m agent.tools.compare_tools <servicio>")
        print("     python -m agent.tools.compare_tools --all")
        sys.exit(1)

    if sys.argv[1] == "--all":
        # Comparar todos los servicios del catálogo
        if CATALOG_DIR.exists():
            for svc_dir in sorted(CATALOG_DIR.iterdir()):
                if svc_dir.is_dir() and (svc_dir / "compose.yml").exists():
                    print(_compare(svc_dir.name))
    else:
        print(_compare(sys.argv[1]))
