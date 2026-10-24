---
name: apply-git-strategy
description: Git管理ファイルの編集前後、worktreeの準備・再利用・整理候補の確認、ブランチ・タスク命名、commit・merge・push・PR操作の前に使う。
---

# Gitと作業場所のルール

Git管理ファイルを編集する前に、登録済みworktree内のパス、適用される指示、既存差分を確認する。mainへ直接編集しない。`~/git/*`のGit書き込みは既定ではステージだけとし、通常の実装依頼で操作権限を広げない。リポジトリ別の例外は`git-policy.md`の参照先で確認する。

Git内部状態を書き換える前は、worktree作成も含めて`~/.agents/docs/common/git-policy.md`を読む。それ以外は必要な場面の資料だけを読む。

| 場面                                            | 資料                                                         |
| ----------------------------------------------- | ------------------------------------------------------------ |
| 編集開始・worktreeの準備・再利用・整理候補・成果物の保存  | `references/worktree.md`                                     |
| ブランチ・コミット・タスク・スキルの命名        | `references/naming.md`                                       |
| commit・merge・push、個人設定の反映、操作の委譲 | `~/.agents/docs/common/git-policy.md`、`references/commit.md` |
| PR作成・本文更新・Ready化の案内                 | `prepare-pr-for-review`、`references/pr-workflow.md`         |
| AGENTS.md・スキル・hookの作成や更新             | `write-agent-instructions`                                   |

個人用設定の改善では、着手前に`~/.agents/docs/common/context-policy.md`の時間帯を確認する。環境固有のGit制限・自動反映の例外が必要なら、非公開資料の`global-policy`と`apply-git-strategy`の該当セクションを読む。

編集後は変更先と差分を確認する。commit・push・merge・PR・Issue作成は、それぞれの操作が恒常的な例外か本人の明示指示で許可された場合だけ実行する。
