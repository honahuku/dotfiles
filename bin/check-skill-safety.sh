#!/usr/bin/env bash
set -euo pipefail

repository="${1:-$(git rev-parse --show-toplevel)}"

if ! git -C "$repository" rev-parse --show-toplevel >/dev/null 2>&1; then
  echo "not a Git repository: $repository" >&2
  exit 2
fi

# 旧配置を含む検査漏れを防ぐため、パスを限定せず全ステージ済みファイルを調べる。
# 語彙・日本語の例外判定は公開候補検査に集約する。

skill_files="$(git -C "$repository" diff --cached --name-only --diff-filter=ACMR)"
if [[ -z "$skill_files" ]]; then
  echo "no staged files"
  exit 0
fi

while IFS= read -r skill_file; do
  [[ -n "$skill_file" ]] || continue
  added_lines="$(git -C "$repository" diff --cached --unified=0 -- "$skill_file" | sed -n '/^+[^+]/s/^+//p')"
  [[ -n "$added_lines" ]] || continue

  match_status=0
  secret_matches="$(rg -n -e '-----BEGIN [A-Z ]+ PRIVATE KEY-----' -e 'gh[opsu]_[A-Za-z0-9_]{20,}' -e 'xox[baprs]-[A-Za-z0-9-]+' -e 'AKIA[0-9A-Z]{16}' <<<"$added_lines")" || match_status=$?
  if [[ "$match_status" != 0 && "$match_status" != 1 ]]; then
    exit "$match_status"
  fi
  if [[ -n "$secret_matches" ]]; then
    echo "file contains possible secret material: $skill_file" >&2
    echo "$secret_matches" >&2
    exit 1
  fi
done <<<"$skill_files"

echo "staged files passed leakage checks"
