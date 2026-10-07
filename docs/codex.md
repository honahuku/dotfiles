# Codex Desktop / CLI

## 共通指示をリンクする

共通指示は [`.agents/AGENTS.md`](../.agents/AGENTS.md) で管理します。Linux / WSLでは `bin/slink.sh` がCodexの設定ディレクトリへリンクします。WindowsではPowerShellから `win/link-codex-agents.ps1` を実行してください。

Windowsで実行する例です。

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File '\\wsl.localhost\archlinux\home\honahuku\git\honahuku\dotfiles\win\link-codex-agents.ps1'
```

この例は、WSLのディストリビューション名が `archlinux` で、リポジトリを `/home/honahuku/git/honahuku/dotfiles` にcloneした場合のパスです。別の場所にcloneした場合は、実際のパスに置き換えてください。リンクスクリプトは自身の場所からリポジトリを特定します。

対象ユーザーと同じアカウントのPowerShellから実行してください。スクリプトは既存ファイルをバックアップへ移してからリンクします。シンボリックリンクの作成には管理者権限が必要な場合があります。PowerShell 7とWindowsの開発者モードを使えば、通常権限でも作成できます。

Windowsで `CODEX_HOME` を設定している場合、リンク先はそのディレクトリの `AGENTS.md` です。設定していない場合は `%USERPROFILE%\.codex\AGENTS.md` にリンクします。UNCパス上のスクリプトを実行する場合、`-ExecutionPolicy Bypass` はそのPowerShellプロセスだけに適用されます。

`AGENTS.override.md` は共通の `AGENTS.md` より優先されます。共通指示が反映されない場合は、対象ディレクトリにこのファイルがないか確認してください。リンク後、新しいCodexセッションを開きます。

Windowsでリポジトリをcloneし、リンクスクリプトを実行する手順は[新しい環境で dotfiles を使う](setup.md)を参照してください。

## WSLでスキルを使う

Windows版Codex DesktopでWSLを実行環境に選ぶと、エージェントはWSL内で動きます。Codexは実行環境の `$HOME/.agents/skills` から個人スキルを読み込みます。Linux / WSLでは `bin/slink.sh` が `.agents/skills/` をこの場所へリンクします。そのため、Codex CLIとDesktopのWSL実行環境で同じスキルを使えます。

同じスキルをWindows側の `%USERPROFILE%\.codex\skills` にも複製すると、Codexに同名スキルが重複して表示されることがあります。Windows DesktopからWSLで作業する場合も、WSL側でリンクしたスキルを使います。

[Windows版DesktopのWSL実行](https://learn.chatgpt.com/docs/windows/windows-app)と[Codexのスキル配置・探索](https://learn.chatgpt.com/docs/build-skills)も参照してください。
