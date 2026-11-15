# Dotfiles 構造解説（Windows / WSL）

## ディレクトリ構成

```
honahuku/
├── agents/          # ✅ コモン：opencode skill data (.agents/* を移動)
│   ├── skills/     # opencode の skills データ
│   └── hooks.json  # codex hooks など
│
├── bin/             # tasks (コモン)
│
├── docs/            # ドキュメント (コモン)
│
├── .config/         # mise, nvim 設定など（コモン）
│   ├── mise/       # mise 設定
│   ├── nvim/       # neovim 設定
│   └── lazygit/    # lazygit 設定
│
├── linux/           # WSL/Linux 特有設定のみ
│   ├── bashrc.sh   # shell スクリプト（WSL）
│   └── profile.sh   # プロファイル設定
│
├── windows/         # Windows 特有設定のみ
│   ├── chezmoi/    # chezmoi テンプレートなど
│   └── terminal/   # PowerShell 統合用設定
│
├── shell/           # ✅ 共有シェル設定（保留）
│   ├── bashrc.sh   # bashrc の元ファイル
│   └── profile.sh  # profile の元ファイル
│
├── aqua.yaml        # ✅ コモン：aqua 依存定義（root で共有）
└── vendir.yml       # ✅ コモン：vendir 管理ファイル

.bashrc              # bash の起動ファイル（WSL）
.gitignore
AGENTS.md
lefthook.yml
mise-tasks.toml      # WSL/Windows 共通タスク定義
mise.toml            # mise の設定とシンボリックリンク定義
README.md
renovate.json
```

## 利用方法

### Linux / WSL での使用

```bash
# mise.toml を確認して、以下のように配置されることを確認
cd $HOME/.local/share/dotfiles

# シンボリックリンク展開：
# - agents/skills -> ~/.local/share/dotfiles/agents/skills
# - bin/tasks     -> ~/.local/bin/tasks
# - .bashrc/*     -> linux/bashrc.sh など
```

### Windows での使用

1. **mise をインストール**（別場所または新しいディレクトリ）
2. **mise.toml をコピー**：`C:\Users\<ユーザー名>\Documents\git\honahuku\dotfiles\mise.toml`
3. **必要な設定を適用**（PowerShell や chezmoi など）

詳細は `docs/windows.md` を参照してください。

## 設計思想

1. **コモンと OS 固有の切り分け**：
   - `agents/`, `bin/`, `docs/`, `.config/*` はコモン設定
   - `linux/` と `windows/` で OS 固有のファイルだけを保持
   
2. **WSL と Windows の完全分離**：
   - `/mnt` 経由での相互操作なし
   - WSL と Windows を独立した mise インストールで使用

3. **シンプルで保守しやすい**：
   - 深い階層にならないよう、必要なファイルだけ配置
   - シンボリックリンクとコピーを適切に使用

## 注意事項

- `shell/` フォルダは古い設定のため、必要に応じて削除・更新してください。
- Windows では `linux/bashrc.sh` は使用しない（または適宜調整）。
