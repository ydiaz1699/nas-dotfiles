#!/usr/bin/env bash
# =============================================================================
# Instalación de Docker Engine en Debian
# Fuente: https://docs.docker.com/engine/install/debian/
#
# Opciones:
#   --dry-run              Simula la instalación sin modificar el sistema.
#   --log-file RUTA        Cambia la ruta del log.
#   --help                 Muestra esta ayuda.
# =============================================================================

set -Eeuo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

DRY_RUN=false
DOCKER_USER="${DOCKER_INSTALL_USER:-}"
OS_RELEASE_FILE="${DOCKER_INSTALL_OS_RELEASE:-/etc/os-release}"
APT_SOURCES_DIR="${DOCKER_INSTALL_APT_SOURCES_DIR:-/etc/apt/sources.list.d}"
APT_KEYRINGS_DIR="${DOCKER_INSTALL_APT_KEYRINGS_DIR:-/etc/apt/keyrings}"
LOG_FILE="${DOCKER_INSTALL_LOG:-}"
DOCKER_ALREADY_INSTALLED=false

usage() {
  cat <<'EOF'
Uso: install_docker.sh [opciones]

Instala Docker Engine desde el repositorio oficial de Docker para Debian.

Opciones:
  --dry-run              Simula las acciones sin modificar el sistema.
  --log-file RUTA        Guarda la salida en RUTA.
  --help                 Muestra esta ayuda.

Variables útiles para pruebas/simulación:
  DOCKER_INSTALL_OS_RELEASE       Archivo os-release alternativo.
  DOCKER_INSTALL_APT_SOURCES_DIR  Directorio alternativo de sources.list.d.
  DOCKER_INSTALL_APT_KEYRINGS_DIR Directorio alternativo de keyrings.
  DOCKER_INSTALL_USER              Usuario a seleccionar sin prompt.
  DOCKER_INSTALL_ASSUME_DOCKER_ABSENT Fuerza la ruta de instalación en pruebas.
  DOCKER_INSTALL_LOG               Ruta del log.
EOF
}

parse_args() {
  while (($# > 0)); do
    case "$1" in
      --dry-run)
        DRY_RUN=true
        shift
        ;;
      --log-file)
        if [[ $# -lt 2 || -z "$2" ]]; then
          echo_error "--log-file necesita una ruta."
          exit 2
        fi
        LOG_FILE="$2"
        shift 2
        ;;
      --help|-h)
        usage
        exit 0
        ;;
      *)
        echo_error "Opción desconocida: $1"
        usage >&2
        exit 2
        ;;
    esac
  done

  if [[ "${DOCKER_INSTALL_DRY_RUN:-0}" == "1" ]]; then
    DRY_RUN=true
  fi
}

echo_info()  { echo -e "${GREEN}[INFO]${NC} $1"; }
echo_warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
echo_error() { echo -e "${RED}[ERROR]${NC} $1"; }

setup_logging() {
  if [[ -z "$LOG_FILE" ]]; then
    if [[ "$DRY_RUN" == true ]]; then
      LOG_FILE="${TMPDIR:-/tmp}/docker-install-dry-run.log"
    else
      LOG_FILE="/var/log/docker-install.log"
    fi
  fi

  if [[ "$LOG_FILE" != "/dev/null" ]]; then
    mkdir -p "$(dirname "$LOG_FILE")"
    touch "$LOG_FILE"
    chmod 600 "$LOG_FILE"
  fi

  # tee conserva la salida en la terminal y en el log.
  exec > >(tee -a "$LOG_FILE") 2>&1
  echo_info "Log: $LOG_FILE"
  [[ "$DRY_RUN" == true ]] && echo_warn "Modo simulación: no se modificarán paquetes, repositorios, servicios ni usuarios."
}

print_command() {
  printf '  +'
  printf ' %q' "$@"
  printf '\n'
}

run_command() {
  if [[ "$DRY_RUN" == true ]]; then
    print_command "$@"
  else
    "$@"
  fi
}

run_optional_command() {
  if [[ "$DRY_RUN" == true ]]; then
    print_command "$@"
  elif ! "$@"; then
    echo_warn "El comando falló, pero se continuará: $*"
  fi
}

