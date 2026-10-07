#!/usr/bin/env bash
# Baja TODOS los servicios en orden inverso a las capas y apaga el NAS.
# Usa stop-order.sh (contraparte de boot-order.sh); ya no baja solo 3 servicios.
#
# El apagado escalonado se ejecuta DESACOPLADO de la sesión SSH para que cerrar
# la terminal (MobaXterm) no lo mate a medias con SIGHUP. Preferencia:
#   1) servicio systemd docker-shutdown-staged (si está instalado) -> PID 1, inmune a SIGHUP
#   2) fallback: setsid (nueva sesión propia, también sobrevive al cierre de la terminal)
# En ambos casos el `poweroff` final lo lanza systemd/PID 1 tras bajar los servicios.
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
: "${NAS_DOTFILES:=$(cd "$SCRIPT_DIR/../.." && pwd)}"

echo "Se bajarán todos los servicios (orden inverso) y se apagará el NAS."
echo "El apagado corre desacoplado: puedes cerrar la terminal sin interrumpirlo."
read -r -p "¿Continuar? Escribe 'apagar' para confirmar: " confirm
if [[ "$confirm" != "apagar" ]]; then
  echo "Cancelado."
  exit 0
fi

# Vía 1: servicio systemd oneshot (lo preferido). Baja los servicios bajo PID 1
# y, al terminar correctamente, apaga. --no-block devuelve el prompt de inmediato;
# el trabajo continúa aunque cierres la sesión.
if systemctl list-unit-files docker-shutdown-staged.service >/dev/null 2>&1 \
   && systemctl cat docker-shutdown-staged.service >/dev/null 2>&1; then
  echo "Lanzando apagado escalonado vía systemd (docker-shutdown-staged.service)..."
  echo "Progreso: journalctl -u docker-shutdown-staged.service -f   (o ${DOCKER_BASE:-/docker}/scripts/stop-order.log)"
  systemd-run --unit=nas-shutdown-now --description="NAS: apagado escalonado + poweroff" \
    /bin/bash -c 'systemctl start docker-shutdown-staged.service && systemctl poweroff'
  echo "Apagado en curso. Ya puedes cerrar la terminal."
  exit 0
fi

# Vía 2 (fallback): sin el servicio instalado, desacoplar con setsid para que
# sobreviva al cierre de la terminal. Instala el servicio para la próxima vez:
#   sudo install-shutdown-service.sh
echo "AVISO: docker-shutdown-staged.service no está instalado; usando fallback (setsid)."
echo "       Instálalo para la próxima vez: sudo $NAS_DOTFILES/shell/scripts/install-shutdown-service.sh"
echo "Progreso: ${DOCKER_BASE:-/docker}/scripts/stop-order.log"
setsid bash -c "'$SCRIPT_DIR/stop-order.sh' --down && poweroff" </dev/null \
  >>"${DOCKER_BASE:-/docker}/scripts/stop-order.log" 2>&1 &
echo "Apagado en curso (PID $!). Ya puedes cerrar la terminal."
