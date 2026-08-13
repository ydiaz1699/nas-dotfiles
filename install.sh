#!/usr/bin/env bash
# install.sh — Instalador bash interactivo (fallback sin Python)
#
# Se ejecuta directamente o como fallback de ./setup cuando no hay Python.
# Hace lo mismo que setup.py pero con interfaz bash básica.
set -e

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
INSTALL_DIR="/nas-dotfiles"

# ── Colores ────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GRN='\033[0;32m'
BLU='\033[0;34m'
CYN='\033[0;36m'
YLW='\033[1;33m'
DIM='\033[0;37m'
BOLD='\033[1m'
NC='\033[0m'

# ── Header ─────────────────────────────────────────────────────────────────
echo ""
echo -e "${CYN}  ╭──────────────────────────────────────────────╮${NC}"
echo -e "${CYN}  │${NC}     🖥️  ${BLU}nas-dotfiles — Instalación${NC}           ${CYN}│${NC}"
echo -e "${CYN}  │${NC}     ${DIM}Modo: bash interactivo${NC}                   ${CYN}│${NC}"
echo -e "${CYN}  ╰──────────────────────────────────────────────╯${NC}"
echo ""

# ── [0/7] Pre-requisitos del sistema ───────────────────────────────────────
echo -e "  ${BOLD}[0/7] Verificando pre-requisitos${NC}"
echo ""

_check_install_pkg() {
  local pkg="$1"
  local desc="$2"
  if dpkg -l "$pkg" 2>/dev/null | grep -q "^ii"; then
    echo -e "    ${GRN}✓${NC} $desc ($pkg)"
  else
    echo -e "    ${YLW}⚠${NC} $desc no instalado — instalando $pkg..."
    apt-get install -y -q "$pkg" >/dev/null 2>&1 || sudo apt-get install -y -q "$pkg" >/dev/null 2>&1 || {
      echo -e "    ${RED}✗${NC} No se pudo instalar $pkg"
      echo -e "    ${DIM}   Ejecutar manualmente: apt install $pkg${NC}"
    }
  fi
}

# Python + pip + venv (necesarios para el agente)
if command -v python3 &>/dev/null; then
  PY_MAJOR_MINOR=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
  _check_install_pkg "python3-pip" "pip"
  _check_install_pkg "python3.${PY_MAJOR_MINOR##*.}-venv" "venv (python3.${PY_MAJOR_MINOR##*.}-venv)"
else
  echo -e "    ${DIM}~ Python no instalado — el agente no estará disponible${NC}"
fi

# Herramientas opcionales
_check_install_pkg "eza" "eza (reemplazo de ls)"
command -v fzf &>/dev/null || _check_install_pkg "fzf" "fzf (menú interactivo)"
echo ""
echo -e "  ${BOLD}[1/7] Detectando sistema${NC}"
echo ""

_detect() {
  local label="$1" cmd="$2" fallback="$3"
  local result
  result=$(eval "$cmd" 2>/dev/null) || result="$fallback"
  printf "    %-12s %s\n" "$label" "$result"
  echo "$result"
}

SYS_USER=$(whoami)
SYS_HOST=$(hostname 2>/dev/null || echo "nas")
SYS_OS=$(grep PRETTY_NAME /etc/os-release 2>/dev/null | cut -d'"' -f2 || echo "Linux")
SYS_DOCKER=$(docker --version 2>/dev/null | cut -d',' -f1 | sed 's/Docker version /v/' || echo "")
SYS_BASH=$(bash --version 2>/dev/null | head -1 | grep -oP 'version \K[0-9.]+' || echo "?")
SYS_TZ=$(timedatectl show -p Timezone --value 2>/dev/null || cat /etc/timezone 2>/dev/null || echo "UTC")

echo -e "    ${DIM}OS${NC}          $SYS_OS"
echo -e "    ${DIM}Usuario${NC}     $SYS_USER"
echo -e "    ${DIM}Host${NC}        $SYS_HOST"
if [[ -n "$SYS_DOCKER" ]]; then
  echo -e "    ${DIM}Docker${NC}      ${GRN}$SYS_DOCKER ✓${NC}"
else
  echo -e "    ${DIM}Docker${NC}      ${RED}no instalado ✗${NC}"
fi
echo -e "    ${DIM}Bash${NC}        $SYS_BASH"
echo -e "    ${DIM}Timezone${NC}    $SYS_TZ"
echo ""

# ── [2/7] Preguntar configuración ─────────────────────────────────────────
echo -e "  ${BOLD}[2/7] Configuración${NC}"
echo ""

