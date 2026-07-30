"""
compose_manager.py — Generación y validación de archivos compose.

Centraliza la lógica de: crear servicios, validar compose, leer compose.
Los tools de compose_tools.py delegan aquí.
"""

import re
from pathlib import Path
from typing import Dict, List, Optional, Any

import yaml

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

CATALOG_DIR = Path(__file__).resolve().parent.parent / "catalog"
RULES_FILE = CATALOG_DIR / "_rules.md"
COMPOSE_BASE_FILE = CATALOG_DIR / "_compose_base.md"

REQUIRED_ANCHORS = [
    "x-security-defaults",
    "x-healthcheck-defaults",
    "x-logging-defaults",
    "x-resource-defaults",
]

_YAML_UNSAFE_RE = re.compile(r'[`\x00-\x1f]')


class ComposeManager:
    """Gestor de archivos Docker Compose."""

    @staticmethod
    def load_rules() -> dict:
        """Carga las reglas del catálogo (_rules.md frontmatter)."""
        try:
            import frontmatter as fm
            if RULES_FILE.exists():
                post = fm.load(str(RULES_FILE))
                return post.metadata
        except ImportError:
            pass
        return {}

    @staticmethod
    def load_compose_base_anchors() -> str:
        """Extrae anchors YAML desde _compose_base.md."""
        if not COMPOSE_BASE_FILE.exists():
            return ComposeManager._fallback_anchors()

        content = COMPOSE_BASE_FILE.read_text(encoding="utf-8")
        matches = re.findall(r"```yaml\n(.*?)```", content, re.DOTALL)
        for block in matches:
            if "x-security-defaults" in block and "x-resource-defaults" in block:
                return block.rstrip("\n")

        return ComposeManager._fallback_anchors()

    @staticmethod
    def _fallback_anchors() -> str:
        """Anchors mínimos de respaldo."""
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

    @staticmethod
    def sanitize_value(val: str, field_name: str) -> str:
        """Limpia un valor antes de escribirlo en YAML.

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

    @staticmethod
    def read(service_name: str) -> ToolResult:
        """Lee el compose de un servicio."""
        try:
            validate_service_name(service_name)
        except InvalidServiceName as e:
            return ToolResult.error(f"ERROR: {e}", tool_name="read_compose")

        compose = find_compose(service_name)
        if not compose:
            return ToolResult.error(
                f"ERROR: Servicio '{service_name}' no encontrado en {DOCKER_BASE}",
                tool_name="read_compose",
            )
        content = compose.read_text(encoding="utf-8")
        return ToolResult.ok(
            f"=== {compose} ===\n\n{content}",
            data={"service": service_name, "path": str(compose), "content": content},
            tool_name="read_compose",
        )

    @staticmethod
    def validate(service_name: str) -> ToolResult:
        """Valida un compose contra _rules.md y _compose_base.md."""
        try:
            validate_service_name(service_name)
        except InvalidServiceName as e:
            return ToolResult.error(f"ERROR: {e}", tool_name="validate_compose")

        compose_path = find_compose(service_name)
        if not compose_path:
            return ToolResult.error(
                f"ERROR: Servicio '{service_name}' no encontrado",
                tool_name="validate_compose",
            )

        try:
            content = compose_path.read_text(encoding="utf-8")
            data = yaml.safe_load(content)
        except Exception as e:
            return ToolResult.error(
                f"❌ Error de sintaxis YAML: {e}",
                tool_name="validate_compose",
            )

        rules = ComposeManager.load_rules()
        ports_config = rules.get("ports", {})
        reserved_ports = ports_config.get("reserved", [22, 53, 80, 443])

        errores: List[str] = []
        advertencias: List[str] = []
        ok: List[str] = []

        # Nombre de archivo
        if compose_path.name in ("compose.yml", "compose.yaml",
                                  "docker-compose.yml", "docker-compose.yaml"):
            ok.append(f"✅ nombre de archivo válido: {compose_path.name}")
        else:
            errores.append(f"❌ nombre de archivo inválido: {compose_path.name}")

        # Anchors base
        anchors_faltantes = [a for a in REQUIRED_ANCHORS if a not in content]
        if anchors_faltantes:
            advertencias.append(
                f"⚠️  Faltan anchors base: {', '.join(anchors_faltantes)} "
                f"(ver _compose_base.md)"
            )
        else:
            ok.append("✅ anchors base presentes")

        services = data.get("services", {})
        if not services:
            return ToolResult.error(
                "❌ No se encontró sección 'services:' en el compose",
                tool_name="validate_compose",
            )

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

                # Dashboard sin localhost
                svc_blob = str(svc_config).lower()
                if "dashboard" in svc_blob and not p_str.startswith("127.0.0.1:"):
                    advertencias.append(
                        f"⚠️  {svc_name}: dashboard sin bind a 127.0.0.1 "
                        f"— confirmar exposición LAN documentada"
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
                            errores.append(
                                f"❌ credencial inline: {e.split('=')[0]}"
                            )

        svc_dir = validated_service_path(service_name)
        if (svc_dir / ".env").exists():
            ok.append("✅ .env presente")
        else:
            advertencias.append("⚠️  Falta .env")
        if (svc_dir / "README.md").exists():
            ok.append("✅ README.md presente")
        else:
            advertencias.append("⚠️  Falta README.md")

        # docker compose config
        config_check = safe_run(
            ["docker", "compose", "-f", str(compose_path), "config", "--quiet"],
            timeout=15,
        )
        if "error" in config_check.lower():
            errores.append(f"❌ docker compose config: {config_check}")
        else:
            ok.append("✅ Sintaxis válida")

        # Construir resultado
        resultado = f"=== VALIDACIÓN: {service_name} ===\n\n"
        if errores:
            resultado += "ERRORES:\n" + "\n".join(f"  {e}" for e in errores) + "\n\n"
        if advertencias:
            resultado += "ADVERTENCIAS:\n" + "\n".join(
                f"  {a}" for a in advertencias) + "\n\n"
        if ok:
            resultado += "OK:\n" + "\n".join(f"  {o}" for o in ok) + "\n\n"
        if not errores:
            resultado += "🎉 Sin errores críticos."
        else:
            resultado += f"⚠️  {len(errores)} error(es) que corregir."

        status = "ok" if not errores else "error"
        return ToolResult(
            success=not errores,
            message=resultado,
            status=ToolResult.error("").status if errores else ToolResult.ok("").status,
            data={
                "service": service_name,
                "errors": errores,
                "warnings": advertencias,
                "ok": ok,
                "error_count": len(errores),
                "warning_count": len(advertencias),
            },
            tool_name="validate_compose",
        )
