#!/usr/bin/env bash
set -euo pipefail

DOTFILES="${DOTFILES:-$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)}"
backup_existing=false
case "${1:-}" in
  "") ;;
  --backup) backup_existing=true ;;
  *) echo "Usage: $0 [--backup]" >&2; exit 2 ;;
esac
if (( $# > 1 )); then
  echo "Usage: $0 [--backup]" >&2
  exit 2
fi

link_path() {
  local src="$1" dst="$2" backup
  if [[ ! -e "$src" ]]; then
    echo "skip $src (missing)"
    return
  fi
  if [[ -L "$dst" ]] && [[ "$(readlink -- "$dst")" == "$src" ]]; then
    echo "ok $dst"
    return
  fi
  if [[ -e "$dst" || -L "$dst" ]]; then
    if ! "$backup_existing"; then
      echo "skip $dst (already exists; use --backup to replace)"
      return
    fi
    backup="${dst}.backup-$(date +%Y%m%d-%H%M%S)"
    while [[ -e "$backup" || -L "$backup" ]]; do backup="${backup}.bak"; done
    mv -- "$dst" "$backup"
    echo "backup $dst -> $backup"
  fi
  mkdir -p -- "$(dirname -- "$dst")"
  ln -s -- "$src" "$dst"
  echo "link $dst -> $src"
}

link_path "$DOTFILES/.bashrc" "$HOME/.bashrc"
link_path "$DOTFILES/aqua.yaml" "$HOME/aqua.yaml"
link_path "$DOTFILES/alacritty/alacritty.toml" "$HOME/.config/alacritty/alacritty.toml"
link_path "$DOTFILES/nvim" "$HOME/.config/nvim"
link_path "$DOTFILES/.agents/skills" "$HOME/.agents/skills"
link_path "$DOTFILES/.agents/AGENTS.md" "${CODEX_HOME:-$HOME/.codex}/AGENTS.md"
