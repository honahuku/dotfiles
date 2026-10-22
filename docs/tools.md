# ツールの役割と関係

| ツール | 用途 | このリポジトリでの管理元・使用例 |
| --- | --- | --- |
| [mise](https://mise.jdx.dev/) | 言語ランタイムとaqua本体の管理、設定配置、複数コマンドの実行 | [言語環境とaqua本体](../.config/mise/config.toml)、[配置設定](../mise.toml)、[タスク](../mise-tasks.toml) |
| [aqua](https://aquaproj.github.io/) | CLIのバージョン管理と導入 | [aqua.yaml](../aqua.yaml)でeza・chezmoi・uv・Neovim・Lefthookなどを管理 |
| [chezmoi](https://www.chezmoi.io/what-does-chezmoi-do/) | 設定ファイルの生成・配置と差分管理 | [Windows用テンプレート](../win/chezmoi/)をmiseのタスクから使用 |
| [uv](https://docs.astral.sh/uv/guides/scripts/) | Pythonの依存パッケージ管理と実行環境の用意 | `uv run --with pyyaml python3 …`で、PyYAMLが必要なスキル検証を実行 |
| [npx](https://docs.npmjs.com/cli/v11/commands/npx/) | npmパッケージが提供するコマンドの実行 | `npx --yes --package prh -- prh …`で文書を校正。Node.jsはmiseで管理 |
| [go-task](https://taskfile.dev/) | 複数コマンドや依存関係をTaskfileで定義して実行 | 本体はaquaで管理。現在のdotfilesセットアップはmiseのタスクを使用 |

導入のつながりは、mise → aqua → uvなどのCLIとなる。npxはNode.jsに付属するnpm経由で利用する。CLIを追加・変更するときの管理方針は[作業指示](../AGENTS.md)に従う。Renovateには[既存設定](../renovate.json)で[aqua向けプリセット](https://github.com/aquaproj/aqua-renovate-config)を導入している。

miseのタスクからも`aqua exec`で`aqua.yaml`のバージョンを使う。miseの[aquaバックエンド](https://mise.jdx.dev/dev-tools/backends/aqua.html)は、`aqua.yaml`とは別にバージョンを指定する仕組みなので、このCLI管理には使わない。

uv本体とPython本体のバージョンは別である。uvは[Pythonの取得・選択もできる](https://docs.astral.sh/uv/concepts/python-versions/)ため、処理が使うPythonはプロジェクトや実行時の指定で確認する。npxも、実行対象のnpmパッケージのバージョンとNode.jsのバージョンを別々に扱う。

実際の導入は[セットアップ](setup.md)、設定の更新と競合への対応は[配置手順](mise-dotfiles.md)を参照する。
