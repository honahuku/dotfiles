# CSVとノートタイプの取り込み条件

CSVは通常のカスタムノートタイプへ取り込むデータであり、`.apkg`ではなく、ノートタイプを自動作成しない。個人情報保護士では大文字小文字を含め次の列順を使う。

`Question,Option1,Option2,Option3,Option4,CorrectOptionIndex,OfficialAnswer,OfficialExplanation,Source,Topic,Priority,NeedsReview,Tags`

`Tags`は通常フィールドとして作らず、必ず右端のAnki専用タグ列にする。原文保持カードには試験タグと明示された課題タグを付け、派生カードには最後に`generated`を追加する。`Option5`〜`Option8`は作らない。

表面は`Question`と空でない選択肢を表示する。裏面には`{{FrontSide}}`、`<hr id=answer>`、`OfficialAnswer`、`OfficialExplanation`、`Source`を含める。標準の解答表示を使い、JavaScriptボタン、`pycmd('ans')`、`sessionStorage`を既定にしない。プレビュー、AnkiWeb、モバイルで動かない場合があるためである。

HTMLはカードテンプレート編集欄、CSSはスタイル欄へ設定し、CSVの取り込みは一度だけ行うと説明する。`{{#Option4}}...{{/Option4}}`などの条件付き置換で空の選択肢を隠す。取り込み前にノートタイプの列順と`#columns:`を照合し、`#tags column:13`が専用タグに対応することを確認する。不一致ならノートタイプの訂正を求め、未知のノートタイプへ位置だけで取り込まない。[取り込み手順](anki-import.md)で固定設定と取り込み後の確認を行う。
