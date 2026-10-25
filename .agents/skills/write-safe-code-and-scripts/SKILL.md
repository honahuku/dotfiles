---
name: write-safe-code-and-scripts
description: コード・シェル・nvim設定・hook・Dockerfile・インフラ設定を作成・修正するときに、実行制約と検証手順を確認する。
---

# コードとスクリプトの編集・検証

既存コード、設定、スクリプトを編集する場合に使う。新規スクリプトを作る許可は、このスキルの適用とは別に確認する。作業用の一時スクリプトも対象とし、禁止コマンドを検証用という理由で起動しない。

| 場面 | 資料 |
| --- | --- |
| 新規スクリプトの作成、コマンド・ラッパーの実行 | `references/execution-constraints.md`、共通の`command-policy.md` |
| テキストファイルの編集 | 共通の`editing-policy.md` |
| 編集後のlint・fmt・スタイル確認、警告の判断 | `references/code-validation.md`、`references/languages.md`の該当言語 |
| Terraform・Kubernetes manifestの編集やmerge | `references/infrastructure.md` |

共通資料は`~/.agents/docs/common/`にある。インフラの検証では、禁止CLIの結果を対象SHAのCIで確認する条件を優先する。エラーや警告を隠さず、検査結果を確認してから成果物を提示する。
