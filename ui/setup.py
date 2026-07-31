#!/usr/bin/env python3
"""
setup.py — TUI de primera instalación para nas-dotfiles

Wizard interactivo que guía la configuración inicial del framework.
Usa Rich (paneles, tablas, progreso) + InquirerPy (menús, inputs).

Uso:
    python setup.py

Requisitos:
    pip install rich InquirerPy

Si Python no está disponible, usar el fallback bash:
    ./install.sh
"""

import os
import sys
import shutil
import subprocess
import time
from pathlib import Path

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
    from rich.columns import Columns
    from rich import box
    from InquirerPy import inquirer
    from InquirerPy.separator import Separator
except ImportError:
    print("\n  ⚠  Dependencias del TUI no instaladas.")
    print("  Ejecuta: pip install rich InquirerPy")
    print("  O usa el fallback: ./install.sh\n")
    sys.exit(1)


# ─────────────────────────────────────────────────────────────────────────────
# Constantes
# ─────────────────────────────────────────────────────────────────────────────

REPO_DIR = Path(__file__).resolve().parent
INSTALL_DIR = Path("/nas-dotfiles")
DOCKER_BASE_DEFAULT = "/docker"

console = Console()


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────


def run_cmd(cmd: list[str], timeout: int = 30) -> tuple[bool, str]:
    """Ejecuta un comando y retorna (success, output)."""
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout
        )
        return result.returncode == 0, result.stdout.strip()
    except Exception as e:
        return False, str(e)


def detect_system() -> dict:
    """Detecta información del sistema."""
    info = {
        "user": os.environ.get("USER", "unknown"),
        "hostname": "",
        "os": "",
        "docker": "",
        "python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "bash": "",
        "timezone": "",
    }

    # Hostname
    ok, out = run_cmd(["hostname"])
    info["hostname"] = out if ok else "unknown"

    # OS
    if Path("/etc/os-release").exists():
        for line in Path("/etc/os-release").read_text().splitlines():
            if line.startswith("PRETTY_NAME="):
                info["os"] = line.split("=", 1)[1].strip('"')
                break

    # Docker
    ok, out = run_cmd(["docker", "--version"])
    if ok:
        # "Docker version 27.1.2, build ..."
        info["docker"] = out.split(",")[0].replace("Docker version ", "v")
    else:
        info["docker"] = ""

    # Bash
    ok, out = run_cmd(["bash", "--version"])
    if ok:
        # Primera línea: "GNU bash, version 5.2.15..."
        parts = out.splitlines()[0] if out else ""
        if "version" in parts:
            info["bash"] = parts.split("version ")[1].split("(")[0].strip()

    # Timezone
    ok, out = run_cmd(["timedatectl", "show", "-p", "Timezone", "--value"])
    if ok and out:
        info["timezone"] = out
    elif Path("/etc/timezone").exists():
        info["timezone"] = Path("/etc/timezone").read_text().strip()
    else:
        info["timezone"] = "UTC"

    return info


def check_mark(condition: bool) -> str:
    """Retorna ✅ o ❌ según condición."""
    return "[green]✅[/green]" if condition else "[red]❌[/red]"


# ─────────────────────────────────────────────────────────────────────────────
# Pantallas del wizard
# ─────────────────────────────────────────────────────────────────────────────


def show_header():
    """Muestra el header del wizard."""
    console.clear()
    console.print()
    console.print(
        Panel.fit(
            "[bold cyan]🖥️  nas-dotfiles — Setup[/bold cyan]\n"
            "[dim]Administración inteligente de NAS con Docker[/dim]",
            border_style="cyan",
            padding=(1, 4),
        ),
        justify="center",
    )
    console.print()


def show_system_info(info: dict):
    """Muestra panel con información del sistema detectada."""
    table = Table(
        show_header=False,
        box=box.ROUNDED,
        title="Sistema detectado",
        title_style="bold blue",
        padding=(0, 2),
    )
    table.add_column("Campo", style="dim")
    table.add_column("Valor")
    table.add_column("Estado")

    table.add_row("OS", info["os"] or "No detectado", check_mark(bool(info["os"])))
    table.add_row("Usuario", info["user"], check_mark(True))
    table.add_row("Host", info["hostname"], check_mark(True))
    table.add_row(
        "Docker",
        info["docker"] or "No instalado",
        check_mark(bool(info["docker"])),
    )
    table.add_row("Python", info["python"], check_mark(True))
    table.add_row(
        "Bash",
        info["bash"] or "No detectado",
        check_mark(bool(info["bash"])),
    )
    table.add_row("Timezone", info["timezone"], check_mark(bool(info["timezone"])))

    console.print(table)
    console.print()


