"""
Herramientas para crear y validar archivos docker-compose.

Permiten al agente generar servicios nuevos siguiendo las
reglas de _rules.md y el formato estándar del NAS (_compose_base.md).
"""

import re
import yaml
from pathlib import Path
from strands.tools import tool
import frontmatter

from agent.tools._shell import (
    DOCKER_BASE,
    safe_run,
    find_compose,
    validate_service_name,
    validated_service_path,
    readonly_guard,
    InvalidServiceName,
)

CATALOG_DIR = Path(__file__).resolve().parent.parent / "catalog"
RULES_FILE = CATALOG_DIR / "_rules.md"
COMPOSE_BASE_FILE = CATALOG_DIR / "_compose_base.md"

# Nombres de anchors que _rules.md exige en todo compose (regla #6)
REQUIRED_ANCHORS = [
    "x-security-defaults",
    "x-healthcheck-defaults",
    "x-logging-defaults",
    "x-resource-defaults",
]


def _load_rules() -> dict:
    """Carga las reglas del catálogo (_rules.md frontmatter)."""
    if RULES_FILE.exists():
        post = frontmatter.load(str(RULES_FILE))
        return post.metadata
    return {}


def _load_compose_base_anchors() -> str:
    """Extrae el bloque de anchors YAML desde _compose_base.md.

    Busca el primer fence ```yaml``` bajo la sección "Bloques base (anchors YAML)"
    y retorna su contenido crudo, listo para anteponer a un compose generado.

    Returns:
        str: bloque de anchors en YAML. Si no se encuentra el archivo o el
             fence, retorna un fallback mínimo hardcodeado.
    """
    if not COMPOSE_BASE_FILE.exists():
        return _fallback_anchors()

    content = COMPOSE_BASE_FILE.read_text(encoding="utf-8")

    # Buscar el primer bloque ```yaml ... ``` que contenga los anchors base
    matches = re.findall(r"```yaml\n(.*?)```", content, re.DOTALL)
    for block in matches:
        if "x-security-defaults" in block and "x-resource-defaults" in block:
            return block.rstrip("\n")

    return _fallback_anchors()


