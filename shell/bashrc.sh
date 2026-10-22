# shellcheck shell=bash
# shellcheck source=shell/profile.sh
. "$HOME/git/honahuku/dotfiles/shell/profile.sh"

if command -v rg &>/dev/null; then
  alias grep='rg --color=auto'
  alias egrep='rg --color=auto -e'
  alias fgrep='rg --color=auto -F'
fi

# ghの起動時間を抑えるため、認証済みリクエスト用のトークンを1時間キャッシュする。
# 期限切れの更新はバックグラウンドで行い、次回のシェル起動から反映する。
if command -v gh &>/dev/null; then
  _gh_token_cache="${XDG_CACHE_HOME:-$HOME/.cache}/gh_auth_token"
  mkdir -p "$(dirname "$_gh_token_cache")"
  if [[ -s "$_gh_token_cache" ]]; then
    _gh_token="$(cat "$_gh_token_cache")"
    export GITHUB_TOKEN="$_gh_token"
    if [[ -z "$(find "$_gh_token_cache" -mmin -60 2>/dev/null)" ]]; then
      (gh auth token 2>/dev/null >"$_gh_token_cache" &) 2>/dev/null
    fi
  else
    _gh_token="$(gh auth token 2>/dev/null)"
    export GITHUB_TOKEN="$_gh_token"
    printf '%s' "$GITHUB_TOKEN" >"$_gh_token_cache"
  fi
  unset _gh_token_cache _gh_token
fi