# Usuario que recibirá acceso al grupo docker.
# Prioridad: usuario solicitado, SUDO_USER, login actual y USER.
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

  if [[ -n "$DOCKER_USER" ]]; then
    if [[ "$DOCKER_USER" == "root" ]]; then
      echo_warn "root no necesita pertenecer al grupo docker."
      DOCKER_USER=""
      return 0
    fi
    if ! getent passwd "$DOCKER_USER" >/dev/null 2>&1; then
      echo_error "El usuario indicado no existe: $DOCKER_USER"
      return 1
    fi
    echo_info "Usuario seleccionado por configuración: $DOCKER_USER"
    return 0
  fi

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

package_installed() {
  if [[ "$1" == "docker-ce" && "${DOCKER_INSTALL_ASSUME_DOCKER_ABSENT:-0}" == "1" ]]; then
    return 1
  fi
  dpkg -s "$1" >/dev/null 2>&1
}

validate_operating_system() {
  local os=""
  local codename=""
  local pretty_name=""

  if [[ ! -r "$OS_RELEASE_FILE" ]]; then
    echo_error "No se pudo leer el archivo de sistema: $OS_RELEASE_FILE"
    return 1
  fi

  # shellcheck disable=SC1090
  source "$OS_RELEASE_FILE"
  os="${ID:-}"
  codename="${VERSION_CODENAME:-}"
  pretty_name="${PRETTY_NAME:-$os}"

  if [[ "$os" != "debian" ]]; then
    echo_error "Sistema no compatible: $pretty_name"
    echo_error "Este instalador configura exclusivamente el repositorio Docker para Debian."
    return 1
  fi

  case "$codename" in
    bullseye|bookworm|trixie)
      ;;
    "")
      echo_error "No se pudo detectar VERSION_CODENAME en $OS_RELEASE_FILE"
      echo_error "Versiones soportadas: bullseye (11), bookworm (12), trixie (13)"
      return 1
      ;;
    *)
      echo_error "Codename de Debian no soportado: $codename"
      echo_error "Versiones soportadas: bullseye (11), bookworm (12), trixie (13)"
      return 1
      ;;
  esac

  OS="$os"
  VERSION_CODENAME="$codename"
  PRETTY_NAME="$pretty_name"
  echo_info "Sistema detectado: $PRETTY_NAME ($VERSION_CODENAME)"
}

check_connectivity() {
  if [[ "$DRY_RUN" == true ]]; then
    print_command curl -fsSLI --max-time 10 https://download.docker.com/linux/debian/
    return 0
  fi

  echo_info "Comprobando conectividad con download.docker.com..."
  if ! curl -fsSLI --max-time 10 https://download.docker.com/linux/debian/ >/dev/null; then
    echo_error "No hay conectividad con download.docker.com"
    echo_error "Verifica DNS, red, proxy o firewall antes de continuar."
    return 1
  fi
}

disable_legacy_repo() {
  local legacy_repo="$APT_SOURCES_DIR/docker.list"
  local disabled_repo=""

  [[ -f "$legacy_repo" ]] || return 0

  if ! grep -Eq 'download\.docker\.com/linux/debian|docker-ce' "$legacy_repo"; then
    echo_info "Se conserva $legacy_repo: no parece ser el repositorio de Docker oficial."
    return 0
  fi

  disabled_repo="${legacy_repo}.disabled.$(date +%Y%m%d_%H%M%S)"
  echo_warn "Repositorio Docker legacy detectado: $legacy_repo"
  echo_info "Se desactivará como: $disabled_repo"
  run_command mv "$legacy_repo" "$disabled_repo"
}

write_docker_repo() {
  local repo_file="$APT_SOURCES_DIR/docker.sources"

  if [[ "$DRY_RUN" == true ]]; then
    echo_info "Se escribiría $repo_file con el repositorio Docker deb822 para $VERSION_CODENAME."
    return 0
  fi

  cat > "$repo_file" <<EOF
Types: deb
URIs: https://download.docker.com/linux/debian
Suites: ${VERSION_CODENAME}
Components: stable
Signed-By: ${APT_KEYRINGS_DIR}/docker.asc
EOF
}

