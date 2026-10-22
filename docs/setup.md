# セットアップ

Linux / WSLで[Git](https://git-scm.com/downloads)と[mise 2026.10.17以降](https://mise.jdx.dev/installing-mise.html)を用意する。Windowsへの配置もWSLから行う。

```sh
git clone https://github.com/honahuku/dotfiles.git ~/git/honahuku/dotfiles
cd ~/git/honahuku/dotfiles
# 配置予定の確認、設定配置、miseとaquaの管理対象ツール導入をまとめて行う。
mise run setup
```

private設定を併用する場合は、公開側を適用する前にprivate側のセットアップ手順を使う。

認証情報は復元されない。GitHub・Codex・クラウドなどは利用時にログインする。Neovimの初回起動後は`:Lazy sync`と`:checkhealth`を実行する。

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
