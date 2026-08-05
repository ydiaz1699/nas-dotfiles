"""
info.py — Comandos informativos: port-map, size, net, depends, env, open.
"""

from __future__ import annotations

import re
import subprocess
import webbrowser
from pathlib import Path

import typer
from rich.syntax import Syntax
from rich.tree import Tree

from docker.svc_py.config import DOCKER_BASE
from docker.svc_py.core.discovery import svc_compose_file, svc_list
from docker.svc_py.core.docker import compose_output, compose_passthrough, docker_run
from docker.svc_py.ui import console, error, info, service_table, success, warn

app = typer.Typer()


@app.command("port-map")
def port_map():
    """Mapa global de puertos (detecta conflictos)."""
    table = service_table(
        ["Puerto", ("Servicio", {"min_width": 18}), "Contenedor", "Proto"],
        title="Port Map",
    )

    all_ports = []

    for svc in svc_list():
        cf = svc_compose_file(svc)
        if cf is None:
            continue
        out, rc = compose_output(cf, ["ps", "--format", "{{.Names}}\t{{.Ports}}"])
        if rc != 0 or not out:
            continue
        for line in out.splitlines():
            parts = line.split("\t", 1)
            if len(parts) < 2:
                continue
            name, ports_str = parts
            for m in re.finditer(r"0\.0\.0\.0:(\d+)->(\d+)/(\w+)", ports_str):
                ext_port, _, proto = m.group(1), m.group(2), m.group(3)
                table.add_row(ext_port, svc, name, proto)
                all_ports.append(ext_port)

    console.print()
    console.print(table)

    # Detectar conflictos
    seen = {}
    for p in all_ports:
        seen[p] = seen.get(p, 0) + 1
    dupes = [p for p, c in seen.items() if c > 1]
    if dupes:
        console.print(f"\n  [bold red]CONFLICTOS:[/bold red] puertos {', '.join(dupes)}\n")
    else:
        console.print()


@app.command("size")
def size():
    """Consumo de disco por servicio."""
    table = service_table(
        [("Servicio", {"min_width": 18}), "Imagenes", "Dir"],
        title="Disk Usage",
    )

    for svc in svc_list():
        cf = svc_compose_file(svc)
        if cf is None:
            continue

        svc_dir = cf.parent
        try:
            dir_size = subprocess.run(
                ["du", "-sh", str(svc_dir)],
                capture_output=True, text=True, check=False,
            ).stdout.split("\t")[0]
        except Exception:
            dir_size = "?"

        img_out, _ = compose_output(cf, ["images", "-q"])
        img_size = "--"
        if img_out:
            img_ids = img_out.splitlines()[:1]
            if img_ids:
                r = docker_run(["images", "--format", "{{.Size}}"] + img_ids)
                if r.returncode == 0 and r.stdout.strip():
                    img_size = r.stdout.strip().splitlines()[0]

        table.add_row(svc, img_size, dir_size)

    console.print()
    console.print(table)
    console.print("  [dim]Tip: 'docker system df' para espacio total[/dim]\n")


@app.command("net")
def net():
    """Mapa de redes Docker (árbol visual)."""
    result = docker_run(["network", "ls", "--format", "{{.Name}}"])
    if result.returncode != 0:
        error("No se pudo listar redes Docker")
        raise typer.Exit(1)

    networks = [n for n in result.stdout.strip().splitlines()
                if n not in ("bridge", "host", "none")]

    tree = Tree("[bold cyan]Redes Docker[/bold cyan]")

    for net_name in sorted(networks):
        branch = tree.add(f"[blue]{net_name}[/blue]")
        inspect_r = docker_run([
            "network", "inspect", net_name,
            "--format", "{{range .Containers}}{{.Name}} {{end}}",
        ])
        if inspect_r.returncode == 0 and inspect_r.stdout.strip():
            for container in inspect_r.stdout.strip().split():
                branch.add(f"[dim]{container}[/dim]")
        else:
            branch.add("[dim](sin contenedores)[/dim]")

    console.print()
    console.print(tree)
    console.print()


