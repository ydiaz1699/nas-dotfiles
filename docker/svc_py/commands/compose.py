"""
compose.py — Comandos de compose: create (wizard) y diff.
"""

from __future__ import annotations

import subprocess
from datetime import date
from pathlib import Path

import typer
from rich.syntax import Syntax

from docker.svc_py.config import DOCKER_BASE
from docker.svc_py.core.discovery import svc_compose_file
from docker.svc_py.core.docker import compose_output
from docker.svc_py.ui import console, error, info, success, warn

app = typer.Typer()



@app.command("create")
def create(name: str = typer.Argument(None, help="Nombre del servicio")):
    """Scaffolding de nuevo servicio (wizard interactivo)."""
    # Intentar wizard con InquirerPy
    try:
        from InquirerPy import inquirer
        has_inquirer = True
    except ImportError:
        has_inquirer = False

    if name is None and has_inquirer:
        name = inquirer.text(
            message="Nombre del servicio:",
            validate=lambda x: len(x) > 0,
        ).execute()
    elif name is None:
        name = typer.prompt("Nombre del servicio")

    svc_dir = DOCKER_BASE / name
    if svc_dir.exists():
        error(f"'{svc_dir}' ya existe")
        raise typer.Exit(1)

    # Wizard
    if has_inquirer:
        image = inquirer.text(
            message="Imagen Docker:",
            default="IMAGE:TAG",
        ).execute()
        port = inquirer.text(
            message="Puerto externo:",
            default="8100",
        ).execute()
    else:
        image = typer.prompt("Imagen Docker", default="IMAGE:TAG")
        port = typer.prompt("Puerto externo", default="8100")

    # Crear estructura
    svc_dir.mkdir(parents=True)
    (svc_dir / "data").mkdir()

    # docker-compose.yml
    compose_content = f"""services:
  app:
    image: {image}
    container_name: {name}
    restart: unless-stopped
    ports:
      - "{port}:{port}"
    volumes:
      - ./data:/data
    env_file:
      - .env
    # healthcheck:
    #   test: ["CMD", "curl", "-f", "http://localhost:{port}/health"]
    #   interval: 30s
    #   timeout: 10s
    #   retries: 3
"""
    (svc_dir / "docker-compose.yml").write_text(compose_content)

    # .env
    env_content = f"# Variables de entorno para {name}\n# TZ=America/New_York\n"
    (svc_dir / ".env").write_text(env_content)

    # README
    readme = f"""# {name}

## Descripcion

(Describir el servicio aqui)

## Puertos

- {port}: (descripcion)

## Volumenes

- `./data` -> datos persistentes

## Notas

- Creado: {date.today().isoformat()}
"""
    (svc_dir / "README.md").write_text(readme)

    console.print(f"\n  [green]✓[/green] Servicio '{name}' creado:")
    console.print(f"    {svc_dir}/")
    console.print(f"    ├── docker-compose.yml")
    console.print(f"    ├── .env")
    console.print(f"    ├── README.md")
    console.print(f"    └── data/")
    console.print(f"\n  [dim]Editar: nano {svc_dir}/docker-compose.yml[/dim]\n")



@app.command("diff")
def diff(service: str):
    """Comparar compose en disco vs configuración resuelta."""
    cf = svc_compose_file(service)
    if cf is None:
        error(f"Servicio '{service}' no encontrado")
        raise typer.Exit(1)

    console.print(f"\n  [blue]svc diff: {service}[/blue]")
    console.print(f"  Archivo: {cf}\n")

    # Config resuelta
    resolved, rc = compose_output(cf, ["config"])
    if rc != 0:
        error(f"Error resolviendo config: {resolved}")
        raise typer.Exit(1)

    disk_content = cf.read_text(encoding="utf-8")

    # Diff
    import difflib
    diff_lines = list(difflib.unified_diff(
        disk_content.splitlines(keepends=True),
        resolved.splitlines(keepends=True),
        fromfile="disco",
        tofile="resuelto",
        lineterm="",
    ))

    if not diff_lines:
        success("Sin diferencias — compose y config resuelto son idénticos")
    else:
        warn("Diferencias encontradas (izq=disco, der=resuelto):")
        console.print()
        diff_text = "\n".join(diff_lines)
        syntax = Syntax(diff_text, "diff", theme="monokai", padding=1)
        console.print(syntax)

    # Variables sin resolver
    import re
    unresolved = set(re.findall(r'\$\{[^}]+\}', disk_content))
    if unresolved:
        console.print(f"\n  [blue]Variables referenciadas:[/blue]")
        env_file = cf.parent / ".env"
        env_content = env_file.read_text() if env_file.exists() else ""
        for var in sorted(unresolved):
            varname = var.strip("${}").split(":")[0].split("-")[0]
            if f"{varname}=" in env_content:
                console.print(f"    [green]✓[/green] {varname} (definida)")
            else:
                console.print(f"    [yellow]⚠[/yellow] {varname} (NO en .env)")

    console.print()
