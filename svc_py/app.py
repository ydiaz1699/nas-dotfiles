"""
app.py — Aplicación principal Typer que registra todos los comandos.

Entry point del Python CLI. Registra subcomandos de cada módulo
y maneja el passthrough genérico a docker compose.
"""

from __future__ import annotations

import sys
from typing import List, Optional

import typer
from rich.panel import Panel

from svc_py.commands import health as health_mod
from svc_py.commands import docker as docker_mod
from svc_py.commands import backup as backup_mod
from svc_py.commands import info as info_mod
from svc_py.commands import compose as compose_mod
from svc_py.commands import menu as menu_mod
from svc_py.core.discovery import service_exists, svc_compose_file, svc_list
from svc_py.core.docker import compose_passthrough, compose_run
from svc_py.ui import confirm_action, console, error

app = typer.Typer(
    name="svc",
    help="Docker Service Manager — Python CLI con Rich + InquirerPy",
    add_completion=False,
    no_args_is_help=True,
    pretty_exceptions_enable=False,
)

# ── Registrar sub-apps ─────────────────────────────────────────────────────
# Health commands
app.command("health")(health_mod.health)
app.command("doctor")(health_mod.doctor)
app.command("watch")(health_mod.watch)

# Docker commands
app.command("update-all")(docker_mod.update_all)

# Backup commands
app.command("backup")(backup_mod.backup)
app.command("restore")(backup_mod.restore)

# Info commands
app.command("port-map")(info_mod.port_map)
app.command("size")(info_mod.size)
app.command("net")(info_mod.net)
app.command("depends")(info_mod.depends)
app.command("env")(info_mod.env_cmd)
app.command("open")(info_mod.open_cmd)

# Compose commands
app.command("create")(compose_mod.create)
app.command("diff")(compose_mod.diff)

# Menu
app.command("menu")(menu_mod.menu)


# ── Comandos globales ──────────────────────────────────────────────────────


@app.command("lista")
def lista():
    """Lista servicios con estado (activo/detenido)."""
    from svc_py.core.docker import is_service_running
    from svc_py.ui import service_table, status_dot

    services = svc_list()
    if not services:
        error(f"No se encontraron servicios en DOCKER_BASE")
        raise typer.Exit(1)

    table = service_table(
        [("", {"width": 2}), ("Servicio", {"min_width": 20}), "Estado"],
        title=f"Servicios ({len(services)})",
    )

    for svc in services:
        cf = svc_compose_file(svc)
        if cf and is_service_running(cf):
            table.add_row(status_dot(True), svc, "[green]activo[/green]")
        else:
            table.add_row(status_dot(False), svc, "[red]detenido[/red]")

    console.print()
    console.print(table)
    console.print()


# ── Docker compose commands ────────────────────────────────────────────────


@app.command("up")
def up(service: str, ctx: typer.Context = typer.Context):
    """Crear e iniciar contenedores."""
    _docker_action("up", service, ["-d"] + ctx.args if hasattr(ctx, 'args') else ["-d"])


@app.command("down")
def down(service: str):
    """Detener y eliminar contenedores."""
    _docker_action("down", service)


@app.command("start")
def start(service: str):
    """Iniciar servicio detenido."""
    _docker_action("start", service)


@app.command("stop")
def stop(service: str):
    """Detener servicio."""
    _docker_action("stop", service)


@app.command("restart")
def restart(service: str):
    """Reiniciar servicio."""
    _docker_action("restart", service)


@app.command("kill")
def kill_svc(service: str):
    """Forzar parada."""
    _docker_action("kill", service)


@app.command("update")
def update(service: str):
    """Pull + recrear contenedores."""
    cf = _get_compose_or_exit(service)
    confirm_action("Actualizando", service)
    compose_run(cf, ["pull"], capture=False, check=False)
    compose_run(cf, ["up", "-d", "--remove-orphans"], capture=False, check=False)
    console.print(f"  [green]✓[/green] {service} actualizado\n")


@app.command("recreate")
def recreate(service: str):
    """Recrear contenedores SIN pull (usa imagen local)."""
    cf = _get_compose_or_exit(service)
    confirm_action("Recreando", service)
    compose_run(cf, ["up", "-d", "--force-recreate", "--remove-orphans"], capture=False, check=False)
    console.print(f"  [green]✓[/green] {service} recreado (sin pull)\n")


@app.command("logs")
def logs(service: str, lines: int = typer.Option(200, "--tail", "-n", help="Lineas")):
    """Ver logs en vivo."""
    cf = _get_compose_or_exit(service)
    compose_passthrough(cf, ["logs", "-f", f"--tail={lines}"])


@app.command("ps")
def ps_cmd(service: str):
    """Listar contenedores."""
    cf = _get_compose_or_exit(service)
    compose_passthrough(cf, ["ps"])


@app.command("stats")
def stats(service: str):
    """Uso de CPU/RAM en tiempo real."""
    cf = _get_compose_or_exit(service)
    compose_passthrough(cf, ["stats"])


@app.command("top")
def top(service: str):
    """Procesos corriendo."""
    cf = _get_compose_or_exit(service)
    compose_passthrough(cf, ["top"])


@app.command("exec")
def exec_cmd(service: str, cmd: List[str] = typer.Argument(None)):
    """Ejecutar comando en contenedor."""
    cf = _get_compose_or_exit(service)
    exec_args = ["exec"] + (cmd if cmd else ["sh"])
    compose_passthrough(cf, exec_args)


@app.command("build")
def build(service: str):
    """Construir/reconstruir imagen."""
    _docker_action("build", service)


@app.command("pull")
def pull(service: str):
    """Descargar imagen."""
    _docker_action("pull", service)


@app.command("images")
def images(service: str):
    """Listar imagenes."""
    cf = _get_compose_or_exit(service)
    compose_passthrough(cf, ["images"])


@app.command("rm")
def rm_cmd(service: str):
    """Eliminar contenedores detenidos."""
    _docker_action("rm", service)


@app.command("config")
def config(service: str):
    """Ver configuracion resuelta."""
    cf = _get_compose_or_exit(service)
    compose_passthrough(cf, ["config"])


@app.command("events")
def events(service: str):
    """Eventos en tiempo real."""
    cf = _get_compose_or_exit(service)
    compose_passthrough(cf, ["events"])


@app.command("volumes")
def volumes(service: str):
    """Listar volumenes."""
    cf = _get_compose_or_exit(service)
    compose_passthrough(cf, ["config", "--volumes"])


# ── Helpers ────────────────────────────────────────────────────────────────


def _get_compose_or_exit(service: str):
    """Obtiene compose file o sale con error."""
    cf = svc_compose_file(service)
    if cf is None:
        error(f"Servicio '{service}' no encontrado")
        console.print(f"  Servicios disponibles: {', '.join(svc_list())}\n")
        raise typer.Exit(1)
    return cf


def _docker_action(action: str, service: str, extra_args: list = None):
    """Ejecuta una acción docker compose simple."""
    cf = _get_compose_or_exit(service)
    confirm_action(action.capitalize(), service)
    args = [action] + (extra_args or [])
    compose_run(cf, args, capture=False, check=False)
    console.print()
