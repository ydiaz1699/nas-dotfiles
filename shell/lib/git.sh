# /home/aadm/shell/lib/git.sh
# Aliases y helpers de git

# ── Aliases ────────────────────────────────────────────────────────────────
alias gs='git status -sb'
alias ga='git add'
alias gc='git commit'
alias gcm='git commit -m'
alias gca='git commit --amend'
alias gp='git push'
alias gpl='git pull'
alias gl='git log --oneline -20'
alias glg='git log --oneline --graph --decorate -20'
alias gd='git diff'
alias gds='git diff --staged'
alias gb='git branch'
alias gco='git checkout'
alias gsw='git switch'
alias gsc='git switch -c'
alias gst='git stash'
alias gstp='git stash pop'
alias gf='git fetch --all --prune'

# ── git-clean-branches — eliminar ramas mergeadas localmente ──────────────
git-clean-branches() {
  local main_branch
  main_branch=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@')
  [[ -z "$main_branch" ]] && main_branch="main"

  local branches
  branches=$(git branch --merged "$main_branch" | grep -v "^\*\|$main_branch" | tr -d ' ')

  if [[ -z "$branches" ]]; then
    echo "  No hay ramas mergeadas para eliminar."
    return 0
  fi

  echo "  Ramas mergeadas a eliminar:"
  echo "$branches" | sed 's/^/    /'
  echo ""

  read -rp "  Eliminar? [y/N] " confirm
  if [[ "$confirm" =~ ^[yY]$ ]]; then
    echo "$branches" | xargs git branch -d
    echo "  Listo."
  else
    echo "  Cancelado."
  fi
}

# ── git-quick — add + commit + push rapido ────────────────────────────────
git-quick() {
  local msg="${1:-update}"
  git add -A && git commit -m "$msg" && git push
}
