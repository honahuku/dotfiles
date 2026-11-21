# 引用されたオプションも調べ、検索パターンを示す--より後の引数と区別する。
def uses_search_preprocessor:
  [scan("\"(?:\\\\.|[^\"\\\\])*\"|'[^']*'|[^[:space:]]+")
    | sub("^[\"']"; "") | sub("[\"']$"; "")] as $args
  | ($args | index("--") // length) as $stop
  | any($args[:$stop][]; test("^--pre(?:=|$)"));

def only_reading_arguments:
  test("^[[:space:]]*(?:rg|grep|cat|jq)[[:space:]]")
  and (uses_search_preprocessor | not)
  and (test("\\$\\(|\u0060") | not)
  and (
    gsub("'[^']*'|\"(?:\\\\.|[^\"\\\\])*\""; "")
    | test("[;&|()\\n]") | not
  );

def has_shell_control_operator:
  ((gsub("'[^']*'"; "") | test("`|\\$\\(")))
  or (
    gsub("'[^']*'|\"(?:\\\\.|[^\"\\\\])*\""; "")
    | gsub("&&"; "")
    | test("[;&|()\\n]")
  );

def command_is($name):
  (only_reading_arguments | not)
  and test(
    "(^|[;&|()\\n])[[:space:]]*" +
    "(?:(?:if|then|elif|while|until|sudo(?:[[:space:]]+-[[:alnum:]_-]+(?:=[^[:space:]]+)?(?:[[:space:]]+[^[:space:]]+)?)*|command(?:[[:space:]]+-p)?|exec|env(?:[[:space:]]+-[iu0]+)*|time|nice|nohup)[[:space:]]+)*" +
    "(?:[A-Za-z_][A-Za-z0-9_]*=[^[:space:]]+[[:space:]]+)*" +
    "(?:[\\\"']?[^[:space:]\\\"';&|]+/)?[\\\"']?" + $name + "[\\\"']?([[:space:]]|$)"
  );

def aws_read_only:
  test("(^|[[:space:]])aws([[:space:]]+--[^[:space:]]+)*[[:space:]]+[^[:space:]]+[[:space:]]+(?:describe-|list-|get-|head-|search-|lookup-|query|scan|batch-get-|validate-|simulate-|estimate-|preview-|ls(?:[[:space:]]|$))");

def terraform_state_changing:
  test("(^|[[:space:]])terraform[[:space:]]+(?:apply|destroy|import|state|taint|untaint|force-unlock|workspace[[:space:]]+(?:new|delete))([[:space:]]|$)");

def kubectl_state_changing:
  test("(^|[[:space:]])kubectl([[:space:]]+--[^[:space:]]+)*[[:space:]]+(?:apply|create|delete|replace|patch|edit|scale|set|drain|cordon|uncordon|taint|label|annotate|rollout[[:space:]]+(?:restart|undo|pause|resume))([[:space:]]|$)");

def policy_deny($reason):
  {hookSpecificOutput: {
    hookEventName: "PreToolUse",
    permissionDecision: "deny",
    permissionDecisionReason: $reason
  }};

def deny_sensitive_commands:
(.tool_input.command // .tool_input.cmd // "") as $command
| if (
    (.tool_name == "Bash" or .tool_name == "exec_command" or .tool_name == "functions.exec_command")
    and ($command | has_shell_control_operator)
  ) then
    policy_deny("禁止対象のシェル演算子とコマンド置換は拒否する。独立した処理は別々のツール呼び出しにする。")
  elif (
    (.tool_name == "Bash" or .tool_name == "exec_command" or .tool_name == "functions.exec_command")
    and ($command | ascii_downcase | command_is("aws"))
    and (($command | aws_read_only) | not)
  ) then
    {
      hookSpecificOutput: {
        hookEventName: "PreToolUse",
        permissionDecision: "deny",
        permissionDecisionReason: "AWS CLIの状態変更操作は明示許可が必要。対象リソース・差分・影響・復旧方法を示して許可を得る。describe・list・getなどの読み取りは許可される。検索語やファイルパスにawsが含まれるだけの操作は対象外。"
      }
    }
  elif (
    (.tool_name == "Bash" or .tool_name == "exec_command" or .tool_name == "functions.exec_command")
    and (
      (($command | command_is("terraform")) and ($command | terraform_state_changing))
      or (($command | command_is("kubectl")) and ($command | kubectl_state_changing))
      or (
        ($command | command_is("tfcmt"))
        and ($command | test("--[[:space:]]+(?:[^[:space:]]+/)?terraform([[:space:]]|$)"))
      )
    )
  ) then
    {
      hookSpecificOutput: {
        hookEventName: "PreToolUse",
        permissionDecision: "deny",
        permissionDecisionReason: "terraform・kubectlの状態変更操作は明示許可が必要。対象環境・リソース・差分・影響・復旧方法を示して許可を得る。plan・validate・fmt・get・describe・logsなどの読み取りは許可される。"
      }
    }
  elif (
    ($command | command_is("rg"))
    and ($command | uses_search_preprocessor)
  ) then
    policy_deny("検索の前処理から外部コマンドを起動しない。禁止CLIを別のツールで代行しない。")
  elif (
    ($command | only_reading_arguments | not)
    and ($command | test("(?:^|[[:space:]])(?:--no-verify(?:[[:space:]]|$)|-c[[:space:]]+core\\.hooksPath=|LEFTHOOK(?:_EXCLUDE)?=|SKIP=)"))
  ) then
    policy_deny("hookの一時無効化や差し替えは禁止。検査を迂回せず、条件の修正案を提示する。")
  elif (
    ($command | command_is("git"))
    and ($command | test("(?:checkout.*-b|switch.*-c|worktree[[:space:]]+add.*-b|branch.*-[mM])[[:space:]]+[^[:space:]]*/[^[:space:]]*|\\bbranch[[:space:]]+(?:(?!-(?:a|r)(?:[[:space:]]|$)|--(?:list|all|remotes|contains|no-contains|merged|no-merged|points-at|show-current)(?:[=[:space:]]|$))--?[^[:space:]]+[[:space:]]+)*[^-[:space:]][^\\n;&|]*[/]"))
  ) then
    policy_deny("ブランチ名にスラッシュは使わない。ハイフンで区切る。")
  else
    empty
  end;
