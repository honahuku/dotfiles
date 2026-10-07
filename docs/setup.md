# 新しい環境で dotfiles を使う

cloneしたリポジトリの設定を使うには、ホームディレクトリへのリンクと必要なツールの導入を行います。Linux / WSLでは `bin/slink.sh` を実行してください。Windowsでは、専用スクリプトでCodexの共通指示をリンクします。

このリポジトリでは設定と導入方法を管理し、外部OSSのソースコードやGitサブモジュールは含めません。ツール本体は各プロジェクトの公式配布元から導入します。

## Linux / WSL

### 1. リポジトリをcloneする

Gitが使える状態で、次を実行します。

```sh
mkdir -p ~/git/honahuku
git clone https://github.com/honahuku/dotfiles.git ~/git/honahuku/dotfiles
```

すでにclone済みの場合、この手順は不要です。

### 2. 設定をホームにリンクする

既存の `~/.bashrc` にマシン固有の設定がある場合は、リンクの前に `.bashrc.local` へ保存します。dotfilesの `.bashrc` は、起動時にこのファイルを読み込みます。

```sh
if [ -f ~/.bashrc ] && [ ! -e ~/.bashrc.local ]; then
  cp -p ~/.bashrc ~/.bashrc.local
fi
~/git/honahuku/dotfiles/bin/slink.sh --backup
```

`--backup` を付けると、既存のリンク先を同じディレクトリに `.backup-日時` の名前で退避してからリンクします。既存のリンク先を残す場合は `--backup` を外してください。リンク先がすでにある項目はスキップされ、正しいリンクは再実行後もそのままです。

[`bin/slink.sh`](../bin/slink.sh) は次のリンクを作ります。

| ホーム側のリンク先 | リポジトリ内のリンク元 |
| --- | --- |
| `~/.bashrc` | `.bashrc` |
| `~/aqua.yaml` | `aqua.yaml` |
| `~/.config/alacritty/alacritty.toml` | `alacritty/alacritty.toml`（ファイルがある場合） |
| `~/.config/nvim` | `nvim/` 全体 |
| `~/.agents/skills` | `.agents/skills/` |
| `${CODEX_HOME:-$HOME/.codex}/AGENTS.md` | `.agents/AGENTS.md` |

リンク元のファイルがリポジトリにない項目はスキップします。現在はAlacrittyの設定ファイルがないため、Alacrittyのリンクは作られません。

### 3. aquaとCLIを導入する

