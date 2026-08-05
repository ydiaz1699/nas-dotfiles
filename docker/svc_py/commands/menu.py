"""
menu.py — Menú interactivo con InquirerPy (reemplaza fzf).
"""

from __future__ import annotations

import subprocess

import typer

from docker.svc_py.core.discovery import svc_compose_file, svc_list
from docker.svc_py.core.docker import compose_passthrough, compose_run, is_service_running
from docker.svc_py.ui import confirm_action, console, error, success

app = typer.Typer()

ACTIONS = [
    ("up", "Levantar contenedores"),
    ("down", "Bajar y eliminar"),
    ("restart", "Reiniciar"),
    ("start", "Iniciar detenido"),
    ("stop", "Detener"),
    ("logs", "Ver logs en vivo"),
    ("stats", "Uso CPU/RAM"),
    ("update", "Pull + recrear"),
    ("backup", "Exportar volúmenes"),
    ("restore", "Restaurar backup"),
    ("exec", "Abrir shell"),
    ("depends", "Ver dependencias"),
    ("env", "Ver variables"),
    ("open", "Abrir URL"),
    ("config", "Ver config resuelta"),
]


@app.command("menu")
def menu():
    """Menú TUI interactivo con InquirerPy."""
    try:
        from InquirerPy import inquirer
        from InquirerPy.separator import Separator
    except ImportError:
        error("InquirerPy no instalado. Instalar: pip install InquirerPy")
        console.print("  [dim]Mientras tanto, usa: svc menu (bash CLI)[/dim]\n")
        raise typer.Exit(1)

    while True:
        # 1. Seleccionar servicio
        services = svc_list()
        if not services:
            error("No se encontraron servicios")
            break

        choices = []
        for svc in services:
            cf = svc_compose_file(svc)
            running = is_service_running(cf) if cf else False
            dot = "●" if running else "○"
            status = "activo" if running else "detenido"
            choices.append({"name": f"{dot} {svc:<20} ({status})", "value": svc})
        choices.append(Separator())
        choices.append({"name": "← Salir", "value": None})

        service = inquirer.select(
            message="Servicio:",
            choices=choices,
            pointer="❯",
        ).execute()

        if service is None:
            break

        # 2. Seleccionar acción
        action_choices = [
            {"name": f"{cmd:<12} → {desc}", "value": cmd}
            for cmd, desc in ACTIONS
        ]
        action_choices.append(Separator())
        action_choices.append({"name": "← Volver", "value": None})

        action = inquirer.select(
            message=f"Acción para {service}:",
            choices=action_choices,
            pointer="❯",
        ).execute()

        if action is None:
            continue

        # 3. Ejecutar
        cf = svc_compose_file(service)
        if cf is None:
            error(f"Compose file no encontrado para '{service}'")
            continue

        console.print(f"\n  [cyan]> {action} {service}[/cyan]")
        console.print("  " + "─" * 40)

        if action == "exec":
            # Shell interactivo
            services_out, _ = compose_run(cf, ["ps", "--services"], capture=True, check=False).stdout, 0
            container = services_out.strip().splitlines()[0] if services_out.strip() else "app"
            compose_passthrough(cf, ["exec", container, "sh"])
        elif action == "update":
            compose_run(cf, ["pull"], capture=False, check=False)
            compose_run(cf, ["up", "-d", "--remove-orphans"], capture=False, check=False)
            success(f"{service} actualizado")
        elif action == "backup":
            from docker.svc_py.commands.backup import backup
            backup(service)
        elif action == "restore":
            from docker.svc_py.commands.backup import restore
            restore(service, archive=None)
        elif action == "logs":
            compose_passthrough(cf, ["logs", "-f", "--tail=100"])
        elif action == "stats":
            compose_passthrough(cf, ["stats"])
        elif action in ("depends", "env", "open"):
            # Delegar a info commands
            from docker.svc_py.commands import info as info_mod
            if action == "depends":
                info_mod.depends(service)
            elif action == "env":
                info_mod.env_cmd(service, edit=False)
            elif action == "open":
                info_mod.open_cmd(service)
        elif action == "config":
            compose_passthrough(cf, ["config"])
        else:
            compose_run(cf, [action], capture=False, check=False)

        console.print()
        # Pequeña pausa
        try:
            input("  Enter para continuar...")
        except (EOFError, KeyboardInterrupt):
            break
        console.print()
