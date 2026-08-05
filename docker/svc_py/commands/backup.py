"""
backup.py — Backup y restore con Rich progress + InquirerPy selector.
"""

from __future__ import annotations

import subprocess
from datetime import datetime
from pathlib import Path
from typing import List

import typer
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn

from docker.svc_py.config import BACKUP_DIR, BACKUP_KEEP
from docker.svc_py.core.discovery import svc_compose_file
from docker.svc_py.core.docker import compose_output, compose_run, docker_run
from docker.svc_py.ui import console, error, info, success, warn

app = typer.Typer()


def _get_volumes(compose_file: Path) -> List[str]:
    """Obtiene volúmenes nombrados de un compose file."""
    out, rc = compose_output(compose_file, ["config", "--volumes"])
    if rc != 0 or not out:
        return []
    return [v.strip() for v in out.splitlines() if v.strip()]


def _get_bind_mounts(compose_file: Path) -> List[str]:
    """Obtiene bind mounts de un compose file."""
    out, rc = compose_output(compose_file, ["config"])
    if rc != 0 or not out:
        return []

    mounts = []
    in_volumes = False
    for line in out.splitlines():
        stripped = line.strip()
        if stripped.startswith("volumes:"):
            in_volumes = True
            continue
        if in_volumes:
            if stripped.startswith("- ") and ":" in stripped:
                src = stripped.lstrip("- ").split(":")[0].strip("'\"")
                if src.startswith("/"):
                    mounts.append(src)
            elif not stripped.startswith("-") and stripped and not stripped.startswith("#"):
                in_volumes = False

    return list(set(mounts))


def _rotate_backups(service: str) -> None:
    """Elimina backups viejos según BACKUP_KEEP."""
    pattern = f"{service}_*.tar.gz"
    backups = sorted(BACKUP_DIR.glob(pattern), key=lambda f: f.stat().st_mtime, reverse=True)
    if len(backups) > BACKUP_KEEP:
        for old in backups[BACKUP_KEEP:]:
            old.unlink()
            console.print(f"    [dim]Rotado: {old.name}[/dim]")


@app.command("backup")
def backup(service: str):
    """Backup de volúmenes + bind mounts con progress bar."""
    cf = svc_compose_file(service)
    if cf is None:
        error(f"Servicio '{service}' no encontrado")
        raise typer.Exit(1)

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    volumes = _get_volumes(cf)
    bind_mounts = _get_bind_mounts(cf)

    if not volumes and not bind_mounts:
        warn(f"'{service}' no tiene volúmenes ni bind mounts")
        raise typer.Exit(0)

    items = [(f"vol:{v}", v) for v in volumes] + [(f"bind:{m}", m) for m in bind_mounts]

    console.print(f"\n  [cyan]Backup de '{service}'[/cyan] → {BACKUP_DIR}\n")

    ok = 0
    fail = 0
    project = cf.parent.name

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("{task.completed}/{task.total}"),
        console=console,
    ) as progress:
        task = progress.add_task("Respaldando...", total=len(items))

        for item_type, item_name in items:
            progress.update(task, description=f"  {item_type}")

            if item_type.startswith("vol:"):
                full_vol = f"{project}_{item_name}"
                out_file = BACKUP_DIR / f"{service}_vol_{item_name}_{timestamp}.tar.gz"

                # Intentar con nombre completo, luego sin prefijo
                vol_to_use = full_vol
                check = docker_run(["volume", "inspect", full_vol])
                if check.returncode != 0:
                    check2 = docker_run(["volume", "inspect", item_name])
                    if check2.returncode == 0:
                        vol_to_use = item_name
                    else:
                        fail += 1
                        progress.advance(task)
                        continue

                result = docker_run([
                    "run", "--rm",
                    "-v", f"{vol_to_use}:/data:ro",
                    "-v", f"{BACKUP_DIR}:/backup",
                    "alpine", "tar", "czf", f"/backup/{out_file.name}", "-C", "/data", ".",
                ], capture=True)

                if result.returncode == 0:
                    ok += 1
                else:
                    fail += 1

            elif item_type.startswith("bind:"):
                mount_path = Path(item_name)
                if not mount_path.is_dir():
                    fail += 1
                    progress.advance(task)
                    continue

                mount_name = mount_path.name
                out_file = BACKUP_DIR / f"{service}_bind_{mount_name}_{timestamp}.tar.gz"

                result = subprocess.run(
                    ["tar", "czf", str(out_file), "-C", str(mount_path), "."],
                    capture_output=True, check=False,
                )
                if result.returncode == 0:
                    ok += 1
                else:
                    fail += 1

            progress.advance(task)

    # Rotación
    _rotate_backups(service)

    console.print()
    if fail == 0:
        success(f"{ok} archivos guardados en {BACKUP_DIR}")
    else:
        success(f"{ok} OK")
        error(f"{fail} con error")
    console.print()


