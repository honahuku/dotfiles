---
name: check-command-policy
description: コマンド実行・hook編集の前に、実行禁止、許可済みの例外、実行条件と出力を確認する。
---

# コマンドの実行条件を確認する

実行前に[コマンドと出力](references/command-policy.md#コマンドと出力)を読み、実行対象に関連するツール・操作の見出しを確認する。実行判断を説明するときは、参照した見出し名をMarkdownリンクで示す。シェル構文を含むコマンドでは、[シェルスクリプトとシェルコマンド](../write-safe-code-and-scripts/references/execution-constraints.md#シェルスクリプトとシェルコマンド)の原則も適用する。別ツール・ラッパー・サブエージェントで制限を迂回しない。

自動レビューへ実行要求を渡す前は、[外部の承認レビューへ渡す根拠](references/command-policy.md#外部の承認レビューへ渡す根拠)に従う。worktree内でも、禁止事項と許可例外の出典・適用条件を実行要求に添える。
