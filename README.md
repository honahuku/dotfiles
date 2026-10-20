# dotfiles

Linux、WSL2、Windows向けの個人設定を管理します。

## セットアップ

Linux / WSLでは、mise 2026.10.15以降を導入し、リポジトリをcloneします。

```sh
git clone https://github.com/honahuku/dotfiles.git ~/git/honahuku/dotfiles
cd ~/git/honahuku/dotfiles
mise trust
mise dot apply --dry-run
mise dot apply
```

既存設定の退避と公開・privateの併用は[miseによるリンク管理](docs/mise-dotfiles.md)を参照してください。ツールの導入は[セットアップガイド](docs/setup.md)、Codexは[Codexの設定](docs/codex.md)を参照してください。

## 主な構成

```text
.
├── .agents/
│   └── skills/
├── .config/
│   ├── lazygit/
│   └── mise/
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
    └── terminal/
```
