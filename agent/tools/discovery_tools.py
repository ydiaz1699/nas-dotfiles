"""
Herramientas de descubrimiento de servicios Docker.

Detecta servicios en /docker/, lee sus compose files y puede
generar fichas de catálogo automáticamente.
"""

import yaml
from pathlib import Path
from strands.tools import tool

from agent.core._result import ToolResult, Timer
from agent.tools._shell import (
    DOCKER_BASE,
    safe_run,
    find_compose,
    validate_service_name,
    validated_service_path,
    InvalidServiceName,
)

CATALOG_DIR = Path(__file__).resolve().parent.parent / "catalog" / "services"


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
        if not d.is_dir() or d.name.startswith(".") or d.name in ("cli", "backups", "lost+found"):
            continue
        try:
            validate_service_name(d.name)
        except InvalidServiceName:
            continue
        if find_compose(d.name):
            servicios.append(d.name)

    if not servicios:
        return "No se encontraron servicios Docker en /docker/"

    # Verificar estado de cada uno
    resultados = []
    activos = 0
    detenidos = 0

    for svc in servicios:
        compose = find_compose(svc)
        running = safe_run(
            ["docker", "compose", "-f", str(compose), "ps", "-q"],
            timeout=10,
        )
        count = len(running.strip().splitlines()) if running.strip() and "ERROR" not in running else 0

        if count > 0:
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
    try:
        validate_service_name(service_name)
    except InvalidServiceName as e:
        return f"ERROR: {e}"

    compose_path = find_compose(service_name)

    if not compose_path:
        disponibles = [
            d.name for d in DOCKER_BASE.iterdir()
            if d.is_dir() and not d.name.startswith(".")
            and d.name not in ("cli", "backups")
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

        ports = svc_config.get("ports", [])
        if ports:
            info_parts.append(f"  Puertos: {ports}")

        volumes = svc_config.get("volumes", [])
        if volumes:
            info_parts.append(f"  Volúmenes: {volumes}")

        env = svc_config.get("environment", [])
        env_file = svc_config.get("env_file", [])
        if env:
            if isinstance(env, list):
                env_safe = [
                    e.split("=")[0] + "=***REDACTED***" if any(
                        x in e.lower() for x in [
                            "password", "token", "secret", "cookie", "key",
                            "pass", "user", "login", "credential", "auth",
                            "api_key", "apikey", "private",
                        ]
                    ) else e
                    for e in env
                ]
            else:
                env_safe = list(env.keys())
            info_parts.append(f"  Variables: {env_safe}")
        if env_file:
            info_parts.append(f"  Env file: {env_file}")

        networks = svc_config.get("networks", [])
        if networks:
            info_parts.append(f"  Redes: {networks}")

        health = svc_config.get("healthcheck", None)
        if health:
            info_parts.append(f"  Healthcheck: {health.get('test', '?')}")

        depends = svc_config.get("depends_on", [])
        if depends:
            info_parts.append(f"  Depende de: {depends}")

    info_parts.append(f"\n--- Archivo completo ---\n{content}")

    return "\n".join(info_parts)


@tool
def auto_catalog(service_name: str) -> str:
    """Genera automáticamente una ficha de catálogo para un servicio existente.

    Lee el docker-compose.yml del servicio y crea un archivo .md en
    agent/catalog/services/ con toda la información extraída,
    siguiendo el formato de _template.md.

    Args:
        service_name: Nombre del servicio a catalogar.
                      Ejemplos: plex, nextcloud, grafana
    """
    try:
        validate_service_name(service_name)
    except InvalidServiceName as e:
        return f"ERROR: {e}"

    compose_path = find_compose(service_name)

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

    needs_proxy = "proxy" in str(networks).lower()

    # Generar ficha
    hc_test = ""
    if isinstance(healthcheck.get("test"), list) and len(healthcheck["test"]) > 1:
        hc_test = healthcheck["test"][1]

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
healthcheck: "{hc_test}"
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
    catalog_svc_dir = CATALOG_DIR / service_name
    catalog_svc_dir.mkdir(parents=True, exist_ok=True)
    catalog_file = catalog_svc_dir / "ficha.md"
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



@tool
def bulk_discover() -> str:
    """Descubre todos los servicios en /docker/ y exporta al catálogo.

    Escanea /docker/, identifica servicios con compose, y genera para cada uno:
    - ficha.md (metadatos extraídos del compose)
    - compose.yml (copia del compose real)
    - .env.example (variables sanitizadas — secretos reemplazados por __pega_aqui__)

    Servicios que ya tienen ficha se re-exportan (actualiza compose y .env).
    Al final actualiza el índice catalog.json.

    No requiere argumentos.
    """
    from agent.catalog._index import write_index, build_index

    if not DOCKER_BASE.exists():
        return str(ToolResult.error(
            f"ERROR: No se encontró {DOCKER_BASE}",
            tool_name="bulk_discover",
        ))

    # Encontrar servicios con compose
    servicios_docker = []
    for d in sorted(DOCKER_BASE.iterdir()):
        if not d.is_dir() or d.name.startswith(".") or d.name in ("cli", "backups", "lost+found"):
            continue
        try:
            validate_service_name(d.name)
        except InvalidServiceName:
            continue
        if find_compose(d.name):
            servicios_docker.append(d.name)

    if not servicios_docker:
        return str(ToolResult.warn(
            "No se encontraron servicios Docker en /docker/",
            tool_name="bulk_discover",
        ))

    # Exportar TODOS (genera ficha + compose + .env.example)
    generadas = []
    errores = []

    with Timer() as t:
        for svc in servicios_docker:
            try:
                result = export_service(svc)
                if "✅" in result:
                    generadas.append(svc)
                else:
                    errores.append(f"{svc}: {result[:80]}")
            except Exception as e:
                errores.append(f"{svc}: {e}")
            except Exception as e:
                errores.append(f"{svc}: {e}")

        # Regenerar índice
        index = build_index()
        write_index(index)

    # Construir respuesta
    msg_parts = [
        f"=== BULK DISCOVER & EXPORT ===\n",
        f"Servicios en /docker/: {len(servicios_docker)}",
        f"Exportados (ficha + compose + .env.example): {len(generadas)}",
    ]

    if generadas:
        msg_parts.append(f"\n✅ Exportados:")
        for g in generadas:
            msg_parts.append(f"  • {g}")

    if errores:
        msg_parts.append(f"\n❌ Errores:")
        for e in errores:
            msg_parts.append(f"  • {e}")

    msg_parts.append(f"\n📋 catalog.json actualizado ({index['services_count']} servicios)")
    msg_parts.append(f"\n⚠️  Las fichas generadas son esqueletos — revisar y completar.")

    return str(ToolResult.ok(
        "\n".join(msg_parts),
        data={
            "total_services": len(servicios_docker),
            "exported": generadas,
            "errors": errores,
            "index_count": index["services_count"],
        },
        suggestions=["Revisar fichas en agent/catalog/services/",
                     "validate_compose('<servicio>') para cada uno"],
        tool_name="bulk_discover",
        elapsed_ms=t.elapsed_ms,
    ))



@tool
def export_service(service_name: str) -> str:
    """Exporta la configuración real de un servicio al catálogo de nas-dotfiles.

    Copia compose.yml y .env (sanitizado) desde /docker/<servicio>/ al catálogo
    en agent/catalog/services/<servicio>/ para que sea portable y versionable.

    Los secretos en .env se reemplazan por placeholders (__pega_aqui__).
    Si ya existe una ficha.md, se mantiene. Si no, se genera una básica.

    Esto permite:
    - Reinstalar el NAS y recrear servicios desde el catálogo
    - Versionar la configuración real en git
    - Que el agente sepa exactamente cómo está configurado cada servicio

    Args:
        service_name: Nombre del servicio a exportar.
                      Ejemplo: vaultwarden, emqx, homeassistant
    """
    import re as _re

    try:
        validate_service_name(service_name)
    except InvalidServiceName as e:
        return str(ToolResult.error(f"ERROR: {e}", tool_name="export_service"))

    compose_path = find_compose(service_name)
    if not compose_path:
        return str(ToolResult.error(
            f"ERROR: Servicio '{service_name}' no encontrado en {DOCKER_BASE}",
            tool_name="export_service",
        ))

    svc_docker_dir = compose_path.parent
    catalog_svc_dir = CATALOG_DIR / service_name
    catalog_svc_dir.mkdir(parents=True, exist_ok=True)

    exported = []

    # 1. Copiar compose.yml
    compose_content = compose_path.read_text(encoding="utf-8")
    (catalog_svc_dir / "compose.yml").write_text(compose_content, encoding="utf-8")
    exported.append("compose.yml")

    # 2. Copiar .env sanitizado (reemplazar secretos por placeholders)
    env_path = svc_docker_dir / ".env"
    if env_path.exists():
        env_content = env_path.read_text(encoding="utf-8")
        # Sanitizar: reemplazar valores de variables sensibles
        sensitive_patterns = [
            "password", "secret", "token", "cookie", "key", "pass",
            "user", "username", "login", "credential", "auth",
            "api_key", "apikey", "private",
        ]
        # Excepciones: variables que contienen "user" pero son configs no-sensibles
        safe_exceptions = [
            "allow_anonymous", "allow_user",
        ]
        sanitized_lines = []
        for line in env_content.splitlines():
            if "=" in line and not line.strip().startswith("#"):
                key, _, value = line.partition("=")
                key_lower = key.strip().lower()
                if any(pat in key_lower for pat in sensitive_patterns) and value.strip():
                    # Verificar excepciones (configs que contienen "user" pero no son sensibles)
                    if not any(exc in key_lower for exc in safe_exceptions):
                        sanitized_lines.append(f"{key.strip()}=__pega_aqui__")
                    else:
                        sanitized_lines.append(line)
                else:
                    sanitized_lines.append(line)
            else:
                sanitized_lines.append(line)
        (catalog_svc_dir / ".env.example").write_text(
            "\n".join(sanitized_lines) + "\n", encoding="utf-8"
        )
        exported.append(".env.example (secretos sanitizados)")
    else:
        exported.append("(.env no encontrado)")

    # 3. Copiar README.md si existe
    readme_path = svc_docker_dir / "README.md"
    if readme_path.exists():
        readme_content = readme_path.read_text(encoding="utf-8")
        (catalog_svc_dir / "README.md").write_text(readme_content, encoding="utf-8")
        exported.append("README.md")

    # 4. Generar ficha.md si no existe
    ficha_path = catalog_svc_dir / "ficha.md"
    if not ficha_path.exists():
        # Generar ficha básica con auto_catalog
        auto_catalog(service_name)
        # auto_catalog now writes to catalog_svc_dir/ficha.md directly
        if ficha_path.exists():
            exported.append("ficha.md (generada)")
        else:
            exported.append("ficha.md (no se pudo generar)")
    else:
        exported.append("ficha.md (ya existía)")

    # 5. Regenerar catalog.json
    try:
        from agent.catalog._index import write_index
        write_index()
    except Exception:
        pass

    return str(ToolResult.ok(
        f"✅ Servicio '{service_name}' exportado al catálogo\n\n"
        f"Ubicación: agent/catalog/services/{service_name}/\n"
        f"Archivos:\n" + "\n".join(f"  • {f}" for f in exported) + "\n\n"
        f"Para versionar: git add agent/catalog/services/{service_name}/\n"
        f"En una reinstalación, el agente puede recrear el servicio desde estos archivos.",
        data={
            "service": service_name,
            "catalog_path": str(catalog_svc_dir),
            "exported_files": exported,
        },
        suggestions=[
            f"validate_compose('{service_name}')",
            f"git add agent/catalog/services/{service_name}/",
        ],
        tool_name="export_service",
    ))
