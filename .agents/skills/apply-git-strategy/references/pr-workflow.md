# プルリクエストの作成・更新

## プルリクエスト

- draftを含むPRの新規作成・本文の作成や更新を始める前に、`prepare-pr-for-review`を読み、PR説明と確認項目の作成、セルフレビュー、PR本文の反映前後の確認に適用する。draft解除時まで読み込みを先送りしない。
- PR作成を依頼された場合はdraftで作る。Ready化はユーザーが行う。無断でReadyにしない。
- タイトルはIDがあれば `<type>(<ID>): <日本語説明>`、なければ `<type>: <日本語説明>` とする。
- テンプレートの探索と本文の構成は、執筆前に`write-technical-docs`の`references/pr-writing.md`「PR説明の構成」を確認する。
- 本文の執筆前と送信前に`review-output`の「説明先をまたぐ重複チェック」を行い、構成は`write-technical-docs`の「PR説明の構成」に従う。
- PR本文の確認項目は、`write-technical-docs`の`references/pr-writing.md`に従う。
- 投稿直前の最新状態の取得と二重投稿の確認は、`prepare-pr-for-review`の「PR / Issue への書き込み前の確認」に従う。
- **コメント投稿（新規コメント・レビュー返信を含む）は、文面を提示しユーザーがその場で投稿してよいと言うまで実行しない（共通のcommand-policy.md参照）。** 「直して」「反映して」はコード修正・コミット・pushまでの指示で、投稿の許可を含まない。
- レビューコメント・返信の文体は、共通資料`docs/agents/output-policy.md`の「レビュー返信コメント（Reviewee）」に従う。
- draft解除を案内する前に `prepare-pr-for-review` スキルを使う。
- 他人のPRをレビューするときは `review` スキルを使う。
- PRの署名など本名表記が必要な場合は、ユーザーに表記と公開可否を確認する。本名は許可された場面だけで使う。
