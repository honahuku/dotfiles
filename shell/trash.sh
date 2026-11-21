# shellcheck shell=bash

# Bashのファイル削除関数をXDG Trashの操作として提供する。
#
# trashは対象をXDG Trashへ移動する。
# Globals: PATH。
# Arguments: rm互換のオプションと対象パス。
# Outputs: GIOのエラーと、-v指定時の移動結果を出力する。
# Returns: 成功時0、処理失敗時1、gio未導入時127。
# 既存の~/.trashは元パスの情報がないため、
# 自動移行しない。
trash() {
  local force=0 recursive=0 dir_mode=0 verbose=0 interactive=0
  local files=()
  local end_of_opts=0
  local arg f answer

  if ! command -v gio >/dev/null 2>&1; then
    echo "trash: gio is required to use the XDG Trash." >&2
    return 127
  fi

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
        -n "$(ls -A -- "$f" 2>/dev/null)" ]]; then
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

    if command gio trash -- "$f"; then
      [[ $verbose -eq 1 ]] && echo "removed '$f'"
    else
      status=1
    fi
  done

  return "$status"
}

alias rm=trash
