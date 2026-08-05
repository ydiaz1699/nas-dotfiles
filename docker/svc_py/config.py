"""
config.py — Configuración centralizada del CLI.

Lee variables de entorno con defaults sensatos.
"""

import os
from pathlib import Path

# Base donde viven los servicios Docker (datos)
DOCKER_BASE = Path(os.environ.get("DOCKER_BASE", "/docker"))

# Directorio de backups
BACKUP_DIR = Path(os.environ.get("BACKUP_DIR", "/docker/backups"))

# Cantidad de backups a conservar por servicio (rotación)
BACKUP_KEEP = int(os.environ.get("BACKUP_KEEP", "5"))

# Intervalo de refresh para watch (segundos)
WATCH_INTERVAL = int(os.environ.get("SVC_WATCH_INTERVAL", "5"))

# NAS_DOTFILES root
NAS_DOTFILES = Path(os.environ.get("NAS_DOTFILES", str(Path.home() / "nas-dotfiles")))

# Nombres de compose file válidos (orden de prioridad)
COMPOSE_FILENAMES = [
    "docker-compose.yml",
    "docker-compose.yaml",
    "compose.yml",
    "compose.yaml",
]
