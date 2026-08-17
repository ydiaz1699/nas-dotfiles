"""
scanner.py — Comando 'svc scan' para el Python CLI.

Ejecuta el Project Scanner que detecta lagunas e inconsistencias
en el ecosistema nas-dotfiles (servicios, docs, CLI, agente, config).
"""

from __future__ import annotations

import sys
from pathlib import Path

import typer

from svc_py.config import DOCKER_BASE, NAS_DOTFILES
from svc_py.ui import console

# Agregar el directorio raíz al path para importar el scanner
_nas_root = str(NAS_DOTFILES)
if _nas_root not in sys.path:
    sys.path.insert(0, _nas_root)


def scan(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Incluir issues de severidad 'info'"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output en JSON"),
):
    """Escanear proyecto y detectar lagunas/inconsistencias.

    Verifica: servicios sin docs, IP hardcodeada, CLI sin paridad,
    prompt del agente desactualizado, docs_url rotos.
    """
    import os
    import subprocess

    # Configurar variables de entorno para el scanner
    env = os.environ.copy()
    env.setdefault("NAS_DOTFILES", str(NAS_DOTFILES))
    env.setdefault("DOCKER_BASE", str(DOCKER_BASE))

    scanner_path = NAS_DOTFILES / "agent" / "tools" / "project_scanner.py"
    if not scanner_path.exists():
        console.print(f"  [red]Error:[/red] No se encontró project_scanner.py")
        console.print(f"  Esperado en: {scanner_path}")
        raise typer.Exit(1)

    # Ejecutar el scanner como script standalone (evita conflictos de importación)
    args = ["python3", str(scanner_path)]
    if verbose:
        args.append("--verbose")
    if json_output:
        args.append("--json")

    result = subprocess.run(args, capture_output=True, text=True, env=env)

    if result.stdout:
        console.print(result.stdout, highlight=False)
    if result.stderr:
        console.print(f"[red]{result.stderr}[/red]")

    if result.returncode != 0:
        raise typer.Exit(result.returncode)