[`aqua.yaml`](../aqua.yaml) には、aquaで管理するCLIとバージョンが記録されています。aqua本体は一覧に含まれないため、先に[公式のインストール手順](https://aquaproj.github.io/docs/install/)で導入します。dotfilesの `.bashrc` はaquaのbinディレクトリを `PATH` に追加します。新しいシェルを開くか、次を実行してください。

```sh
source ~/.bashrc
aqua --version
```

必要なコマンドだけ入れる場合は、ホームディレクトリで実行します。

```sh
cd ~
aqua install stylua tflint
```

`aqua install` に引数を付けない場合、`aqua.yaml` にあるすべてのCLIを導入します。定義しているのはGitHub CLI、Terraform、Codex CLI、StyLua、TFLintなどです。aquaはカレントディレクトリから親ディレクトリへ設定ファイルを探します。ホームの `aqua.yaml` を使う場合は `cd ~` して実行してください。[aquaの設定探索とinstall](https://aquaproj.github.io/docs/reference/config/)も参照してください。

### 4. Neovimを導入する

Neovim本体はaquaの管理対象ではありません。利用するLinuxディストリビューションの手順に従い、NeovimとGitを導入します。Arch Linuxでは次のコマンドを使います。

```sh
sudo pacman -S --needed git neovim
```

他のOSやディストリビューションでは[Neovimの公式インストールガイド](https://github.com/neovim/neovim/blob/master/INSTALL.md)を参照してください。

### 5. Neovimとプラグインを起動する

```sh
nvim
```

初回起動時、[`nvim/init.lua`](../nvim/init.lua) がlazy.nvimを取得します。[`nvim/lua/config/lazy.lua`](../nvim/lua/config/lazy.lua) はLazyVimとリポジトリ内のプラグイン定義を読み込みます。初回起動にはネットワーク接続が必要です。プラグインのバージョンは [`nvim/lazy-lock.json`](../nvim/lazy-lock.json) に記録したコミットで固定します。Neovim内で `:Lazy` を実行すると、プラグインの状態を確認できます。

Neovimの設定とプラグイン定義は `nvim/` で管理します。プラグイン本体とキャッシュはホームのNeovimデータディレクトリに保存し、リポジトリには含めません。プラグインは設定に応じて必要なタイミングで読み込みます。

Masonが管理するLSPサーバーやフォーマッターなど、追加ツールが必要になる場合があります。CLIをaquaで管理するときは、`aqua.yaml` に追加し、`aqua install <command>` を実行してください。Neovim本体、Git、aqua本体は `aqua.yaml` に含まれていません。

WSLのクリップボード連携は、`win32yank.exe` が `PATH` にある場合に有効になります。IME連携も、対応するWindows側のコマンドがある場合に有効になります。どちらもNeovimの起動には必要ありません。

導入後は次のコマンドで確認できます。

```sh
readlink -f ~/.config/nvim
nvim --version
command -v stylua tflint
```

`readlink` の出力先が、cloneしたリポジトリの `nvim/` であることを確認してください。プラグインの状態はNeovim内の `:Lazy` で確認できます。

## WindowsのCodex

WindowsでCodex Desktop / CLIに共通指示を読み込ませる場合は、Windows側にリポジトリをcloneし、PowerShellからリンクスクリプトを実行します。

```powershell
New-Item -ItemType Directory -Path (Join-Path $HOME 'git\honahuku') -Force | Out-Null
$repo = Join-Path $HOME 'git\honahuku\dotfiles'
git clone https://github.com/honahuku/dotfiles.git $repo
& "$repo\win\link-codex-agents.ps1"
```

すでにclone済みの場合は、`git clone` を省略してください。clone先を変えた場合は、`$repo` を実際のパスに合わせます。[`win/link-codex-agents.ps1`](../win/link-codex-agents.ps1) は `.agents/AGENTS.md` を `%USERPROFILE%\.codex\AGENTS.md` にリンクします。`CODEX_HOME` が定義されていれば、そのディレクトリがリンク先です。既存ファイルがある場合、スクリプトはバックアップを作成します。

Windowsでシンボリックリンクを作るには、管理者権限が必要な場合があります。PowerShell 7とWindowsの開発者モードを使う場合は、通常権限で作成できます。

このスクリプトがリンクするのはWindowsのCodex共通指示だけです。Neovimやシェルの設定はWindows側に展開しません。aquaの `openai/codex` はCodex CLI用で、Codex Desktopはインストールされません。CodexとWSLの実行環境、スキルの配置は[Codexの設定手順](codex.md)を参照してください。リンク後、新しいCodexセッションを開くと指示が読み込まれます。

## Windows用ファイルを個別に使う

`win/` には、アプリの一括導入やWindowsの設定変更に使う既存バッチがあります。dotfilesのcloneや基本リンクには使わず、内容を確認してから実行してください。[`win/chocolatey.bat`](../win/chocolatey.bat) はアプリを導入し、レジストリも変更します。[`win/scoop.bat`](../win/scoop.bat) にはGitの初期化・追加コマンドがあります。Codexの指示だけをリンクするときは `win/link-codex-agents.ps1` を使います。

## 設定ファイルの場所

| 目的 | ファイル |
| --- | --- |
| Neovimの設定とプラグイン定義 | `nvim/` |
| aquaで管理するCLIとバージョン | `aqua.yaml` |
| Linux / WSLのリンク処理 | `bin/slink.sh` |
| Codexの共通指示とスキル | `.agents/` |
| WindowsのCodex共通指示リンク | `win/link-codex-agents.ps1` |

リンクしたファイルを編集すると、リポジトリ内のファイルが更新されます。ツールやプラグイン本体は設定ファイルとは別に導入します。各バージョンは `aqua.yaml` と `nvim/lazy-lock.json` で管理します。
