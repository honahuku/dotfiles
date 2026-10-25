#!/usr/bin/env bash
# コミットされるファイル全体を検査し、未ステージの修正で検出を隠さない。
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
private_root="${DOTFILES_PRIVATE_ROOT:-}"
# GUIからのcommitでも検査できるよう、シェルの初期化には依存しない。
if [[ -z "$private_root" ]]; then
  private_candidates=""
  if [[ -d "$HOME/git" ]]; then
    private_candidates="$(find "$HOME/git" -type d -name dotfiles-private -prune -print)"
  fi
  while IFS= read -r private_candidate; do
    [[ -d "$private_candidate" ]] || continue
    if [[ -n "$private_root" ]]; then
      echo "multiple private configuration repositories; set DOTFILES_PRIVATE_ROOT" >&2
      exit 2
    fi
    private_root="$private_candidate"
  done <<<"$private_candidates"
fi
patterns_file=""
if [[ -n "$private_root" ]]; then
  patterns_file="$private_root/config/public-forbidden-patterns.txt"
  if [[ ! -s "$patterns_file" ]]; then
    echo "missing or empty patterns file: $patterns_file" >&2
    exit 2
  fi
else
  echo "SKIP: private pattern check (dotfiles-private not found under ~/git)" >&2
fi
mode="${1:---staged}"
repository="${2:-.}"
violations=0

check_text() {
  [[ -n "$patterns_file" ]] || return 0
  local label="$1"
  local content="$2"
  local result=0
  local matches
  matches="$(rg --line-number --only-matching --text --ignore-case --file "$patterns_file" <<<"$content")" || result=$?
  if [[ "$result" == 0 ]]; then
    printf 'forbidden content: %s\n' "$label" >&2
    printf '%s\n' "$matches" >&2
    # 最初の違反で停止すると、後続ファイルの修正対象を見落とすため最後に失敗させる。
    violations=1
  elif [[ "$result" != 1 ]]; then
    exit "$result"
  fi
}

if [[ "$mode" == "--check-text" ]]; then
  text="$(cat)"
  check_text "standard input" "$text"
  exit "$violations"
fi
if [[ "$mode" == "--check-skill-text" ]]; then
  jq --raw-input --slurp --from-file "$script_dir/../config/check-skill-language.jq"
  exit
fi
if [[ "$mode" != "--staged" && "$mode" != "--worktree" && "$mode" != "--all" ]]; then
  echo "usage: $0 [--staged|--worktree|--all] [REPOSITORY]" >&2
  exit 2
fi
repository="$(git -C "$repository" rev-parse --show-toplevel)"
# worktree直下の.gitは管理用ファイルのため、配下の.gitだけを別リポジトリの混入として検出する。
nested_git_paths="$(find "$repository" -mindepth 2 -name .git -print)"
if [[ -n "$nested_git_paths" ]]; then
  echo "public candidate contains nested Git repositories:" >&2
  echo "$nested_git_paths" >&2
  exit 1
fi
# 除外を固定リストにすると、自作スキルまで誤って除外し続けるため両定義を照合する。
if [[ "$mode" == "--staged" ]]; then
  vendir_roots="$(git -C "$repository" show :vendir.yml | yq -r '.directories[].path' -)"
  locked_roots="$(git -C "$repository" show :vendir.lock.yml | yq -r '.directories[].path' -)"
else
  vendir_roots="$(yq -r '.directories[].path' "$repository/vendir.yml")"
  locked_roots="$(yq -r '.directories[].path' "$repository/vendir.lock.yml")"
fi
paths=()
if [[ "$mode" == "--staged" ]]; then
  mapfile -d '' -t paths < <(
    git -C "$repository" diff --cached --name-only --diff-filter=ACMR -z
  )
elif [[ "$mode" == "--all" ]]; then
  mapfile -d '' -t paths < <(
    git -C "$repository" ls-files --cached --others --exclude-standard -z
  )
else
  mapfile -d '' -t paths < <(
    git -C "$repository" diff HEAD --name-only --diff-filter=ACMR -z
    git -C "$repository" ls-files --others --exclude-standard -z
  )
fi

declare -A seen=()
for path in "${paths[@]}"; do
  [[ -z "${seen[$path]:-}" ]] || continue
  seen["$path"]=1
  imported=false
  while IFS= read -r root; do
    [[ "$root" == .agents/skills/* ]] || continue
    if [[ "$path" == "$root/"* ]] &&
      rg --quiet --fixed-strings --line-regexp -- "$root" <<<"$locked_roots"; then
      imported=true
      break
    fi
  done <<<"$vendir_roots"
  [[ "$imported" == false ]] || continue
  check_text "path: $path" "$path"
  if [[ "$path" == vendor/* || "$path" == */.git/* ||
    "$path" == .gitmodules || "$path" == .worktree/* ]]; then
    echo "external or local repository path: $path" >&2
    violations=1
    continue
  fi
  if [[ "$mode" == "--staged" ]]; then
    content="$(git -C "$repository" show ":$path")"
  elif [[ -L "$repository/$path" ]]; then
    content="$(readlink -- "$repository/$path")"
  else
    content="$(cat -- "$repository/$path")"
  fi
  check_text "file: $path" "$content"
  if [[ "$path" == .agents/skills/*.md || "$path" == .agents/skills/*/agents/openai.yaml ]]; then
    if ! jq --raw-input --slurp --from-file "$script_dir/../config/check-skill-language.jq" <<<"$content"; then
      echo "skill language check failed: $path" >&2
      violations=1
    fi
  fi
done

if [[ "$violations" != 0 ]]; then
  exit 1
fi

echo "public candidate passed ($mode)"
