"""
codemap.py — Comando 'svc code-map' para el Python CLI.

Genera docs/CODE-MAP.md: el mapa legible de qué hace cada archivo de código,
sus símbolos y sus conexiones internas. Delega en project_index.py --code-map
(misma fuente de verdad que el CLI Bash) para no duplicar la lógica.
"""

from __future__ import annotations

import os
import subprocess

import typer

from svc_py.config import DOCKER_BASE, NAS_DOTFILES
from svc_py.ui import console


def code_map():
    """Generar docs/CODE-MAP.md (mapa legible del código del repo).

    Índice generado (no editar a mano) de qué hace cada archivo, sus símbolos
    y sus conexiones. Se consulta para saber QUÉ archivo tocar sin releer todo
    el repo, y complementa docs/dependency-map.md (qué actualizar en cascada).
    """
    env = os.environ.copy()
    env.setdefault("NAS_DOTFILES", str(NAS_DOTFILES))
    env.setdefault("DOCKER_BASE", str(DOCKER_BASE))

    index_path = NAS_DOTFILES / "agent" / "tools" / "project_index.py"
    if not index_path.exists():
        console.print("  [red]Error:[/red] No se encontró project_index.py")
        console.print(f"  Esperado en: {index_path}")
        raise typer.Exit(1)

    result = subprocess.run(
        ["python3", str(index_path), "--code-map"],
        capture_output=True, text=True, env=env,
    )

    if result.stdout:
        console.print(result.stdout, highlight=False)
    if result.stderr:
        console.print(f"[red]{result.stderr}[/red]")

    if result.returncode != 0:
        raise typer.Exit(result.returncode)
