#!/usr/bin/env bash
# install.sh — Configura nas-dotfiles (Opción B: todo dentro del repo)
#
# NO crea symlinks de shell/ ni docker/cli/ hacia el sistema.
# Solo configura ~/.bashrc con NAS_DOTFILES + source del init.sh.
# El CLI 'svc' se expone como alias (definido en shell/init.sh).
set -e

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"

echo ""
echo "  nas-dotfiles installer (v2 — sin symlinks)"
echo "  ────────────────────────────────────────────"
echo ""
echo "  Repo detectado: $REPO_DIR"
echo ""

# ── [1/3] Configurar ~/.bashrc ─────────────────────────────────────────────
echo "  [1/3] Configurando ~/.bashrc"

BASHRC="$HOME/.bashrc"
EXPORT_LINE="export NAS_DOTFILES=\"$REPO_DIR\""
SOURCE_LINE='source "$NAS_DOTFILES/shell/init.sh"'
MARKER="# nas-dotfiles shell framework"

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

# ── [2/3] Permisos de ejecución ────────────────────────────────────────────
echo "  [2/3] Verificando permisos"
chmod +x "$REPO_DIR/docker/cli/svc.sh"
echo "  + docker/cli/svc.sh → ejecutable"

# ── [3/3] Limpiar symlinks antiguos (si existen) ───────────────────────────
echo "  [3/3] Limpiando symlinks antiguos (si existen)"

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
echo "  Rastro fuera del repo: SOLO 2 líneas en ~/.bashrc"
echo ""
echo "  Ejecuta:  source ~/.bashrc"
echo ""
echo "  Para desinstalar:  $REPO_DIR/uninstall.sh"
echo ""

# ── Nota para root ─────────────────────────────────────────────────────────
if [[ "$EUID" -ne 0 ]]; then
  echo "  NOTA: Para que root también use el framework,"
  echo "        agrega a /root/.bashrc:"
  echo ""
  echo "        export NAS_DOTFILES=\"$REPO_DIR\""
  echo '        source "$NAS_DOTFILES/shell/init.sh"'
  echo ""
fi
