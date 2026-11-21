---
name: write-safe-code-and-scripts
description: コード・シェル・nvim設定・hook・Dockerfile・インフラ設定を作成・修正するときに、実行制約と検証手順を確認する。
---

# コードとスクリプトの編集・検証

既存コード、設定、スクリプトを編集する場合に使う。新規スクリプトも依頼の範囲と可逆性を確認して扱う。作業用の一時スクリプトも対象とし、起動前に内容と副作用を確認する。

| 場面 | 資料 |
| --- | --- |
| 新規スクリプトの作成、コマンド・ラッパーの実行 | `references/execution-constraints.md`、共通の`~/.agents/skills/check-command-policy/references/command-policy.md` |
| テキストファイルの編集 | 共通の`~/.agents/skills/write-safe-code-and-scripts/references/editing-policy.md` |
| 編集後のlint・fmt・スタイル確認、警告の判断 | `references/code-validation.md`、`references/languages.md`の該当言語 |
| Terraform・Kubernetes manifestの編集やmerge | `references/infrastructure.md` |

コマンド実行の条件は`check-command-policy`を使う。インフラの検証では、`terraform`・`kubectl`の読み取り・planをローカルで実行でき、必要なCI結果も対象SHAで確認する。エラーや警告を隠さず、検査結果を確認してから成果物を提示する。
