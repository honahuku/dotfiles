# shellcheck shell=sh
for _dotfiles_bin in "$HOME/.local/bin" "${AQUA_ROOT_DIR:-${XDG_DATA_HOME:-$HOME/.local/share}/aquaproj-aqua}/bin" "$HOME/.local/share/mise/shims"; do
  case ":${PATH:-}:" in
    *":$_dotfiles_bin:"*) ;;
    *) PATH="$_dotfiles_bin${PATH:+:$PATH}" ;;
  esac
done
export PATH
unset _dotfiles_bin

# private repoを明示指定していない場合は、候補が1つだけなら読み込む。
if [ -z "${DOTFILES_PRIVATE_ROOT:-}" ]; then
  _dotfiles_private_candidate=
  _dotfiles_private_ambiguous=0
  for _dotfiles_private_dir in "$HOME"/git/*/dotfiles-private; do
    [ -f "$_dotfiles_private_dir/shell/profile.sh" ] || continue
    if [ -n "$_dotfiles_private_candidate" ]; then
      _dotfiles_private_ambiguous=1
      break
    fi
    _dotfiles_private_candidate=$_dotfiles_private_dir
  done
  if [ "$_dotfiles_private_ambiguous" -eq 0 ]; then
    DOTFILES_PRIVATE_ROOT=$_dotfiles_private_candidate
  fi
  unset _dotfiles_private_candidate _dotfiles_private_ambiguous _dotfiles_private_dir
fi

if [ -n "${DOTFILES_PRIVATE_ROOT:-}" ] && [ -f "$DOTFILES_PRIVATE_ROOT/shell/profile.sh" ]; then
  # ShellCheckではprivate repoを含めず、private側で個別に検査する。
  # shellcheck source=/dev/null
  . "$DOTFILES_PRIVATE_ROOT/shell/profile.sh"
fi