def ask_configuration(info: dict) -> dict:
    """Wizard interactivo de configuración."""
    config = {}

    # ── Navegación personalizada ───────────────────────────────────────────
    console.print(
        "\n  [dim]Configura el atajo de navegación a tu home.[/dim]"
        "\n  [dim]Ejemplo: comando 'adm' → variable $aadm → /home/aadm[/dim]\n"
    )

    user_home = str(Path.home())
    username = info["user"]

    config["nav_home"] = inquirer.text(
        message="Ruta de home:",
        default=user_home,
        validate=lambda x: Path(x).is_absolute() or "Debe ser ruta absoluta",
    ).execute()

    # Sugerir variable basada en el usuario (primeras 3-4 letras)
    default_var = username[:4] if len(username) >= 4 else username
    config["nav_var"] = inquirer.text(
        message=f"Variable (${default_var}):",
        default=default_var,
        validate=lambda x: x.isidentifier() or "Solo letras, números y _",
    ).execute()

    # Sugerir comando = primeras 3 letras del var
    default_cmd = config["nav_var"][:3]
    config["nav_cmd"] = inquirer.text(
        message=f"Comando ({default_cmd}):",
        default=default_cmd,
        validate=lambda x: x.isidentifier() or "Solo letras, números y _",
    ).execute()

    console.print(
        f"\n  [green]→[/green] [bold]{config['nav_cmd']}[/bold] llevará a "
        f"[cyan]{config['nav_home']}[/cyan] (variable: ${config['nav_var']})\n"
    )

    # Docker base
    config["docker_base"] = inquirer.text(
        message="Ruta datos Docker:",
        default=DOCKER_BASE_DEFAULT,
        validate=lambda x: Path(x).is_absolute() or "Debe ser ruta absoluta",
    ).execute()

    # Timezone
    config["timezone"] = inquirer.text(
        message="Timezone:",
        default=info["timezone"] or "UTC",
    ).execute()

    # Provider del agente
    config["provider"] = inquirer.select(
        message="Provider de IA para el agente:",
        choices=[
            {"name": "🟢 Gemini (recomendado — barato, solo API key)", "value": "gemini"},
            {"name": "🔵 Bedrock / Claude (mejor razonamiento, requiere AWS)", "value": "bedrock"},
            {"name": "⚪ Ollama (local, gratis, sin internet)", "value": "ollama"},
            {"name": "⏭️  Saltar (configurar después)", "value": "skip"},
        ],
        default="gemini",
    ).execute()

    # API key según provider
    if config["provider"] == "gemini":
        console.print(
            "\n  [dim]Obtener gratis en: https://aistudio.google.com/apikey[/dim]\n"
        )
        config["api_key"] = inquirer.secret(
            message="GOOGLE_API_KEY:",
            validate=lambda x: len(x) > 10 or "Key demasiado corta",
            transformer=lambda x: "•" * min(len(x), 20) + f" ({len(x)} chars)",
        ).execute()
    elif config["provider"] == "bedrock":
        console.print(
            "\n  [dim]Necesita: aws configure (con acceso a Bedrock)[/dim]\n"
        )
        config["aws_region"] = inquirer.text(
            message="AWS Region:",
            default="us-east-1",
        ).execute()
        config["api_key"] = ""
    elif config["provider"] == "ollama":
        config["ollama_host"] = inquirer.text(
            message="Ollama host:",
            default="http://localhost:11434",
        ).execute()
        config["api_key"] = ""
    else:
        config["api_key"] = ""

    # Configurar para root
    config["setup_root"] = inquirer.confirm(
        message="¿Configurar también para root?",
        default=True,
    ).execute()

    # Instalar dependencias Python
    config["install_python_deps"] = inquirer.confirm(
        message="¿Instalar dependencias Python del agente?",
        default=True,
    ).execute()

    return config


def show_summary(config: dict, info: dict):
    """Muestra resumen antes de instalar."""
    console.print()

    table = Table(
        title="Resumen de configuración",
        title_style="bold green",
        box=box.ROUNDED,
        padding=(0, 2),
    )
    table.add_column("Parámetro", style="bold")
    table.add_column("Valor")

    table.add_row("Ruta del proyecto", str(INSTALL_DIR))
    table.add_row("Navegación", f"{config['nav_cmd']} → ${config['nav_var']} → {config['nav_home']}")
    table.add_row("Datos Docker", config["docker_base"])
    table.add_row("Timezone", config["timezone"])
    table.add_row("Provider IA", config["provider"])
    if config.get("api_key"):
        table.add_row("API Key", "•" * 10 + " (configurada)")
    table.add_row("Config root", "Sí" if config["setup_root"] else "No")
    table.add_row("Deps Python", "Sí" if config["install_python_deps"] else "No")
    table.add_row("Usuario", info["user"])

    console.print(table)
    console.print()


