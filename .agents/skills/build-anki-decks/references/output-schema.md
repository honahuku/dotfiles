# Ankiの出力形式

原文保持の過去問と、LLMが作る学習カードは形式を分ける。

## 原文保持の選択問題

個人情報保護士ではUTF-8のCSVを使い、Ankiファイルヘッダーの後にデータ行を置く。`#columns:`の列順は大文字小文字を含め次のとおりとする。

`Question`、`Option1`、`Option2`、`Option3`、`Option4`、`CorrectOptionIndex`、`OfficialAnswer`、`OfficialExplanation`、`Source`、`Topic`、`Priority`、`NeedsReview`、`Tags`

`Tags`は常に右端にし、`#tags column:13`を指定する。`Option5`〜`Option8`は追加しない。

```text
#separator:Comma
#html:true
#columns:Question,Option1,Option2,Option3,Option4,CorrectOptionIndex,OfficialAnswer,OfficialExplanation,Source,Topic,Priority,NeedsReview,Tags
#tags column:13
```

`"Question","Option1",...`のような通常のヘッダー行は、ノートとして取り込まれるため出力しない。

### 原本のフィールド

`Question`の原文、`Option1`〜`Option4`、公式解答、公式解説はそのままコピーする。`Question`先頭の問題番号だけをASCII数字の`問題<N>. `へ正規化する。問題と数字の間に空白を置かず、半角ピリオドと半角空白一つを続ける。`問題 28. `・`問題２８．`・`問題28。`はいずれも`問題28. `になる。

原本の実際の番号を使い、後続本文を正規化したり、自作番号へ振り直したり、選択肢の順序を変えたりしない。番号は`Source`だけではなく、見える`Question`にも含める。個人情報保護士では末尾に空行一つと回数行を付ける。

```text
問題81. オフィス内の盗難の防止策に関する...

第81回
```

回数行はAnkiの重複検査用の追跡情報である。選択肢、公式解答、公式解説には付けず、`OfficialExplanation`内の問題番号も正規化しない。

### メタデータ

- `CorrectOptionIndex`: 1から数える1〜4の整数。正しい選択肢を示し、`OfficialAnswer`と一致させる。公式解答文の代わりにはしない。
- `Source`: 安定した追跡用文字列。PDF入力は`question_file=<absolute path>;question_sha256=<64-hex-digest>;question_pdf_page=<N>;question_printed_page=<N or ->;question=<ID>;answer_file=<absolute path>;answer_sha256=<64-hex-digest>;answer_pdf_page=<N or ->;answer_printed_page=<N or ->`の順にする。JSON入力は`input_json_file=<absolute path>;input_json_sha256=<64-hex-digest>;question=<ID>`にし、架空のPDFパス・ページを加えない。
- `Topic`: 短く読める分野名。LLMによる分類を認める。
- `Priority`: `high`・`medium`・`low`のいずれか。
- `NeedsReview`: JSONの真偽値。CSVでは小文字の`true`・`false`。抽出や解答対応が不確実なら`true`。
- `Tags`: Anki専用タグ。個人情報保護士では`第<回>回個人情報保護士`を必ず入れ、課題が明示された場合だけ`課題I`・`課題II`を続ける。分野名、従来の英語タグ、ファイル名、推測した課題を足さない。最後のCSV列にする。

検証が終わるまで作業記録はJSON配列で保持する。通常の学習用は`status: "ready"`、`NeedsReview: false`、空でない問題・公式解答・公式解説、有効な優先度、空でない選択肢を指す解答番号を満たす。個人情報保護士では問題先頭の番号と末尾の回数行も確認する。`Tags`は文字列にする。`NeedsReview: true`を別の確認用ファイルへ出すのは明示依頼時だけとする。

原文はJSONに保持し、Ankiの表示値だけ[原文保持の規則](verbatim-mcq.md)でHTMLエスケープする。出力前に`jq -e`で検証する。

```text
jq -e 'type == "array" and all(.[]; . as $row | ($row.status == "ready" and $row.NeedsReview == false) and (["Question","Option1","Option2","Option3","Option4","CorrectOptionIndex","OfficialAnswer","OfficialExplanation","Source","Topic","Priority","NeedsReview","Tags"] | all(. as $field | $row | has($field))) and ($row.Question | type == "string" and length > 0) and ($row.OfficialAnswer | type == "string" and length > 0) and ($row.OfficialExplanation | type == "string" and length > 0) and ([$row.Option1,$row.Option2,$row.Option3,$row.Option4] | map(select(type == "string" and length > 0)) | length >= 2) and ($row.CorrectOptionIndex | type == "number" and floor == . and . >= 1 and . <= 4) and ($row.Priority | . == "high" or . == "medium" or . == "low") and ($row.NeedsReview | type == "boolean"))' records.json
```

カンマ、引用符、改行を正しく扱うため、Ankiヘッダーと`jq -r`の`@csv`で出力する。検証中は一時出力を使い、最終CSVを入力規則の保存先へ置く。JSONディレクトリ入力の既定は原本と同じディレクトリである。

```text
{
  printf '%s\n' '#separator:Comma' '#html:true' '#columns:Question,Option1,Option2,Option3,Option4,CorrectOptionIndex,OfficialAnswer,OfficialExplanation,Source,Topic,Priority,NeedsReview,Tags' '#tags column:13'
  jq -r 'def e: gsub("&";"&amp;") | gsub("<";"&lt;") | gsub(">";"&gt;"); .[] | select(.status == "ready") | [(.Question|e),(.Option1|e),(.Option2|e),(.Option3|e),(.Option4|e),.CorrectOptionIndex,(.OfficialAnswer|e),(.OfficialExplanation|e),(.Source|e),(.Topic|e),.Priority,.NeedsReview,.Tags] | @csv' records.json
} > output.csv
```

ヘッダーの完全一致を確認し、その後のデータ行数を`ready`かつ`NeedsReview=false`の記録数と照合する。取り込み前にAnkiのプレビューを見る。`ready`以外を通常学習用に出さない。

見える`Question`全文が出力内で一意か確認し、可能なら取り込み済みの別回とも比較する。同じ一般的な問題文が別回にあっても、問題番号と回数行を残して重複扱いを防ぐ。

通常のカスタムノートタイプは`Tags`以外の通常フィールドを持つ。`Tags`を通常フィールドにしない。個人情報保護士の選択肢は最大四つとする。付属テンプレートは表面に問題と選択肢、裏面に`{{FrontSide}}`と公式解答・解説を表示する。クリック式の選択肢採点が使えるとはみなさない。

## 派生した学習カード

想起・区別用の生成を明示的に依頼された場合、または修復に必要な場合だけ使う。年、日付、条文番号、個数、穴埋め番号を含め、生成フィールドの数字をすべてASCII半角数字にする。原文保持フィールドには適用しない。

列順は`Front`、`Back`、`Source`、`Topic`、`CardType`、`Priority`、`Tags`とする。

```text
#separator:Comma
#html:true
#columns:Front,Back,Source,Topic,CardType,Priority,Tags
#tags column:7
```

`CardType`は`recall`・`distinction`にし、`original_question`と表示しない。試験に関連するタグは`第<回>回個人情報保護士 generated`、課題が明示されていれば`第<回>回個人情報保護士 課題I generated`などにする。試験タグを最初、`generated`を最後にする。

原文の過去問とはJSON配列とCSVを分ける。`status: "ready"`、空でない表面・裏面、有効なカード種別と優先度を確認してから、同じAnkiヘッダーと`jq @csv`の方法で七列を出力する。
