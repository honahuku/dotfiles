# shellcheck shell=sh
# 外部エディタは非対話シェルから起動するCLIにも引き継ぐ。
export EDITOR=nvim
export VISUAL=nvim
export AQUA_GLOBAL_CONFIG="$HOME/aqua.yaml"

if [ "${CODEX_INTERNAL_ORIGINATOR_OVERRIDE:-}" = "Codex Desktop" ]; then
  export CODEX_HOME="$HOME/.codex"
fi

for _dotfiles_bin in "$HOME/.local/bin" "${AQUA_ROOT_DIR:-${XDG_DATA_HOME:-$HOME/.local/share}/aquaproj-aqua}/bin" "$HOME/.local/share/mise/shims"; do
  case ":${PATH:-}:" in
    *":$_dotfiles_bin:"*) ;;
    *) PATH="$_dotfiles_bin${PATH:+:$PATH}" ;;
  esac
done
export PATH
unset _dotfiles_bin
