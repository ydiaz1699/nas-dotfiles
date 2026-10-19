#!/usr/bin/env bash
# tool-lookup.sh — busca una herramienta del framework nas-dotfiles por nombre
# dentro del SKILL.md de esta skill portable y muestra su(s) fila(s).
#
# Uso:
#   bash scripts/tool-lookup.sh bat
#   bash scripts/tool-lookup.sh "svc doctor"
#
# Sin argumentos lista todas las herramientas detectadas en las tablas.

set -euo pipefail

# Localizar el SKILL.md relativo a este script (funciona desde cualquier cwd)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_MD="$SCRIPT_DIR/../SKILL.md"

if [ ! -f "$SKILL_MD" ]; then
    echo "ERROR: no encuentro SKILL.md junto al script ($SKILL_MD)" >&2
    exit 1
fi

query="${1:-}"

if [ -z "$query" ]; then
    echo "Herramientas documentadas (primera columna de cada tabla):"
    # Extrae el contenido de la primera celda de cada fila de tabla markdown
    grep -E '^\| `' "$SKILL_MD" \
        | sed -E 's/^\| (`[^|]*`).*/\1/' \
        | sort -u
    exit 0
fi

echo "== Resultado para: '$query' =="
# -F: literal; -i: case-insensitive. Muestra las filas de tabla que lo contienen.
if ! grep -iF -- "$query" "$SKILL_MD" | grep -E '^\|'; then
    echo "No está en el índice. Revisa docs/tools-index.md o"
    echo "docker-nas/references/entorno.md | svc.md en el repo nas-dotfiles."
    exit 1
fi
