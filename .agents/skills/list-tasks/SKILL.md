---
name: list-tasks
description: 未完了・完了タスクや、依頼者・保存元・タグで絞ったローカルタスク一覧を確認するときに使う。
---

タスク一覧を表示する。

絞り込み: $ARGUMENTS

引数なし → open タスクを queue_pos 昇順（due overdue は先頭に浮上）で一覧表示。id を必ず表示する。

`tasks list` は常に `{"tasks": [...]}` 形式の JSON を返す。`.tasks[]` でアクセスする。`--format` は渡さない（無効なオプションで `_warning` フィールドが混入する）。

タスクは `queue_pos` 昇順でソートされる。overdue（due < today）のタスクは queue_pos に関わらず先頭に浮上する。絞り込みは `--from others|me`・`--source`・`--tag`・`--status`。`--layer` と `--importance` は廃止済み。

どの入口でも pending の滞留チェックをする。`updated_at` が1週間以上動いていない pending は `open` に戻り、結果 JSON の `_stale_unblocked`（`id` / `title` / `blocked_by` / `stale_days`）に出る。あれば「<title> が <stale_days> 日動いてないので候補に戻しました。状態を確認してください」と1行添える。

引数がある場合は、次のように絞り込む。
- `all` / "全部" → done/cancelled を含む全件
- `done` / "完了" → status=done のみ
- `GitHub` / `github` → source=github のみ
- `Notion` / `notion` → source=notion のみ
- タグ名 → そのタグを持つタスクのみ

## しないこと

- `--format` フラグを渡さない
- `--layer` / `--importance` フラグを渡さない（廃止済み）
- プランニング（キャパ判定・タイムライン）はしない（それは `/todo` の役割）
