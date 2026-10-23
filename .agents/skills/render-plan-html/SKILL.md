---
name: render-plan-html
description: PLANS.mdまたはplan.mdを変更せず、ローカルで確認するHTMLを生成・更新する。
---

# Markdown planをHTMLで表示する

Markdown形式のplanを、ローカルで確認しやすいHTMLへ変換する。目的、進捗、作業、依存関係、意思決定、発見事項、リスク、検証の各情報を、元ファイルの見出しと本文を保ったまま表示する。

## 入力ファイルの選択

- ユーザーがパスを指定した場合は、そのファイルだけを対象にする。
- パスが指定されていない場合は、現在のプロジェクト配下で`rg --files -g 'PLANS.md' -g 'plan.md'`を実行する。ホームディレクトリ全体は検索しない。
- 候補が0件なら、対象ファイルのパスを確認する。
- 候補が複数なら、候補をすべて示して選択を求める。ファイル名や更新日時だけで決めない。
- 対象はファイル名が正確に`PLANS.md`または`plan.md`のMarkdownファイルに限る。

## HTMLの生成と更新

- 変換前にMarkdownを読み、目的、対象範囲、作業、依存関係、意思決定、発見事項、リスク、検証に相当する見出しがあるか確認する。見出しがない情報を推測して追加しない。
- Markdownは読み取り専用で扱う。HTMLは入力ファイルと同じディレクトリに、拡張子を`.html`へ置き換えた名前で作成する。
- `scripts/render-plan-html.awk`を使い、見出し、チェックボックス、箇条書き、引用、表、コードブロック、段落をHTMLへ変換する。HTMLエスケープを適用し、Markdown本文をHTMLとして実行しない。
- HTMLには入力ファイルの絶対パス、SHA-256、生成時刻、`data-renderer="render-plan-html"`を記録する。
- HTMLがすでにあり、`data-renderer="render-plan-html"`が含まれる場合は、入力Markdownから再生成して更新する。それ以外のHTMLを上書きする前は、別用途のファイルでないか確認を求める。
- 生成途中の一時ファイルで変換結果を確認し、AWKがエラーを返した場合はHTMLを置き換えない。コードブロックが閉じていないなど形式を解釈できない場合は、原因を示して確認を求める。

生成例

```sh
set -eu

source="$(readlink -f "$source")"
source_sha256="$(sha256sum "$source" | awk '{print $1}')"
generated_at="$(date -Is)"
output="${source%.md}.html"
skill_dir=/absolute/skill-directory/render-plan-html
if awk -v source_path="$source" -v source_name="$(basename "$source")" \
  -v source_sha256="$source_sha256" -v generated_at="$generated_at" \
  -f "$skill_dir/scripts/render-plan-html.awk" "$source" > "$output.tmp"; then
  mv -- "$output.tmp" "$output"
else
  printf 'HTMLを更新しませんでした。変換結果は %s に残っています。\n' "$output.tmp" >&2
  exit 1
fi
```

## 表示確認

- 生成後にHTMLの存在、入力パス、SHA-256、見出し、未完了・完了チェックボックスを確認する。
- Codexのブラウザ表示機能で`file:///`から生成HTMLを開き、表示結果を確認する。表示機能が使えない場合は、HTMLファイルを指定してユーザーが開ける状態にする。
- 更新時はMarkdownの変更を読み直して同じHTMLを再生成し、Markdownの内容が変更されていないことと、HTMLのSHA-256が更新後の値になっていることを確認する。
