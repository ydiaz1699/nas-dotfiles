#!/usr/bin/env bash
# uninstall.sh — Revierte la instalación de nas-dotfiles
#
# Elimina las líneas de ~/.bashrc y cualquier symlink residual.
# Después de ejecutar esto, puedes borrar ~/nas-dotfiles/ y el
# sistema queda completamente limpio.
set -e

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"

echo ""
echo "  nas-dotfiles uninstaller"
echo "  ────────────────────────────────────────────"
echo ""

# ── [1/3] Limpiar ~/.bashrc ────────────────────────────────────────────────
echo "  [1/3] Limpiando ~/.bashrc"

BASHRC="$HOME/.bashrc"

if [[ -f "$BASHRC" ]]; then
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

# ── [3/3] Limpiar /root/.bashrc si tiene referencia ───────────────────────
echo "  [3/3] Verificando /root/.bashrc"

ROOT_BASHRC="/root/.bashrc"
if [[ -f "$ROOT_BASHRC" ]] && grep -q "NAS_DOTFILES" "$ROOT_BASHRC" 2>/dev/null; then
  if [[ "$EUID" -eq 0 ]]; then
    sed -i '/# nas-dotfiles shell framework/d' "$ROOT_BASHRC"
    sed -i '\|export NAS_DOTFILES=|d' "$ROOT_BASHRC"
    sed -i '\|source "\$NAS_DOTFILES/shell/init.sh"|d' "$ROOT_BASHRC"
    echo "  - Limpiado /root/.bashrc"
  else
    echo "  ~ /root/.bashrc tiene referencia a nas-dotfiles."
    echo "    Ejecuta como root: sudo sed -i '/NAS_DOTFILES/d' /root/.bashrc"
  fi
else
  echo "  ~ /root/.bashrc limpio (nada que hacer)"
fi

# ── Resultado ──────────────────────────────────────────────────────────────
echo ""
echo "  ────────────────────────────────────────────"
echo "  ✅ Desinstalación completa."
echo ""
echo "  El sistema ya no tiene referencias a nas-dotfiles."
echo "  Puedes borrar el repo con:"
echo ""
echo "    rm -rf $REPO_DIR"
echo ""
echo "  Para aplicar los cambios en la sesión actual:"
echo "    exec bash"
echo ""