def execute_installation(config: dict, info: dict):
    """Ejecuta la instalación con barra de progreso."""
    steps = []

    steps.append(("Copiando a /nas-dotfiles/", _step_copy))
    steps.append(("Generando configuración de navegación", _step_user_conf))
    steps.append(("Configurando ~/.bashrc", _step_bashrc_user))
    if config["setup_root"]:
        steps.append(("Configurando /root/.bashrc", _step_bashrc_root))
    steps.append(("Configurando variables de entorno", _step_env_vars))
    steps.append(("Verificando permisos", _step_permissions))
    if config["install_python_deps"]:
        steps.append(("Instalando dependencias Python", _step_python_deps))

    console.print()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console,
    ) as progress:
        task = progress.add_task("Instalando...", total=len(steps))

        for description, step_func in steps:
            progress.update(task, description=description)
            try:
                step_func(config, info)
                time.sleep(0.3)  # Visual feedback
            except Exception as e:
                console.print(f"\n  [red]❌ Error en '{description}': {e}[/red]")
                return False
            progress.advance(task)

    return True


# ─────────────────────────────────────────────────────────────────────────────
# Pasos de instalación
# ─────────────────────────────────────────────────────────────────────────────


def _step_copy(config: dict, info: dict):
    """Copia el repo a /nas-dotfiles/ si no está ahí."""
    if REPO_DIR == INSTALL_DIR:
        return  # Ya está en la ubicación correcta

    if INSTALL_DIR.exists():
        # Actualizar
        subprocess.run(
            ["rsync", "-a", "--delete", f"{REPO_DIR}/", f"{INSTALL_DIR}/"],
            check=True, capture_output=True,
        )
    else:
        # Copiar
        shutil.copytree(REPO_DIR, INSTALL_DIR)

    # Permisos
    user = info["user"]
    subprocess.run(
        ["chown", "-R", f"{user}:{user}", str(INSTALL_DIR)],
        capture_output=True,
    )


def _step_bashrc_user(config: dict, info: dict):
    """Configura ~/.bashrc del usuario."""
    _configure_bashrc(Path.home() / ".bashrc", config)


def _step_user_conf(config: dict, info: dict):
    """Genera .config/user.conf con la configuración de navegación."""
    conf_dir = INSTALL_DIR / ".config"
    conf_dir.mkdir(parents=True, exist_ok=True)
    conf_file = conf_dir / "user.conf"

    lines = [
        "# .config/user.conf — Configuración personalizada del usuario",
        f"# Generado por setup.py — {time.strftime('%Y-%m-%d %H:%M')}",
        "#",
        "# NAV_HOME: Ruta del directorio home (para navegación rápida)",
        "# NAV_VAR:  Nombre de la variable exportada (ej: $aadm, $nilo)",
        "# NAV_CMD:  Nombre del comando de navegación (ej: adm, nil)",
        "",
        f'NAV_HOME="{config["nav_home"]}"',
        f'NAV_VAR="{config["nav_var"]}"',
        f'NAV_CMD="{config["nav_cmd"]}"',
    ]

    conf_file.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _step_bashrc_root(config: dict, info: dict):
    """Configura /root/.bashrc."""
    root_bashrc = Path("/root/.bashrc")
    if root_bashrc.exists() or os.geteuid() == 0:
        _configure_bashrc(root_bashrc, config)


