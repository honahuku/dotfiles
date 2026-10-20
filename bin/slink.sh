#!/usr/bin/env bash
set -euo pipefail

DOTFILES="${DOTFILES:-$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)}"

if [[ "${1:-}" == "--backup" ]]; then
  echo "--backup は廃止しました。--dry-run で確認し、不要な競合対象を手動で rm してください。" >&2
  exit 2
fi

if ! command -v mise >/dev/null 2>&1; then
  echo "mise 2026.10.15 以降を導入してください: https://mise.jdx.dev/installing-mise.html" >&2
  exit 1
fi

exec mise -C "$DOTFILES" dot apply "$@"
