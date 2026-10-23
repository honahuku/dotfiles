---
name: todo
description: 明示された勤怠打刻と休暇取得を記録し、勤怠サマリーと退勤目安をObsidianの日次ノートへ保存する。
---

明示された勤怠打刻と休暇取得を記録し、当日の勤怠を確認して日次ノートを更新する。引数: $ARGUMENTS

## 手順

1. `env TZ=Asia/Tokyo date '+%Y-%m-%d %H:%M %u'` で今日の日付・時刻・曜日番号を得る。曜日番号 `1`〜`7` は順に月・火・水・木・金・土・日へ置き換える。
2. 引数から打刻と休暇取得を別々に抽出する。どちらも明示された値だけを記録し、Slack・Calendar・日次ノートから補わない。

   - `始業: YYYY/MM/DD HH:MM:SS` または `終業: YYYY/MM/DD HH:MM:SS`
   - `YYYY/MM/DD HH:MM 「...始業...」ボタンが押されました。` または終業の同形式
   - 終日有給: `有給` または `年次有給` と日付
   - 半日有給: `午前休` または `午前半休`、`午後休` または `午後半休`、日付
   - 終日代休: `代休` と日付
   - 半日代休: `代休` と `午前` または `午後`、日付
   - 時間休: `時間休` または `時間単位有給`、日付、整数の取得時間

   打刻は入力順を保ち、日付付きのまま `tasks work punches --punch "start:YYYY/MM/DD HH:MM:SS" --punch "end:YYYY/MM/DD HH:MM:SS"` に渡す。終業が始業日の翌日なら、終業を始業日の区間へ24時以降の時刻として保存する。翌日の始業は翌日の日付に別途保存する。日付は推測せず、秒は切り捨てる。[check-kintai](../check-kintai/SKILL.md) のStep Aで当月の所定勤務時間を確認する。未設定なら入力を推測せず、ユーザーに確認して `tasks meta set target_hours_<YYYY-MM> <時間数>` で保存してから続ける。午前休は12:00まで、午後休は13:00からの休暇として期間を保持する。半日休を時間休の4時間へ変換しない。
3. 休暇取得がある日付は、保存前に `tasks work show log --date <YYYY-MM-DD>` で既存記録を確認する。

   - 終日有給は `tasks work leave set --date <YYYY-MM-DD> --type paid`。
   - 午前有給は `tasks work leave set --date <YYYY-MM-DD> --type paid --period am`。
   - 午後有給は `tasks work leave set --date <YYYY-MM-DD> --type paid --period pm`。
   - 終日代休は `tasks work leave set --date <YYYY-MM-DD> --type comp`。
   - 午前代休は `tasks work leave set --date <YYYY-MM-DD> --type comp --period am`。
   - 午後代休は `tasks work leave set --date <YYYY-MM-DD> --type comp --period pm`。
   - 時間休は `tasks work leave set --date <YYYY-MM-DD> --type paid --hours <整数時間>`。30分単位に変換しない。

   終日・半日休暇は既存の勤務区間を置き換えるため、同じ日付に打刻や勤務区間があれば上書きせず確認する。半日休暇は所定労働時間の半分を休暇時間として記録し、`leave.period` に `am` または `pm` を保持する。時間休は既存の実働時間と合算され、実働の記録がない場合も休暇時間だけで記録される。保存後に同じログを再取得し、`leave.type`、`leave.hours`、必要な場合は `leave.period`、`hours` を照合する。
4. 打刻がある場合、保存前に対象となる全日付の `tasks work show log --date <YYYY-MM-DD>` を取得する。明示された打刻を時系列順に並べ、`start:`・`end:` と日付時刻を付けて1回の `tasks work punches` に渡す。終業だけが入力された場合は既存ログの始業日と時刻を確認し、その日付時刻を `start:` として加える。始業記録がなければ記録せず確認する。例: `始業: 2026/10/08 09:46:28`、`終業: 2026/10/09 00:55:45`、`始業: 2026/10/09 09:10:28` は、10/8の `09:46-24:55` と10/9の始業のみ `09:10` になる。日またぎ勤務は始業日にまとめ、24時超の区間でも休憩を1回だけ控除する。翌日の始業を前日の区間へ連結しない。コマンドは対象日の区間全体を置き換えるため、既存の区間も含めた保存内容に不明点があれば記録前に確認する。保存後に対象となる全日付のログを再取得し、始業日・終業時刻・翌日の始業・実働時間を照合する。打刻がない実行では勤怠ログを書き換えない。
5. [check-kintai](../check-kintai/SKILL.md) のStep B・Cに従い、未記録日・始業のみの日を確認してから勤怠サマリーを1回取得する。Step Aは直前に完了しているため重ねて実行しない。休暇だけの記録は未入力として扱わず、今日の始業のみは勤務中として扱う。Slack・Calendar・日次ノートから時刻を推定しない。詳細は同スキルのフィールド説明を使い、退勤時刻・累積時間・残営業日を計算し直さない。
6. 保存先は設定済みObsidian vaultの`daily/<YYYY-MM-DD>.md`。編集前に必ず現在の内容を読み、先頭の勤怠行・退勤行・朝会メモ見出しだけを更新する。既存の手書き内容は保持する。
7. 日次ノートの先頭を次の形式にする。値は取得した勤怠サマリーから埋める。
  ```md
  YYYY-MM-DD (曜) HH:MM ｜ あと X.Xh（今月 X.X/Y.Yh・残 N日・Z.Zh不足/貯金）
  HH:MM 退勤
  
  ## 明日の朝会メモ
  
  昨日やったこと 
  -  
  今日やること(会議は除外) 
  - 
  共有したいこと 
  - 
  困ってること 
  - 
  朝会で話したいこと
  - 
  
  ## 作業したPR
  - レビュイー(自分)
	  - 
  - レビュワー(メンバーからの依頼)
	  - 
  
  ```
   `あと X.Xh` は `today_plan.remaining_work_minutes` を60で割り、小数点以下1桁で切り捨てる。今月の実績は `today_plan.actual_cumul`、目標は `target_hours`、残日数は `remaining_workdays`、ペース差は `today_plan.pace_diff` を使う。`Z.Zh` はペース差の絶対値を小数点以下1桁で表示し、正なら貯金、負なら不足とする。数値計算には `bc -l` を使う。退勤時刻は `today_plan.clock_out_estimate` をそのまま使い、値がなければ退勤行を生成せず理由を伝える。`core_time_floored`・`capped_12h`・`flex_carryover_hours` が該当する場合は、[check-kintai](../check-kintai/SKILL.md) Step Dの注記を退勤行へ付ける。
8. 既存の朝会メモ本文は保持する。引数に明日の朝会メモがあれば見出しの下へ追記し、入力がなければ空の見出しだけを残す。
9. 保存後に `tasks vault-backup` を1回実行し、終了結果を確認する。

## 対象外

ローカルタスクの一覧・完了記録・並べ替え、GitHub・Calendar・Notionの取得や同期、作業時間の配分、休憩・予定の作成は行わない。

最後に日次ノートへのリンクと、未記録打刻・勤怠設定不足・保存失敗など対応が必要な点だけを返す。