install_docker() {
  local -a conflict_packages=(
    docker.io
    docker-compose
    docker-doc
    podman-docker
    containerd
    runc
  )
  local -a docker_packages=(
    docker-ce
    docker-ce-cli
    containerd.io
    docker-buildx-plugin
    docker-compose-plugin
  )
  local pkg

  if package_installed docker-ce; then
    DOCKER_ALREADY_INSTALLED=true
    echo_info "docker-ce ya está instalado; se omite la reinstalación de paquetes."
    return 0
  fi

  check_connectivity
  disable_legacy_repo

  echo_info "Eliminando paquetes conflictivos si existen..."
  for pkg in "${conflict_packages[@]}"; do
    if package_installed "$pkg"; then
      echo_warn "Eliminando paquete conflictivo: $pkg"
      run_optional_command apt remove -y "$pkg"
    fi
  done

  echo_info "Actualizando lista de paquetes e instalando dependencias..."
  run_command apt update
  run_command apt install -y ca-certificates curl

  echo_info "Configurando repositorio oficial de Docker..."
  run_command install -m 0755 -d "$APT_KEYRINGS_DIR" "$APT_SOURCES_DIR"
  run_command curl -fsSL https://download.docker.com/linux/debian/gpg -o "$APT_KEYRINGS_DIR/docker.asc"
  run_command chmod a+r "$APT_KEYRINGS_DIR/docker.asc"
  write_docker_repo

  echo_info "Actualizando lista de paquetes con el repositorio oficial..."
  run_command apt update

  echo_info "Instalando Docker Engine, CLI, containerd y plugins..."
  run_command apt install -y "${docker_packages[@]}"
}

start_and_verify_docker() {
  echo_info "Habilitando e iniciando el servicio Docker..."
  run_command systemctl enable docker
  run_command systemctl start docker

  echo_info "Verificando la instalación con la imagen hello-world..."
  run_command docker run --rm hello-world
}

configure_user_group() {
  if ! select_docker_user; then
    echo_error "No se pudo seleccionar un usuario válido."
    return 1
  fi

  if [[ -z "$DOCKER_USER" ]]; then
    echo_warn "Ningún usuario recibió acceso al grupo docker."
    echo_warn "Un administrador puede agregarlo después con: usermod -aG docker <usuario>"
    return 0
  fi

  echo_warn "El grupo docker permite administrar Docker con privilegios equivalentes a root en este host."

  if id -nG "$DOCKER_USER" | tr ' ' '\n' | grep -qx docker; then
    echo_info "El usuario '$DOCKER_USER' ya pertenece al grupo 'docker'."
    echo_info "Si la sesión actual aún no lo reconoce, ejecuta: newgrp docker"
  else
    if [[ "$DRY_RUN" == true ]]; then
      print_command usermod -aG docker "$DOCKER_USER"
    else
      usermod -aG docker "$DOCKER_USER"
    fi
    echo_warn "Cierra la sesión de '$DOCKER_USER' y vuelve a iniciarla para aplicar el cambio."
    echo_warn "Alternativamente, '$DOCKER_USER' puede ejecutar ahora: newgrp docker"
  fi
}

print_summary() {
  echo ""
  echo_info "=============================="
  if [[ "$DRY_RUN" == true ]]; then
    echo_info " Simulación terminada sin cambios"
  else
    echo_info " Docker instalado/validado exitosamente"
  fi
  echo_info "=============================="

  if [[ "$DRY_RUN" == true ]]; then
    echo_info "Estado real: no consultado (modo simulación)"
  elif systemctl is-active --quiet docker; then
    echo_info "Estado Docker: activo"
  else
    echo_error "Estado Docker: inactivo"
    return 1
  fi

  if [[ "$DRY_RUN" == true ]]; then
    echo_info "Versiones: se consultarían docker --version y docker compose version"
  else
    docker --version
    docker compose version
  fi

  echo_info "Log: $LOG_FILE"
  if [[ -n "$DOCKER_USER" ]]; then
    echo_info "Usuario Docker: $DOCKER_USER"
    echo_warn "Ese usuario debe abrir una nueva sesión o ejecutar: newgrp docker"
  fi
}

main() {
  parse_args "$@"

  if [[ "$DRY_RUN" != true && "$EUID" -ne 0 ]]; then
    echo_error "Este script debe ejecutarse como root o con sudo."
    exit 1
  fi

  setup_logging
  validate_operating_system

  if package_installed docker-ce; then
    DOCKER_ALREADY_INSTALLED=true
  fi

  install_docker
  start_and_verify_docker
  configure_user_group
  print_summary
}

main "$@"
