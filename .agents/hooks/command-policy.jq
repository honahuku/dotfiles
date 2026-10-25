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
    | test("[;&|()\\n]")
  );

def targets_git_main_checkout($path):
  ($path | test("(^|/)git/[^/]+/[^/]+/"))
  and (($path | test("(^|/)git/[^/]+/[^/]+/\\.worktree/")) | not);

def command_is($name):
  (only_reading_arguments | not)
  and test(
    "(^|[;&|()\\n])[[:space:]]*" +
    "(?:(?:if|then|elif|while|until|sudo(?:[[:space:]]+-[[:alnum:]_-]+(?:=[^[:space:]]+)?(?:[[:space:]]+[^[:space:]]+)?)*|command(?:[[:space:]]+-p)?|exec|env(?:[[:space:]]+-[iu0]+)*|time|nice|nohup)[[:space:]]+)*" +
    "(?:[A-Za-z_][A-Za-z0-9_]*=[^[:space:]]+[[:space:]]+)*" +
    "(?:[\\\"']?[^[:space:]\\\"';&|]+/)?[\\\"']?" + $name + "[\\\"']?([[:space:]]|$)"
  );

def policy_deny($reason):
  {hookSpecificOutput: {
    hookEventName: "PreToolUse",
    permissionDecision: "deny",
    permissionDecisionReason: $reason
  }};

def deny_sensitive_commands:
(.tool_input.command // .tool_input.cmd // "") as $command
| if (
    ((.tool_name == "Write" or .tool_name == "Edit")
      and ((.tool_input.file_path // "") | targets_git_main_checkout(.)))
    or (
      .tool_name == "apply_patch"
      and ($command | test("(?m)^\\*\\*\\* (?:Add|Update) File: [^\\n]*/git/[^/]+/[^/]+/(?!\\.worktree/)"))
    )
  ) then
    policy_deny("~/git配下のGit管理ファイルはmain checkoutで編集しない。登録済みworktree内のパスを指定する。")
  elif (
    (.tool_name == "Bash" or .tool_name == "exec_command" or .tool_name == "functions.exec_command")
    and ($command | has_shell_control_operator)
  ) then
    policy_deny("1回のexec_commandは単一コマンドにする。シェル演算子やコマンド置換を含む複合コマンドは拒否する。独立した処理は別々のツール呼び出しにする。")
  elif (
    (.tool_name == "Bash" or .tool_name == "exec_command" or .tool_name == "functions.exec_command")
    and ($command | ascii_downcase | command_is("aws"))
  ) then
    {
      hookSpecificOutput: {
        hookEventName: "PreToolUse",
        permissionDecision: "deny",
        permissionDecisionReason: "AWS CLIの実行を拒否した。検索語・通常の引数・ファイルパスにAWS CLI名が含まれるだけの読み取り操作は許可する。別名・ラッパー・別ツールでCLIを代行実行しない。CLIが必要なら、実行せず、本人がコピーして実行するコマンドを提示する。AGENTS.mdの「AWS CLIの手動実行」に従い、提示前に試行専用の絶対パスを確保し、標準出力・標準エラー・終了コードと実行条件をファイルへ保存する手順を付ける。ページャーと自動プロンプトを無効にし、--debugは通常付けない。「実行した」の返答後は既知の保存先を読み、結果の貼り付けを求めない。"
      }
    }
  elif (
    .tool_name == "apply_patch"
    and ($command | test("(?m)^\\*\\*\\* Delete File:"))
  ) then
    {
      hookSpecificOutput: {
        hookEventName: "PreToolUse",
        permissionDecision: "deny",
        permissionDecisionReason: "ファイル削除を含むapply_patch操作は実行しない。許可された確認・準備はCoding Agentsが実行してコマンドと結果を示し、本人操作だけを別のコードブロックで依頼する。削除はファイル・ディレクトリともrmで示し、trash aliasを保持する。rmの絶対パス指定・rmdir・alias迂回は提示しない。完了報告後の確認もCoding Agentsが行う。"
      }
    }
  elif (
    (.tool_name == "Bash" or .tool_name == "exec_command" or .tool_name == "functions.exec_command")
    and (
      ($command | command_is("terraform"))
      or ($command | command_is("kubectl"))
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
        permissionDecisionReason: "terraform・kubectlは読み取り・fmt・validate・plan・dry-runを含め実行禁止。wrapperやhookからも起動しない。必要な結果は対象headのCI実行とログで確認する。CIが未実行・skip・結果取得不可なら他の検査で代替せず停止して判断を仰ぐ。"
      }
    }
  elif (
    (.tool_name == "Bash" or .tool_name == "exec_command" or .tool_name == "functions.exec_command")
    and ($command | command_is("rm"))
  ) then
    {
      hookSpecificOutput: {
        hookEventName: "PreToolUse",
        permissionDecision: "deny",
        permissionDecisionReason: "ファイル削除は本人操作とする。許可された確認・準備はCoding Agentsが実行して結果を示し、削除だけをrmで依頼する。本人のtrash aliasを保持し、完了報告後の確認もCoding Agentsが行う。"
      }
    }
  elif (
    ($command | command_is("rg"))
    and ($command | uses_search_preprocessor)
  ) then
    policy_deny("検索の前処理から外部コマンドを起動しない。禁止CLIを別のツールで代行しない。")
  elif ($command | command_is("chmod")) then
    policy_deny("chmodは本人操作とする。必要な対象と理由を示し、実行権限の付与を依頼する。")
  elif ($command | command_is("(?:sh|bash|zsh|dash|ksh|fish|csh|tcsh)")) then
    policy_deny("シェルインタプリタの起動は禁止。実行権限のあるスクリプトを直接指定する。")
  elif ($command | command_is("rmdir")) then
    policy_deny("ディレクトリ削除は本人操作とする。管理元と影響を確認して手順を示す。")
  elif (
    ($command | command_is("git"))
    and ($command | test("(^|[[:space:]])(?:rm|rebase)([[:space:]]|$)"))
  ) then
    policy_deny("git rmとgit rebaseは禁止。削除は本人操作、履歴の取り込みは許可範囲内のmergeで行う。")
  elif (
    ($command | command_is("find"))
    and ($command | test("(?:-delete\\b|-exec[[:space:]]+(?:[^[:space:]]+/)?(?:rm|rmdir)(?:[[:space:]]|$))"))
  ) then
    policy_deny("find経由の削除も本人操作とする。別の起動方法で代行しない。")
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
