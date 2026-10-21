#!/usr/bin/env bash
# dotfiles-preflight-v2
set -euo pipefail

DOTFILES="${DOTFILES:-$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)}"

for argument in "$@"; do
  if [[ "$argument" != "--dry-run" ]]; then
    echo "使用法: $0 [--dry-run]（強制上書き・退避・削除は行いません）" >&2
    exit 2
  fi
done

if ! command -v mise >/dev/null 2>&1; then
  echo "mise 2026.10.15 以降を導入してください: https://mise.jdx.dev/installing-mise.html" >&2
  exit 1
fi

if ! command -v jq >/dev/null 2>&1; then
  echo "jq を導入してください。" >&2
  exit 1
fi

for source in "$HOME/git/honahuku/dotfiles/shell/profile.sh" \
  "$HOME/git/honahuku/dotfiles/shell/bashrc.sh" \
  "$DOTFILES/shell/profile.sh" "$DOTFILES/shell/bashrc.sh"; do
  if [[ ! -r "$source" ]]; then
    printf 'シェル設定の取得元がありません: %s\n' "$source" >&2
    exit 1
  fi
done

status=$(mise -C "$DOTFILES" dot status --json)
conflict=0
report_conflict() {
  local target="$1"
  printf '競合: %s\n' "$target" >&2
  if [[ -d "$target" && ! -L "$target" ]]; then
    printf '必要な内容を引き継いだ後で手動実行: rm -r -- %q\n' "$target" >&2
  else
    printf '必要な内容を引き継いだ後で手動実行: rm -- %q\n' "$target" >&2
  fi
  conflict=1
}

while IFS=$'\t' read -r target source mode state; do
  target="${target/#\~/$HOME}"
  source="${source/#\~/$HOME}"
  if [[ "$state" == "source_missing" ]]; then
    printf '取得元がありません: %s\n' "$source" >&2
    conflict=1
  elif [[ "$mode" == "symlink" && ( -e "$target" || -L "$target" ) && "$state" != "applied" ]]; then
    report_conflict "$target"
  fi
done < <(jq -r '.files[] | [.target, .source, .mode, .state] | @tsv' <<< "$status")

while IFS= read -r target; do
  target="${target/#\~/$HOME}"
  if [[ -e "$target" || -L "$target" ]]; then
    report_conflict "$target"
  fi
done < <(jq -r '.orphaned[]? | .target' <<< "$status")

# グループ配下の別リンクも、miseによる自動付け替えの前に検査する。
while IFS= read -r target; do
  target="${target/#\~/$HOME}"
  if [[ -L "$target" ]]; then
    report_conflict "$target"
    continue
  fi
  [[ -d "$target" ]] || continue
  while IFS= read -r -d '' link; do
    relative="${link#"$target"/}"
    managed=0
    matches=0
    while IFS= read -r source; do
      source="${source/#\~/$HOME}/$relative"
      if [[ -e "$source" || -L "$source" ]]; then
        managed=1
        if [[ "$(realpath -m -- "$link")" == "$(realpath -m -- "$source")" ]]; then
          matches=1
        fi
      fi
    done < <(jq -r --arg target "${target/#$HOME/\~}" '.files[] | select(.mode == "symlink-each" and .target == $target) | .source' <<< "$status")
    if [[ "$managed" == 1 && "$matches" == 0 ]]; then
      report_conflict "$link"
    fi
  done < <(find "$target" -type l -print0)
done < <(jq -r '.files[] | select(.mode == "symlink-each") | .target' <<< "$status")

for target in "$HOME/.bashrc" "$HOME/.profile"; do
  if [[ -L "$target" ]]; then
    printf '管理ブロックは既存リンクへ書き込めません: %s -> %s\n' "$target" "$(readlink -- "$target")" >&2
    printf 'リンク元を確認後、リンクだけを手動削除: rm -- %q\n' "$target" >&2
    conflict=1
  fi
done

mise -C "$DOTFILES" dot diff
if [[ "$conflict" != 0 ]]; then
  exit 1
fi
# 他のファイルを書き始める前に、実ファイルや壊れたマーカーの競合も検出する。
mise -C "$DOTFILES" dot apply --dry-run
if [[ "${1:-}" != "--dry-run" ]]; then
  exec mise -C "$DOTFILES" dot apply
fi
