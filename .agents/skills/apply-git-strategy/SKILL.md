---
name: apply-git-strategy
description: Git操作の許可範囲と、既存ブランチ・PR・worktreeを使う作業場所を確認する。リポジトリでの実装・修正・PRレビュー・ローカル検証の着手や再開、ブランチ作成・切替、worktree準備、ステージ・commit・push・merge、Git作業の完了報告・引き渡しの前に使う。命名やmise・dotfilesの配置も対象。
---

# Gitと作業場所のルール

読み取りを含むGit操作とGit管理ファイルの編集の前に、`references/git-policy.md`の「Git操作の許可範囲」と実行条件を読む。既定とリポジトリ別の例外は同資料で管理する。それ以外は必要な場面の資料だけを読む。

実装・修正・PRレビュー・ローカル検証に着手・再開するときは、編集の有無にかかわらず、作業場所を選ぶ前に`references/worktree.md`の「作業開始」を読む。ブランチ作成・切替やworktree準備の前も同様とする。既存ブランチ・open PRの再利用と別ブランチへ分離する際の許可条件は、同資料で管理する。

| 場面                                            | 資料                                                         |
| ----------------------------------------------- | ------------------------------------------------------------ |
| 編集開始・ブランチ作成前・既存PRへの対応・worktreeの準備と再利用・整理候補・成果物の保存 | `references/worktree.md` |
| ブランチ・コミット・タスク・スキルの命名        | `references/naming.md`                                       |
| commit・merge・push、個人設定の反映、操作の委譲 | `references/git-policy.md`、`references/commit.md` |
| ステージ後の報告、未コミットの変更を残す完了報告・引き渡し | `references/git-policy.md`の「ステージ後の報告」。操作を依頼しない状態報告にも適用する |
| PR作成・本文更新・Ready化の案内                 | `prepare-pr-for-review`、`references/pr-workflow.md`         |
| AGENTS.md・スキル・hookの作成や更新             | `write-agent-instructions`                                   |

dotfiles・個人ツールの変更では、着手前に`~/.agents/skills/write-agent-instructions/references/context-policy.md`の配置判断と時間帯を確認する。

編集後は変更先と差分を確認する。設定移行の反映確認には`~/.agents/skills/write-agent-instructions/references/context-policy.md`の「端末への反映確認」を使う。

miseやdotfilesのファイル配置を変更する前にも、同資料の「端末への反映確認」を読み、配置定義と冪等性の条件を確認する。
