#!/bin/bash
# =============================================================================
# Instalación de Docker Engine en Debian
# Fuente: https://docs.docker.com/engine/install/debian/
# =============================================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo_info()    { echo -e "${GREEN}[INFO]${NC} $1"; }
echo_warn()    { echo -e "${YELLOW}[WARN]${NC} $1"; }
echo_error()   { echo -e "${RED}[ERROR]${NC} $1"; }

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
  if dpkg -l "$pkg" &>/dev/null; then
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

# 9. Agregar usuario al grupo docker
if [ -n "$SUDO_USER" ]; then
  echo_info "Agregando el usuario '$SUDO_USER' al grupo 'docker'..."
  usermod -aG docker "$SUDO_USER"
  echo_warn "Cierra sesión y vuelve a iniciarla para que el cambio surta efecto."
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
