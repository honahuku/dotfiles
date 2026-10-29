# 共通hookの判定

コマンド実行とhook設定の変更を、ツール固有の登録先から共通のjqフィルターで検査する。

- `command-policy.jq`：AWS CLI・terraform・kubectl、削除、実行権限変更、インタプリタ起動、複合コマンド、`~/git/<所有者>/<repo>/`直下のmain checkoutへの直接編集、検索の外部前処理、hook迂回、ブランチ名を判定する。
- `hook-settings-policy.jq`：設定への書き込みやパッチに含まれる、インタプリタ経由のhook起動を判定する。
- `guard.jq`：両方の拒否結果をまとめる。拒否理由がある場合だけJSONを返し、許可を先に返して後続の拒否判定を隠さない。

## 配置と登録

Codexの共通登録は`.codex/hooks.json`で管理し、miseで`~/.codex/hooks.json`へ配置する。

miseの`public-agent-hooks`グループで`~/.agents/hooks/`へ配置し、利用環境のPreToolUse登録から次のコマンドを呼ぶ。入力は既存の`tool_name`・`tool_input`形式を使う。ツール側のイベント・入力形式が違う場合は、登録側で対応を確認する。

```sh
# 共通の判定処理を使い、シェルスクリプトの実行権限を迂回しない。
jq -c -L "$HOME/.agents/hooks" -f "$HOME/.agents/hooks/guard.jq"
```

対象イベントはコマンド実行、ファイルの書き込み・編集、パッチ適用とする。既存の登録や専用のMCP検査を無効化しない。リンク適用と登録の再読み込み後に、実際のイベントで拒否・通過を確認する。JSON入力の検証成功だけで、実行中のセッションで有効だと判断しない。

## 回帰確認

危険なコマンドを実行せず、入力文字列として期待する判定と照合する。

```sh
mise run hooks:check
```