def _configure_bashrc(bashrc_path: Path, config: dict):
    """Agrega las líneas de nas-dotfiles a un .bashrc."""
    marker = "# nas-dotfiles shell framework"
    export_line = 'export NAS_DOTFILES="/nas-dotfiles"'
    source_line = 'source "$NAS_DOTFILES/shell/init.sh"'

    if not bashrc_path.exists():
        bashrc_path.touch()

    content = bashrc_path.read_text(encoding="utf-8")

    # Ya configurado?
    if export_line in content and source_line in content:
        return

    # Backup
    backup = bashrc_path.with_suffix(f".bak.{int(time.time())}")
    shutil.copy2(bashrc_path, backup)

    # Limpiar versiones anteriores
    lines = content.splitlines()
    lines = [
        l for l in lines
        if marker not in l
        and "NAS_DOTFILES" not in l
        and 'source "$NAS_DOTFILES/shell/init.sh"' not in l
        and "source ~/shell/init.sh" not in l
    ]

    # Agregar
    lines.append("")
    lines.append(marker)
    lines.append(export_line)
    lines.append(source_line)

    bashrc_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _step_env_vars(config: dict, info: dict):
    """Configura variables de entorno en un archivo .env del proyecto."""
    env_file = INSTALL_DIR / ".env.agent"
    env_lines = [
        "# Configuración del agente nas-dotfiles",
        f"# Generado por setup.py — {time.strftime('%Y-%m-%d %H:%M')}",
        "",
        f"NAS_AGENT_MODEL={config['provider']}" if config["provider"] != "skip" else "# NAS_AGENT_MODEL=gemini",
    ]

    if config.get("api_key"):
        env_lines.append(f"GOOGLE_API_KEY={config['api_key']}")
    if config.get("aws_region"):
        env_lines.append(f"AWS_REGION={config['aws_region']}")
    if config.get("ollama_host"):
        env_lines.append(f"OLLAMA_HOST={config['ollama_host']}")

    env_lines.extend([
        "",
        f"DOCKER_BASE={config['docker_base']}",
        f"TZ={config['timezone']}",
        "",
        "# Modos de seguridad (descomentar para activar)",
        "# NAS_AGENT_READONLY=1",
        "# NAS_AGENT_DRYRUN=1",
    ])

    env_file.write_text("\n".join(env_lines) + "\n", encoding="utf-8")
    os.chmod(env_file, 0o600)  # Solo el dueño puede leer (tiene API key)


def _step_permissions(config: dict, info: dict):
    """Verifica y corrige permisos."""
    svc_path = INSTALL_DIR / "docker" / "cli" / "svc.sh"
    if svc_path.exists():
        svc_path.chmod(0o755)

    setup_path = INSTALL_DIR / "setup.py"
    if setup_path.exists():
        setup_path.chmod(0o755)


def _step_python_deps(config: dict, info: dict):
    """Instala dependencias Python."""
    req_file = INSTALL_DIR / "requirements.txt"
    if req_file.exists():
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-q",
             "--break-system-packages", "-r", str(req_file)],
            capture_output=True,
            timeout=120,
        )


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────


def main():
    show_header()

    # Detectar sistema
    console.print("  [dim]Detectando sistema...[/dim]\n")
    info = detect_system()
    show_system_info(info)

    # Verificar requisitos mínimos
    if not info["docker"]:
        console.print(
            "  [yellow]⚠  Docker no detectado. El CLI (svc) no funcionará"
            " hasta que instales Docker.[/yellow]\n"
        )

    # Preguntar si continuar
    proceed = inquirer.confirm(
        message="¿Continuar con la configuración?",
        default=True,
    ).execute()

    if not proceed:
        console.print("\n  [dim]Cancelado. Nada se modificó.[/dim]\n")
        return

    # Wizard de configuración
    console.print()
    config = ask_configuration(info)

    # Resumen
    show_header()
    show_summary(config, info)

    # Confirmar
    confirm = inquirer.confirm(
        message="¿Instalar con esta configuración?",
        default=True,
    ).execute()

    if not confirm:
        console.print("\n  [dim]Cancelado.[/dim]\n")
        return

    # Ejecutar
    success = execute_installation(config, info)

    # Resultado
    console.print()
    if success:
        console.print(
            Panel(
                "[bold green]✅ Instalación completa[/bold green]\n\n"
                f"  Proyecto:  {INSTALL_DIR}\n"
                f"  Provider:  {config['provider']}\n"
                f"  Usuarios:  {info['user']}" + (" + root" if config["setup_root"] else "") + "\n\n"
                "[dim]Ejecuta:[/dim]\n"
                "  [cyan]source ~/.bashrc[/cyan]\n"
                "  [cyan]svc doctor[/cyan]\n"
                "  [cyan]python -m agent.nas_agent \"hola\"[/cyan]",
                border_style="green",
                padding=(1, 2),
            )
        )
    else:
        console.print(
            Panel(
                "[bold red]❌ Instalación incompleta[/bold red]\n\n"
                "Revisa los errores arriba.\n"
                "Podés reintentar: [cyan]python setup.py[/cyan]\n"
                "O usar el fallback: [cyan]./install.sh[/cyan]",
                border_style="red",
                padding=(1, 2),
            )
        )

    console.print()


if __name__ == "__main__":
    main()
