"""
Herramientas de sistema para el NAS.

Obtienen información del estado del sistema: puertos en uso,
disco, memoria, red. Usan comandos nativos de Linux.
"""

import subprocess
from strands.tools import tool


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


@tool
def scan_ports() -> str:
    """Escanea los puertos TCP y UDP actualmente en uso en el NAS.

    Retorna los puertos ocupados separados por protocolo (TCP/UDP).
    Útil antes de asignar un puerto a un nuevo servicio para evitar conflictos.

    No requiere argumentos.
    """
    tcp = _run("ss -tnlp 2>/dev/null | grep -oP ':\\K[0-9]+(?=\\s)' | sort -n | uniq")
    udp = _run("ss -unlp 2>/dev/null | grep -oP ':\\K[0-9]+(?=\\s)' | sort -n | uniq")

    tcp_list = [int(p) for p in tcp.split("\n") if p.strip().isdigit()]
    udp_list = [int(p) for p in udp.split("\n") if p.strip().isdigit()]

    # Encontrar puertos libres en el rango 8100-8999
    ocupados_tcp = set(tcp_list)
    libres = []
    for p in range(8100, 9000):
        if p not in ocupados_tcp:
            libres.append(p)
            if len(libres) >= 10:
                break

    return (
        f"=== PUERTOS EN USO ===\n\n"
        f"TCP ({len(tcp_list)}): {', '.join(str(p) for p in tcp_list)}\n\n"
        f"UDP ({len(udp_list)}): {', '.join(str(p) for p in udp_list)}\n\n"
        f"--- Próximos 10 puertos libres (rango 8100-8999) ---\n"
        f"{', '.join(str(p) for p in libres)}\n\n"
        f"Usa estos puertos para servicios nuevos."
    )


@tool
def disk_usage() -> str:
    """Muestra el uso de disco de todas las particiones montadas.

    Excluye filesystems temporales (tmpfs, udev, loop, overlay).
    Alerta si alguna partición supera 75% o 90% de uso.

    No requiere argumentos.
    """
    output = _run(
        "df -h --output=target,used,size,pcent 2>/dev/null "
        "| grep -v 'tmpfs\\|udev\\|/dev/loop\\|Filesystem\\|overlay'"
    )

    if not output:
        return "ERROR: No se pudo obtener información de disco"

    lineas = output.strip().splitlines()
    alertas = []

    for linea in lineas:
        partes = linea.split()
        if len(partes) >= 4:
            pct_str = partes[-1].replace("%", "")
            try:
                pct = int(pct_str)
                mount = partes[0]
                if pct >= 90:
                    alertas.append(f"  🔴 CRÍTICO: {mount} al {pct}%")
                elif pct >= 75:
                    alertas.append(f"  🟡 ATENCIÓN: {mount} al {pct}%")
            except ValueError:
                pass

    alertas_str = "\n".join(alertas) if alertas else "  ✅ Todo dentro de rango normal"

    return (
        f"=== USO DE DISCO ===\n\n"
        f"{output}\n\n"
        f"--- Alertas ---\n{alertas_str}"
    )


@tool
def memory_info() -> str:
    """Muestra el uso de memoria RAM y swap del NAS.

    Incluye total, usado, libre, caches y porcentaje de uso.
    Alerta si la memoria supera 80%.

    No requiere argumentos.
    """
    free_output = _run("free -h")
    if not free_output:
        return "ERROR: No se pudo obtener información de memoria"

    # Obtener porcentaje de uso
    mem_pct = _run(
        "free | awk '/^Mem:/{printf \"%.0f\", $3/$2*100}'"
    )
    swap_pct = _run(
        "free | awk '/^Swap:/{if($2>0) printf \"%.0f\", $3/$2*100; else print \"0\"}'"
    )

    # Alerta
    alerta = ""
    try:
        pct = int(mem_pct)
        if pct >= 90:
            alerta = "🔴 CRÍTICO: Memoria al " + mem_pct + "%"
        elif pct >= 80:
            alerta = "🟡 ATENCIÓN: Memoria al " + mem_pct + "%"
        else:
            alerta = "✅ Memoria al " + mem_pct + "% (normal)"
    except ValueError:
        alerta = "⚠️ No se pudo calcular porcentaje"

    # Procesos que más consumen
    top_mem = _run(
        "ps aux --sort=-%mem | head -6 | "
        "awk '{printf \"  %-8s %5s%% %s\\n\", $1, $4, $11}'"
    )

    return (
        f"=== MEMORIA ===\n\n"
        f"{free_output}\n\n"
        f"Uso RAM: {mem_pct}% | Swap: {swap_pct}%\n"
        f"{alerta}\n\n"
        f"--- Top 5 procesos por memoria ---\n{top_mem}"
    )


@tool
def network_info() -> str:
    """Muestra información de red: interfaces, IPs y puertos en escucha.

    Incluye interfaces activas con su IP, y los puertos TCP en modo LISTEN
    con el proceso asociado.

    No requiere argumentos.
    """
    # Interfaces
    interfaces = _run(
        "ip -4 addr show 2>/dev/null | "
        "awk '/^[0-9]+:/{iface=$2} /inet /{printf \"  %-15s %s\\n\", iface, $2}' | "
        "grep -v '^\\s*lo'"
    )

    # IP principal
    ip_principal = _run("hostname -I 2>/dev/null | awk '{print $1}'")

    # Redes Docker
    docker_nets = _run(
        "docker network ls --format '{{.Name}}' 2>/dev/null | "
        "grep -v '^bridge$\\|^host$\\|^none$'"
    )

    # Contenedores por red
    nets_detail = ""
    if docker_nets:
        nets_list = docker_nets.strip().splitlines()
        parts = []
        for net in nets_list[:10]:
            containers = _run(
                f"docker network inspect {net} "
                f"--format '{{{{range .Containers}}}}{{{{.Name}}}} {{{{end}}}}' 2>/dev/null"
            )
            if containers.strip():
                parts.append(f"  {net}: {containers.strip()}")
            else:
                parts.append(f"  {net}: (vacía)")
        nets_detail = "\n".join(parts)

    return (
        f"=== RED DEL NAS ===\n\n"
        f"IP principal: {ip_principal}\n\n"
        f"Interfaces:\n{interfaces}\n\n"
        f"--- Redes Docker ---\n"
        f"{nets_detail or '  (ninguna red custom)'}\n\n"
        f"Usa scan_ports() para ver puertos en detalle."
    )
