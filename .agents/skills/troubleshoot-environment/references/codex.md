# Codexの設定と実際の権限の調査

### Codexの設定を調べる場合

OpenAI公式の[サンドボックス説明](https://learn.chatgpt.com/docs/sandboxing)と[設定の優先順位](https://learn.chatgpt.com/docs/config-file/config-basic)を取得してから判断する。ユーザー設定、プロジェクト設定、セッションで実際に適用されている権限を区別する。

設定の調査・提案と、許可された設定変更は分けて扱う。変更後も、実際に適用されている権限を確認する。提案しただけで、現在のセッションの権限が変わったと扱わない。
