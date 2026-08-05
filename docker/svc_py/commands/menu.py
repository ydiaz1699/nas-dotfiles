"""
menu.py — Menú TUI interactivo avanzado con InquirerPy + Rich.

Mejoras sobre el menú bash (fzf):
- Búsqueda fuzzy mientras escribes
- Preview del servicio (estado, imagen, puertos, uptime)
- Acciones agrupadas por categoría con descripciones
- Confirmación visual antes de acciones destructivas
- Loop continuo hasta Esc/salir
"""

from __future__ import annotations

import typer
from rich.panel import Panel
from rich.table import Table
from rich import box

from docker.svc_py.core.discovery import svc_compose_file, svc_list
from docker.svc_py.core.docker import (
    compose_output,
    compose_passthrough,
    compose_run,
    container_inspect,
    get_container_ids,
    get_container_info,
    is_service_running,
    sdk_available,
)
from docker.svc_py.ui import console, error, success, warn

app = typer.Typer()

# Acciones agrupadas por tipo (para mejor UX)
ACTION_GROUPS = [
    ("── Ciclo de vida ──", None),
    ("up", "Levantar contenedores", "green"),
    ("start", "Iniciar detenido", "green"),
    ("restart", "Reiniciar servicio", "yellow"),
    ("stop", "Detener servicio", "yellow"),
    ("down", "Bajar y eliminar", "red"),
    ("── Información ──", None),
    ("logs", "Ver logs en vivo", "cyan"),
    ("stats", "Uso CPU/RAM tiempo real", "cyan"),
    ("config", "Ver compose resuelto", "cyan"),
    ("depends", "Ver dependencias", "cyan"),
    ("env", "Variables de entorno", "cyan"),
    ("open", "Abrir URL del servicio", "cyan"),
    ("── Mantenimiento ──", None),
    ("update", "Pull imagen + recrear", "blue"),
    ("backup", "Exportar volúmenes", "blue"),
    ("restore", "Restaurar desde backup", "blue"),
    ("exec", "Abrir shell en contenedor", "magenta"),
]


def _service_preview(service: str) -> str:
    """Genera preview rico de un servicio para mostrar en el menú."""
    cf = svc_compose_file(service)
    if cf is None:
        return "  (compose file no encontrado)"

    lines = []
    lines.append(f"  Servicio: {service}")
    lines.append(f"  Compose:  {cf}")

    # Estado
    running = is_service_running(cf)
    lines.append(f"  Estado:   {'● Activo' if running else '○ Detenido'}")

    if running:
        containers = get_container_ids(cf)
        if containers:
            cid = containers[0]
            info = get_container_info(cid)
            if info:
                lines.append(f"  Imagen:   {info['image']}")
                lines.append(f"  Health:   {info['health']}")
                lines.append(f"  Restarts: {info['restart_count']}")
            else:
                # Fallback sin SDK
                health = container_inspect(cid, "{{if .State.Health}}{{.State.Health.Status}}{{else}}--{{end}}")
                restarts = container_inspect(cid, "{{.RestartCount}}")
                lines.append(f"  Health:   {health}")
                lines.append(f"  Restarts: {restarts}")

    # Puertos
    ports_out, _ = compose_output(cf, ["ps", "--format", "{{.Ports}}"])
    if ports_out:
        ports_clean = ports_out.splitlines()[0][:60]
        lines.append(f"  Puertos:  {ports_clean}")

    return "\n".join(lines)


