# dotfilesの作業指示

- CLIは原則aquaで管理し、バージョン指定を`aqua.yaml`に集約する。既存のRenovate連携で更新を管理するため、miseのタスク内にCLIのバージョン指定を分散させない。aquaで扱えないCLIのみ別方式を検討する。
- gcloudは例外としてmiseのHTTPバックエンドで管理する。本体とバージョン情報はGoogle公式から取得し、非公式リポジトリのタグやフォークには依存しない。バージョンと取得設定は`.config/mise/config.toml`に集約する。
- miseは言語ランタイム・aqua本体の管理と設定配置に使う。miseで対応できない設定配置にはchezmoiを使う。
- 複数のコマンドで行う処理はmiseのタスクにまとめ、miseで対応できない場合に限りgo-taskを使う。
- シェルやPythonなどのスクリプトは、Git操作前のLefthookやCodexのhookなど、必要最小限の用途に限って作成・実行する。作成前には必ずユーザーの許可を得る。
- このリポジトリのIssueは、`.github/ISSUE_TEMPLATE/`内の用途に合うテンプレートに従う。作成・本文更新の前にテンプレートを読み、投稿直前の照合と投稿後の再取得確認を行う。
