"""
svc_py — Python CLI para administración de servicios Docker en el NAS.

Replicación completa de svc.sh con UI mejorada via Rich + InquirerPy.
Ambos CLIs (bash y python) coexisten — el usuario elige cuál usar.

Uso:
    python -m docker.svc_py <comando> [servicio] [args]

    # O via el alias svc (si NAS_CLI=python):
    svc health
    svc update-all
    svc menu
"""
