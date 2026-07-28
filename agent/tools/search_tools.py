"""
Herramienta de búsqueda web para servicios no catalogados.

Cuando el agente necesita crear un servicio que NO está en el
catálogo local, busca información en internet y la adapta
al formato estándar definido en _rules.md.
"""

import json
import re
from pathlib import Path
from strands.tools import tool

from agent.tools._shell import safe_run, validate_service_name, InvalidServiceName

CATALOG_DIR = Path(__file__).resolve().parent.parent / "catalog"



@tool
def search_service_info(service_name: str) -> str:
    """Busca información de un servicio Docker en internet.

    Busca la imagen oficial, puertos, volúmenes, variables de entorno
    y configuración recomendada. Retorna datos compatibles con create_service().

    Usar SOLO cuando el servicio NO está en agent/catalog/services/.

    Args:
        service_name: Nombre del servicio Docker a buscar.
                      Ejemplos: immich, authentik, homepage, freshrss
    """
    try:
        validate_service_name(service_name)
    except InvalidServiceName as e:
        return f"ERROR: {e}"

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

    # Búsqueda de info adicional
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
    """Busca en Docker Hub vía API pública (sin shell)."""
    try:
        url = f"https://hub.docker.com/v2/search/repositories/?query={name}&page_size=5"
        result = safe_run(
            ["curl", "-s", "--max-time", "10", url],
            timeout=15,
        )
        if not result or "ERROR" in result:
            return ""

        data = json.loads(result)
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
    """Intenta encontrar info de configuración desde Docker Hub README."""
    try:
        # Intentar imagen oficial o linuxserver
        for namespace in ["library", "linuxserver"]:
            url = f"https://hub.docker.com/v2/repositories/{namespace}/{name}/"
            result = safe_run(
                ["curl", "-s", "--max-time", "10", url],
                timeout=15,
            )
            if result and "ERROR" not in result and "{" in result:
                try:
                    data = json.loads(result)
                    desc = data.get("full_description", "")
                    if desc:
                        return _extract_info_from_readme(desc)
                except json.JSONDecodeError:
                    continue

        return ""
    except Exception:
        return ""


def _extract_info_from_readme(desc: str) -> str:
    """Extrae info útil (puertos, vars, volúmenes) de un README."""
    info_lines = []
    chunk = desc[:3000]

    # Buscar puertos
    ports = re.findall(r'(\d{2,5})(?:/tcp|/udp|:\d+)', chunk)
    if ports:
        info_lines.append(f"  Puertos mencionados: {', '.join(set(ports[:5]))}")

    # Buscar variables de entorno
    envs = re.findall(r'`?([A-Z][A-Z_]{2,})`?(?:\s*[=:])', chunk)
    if envs:
        info_lines.append(f"  Variables: {', '.join(set(envs[:10]))}")

    # Buscar volúmenes
    vols = re.findall(r'(/\w+/\w+(?:/\w+)?)', desc[:2000])
    common_vols = [v for v in set(vols) if
                   any(x in v for x in ["/config", "/data", "/media"])]
    if common_vols:
        info_lines.append(f"  Volúmenes: {', '.join(common_vols[:5])}")

    return "\n".join(info_lines) if info_lines else ""
