# Codex Desktop / CLI

## 共通指示

指示の本体は `.agents/AGENTS.md`。Linux / WSL は `bin/slink.sh` でCodexの設定ディレクトリへリンクする。
Windows は `win/link-codex-agents.ps1` を PowerShell から実行する。
既存ファイルは退避される。管理者 PowerShell で実行する。
PowerShell 7 と開発者モードを利用する場合は、通常権限でもリンク作成が可能。
`-ExecutionPolicy Bypass` は UNC 上のスクリプトをそのプロセスだけ許可する。

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File '\\wsl.localhost\archlinux\home\honahuku\git\honahuku\dotfiles\win\link-codex-agents.ps1'
```

スクリプトは自身の場所から本体を探すため、別の clone でも利用できる。
管理者 PowerShell は対象ユーザーと同じアカウントで起動する。
Windows の `CODEX_HOME` があればそちらを使い、なければ `$env:USERPROFILE\.codex` を使う。
WSL 内の本体をリンクした Windows 環境では、その WSL ディストリビューションが必要。
`AGENTS.override.md` が存在すると優先されるため、共通指示が反映されない場合は確認する。
変更後は新しい Codex セッションで読み込みを確認する。

## WSLで使うスキル

Windows版Codex Desktopのエージェント実行環境をWSLにすると、エージェントはWSL内で動く。
Codexの個人スキルは実行環境の `$HOME/.agents/skills` から読み込まれるため、Linux / WSLでは
`bin/slink.sh` が作る `~/.agents/skills` のリンクだけでCodex CLIとDesktopのWSL実行から使える。
同じスキルをWindows側の `%USERPROFILE%\.codex\skills` にも複製すると、同名スキルが二重に表示されることがある。
[Windows版DesktopのWSL実行](https://learn.chatgpt.com/docs/windows/windows-app)と
[Codexのスキル配置・探索](https://learn.chatgpt.com/docs/build-skills)を参照。
