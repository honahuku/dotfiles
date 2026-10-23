# JSONディレクトリからの入力

文字起こし済みJSONのディレクトリから、個人情報保護士の通常の原文保持CSVを作る場合に使う。

## 入力記録

指定ディレクトリ直下の`*.json`だけを使い、子ディレクトリと他の形式は無視する。`question1.json`・`question2.json`・`question10.json`のような自然順で処理する。

通常問題の形式

```json
{
  "type": "normal",
  "has_explanation": true,
  "question_text": "問題１．...",
  "choices": ["ア. ...", "イ. ...", "ウ. ...", "エ. ..."],
  "correct_answer": "エ",
  "explanation": "問題１．正解　エ ..."
}
```

任意の`topic`・`priority`・`task`はメタデータに使える。`tags`は使わず、試験回数と明示された課題から出力タグを決める。

共通本文付き小問の形式

```json
{
  "type": "bundle",
  "has_explanation": true,
  "passage": "問題98〜100. ...",
  "questions": [
    {
      "question_no": 98,
      "keyword": "WAF",
      "choices": ["ア. ...", "イ. ...", "ウ. ...", "エ. ..."],
      "correct_answer": "エ",
      "explanation": "WAFとは..."
    }
  ]
}
```

`questions`の各要素を一つの記録へ展開する。`Question`は次の形式で共有本文、問題識別子、キーワードを結合する。各原本フィールドは書き換えない。

```text
<passage>

問題<question_no>. <keyword>
```

小問の`topic`・`priority`・`task`を優先し、なければ共通記録の値を継承してから既定値を使う。未知の`type`、`true`以外の`has_explanation`、`questions`の欠落、空のbundleはエラーにする。

## 正規化

通常問題と展開した各小問を、標準の十三列へ対応付ける。

| CSVの列 | JSONとの対応 |
| --- | --- |
| `Question` | 通常問題は`question_text`先頭の番号を正規化。bundleは上記の結合結果。その後に空行一つと`第<回>` |
| `Option1`〜`Option4` | `choices`の四要素を原本順に保持 |
| `CorrectOptionIndex` | `correct_answer`から求める1始まりの番号 |
| `OfficialAnswer` | `correct_answer`を変更せず使用 |
| `OfficialExplanation` | `explanation`を変更せず使用 |
| `Source` | `input_json_file=<absolute path>;input_json_sha256=<64-hex-digest>;question=<ID>` |
| `Topic` | `topic`。なければ空文字列 |
| `Priority` | `priority`。なければ`medium` |
| `NeedsReview` | 下記の検証をすべて通過した場合だけ`false` |
| `Tags` | `第<回>回個人情報保護士`。課題が明示された場合だけ`課題I`・`課題II`を追加 |

JSONファイルのパスを原本パスとし、`sha256sum`でダイジェストを求める。通常問題の識別子は`question_text`から一意に読める問題番号を使い、それ以外はJSONファイル名を使う。bundleの小問は`Q<question_no>`にする。

試験回数は明示されたユーザー入力を優先し、次に原本ファイル名や入力ディレクトリの一意な回数表記を使う。例として`/tmp/privacy_guardian_transcription/80`は試験タグ`第80回個人情報保護士`、問題末尾`第80回`となる。一意に決められなければ止めて確認する。分野、曖昧なファイル名断片、既存の`tags`から回数を作らない。

個人情報保護士の`Question`先頭だけを`問題<N>. `へ正規化する。数字はASCII半角、問題と数字の間は空白なし、半角ピリオドの後は半角空白一つとする。`問題 28. `・`問題２８．`・`問題28．`・`問題28。`などを受け付ける。後続の問題表記、本文の句読点、選択肢ラベル、解説見出し、空白は正規化しない。

続けて末尾に空行一つと回数行を追加する。

```text
<question text with normalized leading marker>

第<回>
```

bundleでは結合した問題の末尾へ追加する。選択肢、公式解答、公式解説へ回数行を入れない。

`task`は小問、共通記録の順に読む。Unicodeのローマ数字、`課題I`、`課題II`、`I`、`II`を受け付け、タグを`課題I`・`課題II`へ統一する。値がなければ省き、その他の値は原本ファイルを示して止める。内容から推測しない。

`correct_answer`は`1`〜`4`、`A`〜`D`、`ア`〜`エ`、または一つの選択肢に完全一致する値だけを受け付ける。`OfficialAnswer`は原文を保ち、`CorrectOptionIndex`だけを正規化する。曖昧または未対応の値なら出力を止める。

問題番号と回数行以外の原本文字列を変えない。`ア.`を`ア．`へ変えたり、ラベルを削ったり、問題本文・解説見出しの句読点を統一したり、文字起こしの誤りに見える箇所を直したりしない。

## 出力前の検証

結合した記録配列を`jq -e`で検証する。

- 正規化後の各記録だけを`status: "ready"`にする。
- 原本の`has_explanation`が`true`である。
- 問題、四つの全選択肢、公式解答、公式解説が空でない文字列である。
- 問題がASCII数字の`問題<N>. `で始まり、空行と`第80回`などの回数行で終わる。
- 解答番号が1〜4の整数で、空でない選択肢を指す。
- 優先度が`high`・`medium`・`low`、`NeedsReview`がJSONの真偽値`false`である。
- 見える`Question`全文が一意である。
- 記録数が通常問題数と展開した全小問数の合計に一致する。
- `Option5`以降のフィールドがない。

失敗したら絶対パスと対象フィールドを示して止める。ファイルを黙って除外したり、一部だけの学習デッキを作ったりしない。検証後に[出力形式](output-schema.md)の原文保持CSV形式と`jq @csv`を使う。

## ファイルの収集と保存

入力ディレクトリを収集前に絶対パスへ解決し、各`Source`にその原本パスを保持する。中間の一覧、正規化済み記録、検証ログ、一時CSVは`mktemp`で作った作業領域に置く。最終CSVは別途指定がなければJSON原本と同じディレクトリに保存する。

試験日が明示入力または一意な原本ファイル名から分かる場合は`第<回>回個人情報保護士_<YYYYMMDD>.csv`、不明なら`第<回>回個人情報保護士.csv`にする。UTF-8のCSVとし、Ankiファイルヘッダーは次と完全一致させる。

```text
#separator:Comma
#html:true
#columns:Question,Option1,Option2,Option3,Option4,CorrectOptionIndex,OfficialAnswer,OfficialExplanation,Source,Topic,Priority,NeedsReview,Tags
#tags column:13
```
