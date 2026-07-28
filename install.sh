#!/usr/bin/env bash
# install.sh — Configura nas-dotfiles (Opción B: todo dentro del repo)
#
# NO crea symlinks de shell/ ni docker/cli/ hacia el sistema.
# Solo configura ~/.bashrc con NAS_DOTFILES + source del init.sh.
# El CLI 'svc' se expone como alias (definido en shell/init.sh).
set -e

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"

# Ruta destino: /nas-dotfiles (independiente del usuario)
INSTALL_DIR="/nas-dotfiles"

echo ""
echo "  nas-dotfiles installer (v2 — sin symlinks)"
echo "  ────────────────────────────────────────────"
echo ""
echo "  Repo origen: $REPO_DIR"
echo "  Destino:     $INSTALL_DIR"
echo ""

# ── [0/4] Copiar/mover a /nas-dotfiles si no está ahí ─────────────────────
if [[ "$REPO_DIR" != "$INSTALL_DIR" ]]; then
  echo "  [0/4] Instalando en $INSTALL_DIR"
  if [[ -d "$INSTALL_DIR" ]]; then
    echo "  ~ $INSTALL_DIR ya existe — actualizando..."
    rsync -a --delete "$REPO_DIR/" "$INSTALL_DIR/"
  else
    sudo cp -a "$REPO_DIR" "$INSTALL_DIR"
  fi
  # Permisos: aadm es dueño, todos pueden leer/ejecutar
  sudo chown -R "$(whoami):$(whoami)" "$INSTALL_DIR"
  sudo chmod -R 755 "$INSTALL_DIR"
  echo "  + Copiado a $INSTALL_DIR (dueño: $(whoami))"
  echo ""
else
  echo "  [0/4] Ya está en $INSTALL_DIR — OK"
  echo ""
fi

# ── [1/4] Configurar ~/.bashrc ─────────────────────────────────────────────
echo "  [1/4] Configurando ~/.bashrc"

BASHRC="$HOME/.bashrc"
EXPORT_LINE='export NAS_DOTFILES="/nas-dotfiles"'
SOURCE_LINE='source "$NAS_DOTFILES/shell/init.sh"'
MARKER="# nas-dotfiles shell framework"

# Backup de seguridad antes de modificar
if [[ -f "$BASHRC" ]]; then
  cp "$BASHRC" "$BASHRC.bak.$(date +%Y%m%d%H%M%S)"
  echo "  ~ Backup creado: $BASHRC.bak.*"
fi

# Limpiar cualquier config antigua (source ~/shell/init.sh, etc.)
if grep -qF "source ~/shell/init.sh" "$BASHRC" 2>/dev/null; then
  echo "  ~ Eliminando referencia antigua: source ~/shell/init.sh"
  sed -i '/source ~\/shell\/init\.sh/d' "$BASHRC"
fi
if grep -qF "source /home/aadm/shell/init.sh" "$BASHRC" 2>/dev/null; then
  echo "  ~ Eliminando referencia antigua: source /home/aadm/shell/init.sh"
  sed -i '\|source /home/aadm/shell/init\.sh|d' "$BASHRC"
fi

# Verificar si ya está configurado correctamente
if grep -qF "$EXPORT_LINE" "$BASHRC" 2>/dev/null && grep -qF "$SOURCE_LINE" "$BASHRC" 2>/dev/null; then
  echo "  ~ ~/.bashrc ya configurado correctamente"
else
  # Limpiar bloque anterior si existe parcialmente
  sed -i "/$MARKER/d" "$BASHRC" 2>/dev/null || true
  sed -i "\|export NAS_DOTFILES=|d" "$BASHRC" 2>/dev/null || true
  sed -i '\|source "\$NAS_DOTFILES/shell/init.sh"|d' "$BASHRC" 2>/dev/null || true

  # Agregar bloque nuevo
  {
    echo ""
    echo "$MARKER"
    echo "$EXPORT_LINE"
    echo "$SOURCE_LINE"
  } >> "$BASHRC"
  echo "  + Agregado a $BASHRC:"
  echo "      $EXPORT_LINE"
  echo "      $SOURCE_LINE"
fi

# ── [2/4] Configurar /root/.bashrc (si somos root o tenemos sudo) ──────────
echo "  [2/4] Configurando /root/.bashrc"

ROOT_BASHRC="/root/.bashrc"
if [[ "$EUID" -eq 0 ]]; then
  # Somos root
  if ! grep -qF "$EXPORT_LINE" "$ROOT_BASHRC" 2>/dev/null; then
    cp "$ROOT_BASHRC" "$ROOT_BASHRC.bak.$(date +%Y%m%d%H%M%S)" 2>/dev/null || true
    {
      echo ""
      echo "$MARKER"
      echo "$EXPORT_LINE"
      echo "$SOURCE_LINE"
    } >> "$ROOT_BASHRC"
    echo "  + Agregado a /root/.bashrc"
  else
    echo "  ~ /root/.bashrc ya configurado"
  fi
elif sudo -n true 2>/dev/null; then
  # Tenemos sudo sin password
  if ! sudo grep -qF "$EXPORT_LINE" "$ROOT_BASHRC" 2>/dev/null; then
    sudo cp "$ROOT_BASHRC" "$ROOT_BASHRC.bak.$(date +%Y%m%d%H%M%S)" 2>/dev/null || true
    echo -e "\n$MARKER\n$EXPORT_LINE\n$SOURCE_LINE" | sudo tee -a "$ROOT_BASHRC" >/dev/null
    echo "  + Agregado a /root/.bashrc"
  else
    echo "  ~ /root/.bashrc ya configurado"
  fi
else
  echo "  ~ Sin acceso a /root/.bashrc (ejecutar como root o con sudo)"
  echo "    Agregar manualmente a /root/.bashrc:"
  echo "      $EXPORT_LINE"
  echo "      $SOURCE_LINE"
fi

# ── [3/4] Permisos de ejecución ────────────────────────────────────────────
echo "  [3/4] Verificando permisos"
chmod +x "$INSTALL_DIR/docker/cli/svc.sh"
echo "  + docker/cli/svc.sh → ejecutable"

# ── [4/4] Limpiar symlinks antiguos (si existen) ───────────────────────────
echo "  [4/4] Limpiando symlinks antiguos (si existen)"

_remove_old_symlink() {
  local target="$1"
  if [[ -L "$target" ]]; then
    rm -f "$target"
    echo "  - Eliminado symlink antiguo: $target"
  fi
}

_remove_old_symlink "/home/aadm/shell"
_remove_old_symlink "$HOME/shell"
_remove_old_symlink "/docker/cli"
_remove_old_symlink "/usr/local/bin/svc"

# ── Resultado ──────────────────────────────────────────────────────────────
echo ""
echo "  ────────────────────────────────────────────"
echo "  ✅ Instalación completa."
echo ""
echo "  Ruta del proyecto: $INSTALL_DIR"
echo "  Funciona para: $(whoami) + root"
echo ""
echo "  Ejecuta:  source ~/.bashrc"
echo ""
echo "  Para desinstalar:  $INSTALL_DIR/uninstall.sh"
echo ""
