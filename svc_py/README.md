# svc_py — Python CLI para Docker Services

CLI alternativa a `svc.sh` con UI mejorada via Rich + InquirerPy.

## Instalación

```bash
pip install typer[all] rich InquirerPy pyyaml
```

## Activar como CLI default

```bash
# En ~/.bashrc o .config/user.conf:
export NAS_CLI=python

# O temporalmente:
NAS_CLI=python svc health
```

## Comandos disponibles

Mismos que `svc.sh` — misma API, mejor UI:

| Comando | Mejora vs bash |
|---------|---------------|
| `svc lista` | Rich table con colores |
| `svc health` | Rich panel con uptime/restarts |
| `svc doctor` | Spinners + resumen coloreado |
| `svc watch` | Rich Live (sin clear) |
| `svc update-all` | InquirerPy checkboxes + progress bar |
| `svc menu` | InquirerPy (reemplaza fzf) |
| `svc backup <svc>` | Rich progress bar |
| `svc restore <svc>` | InquirerPy selector de archivos |
| `svc create` | InquirerPy wizard guiado |
| `svc diff <svc>` | Rich syntax highlight |
| `svc port-map` | Rich table + conflictos |
| `svc net` | Rich tree visual |
| `svc env <svc>` | Syntax highlighting |
| `svc up/down/start/stop/...` | Confirmaciones bonitas |

## Ejecutar directamente

```bash
# Sin configurar NAS_CLI:
cd /nas-dotfiles && python3 -m docker.svc_py health
cd /nas-dotfiles && python3 -m docker.svc_py menu
```

## Diferencias con bash CLI

| Aspecto | Bash | Python |
|---------|------|--------|
| Dependencias | Ninguna | pip install |
| Arranque | 0ms | ~200ms |
| Menú | fzf (si instalado) | InquirerPy (siempre) |
| Output | printf + ANSI | Rich (tablas, panels) |
| Tests | Difícil | pytest |
| Multi-select | No | InquirerPy checkbox |
| Progress bar | No | Rich progress |
| Live update | clear + redraw | Rich Live |

## Notas

- Ambos CLIs coexisten — no se reemplaza `svc.sh`
- Python CLI reutiliza la misma estructura de `/docker/` (DOCKER_BASE)
- InquirerPy es opcional — sin él, los comandos funcionan con prompts simples
- El passthrough genérico a docker compose funciona para cualquier comando no mapeado
