"""
Herramientas de descubrimiento de servicios Docker.

Detecta servicios en /docker/, lee sus compose files y puede
generar fichas de catálogo automáticamente.
"""

import subprocess
import yaml
from pathlib import Path
from strands.tools import tool

DOCKER_BASE = Path("/docker")
CATALOG_DIR = Path(__file__).resolve().parent.parent / "catalog" / "services"


def _run(cmd: str, timeout: int = 30) -> str:
    """Ejecuta un comando shell y retorna stdout."""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=timeout
        )
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        return "ERROR: Comando excedió tiempo límite"
    except Exception as e:
        return f"ERROR: {e}"


def _find_compose_file(service: str) -> Path | None:
    """Busca el archivo compose de un servicio."""
    for name in [
        "docker-compose.yml",
        "docker-compose.yaml",
        "compose.yml",
        "compose.yaml",
    ]:
        path = DOCKER_BASE / service / name
        if path.exists():
            return path
    return None


@tool
def list_services() -> str:
    """Lista todos los servicios Docker detectados en /docker/ con su estado.

    Escanea /docker/ buscando subdirectorios con archivos docker-compose.yml.
    Para cada servicio muestra si está activo o detenido.

    No requiere argumentos.
    """
    if not DOCKER_BASE.exists():
        return (
            f"ERROR: No se encontró {DOCKER_BASE}\n"
            f"¿Está configurada la ruta de Docker correctamente?"
        )

    # Buscar compose files
    servicios = []
    for d in sorted(DOCKER_BASE.iterdir()):
        if not d.is_dir() or d.name.startswith(".") or d.name == "cli":
            continue
        compose = _find_compose_file(d.name)
        if compose:
            servicios.append(d.name)

    if not servicios:
        return "No se encontraron servicios Docker en /docker/"

    # Verificar estado de cada uno
    resultados = []
    activos = 0
    detenidos = 0

    for svc in servicios:
        compose = _find_compose_file(svc)
        running = _run(
            f"docker compose -f {compose} ps -q 2>/dev/null | wc -l"
        ).strip()

        if running and int(running) > 0:
            resultados.append(f"  ● {svc} (activo)")
            activos += 1
        else:
            resultados.append(f"  ○ {svc} (detenido)")
            detenidos += 1

    return (
        f"=== SERVICIOS EN {DOCKER_BASE} ===\n\n"
        f"Total: {len(servicios)} | Activos: {activos} | Detenidos: {detenidos}\n\n"
        + "\n".join(resultados)
    )


@tool
def scan_compose(service_name: str) -> str:
    """Lee y analiza el docker-compose.yml de un servicio específico.

    Extrae: imagen, puertos, volúmenes, redes, variables de entorno,
    healthcheck y dependencias. Útil para entender la configuración
    actual de un servicio.

    Args:
        service_name: Nombre del servicio (= nombre del directorio en /docker/).
                      Ejemplos: nextcloud, plex, grafana, pihole
    """
    compose_path = _find_compose_file(service_name)

    if not compose_path:
        disponibles = [
            d.name for d in DOCKER_BASE.iterdir()
            if d.is_dir() and _find_compose_file(d.name)
        ]
        return (
            f"ERROR: Servicio '{service_name}' no encontrado en {DOCKER_BASE}\n"
            f"Servicios disponibles: {', '.join(sorted(disponibles))}"
        )

    try:
        content = compose_path.read_text(encoding="utf-8")
        data = yaml.safe_load(content)
    except Exception as e:
        return f"ERROR al leer {compose_path}: {e}"

    # Extraer información clave
    services = data.get("services", {})
    info_parts = [f"=== COMPOSE: {service_name} ===\n"]
    info_parts.append(f"Archivo: {compose_path}\n")

    for svc_name, svc_config in services.items():
        info_parts.append(f"\n--- Contenedor: {svc_name} ---")
        info_parts.append(f"  Imagen: {svc_config.get('image', '(build local)')}")
        info_parts.append(
            f"  Container name: {svc_config.get('container_name', '(auto)')}"
        )
        info_parts.append(
            f"  Restart: {svc_config.get('restart', '(no definido)')}"
        )

        # Puertos
        ports = svc_config.get("ports", [])
        if ports:
            info_parts.append(f"  Puertos: {ports}")

        # Volúmenes
        volumes = svc_config.get("volumes", [])
        if volumes:
            info_parts.append(f"  Volúmenes: {volumes}")

        # Environment
        env = svc_config.get("environment", [])
        env_file = svc_config.get("env_file", [])
        if env:
            # Ocultar valores sensibles
            if isinstance(env, list):
                env_safe = [
                    e.split("=")[0] + "=***" if "password" in e.lower()
                    or "token" in e.lower() or "secret" in e.lower()
                    else e
                    for e in env
                ]
            else:
                env_safe = list(env.keys())
            info_parts.append(f"  Variables: {env_safe}")
        if env_file:
            info_parts.append(f"  Env file: {env_file}")

        # Redes
        networks = svc_config.get("networks", [])
        if networks:
            info_parts.append(f"  Redes: {networks}")

        # Healthcheck
        health = svc_config.get("healthcheck", None)
        if health:
            info_parts.append(f"  Healthcheck: {health.get('test', '?')}")

        # Depends
        depends = svc_config.get("depends_on", [])
        if depends:
            info_parts.append(f"  Depende de: {depends}")

    # Compose completo al final
    info_parts.append(f"\n--- Archivo completo ---\n{content}")

    return "\n".join(info_parts)


