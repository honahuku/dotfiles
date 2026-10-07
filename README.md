# dotfiles

個人用のLinux、WSL2、Windowsの設定を管理するリポジトリ。

## セットアップ

```sh
git clone https://github.com/honahuku/dotfiles.git ~/git/honahuku/dotfiles
~/git/honahuku/dotfiles/bin/slink.sh
```

## 公開対象

このリポジトリには、外部OSSをcloneしたディレクトリやGitサブモジュールを含めまない。
外部ツールは利用方法や設定だけを記録し、ソースコードは各プロジェクトの公式配布元から取得する。


## 既存のホームに展開する

`bin/slink.sh` は自身の場所からリポジトリを見つけ、設定をホームへリンクする。
通常は既存ファイルをスキップする。置き換える場合は `--backup` を指定すると、
既存ファイルを同じディレクトリの `.backup-日時` に退避する。再実行も可能。

既存 `.bashrc` のマシン固有設定を残す場合は、展開前に `.bashrc.local` に保存する。
このファイルは dotfiles の `.bashrc` から読み込まれる。既存 `.bashrc.local` は上書きしない。

```sh
test -e ~/.bashrc.local || cp -p ~/.bashrc ~/.bashrc.local
~/git/honahuku/dotfiles/bin/slink.sh --backup
```

リンク対象は `.bashrc`、`aqua.yaml`、Neovim、存在する場合の Alacritty、
`~/.agents/skills`、`${CODEX_HOME:-$HOME/.codex}/AGENTS.md`。
`.codex` 全体はリンクしないため、認証情報や履歴はそれぞれの環境に残る。

## Codex Desktop / CLI の共通指示

指示の本体は `.agents/AGENTS.md`。Linux / WSL は上記スクリプトでリンクする。
Windows は `win/link-codex-agents.ps1` を PowerShell から実行する。
既存ファイルは退避される。上記は管理者 PowerShell で実行する。
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
