"""
Herramientas de backup y restore para servicios Docker.

Se integra con la lógica existente de svc backup/restore
del CLI de nas-dotfiles.
"""

import subprocess
from pathlib import Path
from strands.tools import tool

DOCKER_BASE = Path("/docker")
BACKUP_DIR = Path("/docker/backups")


def _run(cmd: str, timeout: int = 300) -> str:
    """Ejecuta un comando shell."""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True,
            text=True, timeout=timeout
        )
        output = result.stdout.strip()
        if result.returncode != 0 and result.stderr:
            output += f"\n⚠️ {result.stderr.strip()}"
        return output
    except subprocess.TimeoutExpired:
        return "ERROR: Timeout (backup puede tardar)"
    except Exception as e:
        return f"ERROR: {e}"



@tool
def backup_service(service_name: str) -> str:
    """Crea un backup de los volúmenes y bind mounts de un servicio.

    Usa la lógica del CLI existente (svc backup). Comprime datos
    en /docker/backups/ con timestamp. Rotación automática (últimos 5).

    Args:
        service_name: Nombre del servicio a respaldar.
                      Ejemplos: nextcloud, vaultwarden, grafana
    """
    # Verificar que el servicio existe
    svc_dir = DOCKER_BASE / service_name
    if not svc_dir.exists():
        return f"ERROR: Servicio '{service_name}' no encontrado en {DOCKER_BASE}"

    # Usar el CLI existente (svc backup)
    output = _run(f"svc backup {service_name}", timeout=600)

    if not output:
        return f"Backup de '{service_name}' ejecutado (sin salida)"

    return f"=== BACKUP: {service_name} ===\n\n{output}"


@tool
def restore_service(service_name: str, confirm: str = "no") -> str:
    """Lista backups disponibles o restaura un servicio desde backup.

    ⚠️ ACCIÓN DESTRUCTIVA: Sin confirm="si" solo lista los backups.
    Con confirm="si" restaura el más reciente.

    Args:
        service_name: Nombre del servicio a restaurar.
        confirm: "si" para ejecutar restauración del más reciente.
                 Cualquier otro valor solo lista backups disponibles.
    """
    if not BACKUP_DIR.exists():
        return f"ERROR: Directorio de backups no encontrado: {BACKUP_DIR}"

    # Listar backups del servicio
    backups = sorted(
        BACKUP_DIR.glob(f"{service_name}_*.tar.gz"),
        key=lambda f: f.stat().st_mtime,
        reverse=True,
    )

    if not backups:
        return f"No hay backups disponibles para '{service_name}'"

    lista = []
    for i, b in enumerate(backups[:10], 1):
        size_bytes = b.stat().st_size
        size_mb = size_bytes / (1024 * 1024)
        from datetime import datetime
        mtime = datetime.fromtimestamp(b.stat().st_mtime)
        lista.append(
            f"  {i}. {b.name} ({size_mb:.1f} MB) — {mtime:%Y-%m-%d %H:%M}"
        )

    lista_str = "\n".join(lista)

    if confirm.lower() not in ("si", "sí", "yes"):
        return (
            f"=== BACKUPS DISPONIBLES: {service_name} ===\n\n"
            f"{lista_str}\n\n"
            f"Total: {len(backups)} backup(s)\n\n"
            f"⚠️ Para restaurar el más reciente:\n"
            f"   restore_service('{service_name}', confirm='si')\n\n"
            f"ADVERTENCIA: Restaurar SOBREESCRIBE datos actuales."
        )

    # Restaurar el más reciente
    latest = backups[0]
    output = _run(
        f"svc restore {service_name} {latest}",
        timeout=600,
    )

    return (
        f"🔄 Restaurando '{service_name}' desde: {latest.name}\n\n"
        f"{output}"
    )


@tool
def list_backups() -> str:
    """Lista todos los backups existentes en /docker/backups/.

    Muestra: servicio, archivo, tamaño y fecha de cada backup.
    Agrupa por servicio.

    No requiere argumentos.
    """
    if not BACKUP_DIR.exists():
        return f"Directorio de backups no existe: {BACKUP_DIR}"

    backups = sorted(BACKUP_DIR.glob("*.tar.gz"), reverse=True)

    if not backups:
        return "No hay backups en /docker/backups/"

    # Agrupar por servicio
    por_servicio = {}
    total_size = 0

    for b in backups:
        # Nombre: servicio_tipo_nombre_timestamp.tar.gz
        parts = b.name.split("_")
        svc = parts[0] if parts else "desconocido"
        if svc not in por_servicio:
            por_servicio[svc] = []
        size = b.stat().st_size
        total_size += size
        por_servicio[svc].append((b.name, size))

    resultado = "=== BACKUPS EN /docker/backups/ ===\n\n"
    resultado += f"Total: {len(backups)} archivos "
    resultado += f"({total_size / (1024*1024):.1f} MB)\n\n"

    for svc, files in sorted(por_servicio.items()):
        resultado += f"  {svc} ({len(files)} backups):\n"
        for fname, size in files[:3]:
            resultado += f"    - {fname} ({size/(1024*1024):.1f} MB)\n"
        if len(files) > 3:
            resultado += f"    ... y {len(files)-3} más\n"
        resultado += "\n"

    return resultado
