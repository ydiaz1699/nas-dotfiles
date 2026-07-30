"""
backup_manager.py — Gestión de backups de servicios Docker.

Centraliza: backup, restore, list_backups.
Los tools de backup_tools.py delegan aquí.
"""

from datetime import datetime
from pathlib import Path
from typing import List, Optional

from agent.core._result import ToolResult, Timer
from agent.tools._shell import (
    DOCKER_BASE,
    BACKUP_DIR,
    safe_run,
    validate_service_name,
    validated_service_path,
    readonly_guard,
    InvalidServiceName,
)


class BackupManager:
    """Gestor de backups de servicios Docker."""

    @staticmethod
    def backup(service_name: str) -> ToolResult:
        """Crea un backup del servicio."""
        blocked = readonly_guard("backup_service")
        if blocked:
            return ToolResult.error(blocked, tool_name="backup_service")

        try:
            svc_path = validated_service_path(service_name)
        except InvalidServiceName as e:
            return ToolResult.error(f"ERROR: {e}", tool_name="backup_service")

        if not svc_path.exists():
            return ToolResult.error(
                f"ERROR: Servicio '{service_name}' no encontrado en {DOCKER_BASE}",
                tool_name="backup_service",
            )

        with Timer() as t:
            output = safe_run(["svc", "backup", service_name], timeout=600)

        if not output:
            return ToolResult.ok(
                f"Backup de '{service_name}' ejecutado (sin salida)",
                data={"service": service_name, "action": "backup"},
                tool_name="backup_service",
                elapsed_ms=t.elapsed_ms,
            )

        return ToolResult.ok(
            f"=== BACKUP: {service_name} ===\n\n{output}",
            data={"service": service_name, "action": "backup", "output": output},
            tool_name="backup_service",
            elapsed_ms=t.elapsed_ms,
        )

    @staticmethod
    def restore(service_name: str, confirm: str = "no") -> ToolResult:
        """Lista backups o restaura el más reciente."""
        blocked = readonly_guard("restore_service")
        if blocked:
            return ToolResult.error(blocked, tool_name="restore_service")

        try:
            validate_service_name(service_name)
        except InvalidServiceName as e:
            return ToolResult.error(f"ERROR: {e}", tool_name="restore_service")

        if not BACKUP_DIR.exists():
            return ToolResult.error(
                f"ERROR: Directorio de backups no encontrado: {BACKUP_DIR}",
                tool_name="restore_service",
            )

        backups = sorted(
            BACKUP_DIR.glob(f"{service_name}_*.tar.gz"),
            key=lambda f: f.stat().st_mtime,
            reverse=True,
        )

        if not backups:
            return ToolResult.warn(
                f"No hay backups disponibles para '{service_name}'",
                data={"service": service_name, "backups_found": 0},
                tool_name="restore_service",
            )

        lista = []
        for i, b in enumerate(backups[:10], 1):
            size_mb = b.stat().st_size / (1024 * 1024)
            mtime = datetime.fromtimestamp(b.stat().st_mtime)
            lista.append(
                f"  {i}. {b.name} ({size_mb:.1f} MB) — {mtime:%Y-%m-%d %H:%M}"
            )

        lista_str = "\n".join(lista)

        if confirm.lower() not in ("si", "sí", "yes"):
            return ToolResult.warn(
                f"=== BACKUPS DISPONIBLES: {service_name} ===\n\n"
                f"{lista_str}\n\n"
                f"Total: {len(backups)} backup(s)\n\n"
                f"⚠️ Para restaurar el más reciente:\n"
                f"   restore_service('{service_name}', confirm='si')\n\n"
                f"ADVERTENCIA: Restaurar SOBREESCRIBE datos actuales.",
                data={"service": service_name, "backups_count": len(backups),
                      "confirmed": False},
                tool_name="restore_service",
            )

        latest = backups[0]
        with Timer() as t:
            output = safe_run(
                ["svc", "restore", service_name, str(latest)],
                timeout=600,
            )

        return ToolResult.ok(
            f"🔄 Restaurando '{service_name}' desde: {latest.name}\n\n{output}",
            data={"service": service_name, "backup_file": latest.name,
                  "confirmed": True, "output": output},
            tool_name="restore_service",
            elapsed_ms=t.elapsed_ms,
        )

    @staticmethod
    def list_all() -> ToolResult:
        """Lista todos los backups existentes."""
        if not BACKUP_DIR.exists():
            return ToolResult.warn(
                f"Directorio de backups no existe: {BACKUP_DIR}",
                tool_name="list_backups",
            )

        backups = sorted(BACKUP_DIR.glob("*.tar.gz"), reverse=True)

        if not backups:
            return ToolResult.warn(
                "No hay backups en /docker/backups/",
                tool_name="list_backups",
            )

        por_servicio: dict = {}
        total_size = 0

        for b in backups:
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

        return ToolResult.ok(
            resultado,
            data={"total_backups": len(backups),
                  "total_size_mb": round(total_size / (1024*1024), 1),
                  "services": list(por_servicio.keys())},
            tool_name="list_backups",
        )
