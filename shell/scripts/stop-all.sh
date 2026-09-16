#!/usr/bin/env bash
# Baja TODOS los servicios en orden inverso a las capas y apaga el NAS.
# Usa stop-order.sh (contraparte de boot-order.sh); ya no baja solo 3 servicios.
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Se bajarán todos los servicios (orden inverso) y se apagará el NAS."
read -r -p "¿Continuar? Escribe 'apagar' para confirmar: " confirm
if [[ "$confirm" != "apagar" ]]; then
  echo "Cancelado."
  exit 0
fi

"$SCRIPT_DIR/stop-order.sh" --down
echo "Servicios detenidos. Apagando..."
poweroff