# Navegación personalizada
echo -e "    ${BOLD}Navegación rápida${NC}"
echo -e "    ${DIM}Configura un atajo para ir a tu carpeta personal.${NC}"
echo -e "    ${DIM}Ejemplo: escribes 'adm' → vas a /home/aadm${NC}"
echo ""

if [[ "$SYS_USER" == "root" ]]; then
  DEFAULT_NAV_HOME="/root"
  DEFAULT_NAV_VAR="adm"
  DEFAULT_NAV_CMD="adm"
else
  DEFAULT_NAV_HOME="/home/$SYS_USER"
  DEFAULT_NAV_VAR="${SYS_USER:0:4}"
  DEFAULT_NAV_CMD="${SYS_USER:0:3}"
fi

read -r -p "    Carpeta destino [$DEFAULT_NAV_HOME]: " INPUT_NAV_HOME
NAV_HOME="${INPUT_NAV_HOME:-$DEFAULT_NAV_HOME}"

echo -e "    ${DIM}Nombre de la variable (sin \$, solo letras):${NC}"
read -r -p "    Variable [$DEFAULT_NAV_VAR]: " INPUT_NAV_VAR
NAV_VAR="${INPUT_NAV_VAR:-$DEFAULT_NAV_VAR}"

echo -e "    ${DIM}Comando que escribes para navegar:${NC}"
read -r -p "    Comando [$DEFAULT_NAV_CMD]: " INPUT_NAV_CMD
NAV_CMD="${INPUT_NAV_CMD:-$DEFAULT_NAV_CMD}"

echo ""
echo -e "    ${GRN}✓${NC} Escribes ${BOLD}${NAV_CMD}${NC} → vas a ${CYN}${NAV_HOME}${NC} (variable: \$${NAV_VAR})"
echo ""

# Docker base
read -r -p "    Ruta datos Docker [/docker]: " INPUT_DOCKER
DOCKER_BASE="${INPUT_DOCKER:-/docker}"

# Timezone
read -r -p "    Timezone [$SYS_TZ]: " INPUT_TZ
TIMEZONE="${INPUT_TZ:-$SYS_TZ}"

# Provider
echo ""
echo -e "    ${DIM}Providers disponibles:${NC}"
echo -e "      ${GRN}1)${NC} Gemini  — barato, solo API key (recomendado)"
echo -e "      ${BLU}2)${NC} Bedrock — Claude, mejor razonamiento, requiere AWS"
echo -e "      ${DIM}3)${NC} Ollama  — local, gratis, sin internet"
echo -e "      ${DIM}4)${NC} Saltar  — configurar después"
echo ""
read -r -p "    Provider [1]: " INPUT_PROVIDER
case "${INPUT_PROVIDER:-1}" in
  1) PROVIDER="gemini" ;;
  2) PROVIDER="bedrock" ;;
  3) PROVIDER="ollama" ;;
  *) PROVIDER="skip" ;;
esac

# API key según provider
API_KEY=""
AWS_REGION=""
OLLAMA_HOST=""

if [[ "$PROVIDER" == "gemini" ]]; then
  echo ""
  echo -e "    ${DIM}Obtener en: https://aistudio.google.com/apikey${NC}"
  echo -e "    ${DIM}(pegar y presionar Enter — no se muestra por seguridad)${NC}"
  read -r -s -p "    GOOGLE_API_KEY: " API_KEY
  echo ""
  if [[ -n "$API_KEY" ]]; then
    echo -e "    ${GRN}✓${NC} Key recibida (${#API_KEY} caracteres)"
  else
    echo -e "    ${YLW}⚠${NC} Key vacía — configurar después en /nas-dotfiles/.env.agent"
  fi
elif [[ "$PROVIDER" == "bedrock" ]]; then
  read -r -p "    AWS Region [us-east-1]: " INPUT_REGION
  AWS_REGION="${INPUT_REGION:-us-east-1}"
elif [[ "$PROVIDER" == "ollama" ]]; then
  read -r -p "    Ollama host [http://localhost:11434]: " INPUT_OLLAMA
  OLLAMA_HOST="${INPUT_OLLAMA:-http://localhost:11434}"
fi

# Root
echo ""
read -r -p "    ¿Configurar para root también? [S/n]: " INPUT_ROOT
SETUP_ROOT="${INPUT_ROOT:-s}"

