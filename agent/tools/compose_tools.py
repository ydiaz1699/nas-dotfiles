"""
Herramientas para crear y validar archivos docker-compose.

Thin wrappers que delegan a agent.core.compose_manager para validación/lectura.
create_service mantiene su lógica aquí por ahora (es más complejo de extraer).
"""

import re
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
    readonly_guard,
    InvalidServiceName,
)


def _get_compose_manager():
    """Lazy import para evitar circular dependency."""
    from agent.core.compose_manager import ComposeManager
    return ComposeManager


@tool
def read_compose(service_name: str) -> str:
    """Lee el contenido completo del compose de un servicio.

    Retorna el archivo tal cual está, útil para inspección o edición.
    Reconoce tanto compose.yml como docker-compose.yml.

    Args:
        service_name: Nombre del servicio en /docker/.
    """
    return str(_get_compose_manager().read(service_name))


@tool
def validate_compose(service_name: str) -> str:
    """Valida un compose contra las reglas del NAS (_rules.md y _compose_base.md).

    Verifica: estructura, naming, restart policy, puertos reservados,
    healthcheck, anchors base obligatorios, bind de dashboards a localhost,
    variables sensibles, archivos complementarios.

    Args:
        service_name: Nombre del servicio a validar.
    """
    return str(_get_compose_manager().validate(service_name))