@app.command("restore")
def restore(service: str, archive: str = typer.Argument(None, help="Archivo backup")):
    """Restaurar servicio desde backup (selector interactivo)."""
    cf = svc_compose_file(service)
    if cf is None:
        error(f"Servicio '{service}' no encontrado")
        raise typer.Exit(1)

    # Listar backups disponibles
    pattern = f"{service}_*.tar.gz"
    backups = sorted(BACKUP_DIR.glob(pattern), key=lambda f: f.stat().st_mtime, reverse=True)

    if not backups:
        error(f"No hay backups para '{service}'")
        raise typer.Exit(1)

    # Si no se especificó archivo, mostrar selector
    if archive is None:
        try:
            from InquirerPy import inquirer

            choices = []
            for b in backups:
                size_mb = b.stat().st_size / (1024 * 1024)
                label = f"{b.name}  ({size_mb:.1f} MB)"
                choices.append({"name": label, "value": str(b)})

            archive = inquirer.select(
                message="Selecciona backup a restaurar:",
                choices=choices,
            ).execute()

        except ImportError:
            # Sin InquirerPy: mostrar lista
            console.print(f"\n  [blue]Backups para '{service}':[/blue]\n")
            for i, b in enumerate(backups, 1):
                size_mb = b.stat().st_size / (1024 * 1024)
                console.print(f"    {i}) {b.name}  ({size_mb:.1f} MB)")
            console.print(f"\n  Uso: svc restore {service} <archivo.tar.gz>\n")
            raise typer.Exit(0)

    # Validar archivo
    archive_path = Path(archive)
    if not archive_path.exists():
        archive_path = BACKUP_DIR / archive
    if not archive_path.exists():
        error(f"Archivo no encontrado: {archive}")
        raise typer.Exit(1)

    # Confirmación
    console.print(f"\n  [bold yellow]ATENCION: Esto sobreescribirá datos.[/bold yellow]")
    console.print(f"  Archivo: {archive_path.name}")
    console.print(f"  Servicio: {service}\n")

    if not typer.confirm("  ¿Continuar?", default=False):
        console.print("  [dim]Cancelado.[/dim]")
        raise typer.Exit(0)

    fname = archive_path.name

    if "_vol_" in fname:
        # Extraer nombre del volumen
        import re
        vol_match = re.search(rf"^{service}_vol_(.+?)_\d{{8}}_\d{{6}}\.tar\.gz$", fname)
        if not vol_match:
            error("No se pudo determinar el volumen del backup.")
            raise typer.Exit(1)

        vol_name = vol_match.group(1)
        project = cf.parent.name
        full_vol = f"{project}_{vol_name}"

        info(f"Restaurando volumen: {full_vol}")

        # Detener servicio
        compose_run(cf, ["stop"], capture=True, check=False)

        # Restaurar
        docker_run([
            "run", "--rm",
            "-v", f"{full_vol}:/data",
            "-v", f"{archive_path.parent}:/backup:ro",
            "alpine", "sh", "-c",
            f"rm -rf /data/* && tar xzf /backup/{archive_path.name} -C /data",
        ], capture=False)

        success("Volumen restaurado.")

        if typer.confirm("  ¿Levantar servicio?", default=True):
            compose_run(cf, ["up", "-d"], capture=False, check=False)

    elif "_bind_" in fname:
        info("Backup de bind mount — necesitas especificar destino.")
        dest = typer.prompt("  Path destino")
        dest_path = Path(dest)
        if not dest_path.is_dir():
            error(f"Path inválido: {dest}")
            raise typer.Exit(1)

        subprocess.run(["tar", "xzf", str(archive_path), "-C", str(dest_path)], check=False)
        success(f"Restaurado en {dest_path}")
    else:
        error("No se pudo determinar el tipo de backup.")
        info(f"Extraer manualmente: tar xzf {archive_path} -C /destino/")

    console.print()
