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

# ECRにログインし、以降のDockerコマンドにも専用設定を使う。
# 引数: ECRレジストリ、任意のAWS profile。失敗時は環境変数を変えない。
ecrlogin() {
  if [[ $# -lt 1 || $# -gt 2 || ( $# -eq 2 && -z "$2" ) ]]; then
    printf '使い方: ecrlogin <ECRレジストリ> [profile]\n' >&2
    return 2
  fi

  local registry="$1"
  local registry_pattern='^[0-9]{12}\.dkr\.ecr\.([a-z0-9-]+)\.amazonaws\.com(\.cn)?$'
  if [[ ! "$registry" =~ $registry_pattern ]]; then
    printf 'ECRのレジストリホスト名を指定してください。\n' >&2
    return 2
  fi
  local region="${BASH_REMATCH[1]}"
  local -a profile_args=()
  if [[ -n "${2:-}" ]]; then
    profile_args=(--profile "$2")
  fi

  # 別OS用の認証ヘルパーや既存ディレクトリの権限を引き継がない。
  local docker_config
  docker_config="$(mktemp -d "${TMPDIR:-/tmp}/docker-ecr.XXXXXXXX")" || return
  if (
    set -o pipefail
    umask 077
    AWS_PAGER='' AWS_CLI_AUTO_PROMPT=off \
      aws "${profile_args[@]}" --region "$region" \
        --no-cli-pager --no-cli-auto-prompt ecr get-login-password |
      docker --config "$docker_config" login \
        --username AWS --password-stdin "$registry"
  ); then
    export DOCKER_CONFIG="$docker_config"
  else
    return "$?"
  fi
}

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
