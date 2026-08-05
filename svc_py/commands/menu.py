"""
menu.py — Menú TUI interactivo avanzado con InquirerPy + Rich.

Mejoras sobre el menú bash (fzf):
- Búsqueda fuzzy mientras escribes
- Preview del servicio (estado, imagen, puertos, uptime)
- Multi-select: seleccionar varios servicios + acción → ejecuta uno por uno
- Confirmación visual antes de acciones destructivas
- Loop continuo hasta Esc/salir
"""

from __future__ import annotations

import typer
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn
from rich import box

from svc_py.core.discovery import svc_compose_file, svc_list
from svc_py.core.docker import (
    compose_output,
    compose_passthrough,
    compose_run,
    container_inspect,
    get_container_ids,
    get_container_info,
    is_service_running,
)
from svc_py.ui import console, error, success, warn

app = typer.Typer()

# Acciones que se pueden ejecutar en multi-select (secuenciales)
BATCH_ACTIONS = [
    ("up", "Levantar contenedores"),
    ("start", "Iniciar detenido"),
    ("restart", "Reiniciar servicio"),
    ("stop", "Detener servicio"),
    ("down", "Bajar y eliminar"),
    ("update", "Pull imagen + recrear"),
    ("recreate", "Recrear sin pull"),
]

# Acciones solo para un servicio individual
SINGLE_ACTIONS = [
    ("logs", "Ver logs en vivo"),
    ("stats", "Uso CPU/RAM tiempo real"),
    ("config", "Ver compose resuelto"),
    ("depends", "Ver dependencias"),
    ("env", "Variables de entorno"),
    ("open", "Abrir URL del servicio"),
    ("backup", "Exportar volúmenes"),
    ("restore", "Restaurar desde backup"),
    ("exec", "Abrir shell en contenedor"),
]


def _service_preview(service: str) -> str:
    """Genera preview rico de un servicio."""
    cf = svc_compose_file(service)
    if cf is None:
        return "  (compose file no encontrado)"

    lines = []
    lines.append(f"  Servicio: {service}")
    lines.append(f"  Compose:  {cf}")

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
                health = container_inspect(cid, "{{if .State.Health}}{{.State.Health.Status}}{{else}}--{{end}}")
                restarts = container_inspect(cid, "{{.RestartCount}}")
                lines.append(f"  Health:   {health}")
                lines.append(f"  Restarts: {restarts}")

    ports_out, _ = compose_output(cf, ["ps", "--format", "{{.Ports}}"])
    if ports_out:
        ports_clean = ports_out.splitlines()[0][:60]
        lines.append(f"  Puertos:  {ports_clean}")

    return "\n".join(lines)


def _execute_action(action: str, service: str) -> bool:
    """Ejecuta una acción en un servicio. Retorna True si éxito."""
    cf = svc_compose_file(service)
    if cf is None:
        error(f"  {service}: compose file no encontrado")
        return False

    if action == "update":
        result = compose_run(cf, ["pull"], capture=True, check=False)
        if result.returncode != 0:
            error(f"  {service}: error en pull")
            return False
        compose_run(cf, ["up", "-d", "--remove-orphans"], capture=True, check=False)

    elif action == "recreate":
        compose_run(cf, ["up", "-d", "--force-recreate", "--remove-orphans"], capture=True, check=False)

    elif action in ("up",):
        compose_run(cf, ["up", "-d"], capture=True, check=False)

    elif action in ("start", "stop", "restart", "down"):
        compose_run(cf, [action], capture=True, check=False)

    elif action == "backup":
        from svc_py.commands.backup import backup
        backup(service)

    elif action == "restore":
        from svc_py.commands.backup import restore
        restore(service, archive=None)

    elif action == "logs":
        compose_passthrough(cf, ["logs", "-f", "--tail=100"])

    elif action == "stats":
        compose_passthrough(cf, ["stats"])

    elif action == "exec":
        svc_out, _ = compose_output(cf, ["ps", "--services"])
        container = svc_out.strip().splitlines()[0] if svc_out.strip() else "app"
        compose_passthrough(cf, ["exec", container, "sh"])

    elif action == "depends":
        from svc_py.commands import info as info_mod
        info_mod.depends(service)

    elif action == "env":
        from svc_py.commands import info as info_mod
        info_mod.env_cmd(service, edit=False)

    elif action == "open":
        from svc_py.commands import info as info_mod
        info_mod.open_cmd(service)

    elif action == "config":
        compose_passthrough(cf, ["config"])

    else:
        compose_run(cf, [action], capture=True, check=False)

    return True


