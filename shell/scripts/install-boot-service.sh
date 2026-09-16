#!/usr/bin/env bash
# Genera e instala docker-boot-staged.service con las rutas reales de esta
# instalación (NAS_DOTFILES y DOCKER_BASE), a partir de la plantilla del repo.
#
# Uso:
#   sudo NAS_DOTFILES=/nas-dotfiles DOCKER_BASE=/docker \
#     /nas-dotfiles/shell/scripts/install-boot-service.sh [--enable]
#
# Sin --enable solo instala el unit file y hace daemon-reload; no lo habilita
# ni lo arranca (para poder probar boot-order.sh a mano antes).
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Rutas reales de la instalación: se toman del entorno; si no, se deducen.
: "${NAS_DOTFILES:=$REPO_ROOT}"
: "${DOCKER_BASE:=${dkco:-/docker}}"

TEMPLATE="$NAS_DOTFILES/systemd/docker-boot-staged.service.template"
UNIT_DEST="/etc/systemd/system/docker-boot-staged.service"
ENABLE=0

for arg in "$@"; do
  case "$arg" in
    --enable) ENABLE=1 ;;
    -h|--help)
      grep '^#' "$0" | sed 's/^# \{0,1\}//'
      exit 0 ;;
    *) echo "Argumento no reconocido: $arg" >&2; exit 2 ;;
  esac
done

[[ -f "$TEMPLATE" ]] || { echo "ERROR: no existe la plantilla $TEMPLATE" >&2; exit 1; }
[[ -x "$NAS_DOTFILES/shell/scripts/boot-order.sh" ]] || \
  echo "AVISO: $NAS_DOTFILES/shell/scripts/boot-order.sh no es ejecutable; ejecuta chmod +x." >&2

if [[ "$(id -u)" -ne 0 ]]; then
  echo "ERROR: instalar la unidad requiere root (usa sudo)." >&2
  exit 1
fi

# Sustituir placeholders sin usar sed sobre rutas con '/': se escapa cada valor.
render() {
  local nd="${NAS_DOTFILES//&/\\&}" db="${DOCKER_BASE//&/\\&}"
  sed -e "s|{{NAS_DOTFILES}}|$nd|g" -e "s|{{DOCKER_BASE}}|$db|g" "$TEMPLATE"
}

echo "Instalando docker-boot-staged.service"
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

if ((ENABLE == 1)); then
  systemctl enable docker-boot-staged.service
  echo "  -> habilitado (arrancará en el próximo boot)"
else
  echo "  Unidad instalada pero NO habilitada."
  echo "  Prueba primero: NAS_CLI=bash $NAS_DOTFILES/shell/scripts/boot-order.sh"
  echo "  Luego habilítala: sudo systemctl enable docker-boot-staged.service"
fi
