---
name: done
description: ローカルタスクを完了にする依頼で、完了状態、日次ノート、残るworktreeを確認する。
---

タスクを完了にする。

対象: $ARGUMENTS

> **コマンド名の注意**: 完了は `tasks update <id> --status done` で行う。`tasks done <id>` という
> サブコマンドは**存在しない**（`tasks: error: invalid choice: 'done'` になる）。有効なサブコマンドは
> `add / list / update / reorder / delete / get / snooze / notif-keys / meta / work / daily / migrate`。
> 完了・status 変更はすべて `update --status <値>` を使う。
> - 正: `tasks update 77196739 --status done`
> - 誤: `tasks done 77196739`

- $ARGUMENTS が 8文字 hex（タスクID 形式）なら `tasks update <id> --status done` を直接実行
- それ以外（タイトル部分一致）なら `tasks list` で候補を抽出して、一意ならそのまま完了、複数なら ID を提示して確認
- 一致なしなら「該当なし」とだけ返す

引数が空なら未完了一覧を出してから ID を尋ねる。

## 完了後のデイリーノート更新

`tasks update --status done` が成功したら、今日のデイリーノートの `## 今日完了したタスク` に1行追加する。

1. `tasks meta get obsidian_vault_dir` でパスを確定する。値があれば `<vault>/daily/<today-YYYY-MM-DD>.md`、`null`なら非公開の個人資料の`done`セクションで代替保存先を確認する。保存先が不明なら推測せず、日次ノートの更新だけを停止する。
2. 対象ファイルをReadする。存在しない場合はこのセクションをスキップする。
3. `## 今日完了したタスク` セクションの表に、完了したタスクの行を追記する。完了時刻は現在時刻、タイトルは`source_url`があればMarkdownリンク、無ければ素のタイトルにする。
4. 他のセクションには触れない。

## 完了後のworktree確認

タスク完了後は、`apply-git-strategy`の`references/worktree.md`「タスクに対応する作業先」の照合方法で、完了タスクIDに対応するworktreeを確認する。ここでは作業先の新規作成・切り替えを行わない。

該当するものがあれば、同資料の「整理候補の確認」に従う。安全に整理できる候補だけ、対象・理由・本人操作の手順を示す。変更が残る場合、使用状況が不明な場合、該当するものがない場合は、worktreeについての通知を追加しない。

## 完了後の応答

完了したタスクと、日次ノートの更新結果を簡潔に伝える。未実行・失敗した処理があれば明記する。
