---
name: build-anki-decks
description: 過去問を原文のままAnkiデッキへ取り込む、または理解や想起が難しいカードを修復するときに使う。
---

# 原文を保持したAnkiデッキ

原本の問題・選択肢・公式解答・公式解説を保持する。問題番号など明示された例外を除き、短縮・訂正・言い換えをしない。不確実な文字や解答との対応を推測で補わず、確認済みの記録だけを出力する。

| 作業 | 資料 |
| --- | --- |
| PDF・JSONからデッキを作成 | `references/create-deck.md` |
| 原文保持カード・派生カードの修復 | `references/repair-workflow.md`、`references/repair-mode.md` |
| JSONディレクトリの入力処理 | `references/json-directory-input.md` |
| PDF抽出・画像からの文字起こし・下書き確認 | `references/extraction-workflow.md` |
| 問題文と選択肢の保持 | `references/verbatim-mcq.md` |
| CSVの列・フィールド・出力条件 | `references/output-schema.md` |
| ノートタイプ・テンプレート・取り込み確認 | `references/anki-import.md` |
| 試験日から収録範囲を決める | `references/exam-strategy.md` |
| 明示依頼または修復で補助カードを作る | `references/card-design.md` |

派生した穴埋め知識カードは`build-anki-cloze-decks`で別に作り、原文保持デッキへ混ぜない。付属の表面・裏面HTMLとCSSは`assets/`にある。資料不足や部分出力の可否、取り込み形式は、該当資料の確認条件を守る。
