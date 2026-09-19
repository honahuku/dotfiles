#!/usr/bin/env bash
set -euo pipefail

DOTFILES="${DOTFILES:-${HOME}/git/honahuku/dotfiles}"

link_path() {
  local src="$1"
  local dst="$2"

  if [[ ! -e "$src" ]]; then
    echo "skip $src (missing)"
    return
  fi

  if [[ -e "$dst" && ! -L "$dst" ]]; then
    echo "skip $dst (not a symlink)"
    return
  fi

  mkdir -p "$(dirname "$dst")"
  ln -sfn "$src" "$dst"
}

link_path "$DOTFILES/.bashrc" "$HOME/.bashrc"
link_path "$DOTFILES/aqua.yaml" "$HOME/aqua.yaml"
link_path "$DOTFILES/alacritty/alacritty.toml" "$HOME/.config/alacritty/alacritty.toml"
link_path "$DOTFILES/nvim" "$HOME/.config/nvim"
