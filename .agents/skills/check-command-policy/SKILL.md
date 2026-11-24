---
name: check-command-policy
description: コマンド実行・hook編集の前に、可逆性に基づく操作判断、実行条件、許可が必要な操作と出力を確認する。
---

# コマンドの実行条件を確認する

本人がpre-commitの実行を求めた場合は、対象リポジトリの設定を確認し、Lefthookが設定されていればLefthookのpre-commitも実行する。指定されたファイルや範囲を尊重し、他のツールを指定されている場合はその実行も検討する。

実行前に`references/command-policy.md`の該当するツールと操作の条件を読み、実行対象に関連する見出しを確認する。状態を変える操作では、[可逆性に基づく操作判断](references/command-policy.md#可逆性に基づく操作判断)を適用する。実行判断を説明するときは参照した見出し名をMarkdownリンクで示し、明示された許可を操作名だけを理由にした禁止で覆さない。シェル構文を含むコマンドでは、[シェルスクリプトとシェルコマンド](../write-safe-code-and-scripts/references/execution-constraints.md#シェルスクリプトとシェルコマンド)の原則も適用する。別ツール・ラッパー・サブエージェントで制限を迂回しない。適用中の上位指示にある禁止は変更しない。

コマンド実行後に`command not found`など実行ファイルの解決失敗が分かった場合は、利用不能と結論づけたり別経路で再試行したりする前に、[troubleshoot-environment](../troubleshoot-environment/SKILL.md)の[シェル初期化とCLIのPATH確認](../troubleshoot-environment/references/shell-initialization-and-cli-paths.md)を読み、起動モード・初期化ファイル・PATH・CLIの管理元を確認する。

自動レビューへ実行要求を渡す前は、[外部の承認レビューへ渡す根拠](references/command-policy.md#外部の承認レビューへ渡す根拠)に従う。worktree内でも、禁止事項と許可例外の出典・適用条件を実行要求に添える。
