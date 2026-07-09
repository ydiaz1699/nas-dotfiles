"""
Herramientas para crear y validar archivos docker-compose.

Permiten al agente generar servicios nuevos siguiendo las
reglas de _rules.md y el formato estándar del NAS.
"""

import subprocess
import yaml
from pathlib import Path
from strands.tools import tool
import frontmatter

DOCKER_BASE = Path("/docker")
CATALOG_DIR = Path(__file__).resolve().parent.parent / "catalog"
RULES_FILE = CATALOG_DIR / "_rules.md"


def _load_rules() -> dict:
    """Carga las reglas del catálogo (_rules.md frontmatter)."""
    if RULES_FILE.exists():
        post = frontmatter.load(str(RULES_FILE))
        return post.metadata
    return {}


def _run(cmd: str, timeout: int = 30) -> str:
    """Ejecuta un comando shell."""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True,
            text=True, timeout=timeout
        )
        return result.stdout.strip()
    except Exception as e:
        return f"ERROR: {e}"


def _find_compose(service: str) -> Path | None:
    """Busca el archivo compose de un servicio."""
    for name in ["docker-compose.yml", "docker-compose.yaml",
                 "compose.yml", "compose.yaml"]:
        path = DOCKER_BASE / service / name
        if path.exists():
            return path
    return None



@tool
def read_compose(service_name: str) -> str:
    """Lee el contenido completo del docker-compose.yml de un servicio.

    Retorna el archivo tal cual está, útil para inspección o edición.

    Args:
        service_name: Nombre del servicio en /docker/.
    """
    compose = _find_compose(service_name)
    if not compose:
        return f"ERROR: Servicio '{service_name}' no encontrado en {DOCKER_BASE}"
    content = compose.read_text(encoding="utf-8")
    return f"=== {compose} ===\n\n{content}"



@tool
def validate_compose(service_name: str) -> str:
    """Valida un docker-compose.yml contra las reglas del NAS (_rules.md).

    Verifica: estructura, naming, restart policy, puertos reservados,
    healthcheck, variables sensibles, archivos complementarios.

    Args:
        service_name: Nombre del servicio a validar.
    """
    compose_path = _find_compose(service_name)
    if not compose_path:
        return f"ERROR: Servicio '{service_name}' no encontrado"

    try:
        content = compose_path.read_text(encoding="utf-8")
        data = yaml.safe_load(content)
    except Exception as e:
        return f"❌ Error de sintaxis YAML: {e}"

    rules = _load_rules()
    ports_config = rules.get("ports", {})
    reserved_ports = ports_config.get("reserved", [22, 53, 80, 443])

    errores = []
    advertencias = []
    ok = []

    services = data.get("services", {})
    if not services:
        return "❌ No se encontró sección 'services:' en el compose"

    for svc_name, svc_config in services.items():
        if "container_name" in svc_config:
            ok.append(f"✅ container_name: {svc_config['container_name']}")
        else:
            advertencias.append(f"⚠️  {svc_name}: falta container_name")

        restart = svc_config.get("restart", "")
        if restart == "unless-stopped":
            ok.append("✅ restart: unless-stopped")
        elif restart:
            advertencias.append(f"⚠️  restart='{restart}' (usar unless-stopped)")
        else:
            errores.append(f"❌ {svc_name}: falta restart policy")

        for p in svc_config.get("ports", []):
            port_str = str(p).split(":")[0].replace('"', '').replace("'", "")
            try:
                if int(port_str) in reserved_ports:
                    errores.append(f"❌ puerto {port_str} es RESERVADO")
            except ValueError:
                pass

        if "healthcheck" in svc_config:
            ok.append("✅ healthcheck definido")
        else:
            advertencias.append(f"⚠️  {svc_name}: sin healthcheck")

        env = svc_config.get("environment", [])
        if isinstance(env, list):
            for e in env:
                el = e.lower() if isinstance(e, str) else ""
                if any(x in el for x in ["password=", "token=", "secret="]):
                    if "${" not in e:
                        errores.append(f"❌ credencial inline: {e.split('=')[0]}")

    svc_dir = DOCKER_BASE / service_name
    if (svc_dir / ".env").exists():
        ok.append("✅ .env presente")
    else:
        advertencias.append("⚠️  Falta .env")
    if (svc_dir / "README.md").exists():
        ok.append("✅ README.md presente")
    else:
        advertencias.append("⚠️  Falta README.md")

    config_check = _run(f"docker compose -f {compose_path} config --quiet 2>&1")
    if "error" in config_check.lower():
        errores.append(f"❌ docker compose config: {config_check}")
    else:
        ok.append("✅ Sintaxis válida")

    resultado = f"=== VALIDACIÓN: {service_name} ===\n\n"
    if errores:
        resultado += "ERRORES:\n" + "\n".join(f"  {e}" for e in errores) + "\n\n"
    if advertencias:
        resultado += "ADVERTENCIAS:\n" + "\n".join(f"  {a}" for a in advertencias) + "\n\n"
    if ok:
        resultado += "OK:\n" + "\n".join(f"  {o}" for o in ok) + "\n\n"
    if not errores:
        resultado += "🎉 Sin errores críticos."
    else:
        resultado += f"⚠️  {len(errores)} error(es) que corregir."
    return resultado



