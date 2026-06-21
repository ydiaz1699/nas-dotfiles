#!/usr/bin/env bash
# install.sh — Instala symlinks y configura bashrc
set -e

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
SHELL_TARGET="/home/aadm/shell"
DOCKER_CLI_TARGET="/docker/cli"
SVC_BIN="/usr/local/bin/svc"

echo ""
echo "  nas-dotfiles installer"
echo "  ────────────────────────────────────"
echo ""

# ── Funciones ──────────────────────────────────────────────────────────────
link_dir() {
  local src="$1" dst="$2"
  if [[ -L "$dst" ]]; then
    echo "  ~ $dst (symlink ya existe, recreando)"
    rm -f "$dst"
  elif [[ -d "$dst" ]]; then
    echo "  ! $dst existe como directorio"
    echo "    Haz backup manual y elimínalo antes de continuar."
    return 1
  fi
  ln -s "$src" "$dst"
  echo "  + $dst -> $src"
}

# ── Shell ──────────────────────────────────────────────────────────────────
echo "  [1/4] Shell framework"
link_dir "$REPO_DIR/shell" "$SHELL_TARGET"

# ── Docker CLI ─────────────────────────────────────────────────────────────
echo "  [2/4] Docker CLI"
mkdir -p "$(dirname "$DOCKER_CLI_TARGET")"
link_dir "$REPO_DIR/docker/cli" "$DOCKER_CLI_TARGET"

# ── svc en PATH ────────────────────────────────────────────────────────────
echo "  [3/4] svc -> $SVC_BIN"
if [[ -L "$SVC_BIN" || -f "$SVC_BIN" ]]; then
  rm -f "$SVC_BIN"
fi
ln -s "$DOCKER_CLI_TARGET/svc.sh" "$SVC_BIN"
chmod +x "$REPO_DIR/docker/cli/svc.sh"
echo "  + $SVC_BIN -> $DOCKER_CLI_TARGET/svc.sh"

# ── bashrc ─────────────────────────────────────────────────────────────────
echo "  [4/4] Configurando ~/.bashrc"
BASHRC="$HOME/.bashrc"
INIT_LINE='source ~/shell/init.sh'

if grep -qF "$INIT_LINE" "$BASHRC" 2>/dev/null; then
  echo "  ~ bashrc ya contiene '$INIT_LINE'"
else
  echo "" >> "$BASHRC"
  echo "# nas-dotfiles shell framework" >> "$BASHRC"
  echo "$INIT_LINE" >> "$BASHRC"
  echo "  + Agregado a $BASHRC"
fi

# ── Root ───────────────────────────────────────────────────────────────────
echo ""
if [[ "$EUID" -ne 0 ]]; then
  echo "  NOTA: Para que root también use el framework,"
  echo "        agrega a /root/.bashrc:"
  echo ""
  echo "        source /home/aadm/shell/init.sh"
  echo ""
fi

echo "  ────────────────────────────────────"
echo "  Instalacion completa. Ejecuta:"
echo "    source ~/.bashrc"
echo ""
