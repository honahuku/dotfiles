# セットアップ

Linux / WSLのBash環境で設定を配置し、必要なツールを導入する。Windowsへの配置もWSLから行う。

## 初期準備

インターネット接続と、Bash、Git、OpenSSHクライアント、CA証明書、curl、tar、gzip、unzip、xzを用意する。OSパッケージマネージャーの利用は、ブートストラップとOS統合に必要な最小限に留める。導入済みのものは再導入しない。jqなどのCLIはaquaから導入する。C/C++コンパイラー、make、pkg-configや開発用ライブラリは、ソースからのビルドが必要になった場合に追加する。

<details>
<summary>Debian / Ubuntu</summary>

```sh
sudo apt update
sudo apt install --no-install-recommends bash git openssh-client ca-certificates \
  curl tar gzip unzip xz-utils
```

</details>

<details>
<summary>Arch Linux</summary>

部分更新を避けるため、システム更新も同時に行う。

```sh
sudo pacman -Syu --needed bash git openssh ca-certificates curl tar gzip unzip xz
```

</details>

[mise 2026.10.17以降](https://mise.jdx.dev/installing-mise.html)を導入する。既存のmiseが要件を満たす場合は再インストールしない。

```sh
curl -fsSL https://mise.run | sh
export PATH="$HOME/.local/bin:$PATH"
mise --version
```

## 設定とツールを導入する

既存環境では、先に[管理元の移行](#既存環境の管理元を揃える)と設定の競合を確認する。

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

## 既存環境の管理元を揃える

CLIは`aqua.yaml`、言語環境とaqua本体は`.config/mise/config.toml`に従って導入する。初期セットアップは`mise run setup`を入口にする。独立したシェル・Pythonスクリプトを追加する前にmiseのサブコマンドとタスクで対応し、対応できない場合だけgo-taskを使う。

1. `type -a gh node go python nvim`などで実行候補を列挙し、シンボリックリンクの実体とパッケージ所有元を確認する。Archでは`pacman -Qo /usr/bin/gh`、Debian / Ubuntuでは`dpkg-query -S /usr/bin/gh`で確認できる。aqua・miseの設定だけに記載され、まだ導入されていない場合もあるため、設定と実行パスの両方を見る。
2. OS管理版とdotfiles指定版の一覧を作る。アンインストールを予定するパッケージの逆依存、任意依存、削除時に影響するコマンドを確認する。Archでは`pacman -Qi <package>`と`pacman -R --print <package>`、Debian / Ubuntuでは`apt-cache rdepends --installed <package>`と`apt-get --simulate remove <package>`を使う。これらは確認用であり、削除は実行しない。
3. 具体的な削除対象、導入先とバージョン差分、同時に削除されるパッケージ、利用できなくなる期間をユーザーに示し、アンインストールの許可を得る。許可を得るまで削除しない。OSのPythonなど、他のOSパッケージに必要な実体は残す。依存関係が解決できない場合は強制削除せず、その対象の移行を保留する。
4. 許可されたOS管理版をアンインストールしてから、`mise run setup`でaqua・mise管理版を導入する。依存・設定の自動削除や未承認パッケージの連鎖削除は行わない。ユーザーがインストールを自分で実行すると指定している場合は、エージェントはコマンドの提示まで行う。
5. 新しいシェルで`type -a gh node go python nvim`と各コマンドのバージョンを確認する。aqua・mise側が選ばれることと、必要な既存設定・認証情報が残っていることを確認する。nvmなど旧管理元の削除とプロジェクトのバージョン指定変更は、OSパッケージの移行とは別に対象を確認する。

設定配置前には`mise run setup:check`で差分を確認する。旧方式の`~/.bashrc`・`~/.profile`リンクがある場合は、リンク先と内容を保存したうえで実ファイルへの移行方法を決める。管理ブロックの追加によってリポジトリのリンク元を直接書き換えないようにする。ユーザー固有の設定を失う置換は行わない。

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
