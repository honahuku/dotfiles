# 言語別のlint・fmt・スタイルガイド

## 言語別のlint/fmt/スタイルガイド

| 言語 | lint | fmt | スタイルガイド |
|---|---|---|---|
| Dockerfile | `hadolint <file>` | (専用fmtは無し。公式ベストプラクティスに従い手で整える) | https://docs.docker.com/build/building/best-practices/ を編集時に読み、変更内容と照合する。Hadolintの実行だけで照合済みとしない |
| シェル(bash) | `shellcheck <file>` | (専用fmtは無し。2スペースインデント等はスタイルガイドに従い手で揃える) | https://google.github.io/styleguide/shellguide.html。shellcheck通過だけでは照合したことにならない。必ず個別に見る: 条件式は`[ ]`ではなく`[[ ]]`を使う、コマンド置換は`` ` ` ``ではなく`$( )`を使う、変数展開は常にダブルクォートする |
| JavaScript/TypeScript | `npx eslint <file>`(リポジトリに設定があれば使う) | `npx prettier --check <file>` | https://google.github.io/styleguide/jsguide.html (TSは https://google.github.io/styleguide/tsguide.html ) |
| Python | `ruff check <file>` または `pylint <file>`(リポジトリの既存設定に従う) | `ruff format <file>` または `black <file>` | https://google.github.io/styleguide/pyguide.html |
| Terraform/HCL | 利用可能な`tflint`。Terraform CLIによるfmt・validate・planはCI結果を確認 | Terraform CLIは実行せずCIの整形エラーを手で修正 | Google styleguideに個別がないため既存tfファイルの慣習に揃える |
| YAML | 一般YAMLは`yq eval '.' <file> > /dev/null`で構文確認。Kubernetes manifestは下記のCIと同じschema・policy検査も行う | リポジトリ指定の許可済みformatter | リポジトリの慣習に揃える |
| Lua(nvim設定) | (専用lintは無し。手順6のheadless起動でエラーが出ないことを確認する) | `stylua <file>` | (専用styleguideに個別が無いため既存ファイルの慣習に揃える) |

上記に無い言語は、ユーザーに使うツールを確認してから進める。推測でインストールしない。
