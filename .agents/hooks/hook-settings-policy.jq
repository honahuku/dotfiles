# 設定変更だけを対象とし、説明用コードを含む一般文書は拒否しない。
def deny_hook_settings:
  (.tool_input.file_path // "") as $path
  | (.tool_input.command // .tool_input.cmd // "") as $patch
  | (
      (.tool_input.new_string // "") + "\n" +
      (.tool_input.content // "") + "\n" + $patch
    ) as $payload
  | if (
      ($path | test("(^|/)(?:settings(?:\\.local)?|hooks)\\.json$"))
      or (
        .tool_name == "apply_patch"
        and ($patch | test("(?m)^\\*\\*\\* (?:Add|Update) File: .*\\b(?:settings(?:\\.local)?|hooks)\\.json$"))
      )
    )
    and ($payload | test("\"command\"[[:space:]]*:[[:space:]]*\"(?:[^\"[:space:]]*/)?(?:bash|sh|zsh|dash)[[:space:]]+[^\"\\n]*\\.sh"))
  then {
    hookSpecificOutput: {
      hookEventName: "PreToolUse",
      permissionDecision: "deny",
      permissionDecisionReason: "hookはスクリプトのパスを直接指定する。インタプリタ経由で実行権限の付与を迂回しない。必要なchmodは本人へ依頼する。"
    }
  } else empty end;
