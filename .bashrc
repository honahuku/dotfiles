# ~/.bashrc: executed by bash(1) for non-login shells.
# some more ls aliases
alias ll='ls -alF'
alias la='ls -A'
alias l='ls -CF'

# python aliases
alias py='python3'

# aqua
export PATH="${AQUA_ROOT_DIR:-${XDG_DATA_HOME:-$HOME/.local/share}/aquaproj-aqua}/bin:$PATH"

# asdf
[ ! -f "$HOME/.asdf/asdf.sh" ] || . "$HOME/.asdf/asdf.sh"
[ ! -f "$HOME/.asdf/completions/asdf.bash" ] || . "$HOME/.asdf/completions/asdf.bash"

# kubectx/kubens completion from a system-installed bash-completion package
for kubectx_completion in \
  /usr/share/bash-completion/completions/kubectx \
  /usr/share/bash-completion/completions/kubens
do
  if [[ -f "$kubectx_completion" ]]; then
    # shellcheck disable=SC1090
    . "$kubectx_completion"
  fi
done
unset kubectx_completion

# Machine-local settings (not tracked in dotfiles)
if [[ -f "$HOME/.bashrc.local" ]]; then
  . "$HOME/.bashrc.local"
fi