@app.command("depends")
def depends(service: str):
    """Ver servicios y depends_on."""
    cf = svc_compose_file(service)
    if cf is None:
        error(f"Servicio '{service}' no encontrado")
        raise typer.Exit(1)

    # Servicios definidos
    out, _ = compose_output(cf, ["config", "--services"])
    tree = Tree(f"[bold cyan]{service}[/bold cyan]")

    if out:
        svc_branch = tree.add("[blue]Servicios[/blue]")
        for s in out.splitlines():
            svc_branch.add(s.strip())

    # depends_on del compose file
    content = cf.read_text(encoding="utf-8")
    if "depends_on" in content:
        dep_branch = tree.add("[yellow]depends_on[/yellow]")
        in_depends = False
        for line in content.splitlines():
            stripped = line.strip()
            if "depends_on:" in stripped:
                in_depends = True
                continue
            if in_depends:
                if stripped.startswith("-"):
                    dep_branch.add(stripped.lstrip("- ").strip())
                elif stripped and not stripped.startswith("#") and ":" not in stripped:
                    dep_branch.add(stripped.rstrip(":"))
                elif not stripped.startswith(" ") and not stripped.startswith("-"):
                    break
    else:
        tree.add("[dim](sin dependencias)[/dim]")

    console.print()
    console.print(tree)
    console.print()


@app.command("env")
def env_cmd(service: str, edit: bool = typer.Option(False, "--edit", "-e", help="Editar .env")):
    """Ver/editar variables de entorno."""
    cf = svc_compose_file(service)
    if cf is None:
        error(f"Servicio '{service}' no encontrado")
        raise typer.Exit(1)

    env_file = cf.parent / ".env"

    if edit:
        import os
        editor = os.environ.get("EDITOR", "nano")
        if not env_file.exists():
            env_file.touch()
        subprocess.run([editor, str(env_file)], check=False)
        return

    console.print(f"\n  [blue]Variables de '{service}'[/blue]\n")

    if env_file.exists():
        content = env_file.read_text(encoding="utf-8")
        filtered = "\n".join(
            l for l in content.splitlines()
            if l.strip() and not l.strip().startswith("#")
        )
        if filtered:
            console.print("  [dim].env:[/dim]")
            syntax = Syntax(filtered, "ini", theme="monokai", padding=1)
            console.print(syntax)
        else:
            console.print("  [dim].env: (vacío)[/dim]")
    else:
        console.print("  [dim](sin archivo .env)[/dim]")

    console.print(f"\n  [dim]Para editar: svc env {service} --edit[/dim]\n")


@app.command("open")
def open_cmd(service: str):
    """Mostrar URL del servicio + intentar abrir browser."""
    cf = svc_compose_file(service)
    if cf is None:
        error(f"Servicio '{service}' no encontrado")
        raise typer.Exit(1)

    # Detectar puerto
    port = None
    out, _ = compose_output(cf, ["ps", "--format", "{{.Ports}}"])
    if out:
        m = re.search(r"0\.0\.0\.0:(\d+)", out)
        if m:
            port = m.group(1)

    # Fallback: leer del compose file
    if not port:
        content = cf.read_text(encoding="utf-8")
        m = re.search(r'"?(\d+):\d+"?', content)
        if m:
            port = m.group(1)

    if not port:
        warn(f"No se detectó puerto expuesto en '{service}'")
        raise typer.Exit(1)

    # Detectar IP
    try:
        host_ip = subprocess.run(
            ["hostname", "-I"], capture_output=True, text=True, check=False
        ).stdout.strip().split()[0]
    except Exception:
        host_ip = "localhost"

    url = f"http://{host_ip}:{port}"
    console.print(f"\n  [cyan]{service}[/cyan] → [bold]{url}[/bold]")

    # Intentar copiar al clipboard
    for cmd in [["xclip", "-selection", "clipboard"], ["xsel", "--clipboard"]]:
        try:
            subprocess.run(cmd, input=url.encode(), check=True,
                          capture_output=True)
            console.print("  [dim](copiado al clipboard)[/dim]")
            break
        except (FileNotFoundError, subprocess.CalledProcessError):
            continue

    # QR si está disponible
    try:
        qr = subprocess.run(
            ["qrencode", "-t", "UTF8", url],
            capture_output=True, text=True, check=True,
        )
        console.print()
        for line in qr.stdout.splitlines():
            console.print(f"  {line}")
    except (FileNotFoundError, subprocess.CalledProcessError):
        pass

    console.print()
