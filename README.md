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

スクリプトはシェル、エディター、エージェント関連の設定をホームへリンクする。
Codex Desktop / CLI固有の設定とWindowsのWSL実行については [docs/codex.md](docs/codex.md) を参照。