def _fallback_anchors() -> str:
    """Anchors mínimos de respaldo si _compose_base.md no está disponible."""
    return (
        "x-common-env: &common-env\n"
        "  TZ: ${TZ}\n"
        "x-healthcheck-defaults: &healthcheck-defaults\n"
        "  interval: 30s\n"
        "  timeout: 10s\n"
        "  retries: 5\n"
        "  start_period: 40s\n"
        "x-security-defaults: &security-defaults\n"
        "  security_opt:\n"
        "    - no-new-privileges:true\n"
        "x-logging-defaults: &logging-defaults\n"
        "  driver: json-file\n"
        "  options:\n"
        '    max-size: "10m"\n'
        '    max-file: "3"\n'
        "x-resource-defaults: &resource-defaults\n"
        "  deploy:\n"
        "    resources:\n"
        "      limits:\n"
        "        memory: 512m\n"
        "      reservations:\n"
        "        memory: 128m\n"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Sanitización de inputs
# ─────────────────────────────────────────────────────────────────────────────

_YAML_UNSAFE_RE = re.compile(r'[`\x00-\x1f]')


def _sanitize_yaml_value(val: str, field_name: str) -> str:
    """Limpia un valor antes de escribirlo en YAML.

    Bloquea caracteres de control y path traversal.

    Raises:
        InvalidServiceName: Si el valor contiene caracteres peligrosos.
    """
    val = val.strip()
    if _YAML_UNSAFE_RE.search(val):
        raise InvalidServiceName(
            f"Valor de '{field_name}' contiene caracteres no permitidos: {val[:50]}"
        )
    if ".." in val or "\\" in val:
        raise InvalidServiceName(
            f"Valor de '{field_name}' contiene path traversal: {val[:50]}"
        )
    return val


# ─────────────────────────────────────────────────────────────────────────────
# Tools
# ─────────────────────────────────────────────────────────────────────────────


@tool
def read_compose(service_name: str) -> str:
    """Lee el contenido completo del compose de un servicio.

    Retorna el archivo tal cual está, útil para inspección o edición.
    Reconoce tanto compose.yml como docker-compose.yml.

    Args:
        service_name: Nombre del servicio en /docker/.
    """
    try:
        validate_service_name(service_name)
    except InvalidServiceName as e:
        return f"ERROR: {e}"

    compose = find_compose(service_name)
    if not compose:
        return f"ERROR: Servicio '{service_name}' no encontrado en {DOCKER_BASE}"
    content = compose.read_text(encoding="utf-8")
    return f"=== {compose} ===\n\n{content}"


@tool
def validate_compose(service_name: str) -> str:
    """Valida un compose contra las reglas del NAS (_rules.md y _compose_base.md).

    Verifica: estructura, naming, restart policy, puertos reservados,
    healthcheck, anchors base obligatorios, bind de dashboards a localhost,
    variables sensibles, archivos complementarios.

    Args:
        service_name: Nombre del servicio a validar.
    """
    try:
        validate_service_name(service_name)
    except InvalidServiceName as e:
        return f"ERROR: {e}"

    compose_path = find_compose(service_name)
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

    # Nombre de archivo válido (compose.yml o docker-compose.yml)
    if compose_path.name in ("compose.yml", "compose.yaml",
                              "docker-compose.yml", "docker-compose.yaml"):
        ok.append(f"✅ nombre de archivo válido: {compose_path.name}")
    else:
        errores.append(f"❌ nombre de archivo inválido: {compose_path.name}")

    # Anchors base obligatorios (regla #6 de _rules.md)
    anchors_faltantes = [a for a in REQUIRED_ANCHORS if a not in content]
    if anchors_faltantes:
        advertencias.append(
            f"⚠️  Faltan anchors base recomendados: {', '.join(anchors_faltantes)} "
            f"(ver _compose_base.md)"
        )
    else:
        ok.append("✅ anchors base presentes (security/healthcheck/logging/resource)")

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
            p_str = str(p).replace('"', '').replace("'", "")
            port_str = p_str.split(":")[0]
            try:
                if int(port_str) in reserved_ports:
                    errores.append(f"❌ puerto {port_str} es RESERVADO")
            except ValueError:
                pass

            # Advertir si un puerto parece dashboard/admin sin bind a localhost
            svc_blob = str(svc_config).lower()
            if "dashboard" in svc_blob and not p_str.startswith("127.0.0.1:"):
                advertencias.append(
                    f"⚠️  {svc_name}: posible dashboard en puerto '{p_str}' "
                    f"sin bind a 127.0.0.1 — confirmar que la exposición en "
                    f"LAN es intencional y está documentada en la ficha (notes:)"
                )

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

    svc_dir = validated_service_path(service_name)
    if (svc_dir / ".env").exists():
        ok.append("✅ .env presente")
    else:
        advertencias.append("⚠️  Falta .env")
    if (svc_dir / "README.md").exists():
        ok.append("✅ README.md presente")
    else:
        advertencias.append("⚠️  Falta README.md")

    # Validar sintaxis con docker compose config
    config_check = safe_run(
        ["docker", "compose", "-f", str(compose_path), "config", "--quiet"],
        timeout=15,
    )
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
                      Ejemplo: vaultwarden, immich, jellyfin
        image: Imagen Docker con tag. Ejemplo: vaultwarden/server:latest
        port_external: Puerto externo (host). Rango recomendado: 8100-8999.
        port_internal: Puerto interno del contenedor (default: 8080).
        volumes: Bind mounts separados por punto y coma.
                 Ejemplo: ./data:/data;./config:/config
        env_vars: Variables separadas por punto y coma.
                  Ejemplo: ADMIN_TOKEN=CAMBIAR;DOMAIN=http://nas:8200
        healthcheck_url: URL para healthcheck HTTP (ej: http://localhost:8080/health).
                         Si se define, genera un healthcheck tipo CMD curl -f.
        healthcheck_cmd: Comando de healthcheck alternativo (no-HTTP), como lista
                         JSON string. Ejemplo: '["CMD", "emqx", "ctl", "status"]'.
                         Tiene prioridad sobre healthcheck_url si ambos se pasan.
        description: Descripción corta del servicio para README.
        is_dashboard: Si True, indica que port_external corresponde a un panel
                      admin/dashboard. Por defecto se bindea a 127.0.0.1.
        expose_lan: Si True Y is_dashboard es True, expone el dashboard en toda
                    la LAN en vez de solo localhost. Requiere justificación en
                    README/ficha de catálogo — usar con criterio.
        memory_limit: Límite de memoria para x-resource-defaults (default 512m).
        memory_reservation: Reserva de memoria (default 128m).
        high_concurrency: Si True, agrega ulimits nofile altos (1048576) al
                          security block — usar para brokers/proxies con muchas
                          conexiones simultáneas (ej. MQTT).
        networks: Redes Docker externas separadas por punto y coma.
                  Ejemplo: iot_net;db_net
    """
    # Read-only guard
    blocked = readonly_guard("create_service")
    if blocked:
        return blocked

    # Validar nombre de servicio
    try:
        svc_dir = validated_service_path(service_name)
    except InvalidServiceName as e:
        return f"ERROR: {e}"

    if svc_dir.exists():
        return (
            f"ERROR: {svc_dir} ya existe.\n"
            f"Usa read_compose('{service_name}') para ver su config."
        )

    # Verificar puerto
    port_check = safe_run(["ss", "-tnlp"], timeout=10)
    if f":{port_external} " in port_check or f":{port_external}\t" in port_check:
        return f"ERROR: Puerto {port_external} en uso. Usa scan_ports()."

    rules = _load_rules()
    tz = rules.get("nas", {}).get("timezone", "America/La_Paz")

    vol_list = [v.strip() for v in volumes.split(";") if v.strip()]
    env_list = [e.strip() for e in env_vars.split(";") if e.strip()]
    net_list = [n.strip() for n in networks.split(";") if n.strip()]

    # ── Validar inputs ──────────────────────────────────────────────────────

    # Validar image
    try:
        image = _sanitize_yaml_value(image, "image")
        if not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9._/:@-]{0,200}$', image):
            return f"ERROR: Imagen '{image}' no tiene formato válido (namespace/name:tag)"
    except InvalidServiceName as e:
        return f"ERROR: {e}"

    # Validar volumes
    safe_vol_list = []
    for v in vol_list:
        try:
            v = _sanitize_yaml_value(v, "volumes")
            safe_vol_list.append(v)
        except InvalidServiceName as e:
            return f"ERROR: {e}"
    vol_list = safe_vol_list

    # Validar env_vars (formato KEY=VALUE)
    safe_env_list = []
    for e in env_list:
        try:
            e = _sanitize_yaml_value(e, "env_vars")
            if "=" not in e and not re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', e):
                return f"ERROR: Variable '{e}' no tiene formato válido (KEY=VALUE o KEY)"
            safe_env_list.append(e)
        except InvalidServiceName as e_err:
            return f"ERROR: {e_err}"
    env_list = safe_env_list

    # Validar networks
    safe_net_list = []
    for n in net_list:
        try:
            n = _sanitize_yaml_value(n, "networks")
            if not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}$', n):
                return f"ERROR: Red '{n}' no tiene formato válido"
            safe_net_list.append(n)
        except InvalidServiceName as e:
            return f"ERROR: {e}"
    net_list = safe_net_list

    # Validar healthcheck_url
    if healthcheck_url:
        try:
            healthcheck_url = _sanitize_yaml_value(healthcheck_url, "healthcheck_url")
            if not healthcheck_url.startswith(("http://", "https://")):
                return "ERROR: healthcheck_url debe empezar con http:// o https://"
        except InvalidServiceName as e:
            return f"ERROR: {e}"

    # Validar healthcheck_cmd (formato lista JSON-like)
    if healthcheck_cmd:
        try:
            healthcheck_cmd = _sanitize_yaml_value(healthcheck_cmd, "healthcheck_cmd")
            if not (healthcheck_cmd.strip().startswith("[") and healthcheck_cmd.strip().endswith("]")):
                return 'ERROR: healthcheck_cmd debe tener formato de lista, ej. \'["CMD", "cmd", "arg"]\''
        except InvalidServiceName as e:
            return f"ERROR: {e}"

    # ── Determinar bind del puerto principal ────────────────────────────────
    if is_dashboard and not expose_lan:
        port_mapping = f'127.0.0.1:{port_external}:{port_internal}'
        dashboard_note = (
            f"# Dashboard bindeado a localhost (127.0.0.1:{port_external}).\n"
            f"    # Para exponer en LAN, recrear con expose_lan=True y documentar."
        )
    elif is_dashboard and expose_lan:
        port_mapping = f'"{port_external}:{port_internal}"'
        dashboard_note = (
            f"# ⚠️ Dashboard expuesto en LAN (0.0.0.0:{port_external}),\n"
            f"    # NO restringido a localhost. Decisión explícita documentada."
        )
    else:
        port_mapping = f'"{port_external}:{port_internal}"'
        dashboard_note = ""

    # ── Construir bloque de anchors base (desde _compose_base.md) ───────────
    anchors_block = _load_compose_base_anchors()

    # Si high_concurrency, agregar ulimits al anchor de seguridad
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

    # Ajustar memoria del anchor de recursos
    anchors_block = re.sub(
        r"(limits:\n\s+memory: )\S+", rf"\g<1>{memory_limit}", anchors_block
    )
    anchors_block = re.sub(
        r"(reservations:\n\s+memory: )\S+", rf"\g<1>{memory_reservation}", anchors_block
    )

    # ── Construir el compose ────────────────────────────────────────────────
    compose_lines = [anchors_block, "", "services:", f"  {service_name}:"]
    compose_lines.append(f"    image: {image}")
    compose_lines.append(f"    container_name: {service_name}")
    compose_lines.append(f"    restart: unless-stopped")
    compose_lines.append(f"    <<: [*security-defaults, *resource-defaults]")

    # Environment
    compose_lines.append(f"    environment:")
    compose_lines.append(f"      <<: *common-env")
    for e in env_list:
        key = e.split("=")[0]
        compose_lines.append(f"      {key}: ${{{key}}}")

    compose_lines.append(f"    env_file:")
    compose_lines.append(f"      - .env")

    # Healthcheck: prioridad a healthcheck_cmd sobre healthcheck_url
    if healthcheck_cmd:
        compose_lines.append(f"    healthcheck:")
        compose_lines.append(f"      <<: *healthcheck-defaults")
        compose_lines.append(f"      test: {healthcheck_cmd}")
    elif healthcheck_url:
        compose_lines.append(f"    healthcheck:")
        compose_lines.append(f"      <<: *healthcheck-defaults")
        compose_lines.append(f'      test: ["CMD", "curl", "-f", "{healthcheck_url}"]')

    # Logging
    compose_lines.append(f"    logging: *logging-defaults")

    # Volumes
    compose_lines.append(f"    volumes:")
    for v in vol_list:
        compose_lines.append(f"      - {v}")

    # Ports
    if dashboard_note:
        compose_lines.append(f"    {dashboard_note}")
    compose_lines.append(f"    ports:")
    compose_lines.append(f"      - {port_mapping}")

    # Networks (en el servicio)
    if net_list:
        compose_lines.append(f"    networks:")
        for n in net_list:
            compose_lines.append(f"      - {n}")

    # Networks (top-level, declarar como externas)
    if net_list:
        compose_lines.append("")
        compose_lines.append("networks:")
        for n in net_list:
            compose_lines.append(f"  {n}:")
            compose_lines.append(f"    external: true")

    compose = "\n".join(compose_lines) + "\n"

    # ── .env ────────────────────────────────────────────────────────────────
    env_content = f"# Variables para {service_name}\nTZ={tz}\n"
    for e in env_list:
        if "=" in e:
            k, val = e.split("=", 1)
            env_content += f"# CAMBIAR: {k}\n{k}={val}\n"
        else:
            env_content += f"# CAMBIAR: {e}\n{e}=\n"

    # ── README.md ───────────────────────────────────────────────────────────
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
        readme += (
            f"- ⚠️ Dashboard expuesto en LAN (no localhost) — "
            f"justificación: (completar por el usuario)\n"
        )
    if high_concurrency:
        readme += f"- Ulimits nofile alto (1048576) para alta concurrencia\n"

    # ── Escribir archivos ───────────────────────────────────────────────────
    svc_dir.mkdir(parents=True, exist_ok=True)
    (svc_dir / "compose.yml").write_text(compose, encoding="utf-8")
    (svc_dir / ".env").write_text(env_content, encoding="utf-8")
    (svc_dir / "README.md").write_text(readme, encoding="utf-8")

    return (
        f"✅ Servicio '{service_name}' creado en {svc_dir}\n\n"
        f"  - compose.yml (con anchors base de _compose_base.md)\n"
        f"  - .env (revisar CAMBIAR)\n  - README.md\n\n"
        f"Puerto: {port_external}:{port_internal} | Imagen: {image}\n"
        f"Dashboard: {'sí (localhost)' if is_dashboard and not expose_lan else 'sí (LAN)' if is_dashboard else 'no'}\n\n"
        f"Siguiente: service_start('{service_name}') o validate_compose('{service_name}')"
    )
