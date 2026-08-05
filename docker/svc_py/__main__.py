"""Entry point: python -m docker.svc_py"""
from rich.traceback import install as install_rich_traceback

# Rich traceback: errores con colores, código resaltado, variables locales
install_rich_traceback(show_locals=True, width=100)

from docker.svc_py.app import app

if __name__ == "__main__":
    app()
