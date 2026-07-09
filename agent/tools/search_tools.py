"""
Herramienta de búsqueda web para servicios no catalogados.

Cuando el agente necesita crear un servicio que NO está en el
catálogo local, busca información en internet y la adapta
al formato estándar definido en _rules.md.
"""

import subprocess
import json
from pathlib import Path
from strands.tools import tool

CATALOG_DIR = Path(__file__).resolve().parent.parent / "catalog"
RULES_FILE = CATALOG_DIR / "_rules.md"



@tool
def search_service_info(service_name: str) -> str:
    """Busca información de un servicio Docker en internet.

    Busca la imagen oficial, puertos, volúmenes, variables de entorno
    y configuración recomendada. Retorna los datos en un formato
    compatible con el catálogo local para que el agente pueda
    usarlos directamente con create_service().

    Usar SOLO cuando el servicio NO está en agent/catalog/services/.
    Después de crear el servicio, usar auto_catalog() para guardar la ficha.

    Args:
        service_name: Nombre del servicio Docker a buscar.
                      Ejemplos: immich, authentik, homepage, freshrss,
                      uptime-kuma, actual-budget, paperless-ngx
    """
    # Verificar si ya está en catálogo
    catalog_file = CATALOG_DIR / "services" / f"{service_name}.md"
    if catalog_file.exists():
        content = catalog_file.read_text(encoding="utf-8")
        return (
            f"ℹ️  '{service_name}' YA está en el catálogo local.\n\n"
            f"Ficha:\n{content}\n\n"
            f"No es necesario buscar en internet."
        )

    # Búsqueda en Docker Hub vía API
    hub_info = _search_dockerhub(service_name)

    # Búsqueda en GitHub (compose de ejemplo)
    github_info = _search_github_compose(service_name)

    # Combinar resultados
    resultado = f"=== BÚSQUEDA: {service_name} ===\n\n"

    if hub_info:
        resultado += f"--- Docker Hub ---\n{hub_info}\n\n"
    else:
        resultado += "--- Docker Hub ---\n  (sin resultados)\n\n"

    if github_info:
        resultado += f"--- GitHub/Docs ---\n{github_info}\n\n"
    else:
        resultado += "--- GitHub/Docs ---\n  (sin resultados)\n\n"

    resultado += (
        "--- Siguiente paso ---\n"
        "Con esta información, usa create_service() para generar\n"
        "el compose siguiendo las reglas del NAS (_rules.md).\n"
        "Después usa auto_catalog() para guardar la ficha."
    )

    return resultado


def _search_dockerhub(name: str) -> str:
    """Busca en Docker Hub vía API pública."""
    try:
        cmd = (
            f"curl -s 'https://hub.docker.com/v2/search/repositories/"
            f"?query={name}&page_size=5' 2>/dev/null"
        )
        result = subprocess.run(
            cmd, shell=True, capture_output=True,
            text=True, timeout=15
        )
        if result.returncode != 0:
            return ""

        data = json.loads(result.stdout)
        results = data.get("results", [])

        if not results:
            return ""

        lines = []
        for r in results[:5]:
            repo = r.get("repo_name", "?")
            desc = r.get("short_description", "")[:80]
            stars = r.get("star_count", 0)
            official = "✅ OFICIAL" if r.get("is_official") else ""
            lines.append(f"  {repo} ({stars}⭐) {official}")
            if desc:
                lines.append(f"    {desc}")

        return "\n".join(lines)
    except Exception:
        return ""


def _search_github_compose(name: str) -> str:
    """Intenta encontrar info de configuración vía linuxserver o docs."""
    try:
        # Intentar obtener info de la imagen más popular
        cmd = (
            f"curl -s 'https://hub.docker.com/v2/repositories/"
            f"library/{name}/' 2>/dev/null || "
            f"curl -s 'https://hub.docker.com/v2/repositories/"
            f"linuxserver/{name}/' 2>/dev/null"
        )
        result = subprocess.run(
            cmd, shell=True, capture_output=True,
            text=True, timeout=15
        )
        if result.returncode != 0 or not result.stdout.strip():
            return ""

        data = json.loads(result.stdout)
        desc = data.get("full_description", "")

        if not desc:
            return ""

        # Extraer info útil del README del Docker Hub
        info_lines = []

        # Buscar puertos mencionados
        import re
        ports = re.findall(r'(\d{2,5})(?:/tcp|/udp|:\d+)', desc[:3000])
        if ports:
            info_lines.append(f"  Puertos mencionados: {', '.join(set(ports[:5]))}")

        # Buscar variables de entorno
        envs = re.findall(r'`?([A-Z][A-Z_]{2,})`?(?:\s*[=:])', desc[:3000])
        if envs:
            info_lines.append(f"  Variables: {', '.join(set(envs[:10]))}")

        # Buscar volúmenes
        vols = re.findall(r'(/\w+/\w+(?:/\w+)?)', desc[:2000])
        common_vols = [v for v in set(vols) if
                       any(x in v for x in ["/config", "/data", "/media"])]
        if common_vols:
            info_lines.append(f"  Volúmenes: {', '.join(common_vols[:5])}")

        return "\n".join(info_lines) if info_lines else ""
    except Exception:
        return ""