# Python deps
INSTALL_PY_DEPS="n"
if command -v python3 &>/dev/null || command -v python &>/dev/null; then
  read -r -p "    ¿Instalar dependencias Python del agente? [S/n]: " INPUT_PY
  INSTALL_PY_DEPS="${INPUT_PY:-s}"
fi

# ── [3/7] Resumen ──────────────────────────────────────────────────────────
echo ""
echo -e "  ${BOLD}[3/7] Resumen${NC}"
echo ""
echo -e "    ┌────────────────────────────────────────────┐"
echo -e "    │ Proyecto:     $INSTALL_DIR"
echo -e "    │ Navegación:   ${NAV_CMD} → \$${NAV_VAR} → ${NAV_HOME}"
echo -e "    │ Docker datos: $DOCKER_BASE"
echo -e "    │ Timezone:     $TIMEZONE"
echo -e "    │ Provider:     $PROVIDER"
[[ -n "$API_KEY" ]] && echo -e "    │ API Key:      ••••••••••"
echo -e "    │ Root:         ${SETUP_ROOT,,}"
echo -e "    │ Python deps:  ${INSTALL_PY_DEPS,,}"
echo -e "    └────────────────────────────────────────────┘"
echo ""

read -r -p "    ¿Proceder con la instalación? [S/n]: " CONFIRM
if [[ "${CONFIRM,,}" == "n" || "${CONFIRM,,}" == "no" ]]; then
  echo -e "\n  ${DIM}Cancelado. Nada se modificó.${NC}\n"
  exit 0
fi

# ── [4/7] Copiar a /nas-dotfiles ───────────────────────────────────────────
echo ""
echo -e "  ${BOLD}[4/7] Instalando en $INSTALL_DIR${NC}"

if [[ "$REPO_DIR" != "$INSTALL_DIR" ]]; then
  if [[ -d "$INSTALL_DIR" ]]; then
    rsync -a --delete "$REPO_DIR/" "$INSTALL_DIR/"
    echo -e "    ${GRN}✓${NC} Actualizado $INSTALL_DIR"
  else
    sudo cp -a "$REPO_DIR" "$INSTALL_DIR"
    echo -e "    ${GRN}✓${NC} Copiado a $INSTALL_DIR"
  fi
  sudo chown -R "$SYS_USER:$SYS_USER" "$INSTALL_DIR"
else
  echo -e "    ${DIM}~ Ya está en $INSTALL_DIR${NC}"
fi

# ── [5/7] Configurar ~/.bashrc ─────────────────────────────────────────────
echo -e "  ${BOLD}[5/7] Configurando .bashrc${NC}"

# Generar .config/user.conf
mkdir -p "$INSTALL_DIR/.config"
cat > "$INSTALL_DIR/.config/user.conf" << EOF
# .config/user.conf — Configuración personalizada del usuario
# Generado por install.sh — $(date '+%Y-%m-%d %H:%M')
#
# NAV_HOME: Ruta del directorio home (para navegación rápida)
# NAV_VAR:  Nombre de la variable exportada (ej: \$aadm, \$nilo)
# NAV_CMD:  Nombre del comando de navegación (ej: adm, nil)

NAV_HOME="$NAV_HOME"
NAV_VAR="$NAV_VAR"
NAV_CMD="$NAV_CMD"
EOF
echo -e "    ${GRN}✓${NC} .config/user.conf generado"

MARKER="# nas-dotfiles shell framework"
EXPORT_LINE='export NAS_DOTFILES="/nas-dotfiles"'
SOURCE_LINE='source "$NAS_DOTFILES/shell/init.sh"'

