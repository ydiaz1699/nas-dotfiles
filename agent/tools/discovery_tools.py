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

    # ── Extraer ${VAR} de TODO el YAML (no solo environment) ───────────────
    # Esto detecta variables en command, healthcheck, labels, ports, etc.
    var_pattern = re.compile(r'\$\{([A-Za-z_][A-Za-z0-9_]*)')
    all_external_vars = set()
    raw_yaml_str = content  # el YAML original como string
    for match in var_pattern.finditer(raw_yaml_str):
        all_external_vars.add(match.group(1))

    # ── Detectar si es stack multi-servicio ────────────────────────────────
    is_stack = len(services) > 1

    # ── Extraer datos de TODOS los servicios ───────────────────────────────
    all_services_info = []
    main_image = ""
    all_ports = []
    all_volumes = []
    all_networks = set()
    networks_external = set()
    main_healthcheck = {}

    for idx, (svc_name, svc_config) in enumerate(services.items()):
        svc_image = svc_config.get("image", "desconocida")
        svc_ports = svc_config.get("ports", [])
        svc_volumes = svc_config.get("volumes", [])
        svc_networks = svc_config.get("networks", [])
        svc_healthcheck = svc_config.get("healthcheck", {})
        svc_depends = svc_config.get("depends_on", [])
        svc_deploy = svc_config.get("deploy", {})
        svc_security = svc_config.get("security_opt", [])
        svc_cap_drop = svc_config.get("cap_drop", [])
        svc_cap_add = svc_config.get("cap_add", [])

        # Primer servicio = principal
        if idx == 0:
            main_image = svc_image
            main_healthcheck = svc_healthcheck

        # Parsear puertos del servicio
        port_internal = ""
        port_external = ""
        if svc_ports:
            port_str = str(svc_ports[0])
            if ":" in port_str:
                parts = port_str.replace('"', '').replace("'", "").split(":")
                if len(parts) >= 2:
                    port_external = parts[-2].split(".")[-1] if "." in parts[-2] else parts[-2]
                    port_internal = parts[-1].split("/")[0] if "/" in parts[-1] else parts[-1]

        # Healthcheck de este servicio
        hc_str = ""
        if isinstance(svc_healthcheck.get("test"), list) and len(svc_healthcheck["test"]) > 1:
            hc_str = " ".join(svc_healthcheck["test"][1:])

        # Resource limits
        resources = svc_deploy.get("resources", {})
        limits = resources.get("limits", {})
        reservations = resources.get("reservations", {})

        # Info del servicio para el frontmatter
        svc_info = {
            "name": svc_name,
            "image": svc_image,
        }
        if port_internal:
            svc_info["port_internal"] = int(port_internal) if port_internal.isdigit() else port_internal
        if port_external:
            svc_info["port_external"] = int(port_external) if port_external.isdigit() else port_external
        if not svc_ports:
            svc_info["exposure"] = "internal"
        if hc_str:
            svc_info["healthcheck"] = hc_str
        if svc_depends:
            if isinstance(svc_depends, list):
                svc_info["depends_on"] = svc_depends
            elif isinstance(svc_depends, dict):
                svc_info["depends_on"] = list(svc_depends.keys())
        if limits:
            svc_info["resource_limits"] = {}
            if limits.get("cpus"):
                svc_info["resource_limits"]["cpus"] = limits["cpus"]
            if limits.get("memory"):
                svc_info["resource_limits"]["memory"] = limits["memory"]
        if svc_security:
            svc_info["security_opt"] = svc_security
        if svc_cap_drop:
            svc_info["cap_drop"] = svc_cap_drop
        if svc_cap_add:
            svc_info["cap_add"] = svc_cap_add

        all_services_info.append(svc_info)

        # Acumular datos globales
        all_ports.extend(svc_ports)
        all_volumes.extend(svc_volumes)
        if isinstance(svc_networks, list):
            all_networks.update(svc_networks)
        elif isinstance(svc_networks, dict):
            all_networks.update(svc_networks.keys())

    # Detectar redes externas
    top_networks = data.get("networks", {})
    for net_name, net_config in top_networks.items():
        if isinstance(net_config, dict) and net_config.get("external"):
            networks_external.add(net_name)

    # Parsear primer puerto para campos legacy
    first_port_internal = ""
    first_port_external = ""
    if all_ports:
        port_str = str(all_ports[0])
        if ":" in port_str:
            parts = port_str.replace('"', '').replace("'", "").split(":")
            if len(parts) >= 2:
                first_port_external = parts[-2].split(".")[-1] if "." in parts[-2] else parts[-2]
                first_port_internal = parts[-1].split("/")[0] if "/" in parts[-1] else parts[-1]

    # Parsear volúmenes
    vol_list = []
    for v in all_volumes:
        if isinstance(v, str):
            vol_list.append(f'  - "{v}"')
        elif isinstance(v, dict):
            src = v.get("source", "?")
            tgt = v.get("target", "?")
            vol_list.append(f'  - "{src}:{tgt}"')

    # Determinar categoría por imagen principal
    category = "otro"
    image_lower = main_image.lower()
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
    elif any(x in image_lower for x in ["home-assistant", "mosquitto", "emqx"]):
        category = "domótica"

    needs_proxy = "proxy" in str(list(all_networks)).lower()

    # Generar aliases a partir de nombres de servicios e imágenes
    aliases = set()
    aliases.add(service_name)
    for svc_info in all_services_info:
        aliases.add(svc_info["name"])
        img_name = svc_info["image"].split("/")[-1].split(":")[0]
        aliases.add(img_name)
    aliases.discard(service_name)
    aliases_list = sorted(aliases)

    # ── Generar bloque services para el frontmatter ────────────────────────
    services_yaml = ""
    if is_stack:
        services_yaml = "services:\n"
        for svc_info in all_services_info:
            services_yaml += f'  - name: {svc_info["name"]}\n'
            services_yaml += f'    image: "{svc_info["image"]}"\n'
            if "port_internal" in svc_info:
                services_yaml += f'    port_internal: {svc_info["port_internal"]}\n'
            if "port_external" in svc_info:
                services_yaml += f'    port_external: {svc_info["port_external"]}\n'
            if svc_info.get("exposure") == "internal":
                services_yaml += f'    exposure: internal\n'
            if "healthcheck" in svc_info:
                services_yaml += f'    healthcheck: "{svc_info["healthcheck"]}"\n'
            if "depends_on" in svc_info:
                deps = ", ".join(svc_info["depends_on"])
                services_yaml += f'    depends_on: [{deps}]\n'
            if "resource_limits" in svc_info:
                rl = svc_info["resource_limits"]
                if rl.get("cpus"):
                    services_yaml += f'    cpus: "{rl["cpus"]}"\n'
                if rl.get("memory"):
                    services_yaml += f'    memory: "{rl["memory"]}"\n'
            if "security_opt" in svc_info:
                services_yaml += f'    security_opt: {svc_info["security_opt"]}\n'
            if "cap_drop" in svc_info:
                services_yaml += f'    cap_drop: {svc_info["cap_drop"]}\n'
            if "cap_add" in svc_info:
                services_yaml += f'    cap_add: {svc_info["cap_add"]}\n'

    # Nombre legible
    display_name = service_name.replace('-', ' ').replace('_', ' ').title()
    if is_stack:
        display_name = f"Stack {display_name}"

    # Descripción
    if is_stack:
        svc_names = [s["name"] for s in all_services_info]
        description = f"Stack multi-servicio: {' + '.join(svc_names)}"
    else:
        description = "Servicio auto-catalogado desde compose existente"

    # Redes (con indicación de external)
    networks_yaml = ""
    if all_networks:
        networks_yaml = "networks:\n"
        for n in sorted(all_networks):
            if n in networks_external:
                networks_yaml += f"  - name: {n}\n    external: true\n"
            else:
                networks_yaml += f"  - {n}\n"

    # ── Construir ficha (variables pre-calculadas) ─────────────────────────
    newline = "\n"
    vol_lines = newline.join(vol_list) if vol_list else '  - "./data:/data"'
    env_sorted = sorted(all_external_vars)
    env_lines = newline.join(f'  - {e}' for e in env_sorted) if env_sorted else '  # (ninguna detectada)'
    svc_names_str = ", ".join(s["name"] for s in all_services_info)
    nets_str = ", ".join(sorted(all_networks)) if all_networks else "ninguna"
    num_services = len(all_services_info)
    num_volumes = len(all_volumes)
    num_env = len(env_sorted)

    # Healthcheck del principal
    hc_test = ""
    if isinstance(main_healthcheck.get("test"), list) and len(main_healthcheck["test"]) > 1:
        hc_test = " ".join(main_healthcheck["test"][1:])

    ficha = f"""---
id: "{service_name}"
name: "{display_name}"
aliases: {aliases_list}
description: "{description}"
image: "{main_image}"
category: "{category}"
port_internal: {first_port_internal or "0"}
port_default: {first_port_external or "0"}
needs_proxy: {str(needs_proxy).lower()}
needs_db: false
{services_yaml}volumes:
{vol_lines}
env_required:
{env_lines}
healthcheck: "{hc_test}"
backup_critical: true
backup_paths:
  - "./data"
protected: false
docs_url: ""
{networks_yaml}notes: "Ficha generada automáticamente — revisar y completar"
---

# {display_name}

## Qué es

(Completar manualmente — descripción del servicio)

## Configuración detectada

- Imagen principal: `{main_image}`
- Contenedores: {num_services} ({svc_names_str})
- Puerto principal: {first_port_external}:{first_port_internal}
- Volúmenes: {num_volumes} mount(s)
- Variables externas (${{VAR}}): {num_env}
- Redes: {nets_str}

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
        f"✅ Ficha creada: agent/catalog/services/{service_name}/ficha.md\n\n"
        f"Datos extraídos:\n"
        f"  Imagen: {main_image}\n"
        f"  Puerto: {first_port_external}:{first_port_internal}\n"
        f"  Contenedores: {num_services} ({svc_names_str})\n"
        f"  Volúmenes: {num_volumes}\n"
        f"  Variables: {num_env}\n"
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
