# shellcheck shell=bash
# shellcheck source=shell/profile.sh
. "$HOME/git/honahuku/dotfiles/shell/profile.sh"

case $- in
  *i*) ;;
  *) return ;;
esac

alias ll='ls -alF'
alias la='ls -A'
alias l='ls -CF'
alias py='python3'

for kubectx_completion in \
  /usr/share/bash-completion/completions/kubectx \
  /usr/share/bash-completion/completions/kubens
do
  if [[ -f "$kubectx_completion" ]]; then
    # OSが提供する補完は、このrepoの解析には含めない。
    # shellcheck source=/dev/null
    . "$kubectx_completion"
  fi
done
unset kubectx_completion

if [[ -n "${DOTFILES_PRIVATE_ROOT:-}" && -f "$DOTFILES_PRIVATE_ROOT/shell/bashrc.sh" ]]; then
  # ShellCheckではprivate repoを含めず、private側で個別に検査する。
  # shellcheck source=/dev/null
  . "$DOTFILES_PRIVATE_ROOT/shell/bashrc.sh"
fi
if command -v mise >/dev/null 2>&1; then
  eval "$(mise activate bash)"
fi
if [[ -f "$HOME/.bashrc.local" ]]; then
  # 端末固有の設定はrepoに含まれない。
  # shellcheck source=/dev/null
  . "$HOME/.bashrc.local"
fi
# 子シェルの初期化を省略しないよう、.profile用の印はexportしない。
# shellcheck disable=SC2034
DOTFILES_SHELL_LOADED=1