def _multi_select_flow(inquirer) -> None:
    """Flujo multi-select: seleccionar servicios → acción → ejecutar uno por uno."""
    services = svc_list()

    # 1. Seleccionar servicios con checkbox
    choices = []
    for svc in services:
        cf = svc_compose_file(svc)
        running = is_service_running(cf) if cf else False
        dot = "●" if running else "○"
        choices.append({
            "name": f" {dot} {svc}",
            "value": svc,
            "enabled": False,  # Todos deseleccionados por defecto
        })

    selected = inquirer.checkbox(
        message="Selecciona servicios:",
        choices=choices,
        pointer="❯",
        cycle=True,
        instruction="(Space=toggle, Ctrl+A=todos, Enter=confirmar)",
        keybindings={"toggle-all": [{"key": "c-a"}]},
    ).execute()

    if not selected:
        console.print("  [dim]Ningún servicio seleccionado.[/dim]\n")
        return

    console.print(f"\n  [cyan]Seleccionados:[/cyan] {', '.join(selected)}\n")

    # 2. Seleccionar acción (solo batch actions)
    action_choices = [
        {"name": f" {cmd:<12} → {desc}", "value": cmd}
        for cmd, desc in BATCH_ACTIONS
    ]
    action_choices.append({"name": " ← Cancelar", "value": None})

    action = inquirer.select(
        message="Acción a ejecutar en todos:",
        choices=action_choices,
        pointer="❯",
    ).execute()

    if action is None:
        console.print("  [dim]Cancelado.[/dim]\n")
        return

    # 3. Confirmación para acciones destructivas
    destructive = {"down", "stop"}
    if action in destructive:
        confirm = inquirer.confirm(
            message=f"¿Ejecutar '{action}' en {len(selected)} servicios?",
            default=False,
        ).execute()
        if not confirm:
            console.print("  [dim]Cancelado.[/dim]\n")
            return

    # 4. Ejecutar uno por uno con progress
    console.print(f"\n  [bold cyan]> {action}[/bold cyan] en {len(selected)} servicios (secuencial)\n")

    ok = 0
    fail = 0

    for i, svc in enumerate(selected, 1):
        console.print(f"  [{i}/{len(selected)}] [cyan]{svc}[/cyan]...", end=" ")
        result = _execute_action(action, svc)
        if result:
            console.print("[green]✓[/green]")
            ok += 1
        else:
            console.print("[red]✗[/red]")
            fail += 1

    # Resumen
    console.print()
    if fail == 0:
        success(f"{ok}/{len(selected)} completados")
    else:
        success(f"{ok} OK")
        error(f"{fail} con error")
    console.print()


@app.command("menu")
def menu():
    """Menú TUI interactivo — búsqueda fuzzy, multi-select, preview."""
    try:
        from InquirerPy import inquirer
    except ImportError:
        error("InquirerPy no instalado.")
        console.print("  [dim]pipins InquirerPy[/dim]\n")
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
        services = svc_list()
        if not services:
            error("No se encontraron servicios")
            break

        # ── 1. Seleccionar servicio O multi-select ─────────────────────
        svc_choices = []
        # Opción multi-select al inicio
        svc_choices.append({
            "name": " ⊞ multi-select       (varios servicios + acción)",
            "value": "__multi__",
        })
        # Servicios individuales
        for svc in services:
            cf = svc_compose_file(svc)
            running = is_service_running(cf) if cf else False
            dot = "●" if running else "○"
            status = "activo" if running else "detenido"
            svc_choices.append({
                "name": f" {dot} {svc:<22} {status}",
                "value": svc,
            })
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

        # ── Multi-select flow ──────────────────────────────────────────
        if service == "__multi__":
            _multi_select_flow(inquirer)
            # Pausa antes de volver
            try:
                inquirer.confirm(message="Volver al menú?", default=True).execute()
            except (EOFError, KeyboardInterrupt):
                break
            console.print()
            continue

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

        # ── 2. Seleccionar acción ─────────────────────────────────────
        action_choices = []
        # Batch actions
        for cmd, desc in BATCH_ACTIONS:
            action_choices.append({
                "name": f" {cmd:<12} → {desc}",
                "value": cmd,
            })
        # Single actions
        for cmd, desc in SINGLE_ACTIONS:
            action_choices.append({
                "name": f" {cmd:<12} → {desc}",
                "value": cmd,
            })
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

        _execute_action(action, service)

        console.print()

        # Pausa antes de volver al menú
        try:
            inquirer.confirm(message="Volver al menú?", default=True).execute()
        except (EOFError, KeyboardInterrupt):
            break
        console.print()
