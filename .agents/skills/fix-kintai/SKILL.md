---
name: fix-kintai
description: 保存済み勤怠の打刻時刻・勤務区間の訂正や休日登録を依頼されたときに使う。
---

勤怠打刻を修正する。

修正内容: $ARGUMENTS

## コマンドマッピング

| 操作     | コマンド                                                                      |
| -------- | ----------------------------------------------------------------------------- |
| 時刻修正 | `tasks work set --date <YYYY-MM-DD> --segment "HH:MM-HH:MM" --source manual`  |
| 日削除   | `tasks work delete <YYYY-MM-DD>`                                              |
| 休日登録 | `tasks meta set holidays_<YYYY-MM> '[..., "YYYY-MM-DD"]'`（既存リストに追記） |

修正後は `tasks work summary` を再実行してペースを1行出す。

## しないこと

- Slack の打刻 API に書き込みをしない（読み取り専用）
- 修正後に `work summary` を再実行せずに終わらせない
- 休日登録の際に既存リストを上書きしない（追記する）
