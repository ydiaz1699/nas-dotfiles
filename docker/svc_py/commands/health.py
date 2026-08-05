"""
health.py — Comandos de salud: health, doctor, watch.
"""

from __future__ import annotations

import subprocess
import time
from datetime import datetime

import typer
from rich import box
from rich.live import Live
from rich.panel import Panel
from rich.table import Table

from docker.svc_py.config import DOCKER_BASE, WATCH_INTERVAL
from docker.svc_py.core.discovery import svc_compose_file, svc_list
from docker.svc_py.core.docker import (
    compose_output,
    container_inspect,
    docker_run,
    get_container_ids,
    is_service_running,
)
from docker.svc_py.ui import (
    console,
    error,
    health_colored,
    restart_colored,
    service_table,
    status_dot,
    success,
    warn,
)

app = typer.Typer()


def _uptime_str(container_id: str) -> str:
    """Calcula uptime legible de un contenedor."""
    started_at = container_inspect(container_id, "{{.State.StartedAt}}")
    if not started_at or started_at.startswith("0001"):
        return "--"
    try:
        # Parsear ISO format (truncar nanosegundos)
        clean = started_at.split(".")[0].replace("T", " ").replace("Z", "")
        start = datetime.strptime(clean, "%Y-%m-%d %H:%M:%S")
        diff = datetime.now() - start
        seconds = int(diff.total_seconds())
        if seconds < 3600:
            return f"{seconds // 60}m"
        elif seconds < 86400:
            return f"{seconds // 3600}h"
        else:
            return f"{seconds // 86400}d"
    except (ValueError, TypeError):
        return "--"


def _build_health_table() -> Table:
    """Construye la tabla de health para todos los servicios."""
    table = service_table(
        [
            ("", {"width": 2}),
            ("Servicio", {"min_width": 18}),
            "Estado",
            "Health",
            "Uptime",
            "Restarts",
        ],
        title="Docker Health",
    )

    for svc in svc_list():
        cf = svc_compose_file(svc)
        if cf is None:
            continue

        if is_service_running(cf):
            containers = get_container_ids(cf)
            total_out, _ = compose_output(cf, ["ps", "-a", "-q"])
            total = len(total_out.splitlines()) if total_out else 0
            running = len(containers)

            cid = containers[0] if containers else ""

            # Health
            hs = container_inspect(cid, "{{if .State.Health}}{{.State.Health.Status}}{{else}}--{{end}}")
            if not hs:
                hs = "--"

            # Uptime
            uptime = _uptime_str(cid)

            # Restarts
            rc_str = container_inspect(cid, "{{.RestartCount}}")
            rc = int(rc_str) if rc_str.isdigit() else 0

            table.add_row(
                status_dot(True),
                svc,
                f"[green]{running}/{total}[/green]",
                health_colored(hs),
                uptime,
                restart_colored(rc),
            )
        else:
            table.add_row(
                status_dot(False),
                svc,
                "[red]detenido[/red]",
                "",
                "",
                "",
            )

    return table


@app.command()
def health():
    """Dashboard de salud: health, uptime, restarts de todos los servicios."""
    console.print()
    table = _build_health_table()
    console.print(table)
    console.print()


