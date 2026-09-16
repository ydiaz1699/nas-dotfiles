#!/usr/bin/env bash
# Baja TODOS los servicios en orden inverso a las capas y reinicia el NAS.
# Al volver, docker-boot-staged.service los levantará escalonadamente.
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Se bajarán todos los servicios (orden inverso) y se reiniciará el NAS."
read -r -p "¿Continuar? Escribe 'reiniciar' para confirmar: " confirm
if [[ "$confirm" != "reiniciar" ]]; then
  echo "Cancelado."
  exit 0
fi

"$SCRIPT_DIR/stop-order.sh" --down
echo "Servicios detenidos. Reiniciando..."
reboot