@tool
def auto_catalog(service_name: str) -> str:
    """Genera automáticamente una ficha de catálogo para un servicio existente.

    Lee el docker-compose.yml del servicio y crea un archivo .md en
    agent/catalog/services/ con toda la información extraída,
    siguiendo el formato de _template.md.

    Útil para catalogar servicios que ya están corriendo en el NAS.

    Args:
        service_name: Nombre del servicio a catalogar.
                      Ejemplos: plex, nextcloud, grafana
    """
    compose_path = _find_compose_file(service_name)

    if not compose_path:
        return f"ERROR: Servicio '{service_name}' no encontrado en {DOCKER_BASE}"

    try:
        content = compose_path.read_text(encoding="utf-8")
        data = yaml.safe_load(content)
    except Exception as e:
        return f"ERROR al leer compose: {e}"

    services = data.get("services", {})
    if not services:
        return "ERROR: No se encontraron servicios en el compose"

    # Tomar el primer servicio como principal
    main_svc_name = list(services.keys())[0]
    main_svc = services[main_svc_name]

    # Extraer datos
    image = main_svc.get("image", "desconocida")
    ports = main_svc.get("ports", [])
    volumes = main_svc.get("volumes", [])
    networks = main_svc.get("networks", [])
    healthcheck = main_svc.get("healthcheck", {})
    env = main_svc.get("environment", [])
    env_file = main_svc.get("env_file", [])

    # Parsear puertos
    port_internal = ""
    port_external = ""
    if ports:
        port_str = str(ports[0])
        if ":" in port_str:
            parts = port_str.replace('"', '').replace("'", "").split(":")
            port_external = parts[0]
            port_internal = parts[1].split("/")[0] if "/" in parts[1] else parts[1]

    # Parsear volúmenes
    vol_list = []
    for v in volumes:
        if isinstance(v, str):
            vol_list.append(f'  - "{v}"')
        elif isinstance(v, dict):
            src = v.get("source", "?")
            tgt = v.get("target", "?")
            vol_list.append(f'  - "{src}:{tgt}"')

    # Variables de entorno
    env_list = []
    if isinstance(env, list):
        env_list = [e.split("=")[0] for e in env]
    elif isinstance(env, dict):
        env_list = list(env.keys())

    # Determinar si necesita proxy
    needs_proxy = "proxy" in str(networks).lower()

    # Determinar categoría por imagen
    category = "otro"
    image_lower = image.lower()
    if any(x in image_lower for x in ["plex", "jellyfin", "emby", "sonarr", "radarr"]):
        category = "media"
    elif any(x in image_lower for x in ["vault", "auth", "keycloak"]):
        category = "seguridad"
    elif any(x in image_lower for x in ["grafana", "prometheus", "uptime"]):
        category = "monitoreo"
    elif any(x in image_lower for x in ["postgres", "mysql", "maria", "redis", "mongo"]):
        category = "base-datos"
    elif any(x in image_lower for x in ["nextcloud", "wiki", "gitea"]):
        category = "productividad"
    elif any(x in image_lower for x in ["traefik", "nginx", "caddy", "pihole"]):
        category = "red"
    elif any(x in image_lower for x in ["home-assistant", "mosquitto"]):
        category = "domótica"

    # Generar ficha
    ficha = f"""---
id: "{service_name}"
name: "{service_name.replace('-', ' ').title()}"
description: "Servicio auto-catalogado desde compose existente"
image: "{image}"
category: "{category}"
port_internal: {port_internal or "0"}
port_default: {port_external or "0"}
protocol: "http"
needs_proxy: {str(needs_proxy).lower()}
needs_db: false
volumes:
{chr(10).join(vol_list) if vol_list else '  - "./data:/data"'}
env_required:
{chr(10).join(f'  - {e}' for e in env_list[:5]) if env_list else '  # (ninguna detectada)'}
healthcheck: "{healthcheck.get('test', [''])[1] if isinstance(healthcheck.get('test'), list) and len(healthcheck.get('test', [])) > 1 else ''}"
backup_critical: true
backup_paths:
  - "./data"
protected: false
docs_url: ""
notes: "Ficha generada automáticamente — revisar y completar"
---

# {service_name.replace('-', ' ').title()}

## Qué es

(Completar manualmente — descripción del servicio)

## Configuración detectada

- Imagen: `{image}`
- Puerto: {port_external}:{port_internal}
- Volúmenes: {len(volumes)} mount(s)
- Variables: {len(env_list)} definidas

## Notas

- Ficha generada automáticamente por nas-agent
- Revisar y completar la descripción y notas de seguridad
"""

    # Guardar ficha
    catalog_file = CATALOG_DIR / f"{service_name}.md"
    catalog_file.parent.mkdir(parents=True, exist_ok=True)
    catalog_file.write_text(ficha, encoding="utf-8")

    return (
        f"✅ Ficha creada: agent/catalog/services/{service_name}.md\n\n"
        f"Datos extraídos:\n"
        f"  Imagen: {image}\n"
        f"  Puerto: {port_external}:{port_internal}\n"
        f"  Volúmenes: {len(volumes)}\n"
        f"  Variables: {len(env_list)}\n"
        f"  Categoría: {category}\n\n"
        f"⚠️  Revisa y completa la ficha manualmente (descripción, docs_url, notas)."
    )
