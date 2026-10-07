# dotfiles

Linux、WSL2、Windows向けの個人設定を管理します。

## セットアップ

Linux / WSLでは、リポジトリをcloneしてリンクスクリプトを実行します。

```sh
git clone https://github.com/honahuku/dotfiles.git ~/git/honahuku/dotfiles
cd ~/git/honahuku/dotfiles
./bin/slink.sh
```

既存設定の扱いやNeovim、aqua、Windows、Codexの手順は[セットアップガイド](docs/setup.md)と[Codexの設定](docs/codex.md)を参照してください。

## 主な構成

```text
.
├── .agents/
│   └── skills/
├── bin/
├── docs/
├── nvim/
│   ├── lua/
│   │   ├── config/
│   │   ├── platform/
│   │   ├── plugins/
│   │   └── util/
│   └── tests/
└── win/
```
