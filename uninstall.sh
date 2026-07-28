#!/usr/bin/env bash
# uninstall.sh — Revierte la instalación de nas-dotfiles
#
# Elimina las líneas de ~/.bashrc y cualquier symlink residual.
# Después de ejecutar esto, puedes borrar ~/nas-dotfiles/ y el
# sistema queda completamente limpio.
set -e

REPO_DIR="/nas-dotfiles"

echo ""
echo "  nas-dotfiles uninstaller"
echo "  ────────────────────────────────────────────"
echo ""

# ── [1/3] Limpiar ~/.bashrc ────────────────────────────────────────────────
echo "  [1/3] Limpiando ~/.bashrc"

BASHRC="$HOME/.bashrc"

if [[ -f "$BASHRC" ]]; then
  # Backup de seguridad antes de modificar
  cp "$BASHRC" "$BASHRC.bak.$(date +%Y%m%d%H%M%S)"
  echo "  ~ Backup creado: $BASHRC.bak.*"

  # Eliminar líneas relacionadas con nas-dotfiles
  sed -i '/# nas-dotfiles shell framework/d' "$BASHRC"
  sed -i '\|export NAS_DOTFILES=|d' "$BASHRC"
  sed -i '\|source "\$NAS_DOTFILES/shell/init.sh"|d' "$BASHRC"
  # También limpiar formato antiguo por si acaso
  sed -i '/source ~\/shell\/init\.sh/d' "$BASHRC"
  sed -i '\|source /home/aadm/shell/init\.sh|d' "$BASHRC"
  # Limpiar líneas vacías consecutivas al final
  sed -i -e :a -e '/^\n*$/{$d;N;ba' -e '}' "$BASHRC"
  echo "  - Líneas de nas-dotfiles eliminadas de $BASHRC"
else
  echo "  ~ $BASHRC no encontrado (nada que limpiar)"
fi

# ── [2/3] Eliminar symlinks antiguos ──────────────────────────────────────
echo "  [2/3] Eliminando symlinks residuales"

_remove_if_symlink() {
  local target="$1"
  if [[ -L "$target" ]]; then
    rm -f "$target"
    echo "  - Eliminado: $target"
  fi
}

_remove_if_symlink "/home/aadm/shell"
_remove_if_symlink "$HOME/shell"
_remove_if_symlink "/docker/cli"
_remove_if_symlink "/usr/local/bin/svc"

# ── [3/3] Limpiar /root/.bashrc ────────────────────────────────────────────
echo "  [3/3] Limpiando /root/.bashrc"

ROOT_BASHRC="/root/.bashrc"
if [[ "$EUID" -eq 0 ]]; then
  if grep -q "NAS_DOTFILES" "$ROOT_BASHRC" 2>/dev/null; then
    cp "$ROOT_BASHRC" "$ROOT_BASHRC.bak.$(date +%Y%m%d%H%M%S)"
    sed -i '/# nas-dotfiles shell framework/d' "$ROOT_BASHRC"
    sed -i '\|export NAS_DOTFILES=|d' "$ROOT_BASHRC"
    sed -i '\|source "\$NAS_DOTFILES/shell/init.sh"|d' "$ROOT_BASHRC"
    echo "  - Limpiado /root/.bashrc"
  else
    echo "  ~ /root/.bashrc limpio"
  fi
elif sudo -n true 2>/dev/null; then
  if sudo grep -q "NAS_DOTFILES" "$ROOT_BASHRC" 2>/dev/null; then
    sudo cp "$ROOT_BASHRC" "$ROOT_BASHRC.bak.$(date +%Y%m%d%H%M%S)"
    sudo sed -i '/# nas-dotfiles shell framework/d' "$ROOT_BASHRC"
    sudo sed -i '\|export NAS_DOTFILES=|d' "$ROOT_BASHRC"
    sudo sed -i '\|source "\$NAS_DOTFILES/shell/init.sh"|d' "$ROOT_BASHRC"
    echo "  - Limpiado /root/.bashrc"
  else
    echo "  ~ /root/.bashrc limpio"
  fi
else
  echo "  ~ Sin acceso a /root/.bashrc — limpiar manualmente si es necesario"
fi

# ── Resultado ──────────────────────────────────────────────────────────────
echo ""
echo "  ────────────────────────────────────────────"
echo "  ✅ Desinstalación completa."
echo ""
echo "  El sistema ya no tiene referencias a nas-dotfiles."
echo "  Puedes borrar el proyecto con:"
echo ""
echo "    sudo rm -rf /nas-dotfiles"
echo ""
echo "  Para aplicar los cambios en la sesión actual:"
echo "    exec bash"
echo ""