# Windows側のPATHと旧管理経路を継承すると、探索の遅延や管理版との競合が起きる。
_new_path=""
IFS=':' read -ra _path_parts <<<"$PATH"
for _p in "${_path_parts[@]}"; do
  [[ "$_p" == /mnt/c/* ]] && continue
  if [[ "$_p" == "$HOME/.local/share/nvim/mason/bin" ||
    "$_p" == /usr/local/go/bin ]]; then
    continue
  fi
  _new_path="${_new_path:+$_new_path:}$_p"
done
PATH="$_new_path"
PATH="/mnt/c/Program Files/Rancher Desktop/resources/resources/linux/bin:$PATH"
PATH="/mnt/c/Program Files/Rancher Desktop/resources/resources/linux/docker-cli-plugins:$PATH"
# 個別導入版やRancher Desktopより管理対象のCLIを優先する。
PATH="${AQUA_ROOT_DIR:-${XDG_DATA_HOME:-$HOME/.local/share}/aquaproj-aqua}/bin:$PATH"
export PATH="$HOME/.local/share/mise/shims:$PATH"
unset _new_path _p _path_parts

if command -v mise >/dev/null 2>&1; then
  # 非対話シェルにもランタイムを適用する。
  eval "$(mise env --shell bash)"
fi

case $- in
  *i*) ;;
  *) return ;;
esac

HISTCONTROL=ignoreboth
shopt -s histappend
HISTSIZE=1000
HISTFILESIZE=2000
shopt -s checkwinsize

# 必要に応じてglobstar、lesspipe、GCCの色付き診断を有効にする。
# shopt -s globstar
# [[ -x /usr/bin/lesspipe ]] && eval "$(SHELL=/bin/sh lesspipe)"
# export GCC_COLORS='error=01;31:warning=01;35:note=01;36:caret=01;32:locus=01:quote=01'

if [[ -z "${debian_chroot:-}" && -r /etc/debian_chroot ]]; then
  debian_chroot=$(cat /etc/debian_chroot)
fi

case "${TERM:-}" in
  xterm-color | *-256color) color_prompt=yes ;;
esac
# 端末名で判定できない場合は、必要に応じて強制的に色を有効にする。
# force_color_prompt=yes
if [[ -n "${force_color_prompt:-}" ]]; then
  if [[ -x /usr/bin/tput ]] && tput setaf 1 &>/dev/null; then
    color_prompt=yes
  else
    color_prompt=
  fi
fi

# GKEの長いcontext名はクラスタ名だけをプロンプトに表示する。
kube_ps1_context_name() {
  local ctx
  ctx=$(kubectl config current-context 2>/dev/null) || return
  [[ -z "$ctx" ]] && return
  if [[ "$ctx" =~ ^gke_[^_]+_[^_]+_(.+)$ ]]; then
    ctx="${BASH_REMATCH[1]}"
  fi
  printf '%s' "$ctx"
}

if [[ "${color_prompt:-}" == yes ]]; then
  # 色の制御文字を表示幅に数えないよう、プロンプト用の区切りを付ける。
  kube_ps1_context() {
    local ctx
    ctx=$(kube_ps1_context_name) || return
    [[ -z "$ctx" ]] && return
    printf ' \001\033[01;36m\002%s\001\033[00m\002' "$ctx"
  }
  PS1='${debian_chroot:+($debian_chroot)}\[\033[01;34m\]\w\[\033[00m\]$(kube_ps1_context)\$ '
else
  # 色を使わない端末でも同じcontext名を表示する。
  kube_ps1_context() {
    local ctx
    ctx=$(kube_ps1_context_name) || return
    [[ -z "$ctx" ]] && return
    printf ' %s' "$ctx"
  }
  PS1='${debian_chroot:+($debian_chroot)}\w$(kube_ps1_context)\$ '
fi
unset color_prompt force_color_prompt

case "${TERM:-}" in
  xterm* | rxvt*)
    PS1="\[\e]0;${debian_chroot:+($debian_chroot)}\u@\h: \w\a\]$PS1"
    ;;
esac

if [[ -x /usr/bin/dircolors ]]; then
  if [[ -r "$HOME/.dircolors" ]]; then
    eval "$(dircolors -b "$HOME/.dircolors")"
  else
    eval "$(dircolors -b)"
  fi
  alias ls='ls --color=auto'
fi

alias ll='ls -alF'
alias la='ls -A'
alias l='ls -CF'
alias py='python3'
alias gp='git push -u origin HEAD'
alias gpf='git push --force-with-lease --force-if-includes'
alias tasks='"$HOME/.claude/bin/tasks"'
alias nrlogin='codex mcp login newrelic'

if [[ -f "$HOME/.bash_aliases" ]]; then
  # 個別aliasは、このrepoの解析には含めない。
  # shellcheck source=/dev/null
  . "$HOME/.bash_aliases"
fi

if ! shopt -oq posix; then
  if [[ -f /usr/share/bash-completion/bash_completion ]]; then
    # OSの補完定義は、このrepoの解析には含めない。
    # shellcheck source=/dev/null
    . /usr/share/bash-completion/bash_completion
  elif [[ -f /etc/bash_completion ]]; then
    # shellcheck source=/dev/null
    . /etc/bash_completion
  fi
fi

if command -v aqua &>/dev/null; then
  eval "$(aqua completion bash)"
fi

# rm互換のオプションを受け取り、削除の代わりにホーム内のゴミ箱へ移動する。
# 引数はオプションと対象パス。標準エラーへ失敗理由を出し、失敗時は1を返す。
trash() {
  local trash_dir="$HOME/.trash"
  mkdir -p "$trash_dir"

  local force=0 recursive=0 dir_mode=0 verbose=0 interactive=0
  local files=()
  local end_of_opts=0
  local arg f answer

  for arg in "$@"; do
    if [[ $end_of_opts -eq 1 ]]; then
      files+=("$arg")
      continue
    fi
    case "$arg" in
      --) end_of_opts=1 ;;
      --force) force=1 ;;
      --recursive) recursive=1 ;;
      --dir) dir_mode=1 ;;
      --verbose) verbose=1 ;;
      --interactive) interactive=1 ;;
      --*)
        echo "trash: unrecognized option '$arg'" >&2
        echo "Try 'rm --help' for more information." >&2
        return 1
        ;;
      -*)
        local opts="${arg#-}"
        while [[ -n "$opts" ]]; do
          case "${opts:0:1}" in
            f) force=1 ;;
            r | R) recursive=1 ;;
            d) dir_mode=1 ;;
            v) verbose=1 ;;
            i) interactive=1 ;;
            *)
              echo "trash: invalid option -- '${opts:0:1}'" >&2
              echo "Try 'rm --help' for more information." >&2
              return 1
              ;;
          esac
          opts="${opts:1}"
        done
        ;;
      *) files+=("$arg") ;;
    esac
  done

  if [[ ${#files[@]} -eq 0 ]]; then
    echo "trash: missing operand" >&2
    echo "Try 'rm --help' for more information." >&2
    return 1
  fi

  local status=0
  for f in "${files[@]}"; do
    if [[ ! -e "$f" && ! -L "$f" ]]; then
      if [[ $force -eq 0 ]]; then
        echo "trash: cannot remove '$f': No such file or directory" >&2
        status=1
      fi
      continue
    fi

    if [[ -d "$f" ]]; then
      if [[ $recursive -eq 0 && $dir_mode -eq 0 ]]; then
        echo "trash: cannot remove '$f': Is a directory" >&2
        status=1
        continue
      fi
      if [[ $dir_mode -eq 1 && $recursive -eq 0 &&
        -n "$(ls -A "$f" 2>/dev/null)" ]]; then
        echo "trash: cannot remove '$f': Directory not empty" >&2
        status=1
        continue
      fi
    fi

    if [[ $interactive -eq 1 ]]; then
      local ftype="regular file"
      [[ -d "$f" ]] && ftype="directory"
      read -r -p "trash: remove $ftype '$f'? " answer
      [[ "$answer" =~ ^[Yy] ]] || continue
    fi

    local name dest
    name=$(basename "$f")
    # 同秒に同名ファイルを複数処理した場合の衝突を避けるためPIDを含める。
    dest="$trash_dir/$(date +%Y-%m-%dT%H%M%S)_$$_${name}"
    if mv -- "$f" "$dest"; then
      [[ $verbose -eq 1 ]] && echo "removed '$f'"
    else
      status=1
    fi
  done

  return "$status"
}
alias rm=trash

# ECRにログインし、以降のDockerコマンドにも専用設定を使う。
# 引数: ECRレジストリ、任意のAWS profile。失敗時は環境変数を変えない。
ecrlogin() {
  if [[ $# -lt 1 || $# -gt 2 || ($# -eq 2 && -z "$2") ]]; then
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
  /usr/share/bash-completion/completions/kubens; do
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