@app.command("menu")
def menu():
    """Menú TUI interactivo avanzado — búsqueda fuzzy, preview, acciones agrupadas."""
    try:
        from InquirerPy import inquirer
        from InquirerPy.separator import Separator
    except ImportError:
        error("InquirerPy no instalado.")
        console.print("  [dim]pip install InquirerPy[/dim]\n")
        raise typer.Exit(1)

    # Header
    console.print()
    console.print(Panel(
        "[bold white]svc menu[/bold white] — Administrador de servicios\n"
        "[dim]Escribe para buscar · Enter seleccionar · Esc salir[/dim]",
        border_style="cyan",
        padding=(0, 2),
        width=60,
    ))

    while True:
        # ── 1. Seleccionar servicio con búsqueda fuzzy ─────────────────
        services = svc_list()
        if not services:
            error("No se encontraron servicios")
            break

        # Construir choices con estado
        svc_choices = []
        for svc in services:
            cf = svc_compose_file(svc)
            running = is_service_running(cf) if cf else False
            dot = "●" if running else "○"
            status = "activo" if running else "detenido"
            svc_choices.append({
                "name": f" {dot} {svc:<22} {status}",
                "value": svc,
            })
        svc_choices.append(Separator("─" * 40))
        svc_choices.append({"name": " ← Salir", "value": None})

        service = inquirer.fuzzy(
            message="Servicio (escribe para buscar):",
            choices=svc_choices,
            pointer="❯",
            border=True,
            info=True,
            match_exact=False,
            max_height="60%",
        ).execute()

        if service is None:
            break

        # ── Preview del servicio seleccionado ──────────────────────────
        preview = _service_preview(service)
        console.print()
        console.print(Panel(
            preview,
            title=f"[bold cyan]{service}[/bold cyan]",
            border_style="bright_cyan",
            padding=(0, 1),
            width=60,
        ))

        # ── 2. Seleccionar acción con categorías ──────────────────────
        action_choices = []
        for item in ACTION_GROUPS:
            if item[1] is None:
                # Es separador
                action_choices.append(Separator(f"  {item[0]}"))
            else:
                cmd, desc, color = item
                action_choices.append({
                    "name": f" {cmd:<12} {desc}",
                    "value": cmd,
                })
        action_choices.append(Separator("─" * 40))
        action_choices.append({"name": " ← Volver", "value": None})

        action = inquirer.fuzzy(
            message=f"Acción para {service}:",
            choices=action_choices,
            pointer="❯",
            border=True,
            match_exact=False,
            max_height="70%",
        ).execute()

        if action is None:
            console.print()
            continue

        # ── Confirmación para acciones destructivas ────────────────────
        cf = svc_compose_file(service)
        if cf is None:
            error(f"Compose file no encontrado para '{service}'")
            continue

        destructive = {"down", "stop", "restore"}
        if action in destructive:
            confirm = inquirer.confirm(
                message=f"¿Ejecutar '{action}' en {service}?",
                default=False,
            ).execute()
            if not confirm:
                console.print("  [dim]Cancelado.[/dim]\n")
                continue

        # ── 3. Ejecutar acción ─────────────────────────────────────────
        console.print(f"\n  [bold cyan]> {action} {service}[/bold cyan]")
        console.print("  " + "─" * 50)

        if action == "exec":
            svc_out, _ = compose_output(cf, ["ps", "--services"])
            container = svc_out.strip().splitlines()[0] if svc_out.strip() else "app"
            compose_passthrough(cf, ["exec", container, "sh"])

        elif action == "update":
            from rich.progress import Progress, SpinnerColumn, TextColumn
            with Progress(SpinnerColumn(), TextColumn("{task.description}"), console=console) as p:
                t = p.add_task(f"  Pulling {service}...")
                compose_run(cf, ["pull"], capture=True, check=False)
                p.update(t, description=f"  Recreando {service}...")
                compose_run(cf, ["up", "-d", "--remove-orphans"], capture=True, check=False)
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

        elif action == "depends":
            from docker.svc_py.commands import info as info_mod
            info_mod.depends(service)

        elif action == "env":
            from docker.svc_py.commands import info as info_mod
            info_mod.env_cmd(service, edit=False)

        elif action == "open":
            from docker.svc_py.commands import info as info_mod
            info_mod.open_cmd(service)

        elif action == "config":
            compose_passthrough(cf, ["config"])

        else:
            # up, start, restart, stop, down → passthrough
            compose_run(cf, [action], capture=False, check=False)

        console.print()

        # Pausa antes de volver al menú
        try:
            from InquirerPy import inquirer as inq
            inq.confirm(message="Volver al menú?", default=True).execute()
        except (EOFError, KeyboardInterrupt):
            break
        console.print()