@tool
def create_service(
    service_name: str,
    image: str,
    port_external: int,
    port_internal: int = 8080,
    volumes: str = "./data:/data",
    env_vars: str = "",
    healthcheck_url: str = "",
    description: str = "",
) -> str:
    """Crea la estructura completa de un nuevo servicio Docker en /docker/.

    Genera: docker-compose.yml + .env + README.md siguiendo _rules.md.
    Verifica que el puerto no esté en uso antes de crear.

    Args:
        service_name: Nombre del servicio (directorio y container_name).
                      Ejemplo: vaultwarden, immich, jellyfin
        image: Imagen Docker con tag. Ejemplo: vaultwarden/server:latest
        port_external: Puerto externo (host). Rango recomendado: 8100-8999.
        port_internal: Puerto interno del contenedor (default: 8080).
        volumes: Bind mounts separados por punto y coma.
                 Ejemplo: ./data:/data;./config:/config
        env_vars: Variables separadas por punto y coma.
                  Ejemplo: ADMIN_TOKEN=CAMBIAR;DOMAIN=http://nas:8200
        healthcheck_url: URL para healthcheck (ej: http://localhost:8080/health).
        description: Descripción corta del servicio para README.
    """
    svc_dir = DOCKER_BASE / service_name

    if svc_dir.exists():
        return (
            f"ERROR: {svc_dir} ya existe.\n"
            f"Usa read_compose('{service_name}') para ver su config."
        )

    # Verificar puerto
    ports_in_use = _run(
        "ss -tnlp 2>/dev/null | grep -oP ':\\K[0-9]+(?=\\s)' | sort -n | uniq"
    )
    if str(port_external) in ports_in_use.split("\n"):
        return f"ERROR: Puerto {port_external} en uso. Usa scan_ports()."

    rules = _load_rules()
    tz = rules.get("nas", {}).get("timezone", "America/New_York")

    vol_list = [v.strip() for v in volumes.split(";") if v.strip()]
    env_list = [e.strip() for e in env_vars.split(";") if e.strip()]

    # docker-compose.yml
    compose = f"services:\n  {service_name}:\n"
    compose += f"    image: {image}\n"
    compose += f"    container_name: {service_name}\n"
    compose += f"    restart: unless-stopped\n"
    compose += f"    ports:\n      - \"{port_external}:{port_internal}\"\n"
    compose += f"    volumes:\n"
    for v in vol_list:
        compose += f"      - {v}\n"
    compose += f"    environment:\n"
    compose += f"      - TZ=${{{tz}}}\n"
    for e in env_list:
        key = e.split("=")[0]
        compose += f"      - {key}=${{{key}}}\n"
    compose += f"    env_file:\n      - .env\n"
    if healthcheck_url:
        compose += f"    healthcheck:\n"
        compose += f"      test: [\"CMD\", \"curl\", \"-f\", \"{healthcheck_url}\"]\n"
        compose += f"      interval: 30s\n"
        compose += f"      timeout: 10s\n"
        compose += f"      retries: 3\n"
        compose += f"      start_period: 30s\n"

    # .env
    env_content = f"# Variables para {service_name}\nTZ={tz}\n"
    for e in env_list:
        if "=" in e:
            k, val = e.split("=", 1)
            env_content += f"# CAMBIAR: {k}\n{k}={val}\n"
        else:
            env_content += f"# CAMBIAR: {e}\n{e}=\n"

    # README.md
    readme = f"# {service_name}\n\n{description or '(Descripción)'}\n\n"
    readme += f"## Acceso\n\n- Puerto: {port_external}\n"
    readme += f"- URL: http://<IP_NAS>:{port_external}\n\n"
    readme += f"## Datos (backup)\n\n"
    for v in vol_list:
        readme += f"- `{v.split(':')[0]}`\n"
    readme += f"\n## Notas\n\n- Imagen: `{image}`\n- Creado por nas-agent\n"

    # Escribir
    svc_dir.mkdir(parents=True, exist_ok=True)
    (svc_dir / "docker-compose.yml").write_text(compose, encoding="utf-8")
    (svc_dir / ".env").write_text(env_content, encoding="utf-8")
    (svc_dir / "README.md").write_text(readme, encoding="utf-8")

    return (
        f"✅ Servicio '{service_name}' creado en {svc_dir}\n\n"
        f"  - docker-compose.yml\n  - .env (revisar CAMBIAR)\n  - README.md\n\n"
        f"Puerto: {port_external}:{port_internal} | Imagen: {image}\n\n"
        f"Siguiente: service_start('{service_name}') o validate_compose('{service_name}')"
    )
