# Codex Desktop / CLI

## 共通指示をリンクする

共通指示は [`.agents/AGENTS.md`](../.agents/AGENTS.md) で管理します。Linux / WSLでは `bin/slink.sh` がCodexの設定ディレクトリへリンクします。WindowsではPowerShellから `win/link-codex-agents.ps1` を実行してください。

Windowsで実行する例です。

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File '\\wsl.localhost\archlinux\home\honahuku\git\honahuku\dotfiles\win\link-codex-agents.ps1'
```

この例では、WSLのディストリビューション名は `archlinux`、clone先は `/home/honahuku/git/honahuku/dotfiles` です。環境に合わせてパスを置き換えてください。リンクスクリプトは自身の場所からリポジトリを特定します。

対象ユーザーと同じアカウントのPowerShellから実行してください。スクリプトは既存ファイルをバックアップへ移してからリンクします。シンボリックリンクの作成には管理者権限が必要な場合があります。PowerShell 7とWindowsの開発者モードを使えば、通常権限でも作成できます。

Windowsで `CODEX_HOME` を設定している場合、リンク先はそのディレクトリの `AGENTS.md` です。設定していない場合は `%USERPROFILE%\.codex\AGENTS.md` にリンクします。UNCパス上のスクリプトを実行する場合、`-ExecutionPolicy Bypass` はそのPowerShellプロセスだけに適用されます。

`AGENTS.override.md` は共通の `AGENTS.md` より優先されます。共通指示が反映されない場合は、対象ディレクトリにこのファイルがないか確認してください。リンク後、新しいCodexセッションを開きます。

Windowsでリポジトリをcloneし、リンクスクリプトを実行する手順は[新しい環境で dotfiles を使う](setup.md)を参照してください。

## WSLでスキルを使う

Windows版Codex DesktopでWSLを実行環境に選ぶと、エージェントはWSL内で動きます。Codexは実行環境の `$HOME/.agents/skills` から個人スキルを読み込みます。Linux / WSLでは `bin/slink.sh` が `.agents/skills/` をこの場所へリンクします。そのため、Codex CLIとDesktopのWSL実行環境で同じスキルを使えます。

同じスキルをWindows側の `%USERPROFILE%\.codex\skills` にも複製すると、Codexに同名スキルが重複して表示されることがあります。Windows DesktopからWSLで作業する場合も、WSL側でリンクしたスキルを使います。

[Windows版DesktopのWSL実行](https://learn.chatgpt.com/docs/windows/windows-app)と[Codexのスキル配置・探索](https://learn.chatgpt.com/docs/build-skills)も参照してください。

## サンドボックスと承認を設定する

サンドボックスの制限と承認の確認を外すには、実行環境の `~/.codex/config.toml` に次の値を設定します。同名のキーがすでにある場合は、値を変更してください。

```toml
sandbox_mode = "danger-full-access"
approval_policy = "never"
```

`sandbox_mode = "danger-full-access"` は、コマンド実行時のファイルシステムとネットワークのサンドボックス制限を外します。`approval_policy = "never"` は承認の確認を省く設定です。`never` だけではサンドボックスの制限は外れません。

`approvals_reviewer = "auto_review"` は承認の審査方法を指定する設定です。この値を指定してもフルアクセスには切り替わりません。[OpenAI公式のサンドボックス・承認設定](https://learn.chatgpt.com/docs/sandboxing)

この組み合わせでは、コマンドが作業ディレクトリ外のファイルやネットワークにもアクセスできます。承認の確認が必要な環境では、`workspace-write` と `on-request` を選んでください。

### 設定と実際の権限が違う場合

Windows版DesktopでWSLを選ぶと、エージェントはWSL内で動きます。WindowsとWSLではホームディレクトリが異なるため、Windows側に加えてWSL側の `~/.codex/config.toml` も確認してください。[Windows版DesktopのWSL実行](https://learn.chatgpt.com/docs/windows/windows-app)

起動時の指定や信頼済みプロジェクトの `.codex/config.toml` が、ユーザー設定より優先される場合があります。組織の `requirements.toml` で制限される場合もあります。設定ファイルの値に加えて、セッションに適用されている権限も確認してください。[OpenAI公式の設定ファイルと優先順位](https://learn.chatgpt.com/docs/config-file/config-basic)

### コマンドが失敗した場合

GitHub CLIの `gh`、タスク実行ツールの `task`、CLI管理ツールの `aqua` などで通信・認証・書き込みのエラーが出た場合は、サンドボックス内の結果だけで認証情報が無効だと判断しないでください。

1. エラー全文、実行環境、適用されている権限を確認します。`task` の場合はタスク定義も読み、どの操作が実行されるか確認します。
2. 制限付きの環境で失敗した場合は、その操作をサンドボックス外で実行する許可がユーザーから得られているか確認します。許可があればCodexの権限昇格で再試行します。変更を伴うコマンドでは、再試行の前に一部の変更が完了していないか確認します。
3. サンドボックス外でも失敗した場合は、認証、通信、実行ファイルの配置を調べます。復旧後は中断した作業を再開します。

フルアクセスがすでに有効な場合は、追加でサンドボックスを解除しても解決しません。コマンド自体のエラーを調べてください。権限昇格が許可されていない環境では、必要な操作とエラーを示し、設定変更や手動実行を依頼します。