_configure_bashrc() {
  local bashrc="$1"
  local label="$2"

  if [[ ! -f "$bashrc" ]]; then
    touch "$bashrc" 2>/dev/null || sudo touch "$bashrc"
  fi

  # Backup antes de tocar
  cp "$bashrc" "$bashrc.bak.$(date +%Y%m%d%H%M%S)" 2>/dev/null || \
    sudo cp "$bashrc" "$bashrc.bak.$(date +%Y%m%d%H%M%S)" 2>/dev/null || true

  # Limpiar TODO lo del viejo shell framework (path_add, SHELL_INIT_LOADED, etc.)
  # Estas líneas ya no son necesarias — init.sh las define internamente
  local patterns_to_remove=(
    'source ~/shell/init.sh'
    'source /home/aadm/shell/init.sh'
    'source "\$NAS_DOTFILES/shell/init.sh"'
    'export NAS_DOTFILES='
    '# nas-dotfiles shell framework'
    '# ── NAS shell'
    'SHELL_INIT_LOADED'
    "alias svc='/docker/cli/svc.sh'"
    'alias svc="/docker/cli/svc.sh"'
    'path_add()'
    'path_add "'
    'case ":$PATH:"'
    '*":$1:"*)'
    '*) PATH="$1:$PATH"'
  )

  for pattern in "${patterns_to_remove[@]}"; do
    sed -i "\|${pattern}|d" "$bashrc" 2>/dev/null || \
      sudo sed -i "\|${pattern}|d" "$bashrc" 2>/dev/null || true
  done

  # Limpiar bloque path_add completo (función de 4 líneas)
  # y la llave de cierre huérfana que queda
  sed -i '/^path_add/d' "$bashrc" 2>/dev/null || true
  sed -i '/^  esac$/d' "$bashrc" 2>/dev/null || true
  sed -i '/^}$/d' "$bashrc" 2>/dev/null || true
  sed -i '/^export -f path_add$/d' "$bashrc" 2>/dev/null || true

  # Limpiar líneas vacías múltiples consecutivas (dejar máx 2)
  sed -i '/^$/N;/^\n$/d' "$bashrc" 2>/dev/null || true

  # Verificar si ya tiene las líneas nuevas correctas
  if grep -qF "$EXPORT_LINE" "$bashrc" 2>/dev/null && grep -qF "$SOURCE_LINE" "$bashrc" 2>/dev/null; then
    echo -e "    ${GRN}✓${NC} $label configurado (limpiado + actualizado)"
    return
  fi

  # Agregar las 2 líneas nuevas al final
  {
    echo ""
    echo "$MARKER"
    echo "$EXPORT_LINE"
    echo "$SOURCE_LINE"
  } >> "$bashrc" 2>/dev/null || {
    echo -e "\n$MARKER\n$EXPORT_LINE\n$SOURCE_LINE" | sudo tee -a "$bashrc" >/dev/null
  }

  echo -e "    ${GRN}✓${NC} $label configurado (limpiado + actualizado)"
}

_configure_bashrc "$HOME/.bashrc" "~/.bashrc"

# Si NAV_HOME es de otro usuario (ej: corriendo como root pero NAV_HOME=/home/aadm)
# configurar también el .bashrc de ese usuario
NAV_USER_BASHRC="$NAV_HOME/.bashrc"
if [[ "$NAV_USER_BASHRC" != "$HOME/.bashrc" && -d "$NAV_HOME" ]]; then
  _configure_bashrc "$NAV_USER_BASHRC" "$NAV_USER_BASHRC"
fi

if [[ "${SETUP_ROOT,,}" == "s" || "${SETUP_ROOT,,}" == "si" || "${SETUP_ROOT,,}" == "y" ]]; then
  if [[ "$HOME" != "/root" ]]; then
    if [[ "$EUID" -eq 0 ]]; then
      _configure_bashrc "/root/.bashrc" "/root/.bashrc"
    elif sudo -n true 2>/dev/null; then
      _configure_bashrc "/root/.bashrc" "/root/.bashrc"
    else
      echo -e "    ${YLW}⚠${NC} Sin acceso a /root/.bashrc — agregar manualmente"
    fi
  fi
fi

# ── [6/7] Variables de entorno ─────────────────────────────────────────────
echo -e "  ${BOLD}[6/7] Guardando configuración del agente${NC}"

ENV_FILE="$INSTALL_DIR/.env.agent"
{
  echo "# Configuración del agente nas-dotfiles"
  echo "# Generado por install.sh — $(date '+%Y-%m-%d %H:%M')"
  echo ""
  if [[ "$PROVIDER" != "skip" ]]; then
    echo "NAS_AGENT_MODEL=$PROVIDER"
  else
    echo "# NAS_AGENT_MODEL=gemini"
  fi
  [[ -n "$API_KEY" ]] && echo "GOOGLE_API_KEY=$API_KEY"
  [[ -n "$AWS_REGION" ]] && echo "AWS_REGION=$AWS_REGION"
  [[ -n "$OLLAMA_HOST" ]] && echo "OLLAMA_HOST=$OLLAMA_HOST"
  echo ""
  echo "DOCKER_BASE=$DOCKER_BASE"
  echo "TZ=$TIMEZONE"
  echo ""
  echo "# Modos de seguridad (descomentar para activar)"
  echo "# NAS_AGENT_READONLY=1"
  echo "# NAS_AGENT_DRYRUN=1"
} > "$ENV_FILE"
chmod 600 "$ENV_FILE"
echo -e "    ${GRN}✓${NC} .env.agent creado (permisos 600)"

