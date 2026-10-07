#!/usr/bin/env bash
# Genera e instala docker-shutdown-staged.service con las rutas reales de esta
# instalación (NAS_DOTFILES y DOCKER_BASE), a partir de la plantilla del repo.
#
# Gemelo de install-boot-service.sh. El servicio ejecuta el apagado escalonado
# (stop-order.sh --down) FUERA de la sesión SSH, bajo PID 1, para que cerrar la
# terminal (SIGHUP) no interrumpa el apagado a medias.
#
# Uso:
#   sudo NAS_DOTFILES=/nas-dotfiles DOCKER_BASE=/docker \
#     /nas-dotfiles/shell/scripts/install-shutdown-service.sh
#
# El servicio es de tipo oneshot y lo arrancan bajo demanda stop-all.sh /
# restart-all.sh (no se habilita en el boot; no tiene sentido ejecutarlo al arrancar).
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Rutas reales de la instalación: se toman del entorno; si no, se deducen.
: "${NAS_DOTFILES:=$REPO_ROOT}"
: "${DOCKER_BASE:=${dkco:-/docker}}"

TEMPLATE="$NAS_DOTFILES/systemd/docker-shutdown-staged.service.template"
UNIT_DEST="/etc/systemd/system/docker-shutdown-staged.service"

for arg in "$@"; do
  case "$arg" in
    -h|--help)
      grep '^#' "$0" | sed 's/^# \{0,1\}//'
      exit 0 ;;
    *) echo "Argumento no reconocido: $arg" >&2; exit 2 ;;
  esac
done

[[ -f "$TEMPLATE" ]] || { echo "ERROR: no existe la plantilla $TEMPLATE" >&2; exit 1; }
[[ -x "$NAS_DOTFILES/shell/scripts/stop-order.sh" ]] || \
  echo "AVISO: $NAS_DOTFILES/shell/scripts/stop-order.sh no es ejecutable; ejecuta chmod +x." >&2

if [[ "$(id -u)" -ne 0 ]]; then
  echo "ERROR: instalar la unidad requiere root (usa sudo)." >&2
  exit 1
fi

# Sustituir placeholders sin usar sed sobre rutas con '/': se escapa cada valor.
render() {
  local nd="${NAS_DOTFILES//&/\\&}" db="${DOCKER_BASE//&/\\&}"
  sed -e "s|{{NAS_DOTFILES}}|$nd|g" -e "s|{{DOCKER_BASE}}|$db|g" "$TEMPLATE"
}

echo "Instalando docker-shutdown-staged.service"
echo "  NAS_DOTFILES = $NAS_DOTFILES"
echo "  DOCKER_BASE  = $DOCKER_BASE"

render > "$UNIT_DEST"
echo "  -> escrito en $UNIT_DEST"

# Verificar que no quedaron placeholders sin sustituir.
if grep -q '{{' "$UNIT_DEST"; then
  echo "ERROR: quedaron placeholders sin sustituir en $UNIT_DEST" >&2
  grep '{{' "$UNIT_DEST" >&2
  exit 1
fi

systemctl daemon-reload
echo "  -> systemctl daemon-reload OK"
echo "  Unidad instalada. La usan stop-all.sh / restart-all.sh automáticamente."
echo "  (No se habilita en el boot: es un oneshot bajo demanda.)"
