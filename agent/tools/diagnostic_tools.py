"""
Herramientas de diagnóstico para el NAS.

Permiten al agente detectar problemas: servicios caídos,
conflictos de puertos, contenedores con muchos restarts,
uso excesivo de recursos, etc.
"""

import yaml
from pathlib import Path
from strands.tools import tool

from agent.tools._shell import (
    DOCKER_BASE,
    safe_run,
    find_compose,
    service_exists_or_error,
    validate_service_name,
    InvalidServiceName,
)



@tool
def service_health() -> str:
    """Dashboard de salud de todos los servicios Docker.

    Para cada servicio muestra: estado, healthcheck, uptime,
    restart count y alertas. Equivalente a 'svc health'.

    No requiere argumentos.
    """
    # Intentar usar el CLI primero
    output = safe_run(["svc", "health"], timeout=60)

    if output and "ERROR" not in output:
        return f"=== SALUD DE SERVICIOS ===\n\n{output}"

    # Fallback si el CLI no está disponible
    containers = safe_run(
        ["docker", "ps", "-a", "--format", "{{.Names}}\t{{.Status}}\t{{.State}}"],
        timeout=15,
    )

    if not containers or "ERROR" in containers:
        return "No hay contenedores Docker corriendo"

    lines = containers.strip().splitlines()
    activos = sum(1 for l in lines if "running" in l.lower())
    total = len(lines)

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
    puertos = {}  # puerto → [servicio, ...]

    for d in sorted(DOCKER_BASE.iterdir()):
        if not d.is_dir() or d.name.startswith(".") or d.name in ("cli", "backups"):
            continue
        try:
            validate_service_name(d.name)
        except InvalidServiceName:
            continue
        compose = find_compose(d.name)
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

    conflictos = {p: svcs for p, svcs in puertos.items() if len(svcs) > 1}

    resultado = "=== ANÁLISIS DE PUERTOS ===\n\n"
    resultado += f"Servicios escaneados: {sum(1 for d in DOCKER_BASE.iterdir() if d.is_dir())}\n"
    resultado += f"Puertos asignados: {len(puertos)}\n\n"

    if conflictos:
        resultado += "🔴 CONFLICTOS DETECTADOS:\n"
        for port, svcs in sorted(conflictos.items()):
            resultado += f"  Puerto {port}: {', '.join(svcs)}\n"
        resultado += "\n"
    else:
        resultado += "✅ Sin conflictos de puertos.\n\n"

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
    error = service_exists_or_error(service_name)
    if error:
        return error

    compose = find_compose(service_name)
    resultado = f"=== DIAGNÓSTICO: {service_name} ===\n\n"

    # 1. Estado
    status = safe_run(
        ["docker", "compose", "-f", str(compose), "ps",
         "--format", "{{.Name}}\t{{.Status}}\t{{.State}}"],
        timeout=15,
    )
    resultado += f"--- Estado ---\n{status or '(no hay contenedores)'}\n\n"

    # 2. Container ID + health + restarts
    container_id = safe_run(
        ["docker", "compose", "-f", str(compose), "ps", "-q"],
        timeout=10,
    )
    first_container = container_id.strip().splitlines()[0] if container_id.strip() else ""

    restarts = "0"
    if first_container:
        health = safe_run(
            ["docker", "inspect", "--format",
             "{{if .State.Health}}{{.State.Health.Status}}{{else}}sin-healthcheck{{end}}",
             first_container],
            timeout=10,
        )
        resultado += f"--- Healthcheck ---\n  {health}\n\n"

        restarts = safe_run(
            ["docker", "inspect", "--format", "{{.RestartCount}}", first_container],
            timeout=10,
        )
        resultado += f"--- Restarts ---\n  {restarts} veces\n"
        try:
            if int(restarts) > 5:
                resultado += "  ⚠️ Muchos restarts — posible crash loop\n"
        except (ValueError, TypeError):
            pass
        resultado += "\n"

        # Recursos
        stats = safe_run(
            ["docker", "stats", "--no-stream", "--format",
             "CPU: {{.CPUPerc}}  MEM: {{.MemUsage}}  NET: {{.NetIO}}",
             first_container],
            timeout=10,
        )
        resultado += f"--- Recursos ---\n  {stats}\n\n"

    # 3. Logs recientes
    logs = safe_run(
        ["docker", "compose", "-f", str(compose), "logs", "--tail=30", "--no-color"],
        timeout=15,
    )
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
        sugerencias.append(f"  → Intentar: service_start('{service_name}')")
    try:
        if int(restarts) > 5:
            sugerencias.append(f"  → Revisar config: read_compose('{service_name}')")
            sugerencias.append(f"  → Ver logs completos: service_logs('{service_name}')")
    except (ValueError, TypeError):
        pass

    if sugerencias:
        resultado += "\n".join(sugerencias)
    else:
        resultado += "  ✅ El servicio parece estar funcionando correctamente."

    return resultado
