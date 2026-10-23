---
name: write-technical-docs
description: 技術文書・仕様書・実験レポート・PRやIssueの技術的な説明について、構成・事実・出典・検証結果を組み立てる。表現だけの確認はreview-outputを使う。
---

# 技術文書の作成と修正

このスキルは、技術文書に何をどの順で書くかを決め、コード・仕様・議論を根拠に本文を作成・修正する。事実と設計判断の区別、変更理由、出典、設定の関係、検証結果、技術日本語の表記を扱う。

主述・修飾・説明の過不足・重複・投稿先別の文体は`review-output`が担当する。技術的な内容を変えずに表現だけを確認する依頼では、そのスキルを使う。依頼別の使い分けは`review-output`の「依頼に応じた使い分け」を参照する。

## 技術文書を書くときの進め方

読み手と文書の用途を確認し、対象に応じて下表の資料を読む。執筆前に`review-output`の説明先をまたぐ重複チェックを行い、既存の説明を再作成せず、この文書に必要な技術内容を組み立てる。本文の作成後は`review-output`で文章を確認する。既に確認した項目は、内容が変わった場合に再確認する。

| 対象 | 資料 |
| --- | --- |
| 本文の構成・変更理由・コードコメントとの書き分け | `references/technical-writing.md` |
| PR説明・PR本文の確認項目 | `references/pr-writing.md`、`prepare-pr-for-review` |
| 実験・検証レポートの構成と図表 | `references/experiment-reports.md` |
| 複数レイヤーの設定の関係を説明する | `references/layered-settings.md` |
| 外部の実験データを脚注で引用する | `references/experimental-data-citations.md` |
| 出典・リンク・仕様の事実と用途別の含意 | `references/sources.md` |
| ディレクトリ図・折りたたみ見出し | `references/formatting.md` |
| レビュー指摘に応じた修正 | `references/review-response.md` |
| 技術日本語の表記と専用prh検査 | `references/technical-japanese.md` |

技術文書を保存するときは、`yomiyasu`と技術日本語の検査を行う。手順・コメント・PR説明のように並列関係が明確な箇条書きを、文章の比率だけで崩さない。