# ── [7/7] Dependencias + permisos ──────────────────────────────────────────
echo -e "  ${BOLD}[7/7] Finalizando${NC}"

# Permisos
chmod +x "$INSTALL_DIR/docker/cli/svc.sh" 2>/dev/null || true
chmod +x "$INSTALL_DIR/setup.py" 2>/dev/null || true
chmod +x "$INSTALL_DIR/setup" 2>/dev/null || true
chmod +x "$INSTALL_DIR/uninstall.sh" 2>/dev/null || true
echo -e "    ${GRN}✓${NC} Permisos de ejecución verificados"

# Limpiar symlinks antiguos
for old_link in "/home/$SYS_USER/shell" "$HOME/shell" "/docker/cli" "/usr/local/bin/svc"; do
  if [[ -L "$old_link" ]]; then
    rm -f "$old_link" 2>/dev/null || sudo rm -f "$old_link" 2>/dev/null || true
    echo -e "    ${DIM}~ Eliminado symlink antiguo: $old_link${NC}"
  fi
done

# Python deps
if [[ "${INSTALL_PY_DEPS,,}" == "s" || "${INSTALL_PY_DEPS,,}" == "si" || "${INSTALL_PY_DEPS,,}" == "y" ]]; then
  echo -e "    ${DIM}Instalando dependencias Python...${NC}"
  PYTHON=$(command -v python3 || command -v python)
  if [[ -n "$PYTHON" ]]; then
    # Intentar con --break-system-packages (Python 3.12+)
    if $PYTHON -m pip install --break-system-packages -q -r "$INSTALL_DIR/requirements.txt" 2>/dev/null; then
      echo -e "    ${GRN}✓${NC} Dependencias Python instaladas"
    # Intentar sin el flag (Python más viejo)
    elif $PYTHON -m pip install -q -r "$INSTALL_DIR/requirements.txt" 2>/dev/null; then
      echo -e "    ${GRN}✓${NC} Dependencias Python instaladas"
    # Último recurso: venv
    elif $PYTHON -m venv "$INSTALL_DIR/.venv" 2>/dev/null; then
      "$INSTALL_DIR/.venv/bin/pip" install -q -r "$INSTALL_DIR/requirements.txt" 2>/dev/null
      echo -e "    ${GRN}✓${NC} Deps instaladas en venv ($INSTALL_DIR/.venv)"
      echo -e "    ${DIM}   Para usar el agente: source $INSTALL_DIR/.venv/bin/activate${NC}"
    else
      echo -e "    ${RED}✗${NC} No se pudieron instalar deps Python"
      echo -e "    ${DIM}   Intentar manualmente:${NC}"
      echo -e "    ${DIM}   python3 -m pip install --break-system-packages -r $INSTALL_DIR/requirements.txt${NC}"
    fi
  else
    echo -e "    ${YLW}⚠${NC} Python no encontrado — salteando deps"
  fi
fi

# ── Resultado ──────────────────────────────────────────────────────────────
echo ""
echo -e "  ${CYN}╭──────────────────────────────────────────────╮${NC}"
echo -e "  ${CYN}│${NC}  ${GRN}✅ Instalación completa${NC}                     ${CYN}│${NC}"
echo -e "  ${CYN}│${NC}                                              ${CYN}│${NC}"
echo -e "  ${CYN}│${NC}  Proyecto:  ${BOLD}$INSTALL_DIR${NC}                    ${CYN}│${NC}"
echo -e "  ${CYN}│${NC}  Provider:  $PROVIDER                           ${CYN}│${NC}"
echo -e "  ${CYN}│${NC}  Usuarios:  ${SYS_USER}$([ "${SETUP_ROOT,,}" == "s" ] && echo " + root")                         ${CYN}│${NC}"
echo -e "  ${CYN}│${NC}                                              ${CYN}│${NC}"
echo -e "  ${CYN}│${NC}  ${DIM}Ejecuta:${NC}                                   ${CYN}│${NC}"
echo -e "  ${CYN}│${NC}    ${CYN}source ~/.bashrc${NC}                         ${CYN}│${NC}"
echo -e "  ${CYN}│${NC}    ${CYN}svc doctor${NC}                               ${CYN}│${NC}"
echo -e "  ${CYN}│${NC}    ${CYN}python -m agent.nas_agent \"hola\"${NC}         ${CYN}│${NC}"
echo -e "  ${CYN}╰──────────────────────────────────────────────╯${NC}"
echo ""