@tool
def create_service(
    service_name: str,
    image: str,
    port_external: int,
    port_internal: int = 8080,
    volumes: str = "./data:/data",
    env_vars: str = "",
    healthcheck_url: str = "",
    healthcheck_cmd: str = "",
    description: str = "",
    is_dashboard: bool = False,
    expose_lan: bool = False,
    memory_limit: str = "512m",
    memory_reservation: str = "128m",
    high_concurrency: bool = False,
    networks: str = "",
) -> str:
    """Crea la estructura completa de un nuevo servicio Docker en /docker/.

    Genera: compose.yml + .env + README.md siguiendo _rules.md y aplicando
    los anchors base de _compose_base.md (x-security-defaults,
    x-healthcheck-defaults, x-logging-defaults, x-resource-defaults).
    Verifica que el puerto no esté en uso antes de crear.

    Args:
        service_name: Nombre del servicio (directorio y container_name).
        image: Imagen Docker con tag. Ejemplo: vaultwarden/server:latest
        port_external: Puerto externo (host). Rango recomendado: 8100-8999.
        port_internal: Puerto interno del contenedor (default: 8080).
        volumes: Bind mounts separados por punto y coma.
        env_vars: Variables separadas por punto y coma.
        healthcheck_url: URL para healthcheck HTTP.
        healthcheck_cmd: Comando de healthcheck alternativo (formato lista JSON).
        description: Descripción corta del servicio para README.
        is_dashboard: Si True, port_external es un panel admin.
        expose_lan: Si True + is_dashboard, expone en LAN.
        memory_limit: Límite de memoria (default 512m).
        memory_reservation: Reserva de memoria (default 128m).
        high_concurrency: Si True, agrega ulimits nofile altos.
        networks: Redes Docker externas separadas por punto y coma.
    """
    blocked = readonly_guard("create_service")
    if blocked:
        return str(ToolResult.error(blocked, tool_name="create_service"))

    try:
        svc_dir = validated_service_path(service_name)
    except InvalidServiceName as e:
        return str(ToolResult.error(f"ERROR: {e}", tool_name="create_service"))

    if svc_dir.exists():
        return str(ToolResult.error(
            f"ERROR: {svc_dir} ya existe.\n"
            f"Usa read_compose('{service_name}') para ver su config.",
            tool_name="create_service",
        ))

    # Verificar puerto
    port_check = safe_run(["ss", "-tnlp"], timeout=10)
    if f":{port_external} " in port_check or f":{port_external}\t" in port_check:
        return str(ToolResult.error(
            f"ERROR: Puerto {port_external} en uso. Usa scan_ports().",
            tool_name="create_service",
        ))

    rules = _get_compose_manager().load_rules()
    tz = rules.get("nas", {}).get("timezone", "America/La_Paz")

    vol_list = [v.strip() for v in volumes.split(";") if v.strip()]
    env_list = [e.strip() for e in env_vars.split(";") if e.strip()]
    net_list = [n.strip() for n in networks.split(";") if n.strip()]

    # Validar inputs
    try:
        image = _get_compose_manager().sanitize_value(image, "image")
        if not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9._/:@-]{0,200}$', image):
            return str(ToolResult.error(
                f"ERROR: Imagen '{image}' formato inválido",
                tool_name="create_service"))
    except InvalidServiceName as e:
        return str(ToolResult.error(f"ERROR: {e}", tool_name="create_service"))

    safe_vol_list = []
    for v in vol_list:
        try:
            safe_vol_list.append(_get_compose_manager().sanitize_value(v, "volumes"))
        except InvalidServiceName as e:
            return str(ToolResult.error(f"ERROR: {e}", tool_name="create_service"))
    vol_list = safe_vol_list

    safe_env_list = []
    for e in env_list:
        try:
            e = _get_compose_manager().sanitize_value(e, "env_vars")
            if "=" not in e and not re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', e):
                return str(ToolResult.error(
                    f"ERROR: Variable '{e}' formato inválido",
                    tool_name="create_service"))
            safe_env_list.append(e)
        except InvalidServiceName as e_err:
            return str(ToolResult.error(f"ERROR: {e_err}", tool_name="create_service"))
    env_list = safe_env_list

    safe_net_list = []
    for n in net_list:
        try:
            n = _get_compose_manager().sanitize_value(n, "networks")
            if not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}$', n):
                return str(ToolResult.error(
                    f"ERROR: Red '{n}' formato inválido",
                    tool_name="create_service"))
            safe_net_list.append(n)
        except InvalidServiceName as e:
            return str(ToolResult.error(f"ERROR: {e}", tool_name="create_service"))
    net_list = safe_net_list

    if healthcheck_url:
        try:
            healthcheck_url = _get_compose_manager().sanitize_value(healthcheck_url, "healthcheck_url")
            if not healthcheck_url.startswith(("http://", "https://")):
                return str(ToolResult.error(
                    "ERROR: healthcheck_url debe empezar con http://",
                    tool_name="create_service"))
        except InvalidServiceName as e:
            return str(ToolResult.error(f"ERROR: {e}", tool_name="create_service"))

    if healthcheck_cmd:
        try:
            healthcheck_cmd = _get_compose_manager().sanitize_value(healthcheck_cmd, "healthcheck_cmd")
            if not (healthcheck_cmd.strip().startswith("[") and healthcheck_cmd.strip().endswith("]")):
                return str(ToolResult.error(
                    'ERROR: healthcheck_cmd debe ser lista JSON',
                    tool_name="create_service"))
        except InvalidServiceName as e:
            return str(ToolResult.error(f"ERROR: {e}", tool_name="create_service"))

    # Port mapping
    if is_dashboard and not expose_lan:
        port_mapping = f'127.0.0.1:{port_external}:{port_internal}'
        dashboard_note = f"# Dashboard bindeado a localhost (127.0.0.1:{port_external})."
    elif is_dashboard and expose_lan:
        port_mapping = f'"{port_external}:{port_internal}"'
        dashboard_note = f"# Dashboard expuesto en LAN — decisión explícita documentada."
    else:
        port_mapping = f'"{port_external}:{port_internal}"'
        dashboard_note = ""

    # Anchors
    anchors_block = _get_compose_manager().load_compose_base_anchors()
    if high_concurrency:
        anchors_block = anchors_block.replace(
            "x-security-defaults: &security-defaults\n"
            "  security_opt:\n"
            "    - no-new-privileges:true",
            "x-security-defaults: &security-defaults\n"
            "  security_opt:\n"
            "    - no-new-privileges:true\n"
            "  ulimits:\n"
            "    nofile:\n"
            "      soft: 1048576\n"
            "      hard: 1048576",
        )
    anchors_block = re.sub(
        r"(limits:\n\s+memory: )\S+", rf"\g<1>{memory_limit}", anchors_block)
    anchors_block = re.sub(
        r"(reservations:\n\s+memory: )\S+", rf"\g<1>{memory_reservation}", anchors_block)

    # Build compose
    compose_lines = [anchors_block, "", "services:", f"  {service_name}:"]
    compose_lines.append(f"    image: {image}")
    compose_lines.append(f"    container_name: {service_name}")
    compose_lines.append(f"    restart: unless-stopped")
    compose_lines.append(f"    <<: [*security-defaults, *resource-defaults]")
    compose_lines.append(f"    environment:")
    compose_lines.append(f"      <<: *common-env")
    for e in env_list:
        key = e.split("=")[0]
        compose_lines.append(f"      {key}: ${{{key}}}")
    compose_lines.append(f"    env_file:")
    compose_lines.append(f"      - .env")

    if healthcheck_cmd:
        compose_lines.extend([
            f"    healthcheck:",
            f"      <<: *healthcheck-defaults",
            f"      test: {healthcheck_cmd}",
        ])
    elif healthcheck_url:
        compose_lines.extend([
            f"    healthcheck:",
            f"      <<: *healthcheck-defaults",
            f'      test: ["CMD", "curl", "-f", "{healthcheck_url}"]',
        ])

    compose_lines.append(f"    logging: *logging-defaults")
    compose_lines.append(f"    volumes:")
    for v in vol_list:
        compose_lines.append(f"      - {v}")
    if dashboard_note:
        compose_lines.append(f"    {dashboard_note}")
    compose_lines.append(f"    ports:")
    compose_lines.append(f"      - {port_mapping}")
    if net_list:
        compose_lines.append(f"    networks:")
        for n in net_list:
            compose_lines.append(f"      - {n}")
    if net_list:
        compose_lines.append("")
        compose_lines.append("networks:")
        for n in net_list:
            compose_lines.extend([f"  {n}:", f"    external: true"])

    compose = "\n".join(compose_lines) + "\n"

    # .env
    env_content = f"# Variables para {service_name}\nTZ={tz}\n"
    for e in env_list:
        if "=" in e:
            k, val = e.split("=", 1)
            env_content += f"# CAMBIAR: {k}\n{k}={val}\n"
        else:
            env_content += f"# CAMBIAR: {e}\n{e}=\n"

    # README
    readme = f"# {service_name}\n\n{description or '(Descripción)'}\n\n"
    readme += f"## Acceso\n\n- Puerto: {port_external}\n"
    if is_dashboard and not expose_lan:
        readme += f"- URL: http://127.0.0.1:{port_external} (solo localhost)\n\n"
    else:
        readme += f"- URL: http://<IP_NAS>:{port_external}\n\n"
    readme += f"## Datos (backup)\n\n"
    for v in vol_list:
        readme += f"- `{v.split(':')[0]}`\n"
    readme += f"\n## Notas\n\n- Imagen: `{image}`\n- Creado por nas-agent\n"
    if is_dashboard and expose_lan:
        readme += f"- Dashboard expuesto en LAN (justificación: completar)\n"
    if high_concurrency:
        readme += f"- Ulimits nofile alto (1048576)\n"

    # Write
    svc_dir.mkdir(parents=True, exist_ok=True)
    (svc_dir / "compose.yml").write_text(compose, encoding="utf-8")
    (svc_dir / ".env").write_text(env_content, encoding="utf-8")
    (svc_dir / "README.md").write_text(readme, encoding="utf-8")

    return str(ToolResult.ok(
        f"✅ Servicio '{service_name}' creado en {svc_dir}\n\n"
        f"  - compose.yml (con anchors base)\n"
        f"  - .env (revisar CAMBIAR)\n  - README.md\n\n"
        f"Puerto: {port_external}:{port_internal} | Imagen: {image}\n"
        f"Dashboard: {'sí (localhost)' if is_dashboard and not expose_lan else 'sí (LAN)' if is_dashboard else 'no'}\n\n"
        f"Siguiente: service_start('{service_name}') o validate_compose('{service_name}')",
        data={"service": service_name, "image": image, "port": port_external,
              "path": str(svc_dir)},
        suggestions=[f"validate_compose('{service_name}')",
                     f"service_start('{service_name}')"],
        tool_name="create_service",
    ))
