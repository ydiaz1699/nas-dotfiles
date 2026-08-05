"""
ui.py — Rich helpers para el CLI.

Funciones reutilizables para tablas, paneles, colores, progress, etc.
"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box

console = Console()


def error(msg: str) -> None:
    """Muestra mensaje de error."""
    console.print(f"  [bold red]✗[/bold red] {msg}")


def warn(msg: str) -> None:
    """Muestra advertencia."""
    console.print(f"  [bold yellow]⚠[/bold yellow] {msg}")


def success(msg: str) -> None:
    """Muestra mensaje exitoso."""
    console.print(f"  [bold green]✓[/bold green] {msg}")


def info(msg: str) -> None:
    """Muestra información."""
    console.print(f"  [cyan]ℹ[/cyan] {msg}")


def header(title: str, subtitle: str = "") -> None:
    """Muestra header con panel."""
    content = f"[bold white]{title}[/bold white]"
    if subtitle:
        content += f"\n[dim]{subtitle}[/dim]"
    console.print(Panel(
        content,
        border_style="bright_cyan",
        padding=(0, 2),
        width=70,
    ))


def status_dot(running: bool) -> str:
    """Retorna dot verde/rojo según estado."""
    return "[green]●[/green]" if running else "[red]○[/red]"


def health_colored(status: str) -> str:
    """Colorea health status."""
    colors = {
        "healthy": "[green]healthy[/green]",
        "unhealthy": "[red]unhealthy[/red]",
        "starting": "[yellow]starting[/yellow]",
    }
    return colors.get(status, f"[dim]{status}[/dim]")


def restart_colored(count: int) -> str:
    """Colorea restart count según severidad."""
    if count > 5:
        return f"[bold red]{count}[/bold red]"
    elif count > 0:
        return f"[yellow]{count}[/yellow]"
    return f"[dim]{count}[/dim]"


def service_table(columns: list, title: str = "") -> Table:
    """Crea una tabla Rich pre-configurada para servicios."""
    table = Table(
        box=box.ROUNDED,
        title=title if title else None,
        title_style="bold cyan",
        show_header=True,
        header_style="bold",
        padding=(0, 1),
        expand=False,
    )
    for col in columns:
        if isinstance(col, tuple):
            table.add_column(col[0], **col[1])
        else:
            table.add_column(col)
    return table


def confirm_action(action: str, service: str) -> None:
    """Muestra qué acción se va a ejecutar."""
    console.print(f"\n  [cyan]{action}[/cyan] [bold]{service}[/bold]...")
