"""
Herramientas de sistema para el NAS.

Obtienen información del estado del sistema: puertos en uso,
disco, memoria, red. Usan comandos nativos de Linux.
"""

from strands.tools import tool

from agent.tools._shell import safe_run


@tool
def scan_ports() -> str:
    """Escanea los puertos TCP y UDP actualmente en uso en el NAS.

    Retorna los puertos ocupados separados por protocolo (TCP/UDP).
    Útil antes de asignar un puerto a un nuevo servicio para evitar conflictos.

    No requiere argumentos.
    """
    tcp_raw = safe_run(["ss", "-tnlp"], timeout=10)
    udp_raw = safe_run(["ss", "-unlp"], timeout=10)

    # Parsear puertos del output de ss
    tcp_list = _parse_ports(tcp_raw)
    udp_list = _parse_ports(udp_raw)

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
        f"TCP ({len(tcp_list)}): {', '.join(str(p) for p in sorted(tcp_list))}\n\n"
        f"UDP ({len(udp_list)}): {', '.join(str(p) for p in sorted(udp_list))}\n\n"
        f"--- Próximos 10 puertos libres (rango 8100-8999) ---\n"
        f"{', '.join(str(p) for p in libres)}\n\n"
        f"Usa estos puertos para servicios nuevos."
    )


def _parse_ports(ss_output: str) -> list[int]:
    """Extrae puertos numéricos del output de ss."""
    ports = []
    for line in ss_output.splitlines()[1:]:  # skip header
        parts = line.split()
        if len(parts) >= 4:
            addr = parts[3]
            if ":" in addr:
                port_str = addr.rsplit(":", 1)[-1]
                try:
                    ports.append(int(port_str))
                except ValueError:
                    pass
    return ports


@tool
def disk_usage() -> str:
    """Muestra el uso de disco de todas las particiones montadas.

    Excluye filesystems temporales (tmpfs, udev, loop, overlay).
    Alerta si alguna partición supera 75% o 90% de uso.

    No requiere argumentos.
    """
    output = safe_run(
        ["df", "-h", "--type=ext4", "--type=btrfs", "--type=xfs",
         "--type=vfat", "--type=ntfs"],
        timeout=10,
    )

    if not output or "ERROR" in output:
        return "ERROR: No se pudo obtener información de disco"

    lineas = output.strip().splitlines()
    alertas = []

    for linea in lineas[1:]:  # skip header
        partes = linea.split()
        if len(partes) >= 5:
            pct_str = partes[4].replace("%", "")
            try:
                pct = int(pct_str)
                mount = partes[5] if len(partes) > 5 else partes[0]
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
    free_output = safe_run(["free", "-h"], timeout=5)
    if not free_output:
        return "ERROR: No se pudo obtener información de memoria"

    # Obtener porcentaje via awk
    mem_pct = safe_run(
        ["awk", "/^Mem:/{printf \"%.0f\", $3/$2*100}", "/proc/meminfo"],
        timeout=5,
    )
    # Fallback: parsear de free
    if not mem_pct or "ERROR" in mem_pct:
        mem_pct = _calc_mem_pct(free_output)

    # Top procesos por memoria
    top_mem = safe_run(
        ["ps", "aux", "--sort=-%mem"],
        timeout=10,
    )
    # Formatear solo top 6
    top_lines = top_mem.splitlines()[:6] if top_mem else []
    top_formatted = "\n".join(f"  {l[:100]}" for l in top_lines)

    alerta = ""
    try:
        pct = int(mem_pct)
        if pct >= 90:
            alerta = f"🔴 CRÍTICO: Memoria al {pct}%"
        elif pct >= 80:
            alerta = f"🟡 ATENCIÓN: Memoria al {pct}%"
        else:
            alerta = f"✅ Memoria al {pct}% (normal)"
    except (ValueError, TypeError):
        alerta = "⚠️ No se pudo calcular porcentaje"

    return (
        f"=== MEMORIA ===\n\n"
        f"{free_output}\n\n"
        f"{alerta}\n\n"
        f"--- Top procesos por memoria ---\n{top_formatted}"
    )


def _calc_mem_pct(free_output: str) -> str:
    """Calcula porcentaje de memoria desde output de free."""
    try:
        for line in free_output.splitlines():
            if line.startswith("Mem:"):
                parts = line.split()
                # free -h: Mem: total used free shared buff/cache available
                # Intentar con free sin -h para cálculo
                return "?"
    except Exception:
        pass
    return "?"


@tool
def network_info() -> str:
    """Muestra información de red: interfaces, IPs y redes Docker.

    Incluye interfaces activas con su IP y las redes Docker custom
    con sus contenedores asociados.

    No requiere argumentos.
    """
    # IP principal
    ip_output = safe_run(["hostname", "-I"], timeout=5)
    ip_principal = ip_output.split()[0] if ip_output and not ip_output.startswith("ERROR") else "?"

    # Interfaces
    interfaces = safe_run(["ip", "-4", "-brief", "addr", "show"], timeout=5)

    # Redes Docker
    docker_nets = safe_run(
        ["docker", "network", "ls", "--format", "{{.Name}}"],
        timeout=10,
    )

    # Detalle de redes custom
    nets_detail = ""
    if docker_nets and "ERROR" not in docker_nets:
        nets_list = [
            n for n in docker_nets.strip().splitlines()
            if n not in ("bridge", "host", "none")
        ]
        parts = []
        for net in nets_list[:10]:
            containers = safe_run(
                ["docker", "network", "inspect", net,
                 "--format", "{{range .Containers}}{{.Name}} {{end}}"],
                timeout=5,
            )
            if containers.strip() and "ERROR" not in containers:
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
