"""
docker.py — Comando update-all con InquirerPy + Rich progress.
"""

from __future__ import annotations

from typing import List

import typer
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn

from docker.svc_py.core.discovery import svc_compose_file, svc_list
from docker.svc_py.core.docker import compose_output, compose_run, is_service_running
from docker.svc_py.ui import console, error, success, warn

app = typer.Typer()


@app.command("update-all")
def update_all(
    yes: bool = typer.Option(False, "-y", "--yes", help="Skip confirmación"),
):
    """Actualizar todos los servicios (con multi-select si InquirerPy disponible)."""
    services = svc_list()
    if not services:
        error("No se encontraron servicios.")
        raise typer.Exit(1)

    # Intentar usar InquirerPy para multi-select
    selected = services
    if not yes:
        try:
            from InquirerPy import inquirer

            choices = []
            for svc in services:
                cf = svc_compose_file(svc)
                running = is_service_running(cf) if cf else False
                label = f"{'●' if running else '○'} {svc}"
                choices.append({"name": label, "value": svc, "enabled": True})

            selected = inquirer.checkbox(
                message="Selecciona servicios a actualizar:",
                choices=choices,
                instruction="(Space=toggle, Enter=confirmar, Ctrl+A=todos)",
            ).execute()

            if not selected:
                console.print("  [dim]Cancelado.[/dim]")
                raise typer.Exit(0)

        except ImportError:
            # Sin InquirerPy: confirmar con typer
            console.print(f"\n  Actualizar {len(services)} servicios:")
            for svc in services:
                cf = svc_compose_file(svc)
                dot = "[green]●[/green]" if (cf and is_service_running(cf)) else "[red]○[/red]"
                console.print(f"    {dot} {svc}")
            console.print()
            if not typer.confirm("  ¿Continuar?", default=False):
                console.print("  [dim]Cancelado.[/dim]")
                raise typer.Exit(0)

    # Ejecutar updates con progress bar
    console.print()
    ok = 0
    fail = 0

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("{task.completed}/{task.total}"),
        console=console,
    ) as progress:
        task = progress.add_task("Actualizando...", total=len(selected))

        for svc in selected:
            progress.update(task, description=f"[cyan]{svc}[/cyan]")
            cf = svc_compose_file(svc)

            if cf is None:
                warn(f"{svc}: compose file no encontrado")
                fail += 1
                progress.advance(task)
                continue

            # Pull
            result = compose_run(cf, ["pull"], capture=True, check=False)
            if result.returncode != 0:
                error(f"{svc}: error en pull")
                fail += 1
                progress.advance(task)
                continue

            # Recrear solo si estaba corriendo
            if is_service_running(cf):
                compose_run(cf, ["up", "-d", "--remove-orphans"], capture=True, check=False)

            ok += 1
            progress.advance(task)

    console.print()
    success(f"{ok} actualizados")
    if fail > 0:
        error(f"{fail} con error")
    console.print()
