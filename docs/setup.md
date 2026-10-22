# セットアップ

Linux / WSLのBash環境で設定を配置し、必要なツールを導入する。Windowsへの配置もWSLから行う。

## 初期準備

インターネット接続と、Git、OpenSSHクライアント、CA証明書、curl、jq、tar、gzip、unzip、xz、C/C++コンパイラー、make、pkg-configを用意する。システムパッケージの導入には管理者権限が必要になる。導入済みなら省略する。

<details>
<summary>Debian / Ubuntu</summary>

```sh
sudo apt update
sudo apt install -y bash git openssh-client ca-certificates curl jq tar gzip unzip \
  xz-utils build-essential pkg-config bash-completion
```

</details>

<details>
<summary>Arch Linux</summary>

部分更新を避けるため、システム更新も同時に行う。

```sh
sudo pacman -Syu --needed bash git openssh ca-certificates curl jq tar gzip unzip \
  xz base-devel bash-completion
```

</details>

[mise 2026.10.17以降](https://mise.jdx.dev/installing-mise.html)を導入する。既存のmiseが要件を満たす場合は再インストールしない。

```sh
curl -fsSL https://mise.run | sh
export PATH="$HOME/.local/bin:$PATH"
mise --version
```

## 設定とツールを導入する

private設定を併用する場合は、公開側を適用する前にprivate側のセットアップ手順を使う。公開設定だけを使う場合は、次を実行する。

```sh
git clone https://github.com/honahuku/dotfiles.git ~/git/honahuku/dotfiles
cd ~/git/honahuku/dotfiles
# 配置予定の確認、設定配置、miseとaquaの管理対象ツール導入をまとめて行う。
mise run setup
```

clone済みの場合は`git clone`を省略する。更新する場合は未コミットの変更を確認し、`git pull --ff-only`を使う。早送りできない場合は停止する。既存設定との競合には[配置手順](mise-dotfiles.md)に従って対応する。

`~/.bashrc`と`~/.profile`は実ファイルを残し、dotfilesを読み込む管理ブロックを追加する。適用前から開いていたBashには、`source ~/.bashrc`で設定を読み直すか、新しいシェルを開く。

<details>
<summary>Arch Linuxのログインシェルで設定を読み込む</summary>

標準の`~/.bash_profile`がある場合、ログイン時に`~/.profile`が自動で読み込まれない。既存の内容を残し、次の読み込みを追加する。すでに同等の処理があれば追加しない。

```sh
if [ -f "$HOME/.profile" ]; then
  . "$HOME/.profile"
fi
```

</details>

独自の`~/.bash_profile`や`~/.bash_login`を置いている場合も、そこから`~/.profile`が読み込まれることを確認する。

認証情報は復元されない。GitHub・Codex・クラウドなどは利用時にログインする。Neovimの初回起動後は`:Lazy restore`と`:checkhealth`を実行する。[`:Lazy restore`はロックファイルに記録したバージョンへ揃える](https://lazy.folke.io/usage)。Nerd Fontを使う場合は、表示する端末側にも設定する。

## WindowsのCodex

DesktopではWSLを実行環境に選ぶ。[共通指示とスキル](codex.md)の配置には上記セットアップを使う。

## Windows Terminal

初回セットアップで保存先を確認する。設定編集を終えてから適用する。

既定プロファイルは各PCのデフォルトWSLを使う。必要ならWindows側で`wsl --set-default <ディストリビューション名>`を実行する。[WSLの公式手順](https://learn.microsoft.com/windows/wsl/reference)を参照する。

## 設定と更新

| 対象 | 管理元 |
| --- | --- |
| 配置・競合への対応 | [配置手順](mise-dotfiles.md) |
| ツールの役割と管理元 | [ツールの説明](tools.md) |
| シェル | [shell/](../shell/) |
| Neovim設定 | [nvim/](../nvim/) |
| Windows Terminal設定 | [win/terminal/](../win/terminal/) |

## READMEのtreeを更新する

```sh
# miseがezaを用意し、Gitで無視された項目を除いたディレクトリだけを表示する。
mise run docs:tree
```

リポジトリ直下で実行し、出力でREADMEのtreeコードブロックを置き換える。深さは[`mise-tasks.toml`](../mise-tasks.toml)の`--level`で変更する。
