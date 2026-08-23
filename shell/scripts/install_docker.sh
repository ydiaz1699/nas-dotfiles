#!/usr/bin/env bash
# =============================================================================
# Instalación de Docker Engine en Debian
# Fuente: https://docs.docker.com/engine/install/debian/
# =============================================================================

set -Eeuo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo_info()    { echo -e "${GREEN}[INFO]${NC} $1"; }
echo_warn()    { echo -e "${YELLOW}[WARN]${NC} $1"; }
echo_error()   { echo -e "${RED}[ERROR]${NC} $1"; }

# Usuario que recibirá acceso al grupo docker.
# Prioridad de detección: usuario que invocó sudo, login actual y USER.
detect_docker_user() {
  local candidate
  local login_user=""

  login_user=$(logname 2>/dev/null || true)

  for candidate in "${SUDO_USER:-}" "$login_user" "${USER:-}"; do
    [[ -z "$candidate" || "$candidate" == "root" ]] && continue
    if getent passwd "$candidate" >/dev/null 2>&1; then
      printf '%s' "$candidate"
      return 0
    fi
  done

  return 1
}

select_docker_user() {
  local detected=""
  local answer=""
  local selected=""

  detected=$(detect_docker_user || true)

  if [[ -n "$detected" && -t 0 ]]; then
    read -r -p "Usuario detectado '$detected'. ¿Agregarlo al grupo docker? [Y/n]: " answer
    if [[ ! "$answer" =~ ^[nN]$ ]]; then
      DOCKER_USER="$detected"
      return 0
    fi
  elif [[ -n "$detected" ]]; then
    # En ejecuciones no interactivas, usar el usuario detectado.
    DOCKER_USER="$detected"
    echo_info "Usuario detectado automáticamente: $DOCKER_USER"
    return 0
  fi

  if [[ ! -t 0 ]]; then
    echo_warn "No se pudo seleccionar un usuario en modo no interactivo."
    return 0
  fi

  while true; do
    read -r -p "Escribe el usuario que usará Docker (Enter para omitir): " selected

    if [[ -z "$selected" ]]; then
      echo_warn "No se agregará ningún usuario al grupo docker."
      return 0
    fi

    if [[ "$selected" == "root" ]]; then
      echo_warn "root no necesita pertenecer al grupo docker."
      return 0
    fi

    if getent passwd "$selected" >/dev/null 2>&1; then
      DOCKER_USER="$selected"
      return 0
    fi

    echo_error "El usuario '$selected' no existe en este sistema."
  done
}

# 1. Verificar root
if [ "$EUID" -ne 0 ]; then
  echo_error "Este script debe ejecutarse como root o con sudo."
  exit 1
fi

# 2. Verificar SO
echo_info "Verificando sistema operativo..."

if [ -f /etc/os-release ]; then
  . /etc/os-release
  OS=$ID
  VERSION_CODENAME=${VERSION_CODENAME:-}
else
  echo_error "No se pudo detectar el sistema operativo."
  exit 1
fi

if [ "$OS" != "debian" ]; then
  echo_warn "Este script está diseñado para Debian. SO detectado: $OS"
  echo_warn "Continuando de todas formas..."
fi

if [ -z "$VERSION_CODENAME" ]; then
  echo_error "No se pudo detectar el codename de la versión de Debian."
  echo_error "Versiones soportadas: trixie (13), bookworm (12), bullseye (11)"
  exit 1
fi

echo_info "Sistema detectado: $PRETTY_NAME ($VERSION_CODENAME)"

# 3. Desinstalar paquetes conflictivos
echo_info "Eliminando paquetes conflictivos si existen..."

CONFLICT_PACKAGES="docker.io docker-compose docker-doc podman-docker containerd runc"

for pkg in $CONFLICT_PACKAGES; do
  if dpkg -s "$pkg" &>/dev/null; then
    echo_warn "Eliminando paquete conflictivo: $pkg"
    apt remove -y "$pkg" || true
  fi
done

# 4. Instalar dependencias
echo_info "Actualizando lista de paquetes e instalando dependencias..."
apt update
apt install -y ca-certificates curl

# 5. Configurar repositorio oficial de Docker
echo_info "Configurando repositorio oficial de Docker..."

install -m 0755 -d /etc/apt/keyrings

curl -fsSL https://download.docker.com/linux/debian/gpg \
  -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc

tee /etc/apt/sources.list.d/docker.sources <<EOF
Types: deb
URIs: https://download.docker.com/linux/debian
Suites: ${VERSION_CODENAME}
Components: stable
Signed-By: /etc/apt/keyrings/docker.asc
EOF

echo_info "Actualizando lista de paquetes con el nuevo repositorio..."
apt update

# 6. Instalar Docker Engine
echo_info "Instalando Docker Engine, CLI, containerd y plugins..."

apt install -y \
  docker-ce \
  docker-ce-cli \
  containerd.io \
  docker-buildx-plugin \
  docker-compose-plugin

# 7. Habilitar servicio
echo_info "Habilitando e iniciando el servicio Docker..."
systemctl enable docker
systemctl start docker

# 8. Verificar instalación
echo_info "Verificando la instalación con la imagen hello-world..."
docker run --rm hello-world

# 9. Agregar el usuario seleccionado al grupo docker
DOCKER_USER=""
select_docker_user

if [[ -n "$DOCKER_USER" ]]; then
  echo_warn "El grupo docker permite administrar Docker con privilegios equivalentes a root en este host."

  if id -nG "$DOCKER_USER" | tr ' ' '\n' | grep -qx docker; then
    echo_info "El usuario '$DOCKER_USER' ya pertenece al grupo 'docker'."
    echo_info "Si la sesión actual aún no lo reconoce, ejecuta: newgrp docker"
  else
    echo_info "Agregando el usuario '$DOCKER_USER' al grupo 'docker'..."
    usermod -aG docker "$DOCKER_USER"
    echo_warn "Cierra la sesión de '$DOCKER_USER' y vuelve a iniciarla para aplicar el cambio."
    echo_warn "Alternativamente, '$DOCKER_USER' puede ejecutar ahora: newgrp docker"
  fi
else
  echo_warn "Docker quedó instalado, pero ningún usuario recibió acceso al grupo docker."
  echo_warn "Un usuario administrador puede agregarlo después con: usermod -aG docker <usuario>"
fi

# 10. Resumen
echo ""
echo_info "=============================="
echo_info " Docker instalado exitosamente"
echo_info "=============================="
docker --version
docker compose version
echo ""
echo_info "Estado: sudo systemctl status docker"
echo_info "Docs: https://docs.docker.com/engine/install/linux-postinstall/"
