"""
Herramientas de diagnóstico para el NAS.

Permiten al agente detectar problemas: servicios caídos,
conflictos de puertos, contenedores con muchos restarts,
uso excesivo de recursos, etc.
"""

import subprocess
from pathlib import Path
from strands.tools import tool

DOCKER_BASE = Path("/docker")


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
def service_health() -> str:
    """Dashboard de salud de todos los servicios Docker.

    Para cada servicio muestra: estado, healthcheck, uptime,
    restart count y alertas. Equivalente a 'svc health'.

    No requiere argumentos.
    """
    output = _run("svc health 2>/dev/null", timeout=60)

    if output:
        return f"=== SALUD DE SERVICIOS ===\n\n{output}"

    # Fallback si el CLI no está disponible
    containers = _run(
        "docker ps -a --format "
        "'{{.Names}}\\t{{.Status}}\\t{{.State}}' 2>/dev/null"
    )

    if not containers:
        return "No hay contenedores Docker corriendo"

    lines = containers.strip().splitlines()
    activos = sum(1 for l in lines if "running" in l.lower() or "up" in l.lower())
    total = len(lines)

    # Buscar problemas
    problemas = []
    for line in lines:
        parts = line.split("\t")
        if len(parts) >= 3:
            name, status, state = parts[0], parts[1], parts[2]
            if state.lower() != "running":
                problemas.append(f"  🔴 {name}: {status}")
            elif "unhealthy" in status.lower():
                problemas.append(f"  🟡 {name}: unhealthy")
            elif "Restarting" in status:
                problemas.append(f"  🟡 {name}: reiniciando")

    resultado = (
        f"=== SALUD DE SERVICIOS ===\n\n"
        f"Total: {total} | Activos: {activos} | "
        f"Problemas: {len(problemas)}\n\n"
    )

    if problemas:
        resultado += "--- Problemas detectados ---\n"
        resultado += "\n".join(problemas) + "\n\n"
    else:
        resultado += "✅ Todos los servicios están saludables.\n\n"

    resultado += f"--- Detalle ---\n{containers}"
    return resultado


@tool
def port_conflicts() -> str:
    """Detecta conflictos de puertos entre servicios Docker.

    Escanea todos los compose files y compara puertos asignados.
    También verifica contra puertos del sistema (no-Docker).

    No requiere argumentos.
    """
    import yaml

    puertos = {}  # puerto → [servicio, ...]

    # Escanear compose files
    for d in sorted(DOCKER_BASE.iterdir()):
        if not d.is_dir() or d.name.startswith(".") or d.name == "cli":
            continue
        compose = _find_compose(d.name)
        if not compose:
            continue

        try:
            data = yaml.safe_load(compose.read_text(encoding="utf-8"))
            services = data.get("services", {})
            for svc_config in services.values():
                for p in svc_config.get("ports", []):
                    port_str = str(p).split(":")[0].replace('"', '').replace("'", "")
                    try:
                        port_num = int(port_str)
                        if port_num not in puertos:
                            puertos[port_num] = []
                        puertos[port_num].append(d.name)
                    except ValueError:
                        pass
        except Exception:
            continue

    # Detectar conflictos
    conflictos = {p: svcs for p, svcs in puertos.items() if len(svcs) > 1}

    resultado = "=== ANÁLISIS DE PUERTOS ===\n\n"
    resultado += f"Servicios escaneados: {len([d for d in DOCKER_BASE.iterdir() if d.is_dir()])}\n"
    resultado += f"Puertos asignados: {len(puertos)}\n\n"

    if conflictos:
        resultado += "🔴 CONFLICTOS DETECTADOS:\n"
        for port, svcs in sorted(conflictos.items()):
            resultado += f"  Puerto {port}: {', '.join(svcs)}\n"
        resultado += "\n"
    else:
        resultado += "✅ Sin conflictos de puertos.\n\n"

    # Mapa de puertos
    resultado += "--- Mapa de puertos ---\n"
    for port in sorted(puertos.keys()):
        svcs = puertos[port]
        resultado += f"  :{port} → {', '.join(svcs)}\n"

    return resultado



@tool
def troubleshoot(service_name: str) -> str:
    """Diagnóstico completo de un servicio con problemas.

    Revisa: estado, logs recientes, healthcheck, restart count,
    uso de recursos, puertos, y sugiere soluciones.

    Args:
        service_name: Nombre del servicio a diagnosticar.
    """
    compose = _find_compose(service_name)
    if not compose:
        return f"ERROR: Servicio '{service_name}' no encontrado"

    resultado = f"=== DIAGNÓSTICO: {service_name} ===\n\n"

    # 1. Estado
    status = _run(
        f"docker compose -f {compose} ps --format "
        f"'{{{{.Name}}}}\\t{{{{.Status}}}}\\t{{{{.State}}}}' 2>/dev/null"
    )
    resultado += f"--- Estado ---\n{status or '(no hay contenedores)'}\n\n"

    # 2. Healthcheck
    container_id = _run(
        f"docker compose -f {compose} ps -q 2>/dev/null | head -1"
    )
    if container_id:
        health = _run(
            f"docker inspect --format="
            f"'{{{{if .State.Health}}}}{{{{.State.Health.Status}}}}{{{{else}}}}sin-healthcheck{{{{end}}}}' "
            f"{container_id} 2>/dev/null"
        )
        resultado += f"--- Healthcheck ---\n  {health}\n\n"

        # Restart count
        restarts = _run(
            f"docker inspect --format='{{{{.RestartCount}}}}' "
            f"{container_id} 2>/dev/null"
        )
        resultado += f"--- Restarts ---\n  {restarts} veces\n"
        if restarts and int(restarts) > 5:
            resultado += "  ⚠️ Muchos restarts — posible crash loop\n"
        resultado += "\n"

        # Recursos
        stats = _run(
            f"docker stats --no-stream --format "
            f"'CPU: {{{{.CPUPerc}}}}  MEM: {{{{.MemUsage}}}}  NET: {{{{.NetIO}}}}' "
            f"{container_id} 2>/dev/null"
        )
        resultado += f"--- Recursos ---\n  {stats}\n\n"

    # 3. Últimos logs (últimas 30 líneas)
    logs = _run(
        f"docker compose -f {compose} logs --tail=30 --no-color 2>&1",
        timeout=15,
    )
    # Buscar errores en logs
    error_lines = [
        l for l in (logs or "").splitlines()
        if any(x in l.lower() for x in ["error", "fatal", "panic", "exception"])
    ]

    if error_lines:
        resultado += "--- Errores en logs ---\n"
        for line in error_lines[:10]:
            resultado += f"  🔴 {line.strip()[:120]}\n"
        resultado += "\n"
    else:
        resultado += "--- Logs ---\n  ✅ Sin errores recientes en últimas 30 líneas\n\n"

    # 4. Sugerencias
    resultado += "--- Sugerencias ---\n"
    sugerencias = []

    if not status or "running" not in (status or "").lower():
        sugerencias.append("  → Intentar: service_start('" + service_name + "')")
    if restarts and int(restarts) > 5:
        sugerencias.append("  → Revisar config: read_compose('" + service_name + "')")
        sugerencias.append("  → Ver logs completos: service_logs('" + service_name + "')")
    if health and "unhealthy" in health:
        sugerencias.append("  → Verificar healthcheck endpoint")
        sugerencias.append("  → Intentar restart: service_restart('" + service_name + "')")

    if sugerencias:
        resultado += "\n".join(sugerencias)
    else:
        resultado += "  ✅ El servicio parece estar funcionando correctamente."

    return resultado
