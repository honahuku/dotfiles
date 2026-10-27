---
name: apply-git-strategy
description: Git操作の前に、読み取り・worktree作成・ステージ・commit・push等の許可範囲を確認する。Git管理ファイルの編集前後、ブランチ・タスク命名、PR操作にも使う。
---

# Gitと作業場所のルール

読み取りを含むGit操作とGit管理ファイルの編集の前に、`references/git-policy.md`の「Git操作の許可範囲」と実行条件を読む。既定とリポジトリ別の例外は同資料で管理する。それ以外は必要な場面の資料だけを読む。

| 場面                                            | 資料                                                         |
| ----------------------------------------------- | ------------------------------------------------------------ |
| 編集開始・worktreeの準備・再利用・整理候補・成果物の保存  | `references/worktree.md`                                     |
| ブランチ・コミット・タスク・スキルの命名        | `references/naming.md`                                       |
| commit・merge・push、個人設定の反映、操作の委譲 | `references/git-policy.md`、`references/commit.md` |
| PR作成・本文更新・Ready化の案内                 | `prepare-pr-for-review`、`references/pr-workflow.md`         |
| AGENTS.md・スキル・hookの作成や更新             | `write-agent-instructions`                                   |

dotfiles・個人ツールの変更では、着手前に`~/.agents/skills/write-agent-instructions/references/context-policy.md`の配置判断と時間帯を確認する。

編集後は変更先と差分を確認する。設定移行の反映確認には`~/.agents/skills/write-agent-instructions/references/context-policy.md`の「端末への反映確認」を使う。
