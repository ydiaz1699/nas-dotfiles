"""
catalog.py — Comando catalog-sync para el Python CLI.

Wrapper que invoca el script bash catalog-sync.sh, con output
formateado via Rich para la experiencia del Python CLI.

También expone --status como subcomando nativo que lee el catálogo
directamente sin depender del bash script.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Optional

import typer
from rich.table import Table

from svc_py.config import DOCKER_BASE, NAS_DOTFILES
from svc_py.core.discovery import svc_compose_file, svc_list
from svc_py.ui import console, error, info, success, warn

# Paths del ecosistema
CATALOG_DIR = NAS_DOTFILES / "agent" / "catalog" / "services"
DOCS_DIR = NAS_DOTFILES / "docs" / "services"
CATALOG_SYNC_SCRIPT = NAS_DOTFILES / "docker" / "cli" / "lib" / "catalog-sync.sh"
SVC_SH = NAS_DOTFILES / "docker" / "cli" / "svc.sh"


def catalog_sync(
    service: Optional[str] = typer.Argument(None, help="Servicio específico (omitir = todos)"),
    status: bool = typer.Option(False, "--status", "-s", help="Mostrar estado de documentación"),
    dry_run: bool = typer.Option(False, "--dry-run", "-n", help="Mostrar qué haría sin ejecutar"),
    regenerate: bool = typer.Option(False, "--regenerate-index", "-r", help="Regenerar catalog.json"),
):
    """Sincronizar documentación del catálogo (ficha, guía, compose, script DebMenux).

    Sin argumentos: sincroniza todos los servicios detectados en $DOCKER_BASE.
    Con servicio: sincroniza solo ese servicio.
    Con --status: muestra tabla de qué tiene/falta cada servicio.
    Con --regenerate-index: regenera catalog.json desde las fichas.
    """
    if status:
        _show_status()
        return

    if regenerate:
        _regenerate_index()
        return

    # Intentar ejecutar el bash script si existe
    if CATALOG_SYNC_SCRIPT.exists():
        _run_bash_catalog_sync(service, dry_run)
    else:
        # Fallback: implementación nativa mínima
        _native_catalog_sync(service, dry_run)


def _show_status():
    """Muestra tabla de estado de documentación por servicio (nativo Python)."""
    console.print()

    table = Table(
        title="📊 Estado de documentación de servicios",
        show_header=True,
        header_style="bold cyan",
        padding=(0, 1),
    )
    table.add_column("Servicio", style="bold", min_width=14)
    table.add_column("Compose", justify="center", width=8)
    table.add_column("Ficha", justify="center", width=8)
    table.add_column("Guía", justify="center", width=8)
    table.add_column("DebMenux", justify="center", width=8)
    table.add_column("Homepage", justify="center", width=8)

    services = svc_list()
    if not services:
        error("No se encontraron servicios en DOCKER_BASE")
        raise typer.Exit(1)

    total_complete = 0

    for svc in services:
        cf = svc_compose_file(svc)
        has_compose = "✅" if cf else "❌"

        ficha_path = CATALOG_DIR / svc / "ficha.md"
        has_ficha = "✅" if ficha_path.exists() else "❌"

        guide_path = DOCS_DIR / f"{svc}-guide.md"
        has_guide = "✅" if guide_path.exists() else "❌"

        # DebMenux script — buscar en ambas ubicaciones posibles
        debmenux_paths = [
            Path("/debmenux/scripts/services") / f"{svc}.sh",
            NAS_DOTFILES.parent / "DebMenux-" / "scripts" / "services" / f"{svc}.sh",
        ]
        has_debmenux = "❌"
        for dp in debmenux_paths:
            if dp.exists():
                has_debmenux = "✅"
                break

        # Homepage labels
        has_homepage = "❌"
        if cf and cf.exists():
            content = cf.read_text(encoding="utf-8")
            if "homepage." in content:
                has_homepage = "✅"

        # Conteo de completitud
        checks = [has_compose, has_ficha, has_guide, has_debmenux, has_homepage]
        if all(c == "✅" for c in checks):
            total_complete += 1
            svc_style = f"[green]{svc}[/green]"
        elif has_ficha == "❌" or has_guide == "❌":
            svc_style = f"[red]{svc}[/red]"
        else:
            svc_style = f"[yellow]{svc}[/yellow]"

        table.add_row(svc_style, has_compose, has_ficha, has_guide, has_debmenux, has_homepage)

    console.print(table)
    console.print()
    console.print(
        f"  [bold]{total_complete}/{len(services)}[/bold] servicios completamente documentados"
    )
    console.print(
        "  [dim]Leyenda: Compose=$dkco | Ficha=catálogo | Guía=docs/ | "
        "DebMenux=script instalador | Homepage=labels[/dim]"
    )
    console.print()

    if total_complete < len(services):
        console.print(
            "  [dim]Ejecutar[/dim] [bold]svc catalog-sync[/bold] "
            "[dim]para generar lo que falta[/dim]"
        )
        console.print()


def _regenerate_index():
    """Regenerar catalog.json invocando el módulo Python del catálogo."""
    console.print()
    info("Regenerando catalog.json...")

    index_module = NAS_DOTFILES / "agent" / "catalog" / "_index.py"
    if not index_module.exists():
        error(f"No se encontró {index_module}")
        raise typer.Exit(1)

    result = subprocess.run(
        ["python3", "-m", "agent.catalog._index"],
        cwd=str(NAS_DOTFILES),
        capture_output=True,
        text=True,
    )

    if result.returncode == 0:
        for line in result.stdout.strip().splitlines():
            console.print(f"  {line}")
        success("catalog.json regenerado")
    else:
        error("Falló la regeneración")
        if result.stderr:
            console.print(f"  [red]{result.stderr.strip()}[/red]")
        raise typer.Exit(1)

    console.print()


def _run_bash_catalog_sync(service: Optional[str], dry_run: bool):
    """Ejecuta el script bash catalog-sync via svc.sh."""
    console.print()
    info("Ejecutando catalog-sync (bash)...")
    console.print()

    # Construir comando
    # Source catalog-sync.sh y ejecutar la función
    args = []
    if service:
        args.append(service)
    elif dry_run:
        args.append("--dry-run")

    # Ejecutar como subscript bash que sourcea el lib y llama la función
    bash_cmd = f"""
        export DOCKER_BASE="{DOCKER_BASE}"
        export NAS_DOTFILES="{NAS_DOTFILES}"
        source "{CATALOG_SYNC_SCRIPT}"
        catalog_sync {' '.join(args)}
    """

    result = subprocess.run(
        ["bash", "-c", bash_cmd],
        capture_output=False,  # output directo a terminal
    )

    console.print()
    if result.returncode == 0:
        success("catalog-sync completado")
    else:
        warn("catalog-sync terminó con errores (ver output arriba)")

    console.print()


def _native_catalog_sync(service: Optional[str], dry_run: bool):
    """Implementación nativa mínima cuando el script bash no existe."""
    console.print()
    warn("Script bash catalog-sync.sh no encontrado")
    info("Ejecutando sync nativo (limitado)...")
    console.print()

    services = [service] if service else svc_list()

    for svc in services:
        cf = svc_compose_file(svc)
        if cf is None:
            continue

        console.print(f"  ┌─ [bold]{svc}[/bold]")

        # Ficha
        ficha = CATALOG_DIR / svc / "ficha.md"
        if ficha.exists():
            console.print("  │  ⏭️  ficha.md ya existe")
        else:
            if dry_run:
                console.print("  │  🆕 [dry-run] Generaría ficha.md")
            else:
                console.print("  │  ⚠️  ficha.md falta (generar manualmente o instalar bash CLI)")

        # Compose al catálogo
        catalog_compose = CATALOG_DIR / svc / "compose.yml"
        if catalog_compose.exists():
            console.print("  │  ⏭️  compose.yml ya en catálogo")
        else:
            if dry_run:
                console.print("  │  🆕 [dry-run] Copiaría compose.yml")
            else:
                (CATALOG_DIR / svc).mkdir(parents=True, exist_ok=True)
                catalog_compose.write_text(cf.read_text(encoding="utf-8"), encoding="utf-8")
                console.print("  │  ✅ compose.yml copiado al catálogo")

        # Guía
        guide = DOCS_DIR / f"{svc}-guide.md"
        if guide.exists():
            console.print("  │  ⏭️  guía ya existe")
        else:
            if dry_run:
                console.print("  │  🆕 [dry-run] Generaría guía placeholder")
            else:
                console.print("  │  ⚠️  guía falta (usar bash CLI o escribir manualmente)")

        console.print("  └─ done")
        console.print()

    # Regenerar index al final
    if not dry_run:
        _regenerate_index()