@app.command()
def doctor():
    """Chequeo general del NAS (disco, memoria, servicios, puertos, restarts, storage)."""
    console.print()
    console.print(Panel(
        "[bold]svc doctor[/bold] — Chequeo general del NAS",
        border_style="cyan",
        width=70,
    ))
    console.print()

    issues = 0
    warnings = 0

    # 1. Disco
    console.print("  [blue][1/6] Disco[/blue]")
    try:
        df_out = subprocess.run(
            ["df", "-h", "--type=ext4", "--type=btrfs", "--type=xfs"],
            capture_output=True, text=True, check=False,
        ).stdout
        for line in df_out.strip().splitlines()[1:]:
            parts = line.split()
            if len(parts) >= 5:
                pct_str = parts[4].rstrip("%")
                if pct_str.isdigit():
                    pct = int(pct_str)
                    mount = parts[5] if len(parts) > 5 else "?"
                    if pct >= 90:
                        error(f"CRITICO: {mount} al {pct}%")
                        issues += 1
                    elif pct >= 75:
                        warn(f"ATENCION: {mount} al {pct}%")
                        warnings += 1
    except Exception:
        pass
    if issues == 0 and warnings == 0:
        success("Disco OK")
    console.print()

    # 2. Memoria
    console.print("  [blue][2/6] Memoria[/blue]")
    try:
        free_out = subprocess.run(
            ["free"], capture_output=True, text=True, check=False
        ).stdout
        for line in free_out.splitlines():
            if line.startswith("Mem:"):
                parts = line.split()
                total = int(parts[1])
                used = int(parts[2])
                pct = int(used / total * 100) if total > 0 else 0
                if pct >= 90:
                    error(f"CRITICO: Memoria al {pct}%")
                    issues += 1
                elif pct >= 80:
                    warn(f"Memoria al {pct}%")
                    warnings += 1
                else:
                    success(f"Memoria al {pct}% (OK)")
                break
    except Exception:
        success("Memoria: no se pudo verificar")
    console.print()

    # 3. Servicios Docker
    console.print("  [blue][3/6] Servicios Docker[/blue]")
    services = svc_list()
    down_count = 0
    for svc in services:
        cf = svc_compose_file(svc)
        if cf and not is_service_running(cf):
            error(f"{svc}: DETENIDO")
            down_count += 1
            issues += 1

    # Contenedores reiniciando
    restarting = docker_run(["ps", "--filter", "status=restarting", "--format", "{{.Names}}"])
    if restarting.returncode == 0 and restarting.stdout.strip():
        for name in restarting.stdout.strip().splitlines():
            warn(f"{name}: REINICIANDO (crash loop?)")
            warnings += 1

    if down_count == 0 and (restarting.returncode != 0 or not restarting.stdout.strip()):
        success(f"{len(services)} servicios, todos activos")
    console.print()

    # 4. Puertos reservados
    console.print("  [blue][4/6] Puertos reservados[/blue]")
    reserved_ok = True
    try:
        ss_out = subprocess.run(
            ["ss", "-tlnp"], capture_output=True, text=True, check=False
        ).stdout
        for rp in [22, 53, 80, 443]:
            if f":{rp} " in ss_out:
                # Expected processes
                expected = {"sshd", "systemd-resolve", "traefik", "nginx", "pihole"}
                line = [l for l in ss_out.splitlines() if f":{rp} " in l]
                proc = ""
                if line:
                    import re
                    m = re.search(r'users:\(\("([^"]+)"', line[0])
                    if m:
                        proc = m.group(1)
                if proc and proc not in expected:
                    warn(f"Puerto {rp} usado por: {proc}")
                    warnings += 1
                    reserved_ok = False
    except Exception:
        pass
    if reserved_ok:
        success("Puertos reservados libres/esperados")
    console.print()

    # 5. Restart count alto
    console.print("  [blue][5/6] Restart count[/blue]")
    high_restarts = 0
    ps_result = docker_run(["ps", "-q"])
    if ps_result.returncode == 0 and ps_result.stdout.strip():
        for cid in ps_result.stdout.strip().splitlines():
            rc_str = container_inspect(cid, "{{.RestartCount}}")
            name = container_inspect(cid, "{{.Name}}").lstrip("/")
            if rc_str.isdigit() and int(rc_str) > 5:
                warn(f"{name}: {rc_str} restarts")
                high_restarts += 1
                warnings += 1
    if high_restarts == 0:
        success("Sin contenedores con restarts excesivos")
    console.print()

    # 6. Docker storage
    console.print("  [blue][6/6] Docker storage[/blue]")
    df_docker = subprocess.run(
        ["docker", "system", "df"], capture_output=True, text=True, check=False
    )
    if df_docker.returncode == 0:
        for line in df_docker.stdout.strip().splitlines()[1:]:
            console.print(f"    {line}")
    dangling = docker_run(["images", "-f", "dangling=true", "-q"])
    if dangling.returncode == 0 and dangling.stdout.strip():
        count = len(dangling.stdout.strip().splitlines())
        if count > 5:
            warn(f"{count} imagenes dangling (limpiar: docker image prune)")
            warnings += 1
    console.print()

    # Resumen
    console.print("  " + "=" * 60)
    if issues > 0:
        console.print(f"  [bold red]RESULTADO: {issues} error(es), {warnings} advertencia(s)[/bold red]")
    elif warnings > 0:
        console.print(f"  [bold yellow]RESULTADO: 0 errores, {warnings} advertencia(s)[/bold yellow]")
    else:
        console.print("  [bold green]RESULTADO: ✓ Todo en orden[/bold green]")
    console.print()


@app.command()
def watch(interval: int = typer.Argument(WATCH_INTERVAL, help="Segundos entre refresh")):
    """Monitoreo continuo con Rich Live (sin clear, actualiza in-place)."""
    console.print(f"\n  [cyan]svc watch[/cyan] (Ctrl+C para salir, refresh: {interval}s)\n")

    try:
        with Live(console=console, refresh_per_second=1) as live:
            while True:
                # Construir tabla con stats
                table = Table(
                    box=box.ROUNDED,
                    title=f"svc watch — {datetime.now().strftime('%H:%M:%S')}",
                    title_style="bold cyan",
                    show_header=True,
                    header_style="bold",
                )
                table.add_column("", width=2)
                table.add_column("Servicio", min_width=18)
                table.add_column("Estado")
                table.add_column("CPU")
                table.add_column("MEM")
                table.add_column("Uptime")

                for svc in svc_list():
                    cf = svc_compose_file(svc)
                    if cf is None:
                        continue

                    containers = get_container_ids(cf)
                    if not containers:
                        table.add_row(
                            status_dot(False), svc, "[red]detenido[/red]",
                            "", "", "",
                        )
                        continue

                    cid = containers[0]

                    # Stats (single read)
                    stats_result = docker_run([
                        "stats", "--no-stream", "--format",
                        "{{.CPUPerc}}\t{{.MemUsage}}", cid,
                    ])
                    cpu = mem = "N/A"
                    if stats_result.returncode == 0 and stats_result.stdout.strip():
                        parts = stats_result.stdout.strip().split("\t")
                        if len(parts) >= 2:
                            cpu, mem = parts[0], parts[1]

                    uptime = _uptime_str(cid)

                    table.add_row(
                        status_dot(True), svc, "[green]activo[/green]",
                        cpu, mem, uptime,
                    )

                live.update(table)
                time.sleep(interval)
    except KeyboardInterrupt:
        console.print("\n  [dim]Watch detenido.[/dim]\n")
