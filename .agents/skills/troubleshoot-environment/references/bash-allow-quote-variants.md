---
name: feedback-bash-allow-quote-variants
description: Bash allow パターン登録時はダブルクォート有無の両方を用意する
metadata:
  node_type: memory
  type: feedback
  originSessionId: 24115e60-afb3-4be3-8afb-d8efd517d49d
---

# Bashの許可パターンと引数の引用符

`settings.json` の `permissions.allow` にある `Bash(...)` パターンは、実行されたコマンド文字列に対する前方一致で、シェルのクォートは剥がされずそのまま比較される。`Bash(gh api --method PATCH notifications/threads/*)` のようにクォート無しで登録すると、`gh api --method PATCH "notifications/threads/123"` のようにダブルクォート付きで実行された場合はマッチせず確認プロンプトが出る。

**Why**: sync-github agent が `gh api --method PATCH "notifications/threads/24435886358"` を実行した際、ダブルクォート無しパターンしか登録されておらず確認が発生した。以前「クォートの有無は関係なくマッチする」と誤って説明したことがあるが、実際は文字列単位の前方一致なので関係がある。

**How to apply**: 引数がダブルクォートで囲まれる可能性のあるコマンド（`gh api` の JSON パスパラメータなど）を allow に登録するときは、ダブルクォート無し版とダブルクォート付き版の両方を登録する。逆に単一の呼び出し元（固定スクリプト等）しか叩かないコマンドなら、その呼び出し元の実際の引数形式を確認してから1パターンだけ登録すればよい。
