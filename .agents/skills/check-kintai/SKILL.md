---
name: check-kintai
description: 勤怠ペースと退勤目安の確認、不在に伴うフレックス退勤予定の登録に使う。kintai-paceを探している場合も対象とする。
---

勤怠の保存先・集計規則・操作権限を確認し、不明な値はユーザーに尋ねる。

# 勤怠ペースの確認と退勤予定の登録

勤怠ペースの確認は、Step A → B → C → D の順で実行し、Step Dの最終結果だけ出力する。不在・早上がりの予定を登録する明示依頼は、先に「フレックス退勤予定の登録」を実行する。登録だけの依頼なら保存内容を確認して終了し、月次確認は行わない。

このスキルは業務上必要な勤怠ペースの確認に使うため、個人の業務効率化に関する時間帯制限の対象外とする。

追加指定: $ARGUMENTS

実打刻は `/todo` の直後に書かれた打刻行からだけ保存する。このスキルで保存できるのは、明示的に登録を依頼された将来の退勤予定だけとする。

## フレックス退勤予定の登録

1. 対象日と退勤希望時刻を確認する。「その時刻から不在」の依頼は開始時刻を退勤希望として扱う。途中で勤務を再開する予定や終日不在は、この形式へ変換せず確認する。
2. `tasks work show log --date <YYYY-MM-DD>` で既存記録を読む。実打刻や休暇がある日は上書きせず停止し、既存予定を変更する場合も保持すべき内容を確認する。
3. 始業予定は本人の明示指定を使い、指定がなければ `tasks meta get std_start` を確認する。未設定なら始業予定を質問し、過去の説明例から補わない。
4. `tasks work set --date <YYYY-MM-DD> --segment "<始業予定 HH:MM>-<退勤希望 HH:MM>" --planned --note "<明示された不在の時間帯・内容>"` で保存する。`--planned`を省略しない。不在の終了時刻は注記へ残し、勤務区間の終業には使わない。
5. 同日のログを再取得し、`planned: true`、`source: flex_plan`、勤務予定区間、注記を確認する。月次実績には加算されず、後日の実打刻保存で予定フラグが外れる。

予定は退勤目安の前借り計算に使われる。カレンダーへの予定作成や、有給・代休の登録は行わない。

## 勤怠ペースの確認

> **しないこと（勤怠ペース計算の前に確認する）**
> - `tasks work` で存在しないサブコマンド（`list` など）を推測で呼ばない（使えるのは `set / delete / show log / show unfilled-entries / summary` のみ）
> - work_log ファイルを `cat` / `jq` で直接読まない（AGENTS.md 制約）
> - Slack やカレンダーから勤務時刻を取得・推定して保存しない

**Step A: 月次確認**

`target_hours_<YYYY-MM>`が未設定なら、今月の所定勤務時間をユーザーに確認する。回答値を`tasks meta set target_hours_<YYYY-MM> <時間数>`で一つだけ保存してから続ける。設定済みなら再質問しない。

---

**Step B: 保存済み打刻の確認**

`tasks work show unfilled-entries --month <YYYY-MM>` で未記録日と始業のみの日を確認する。どちらも推定で埋めない。過去日の打刻が必要なら `/todo` に続けて実際の始業・終業時刻を入力してもらう。今日の始業のみの記録は勤務中として扱う。

---

**Step C: サマリー計算**（Step B 完了後に実行）

```sh
tasks work summary
```
返却フィールド: `target_hours`, `cumulative_hours`, `remaining_hours`, `remaining_workdays`, `today_target_hours`, `pace`（`on_track` | `behind` | `month_over_*`）。

当月かつ今日が残営業日なら `today_plan` も返る。退勤目安の補正（月初ペース・フレックス前借り・コアタイム下限・不在上限）はすべてツールが済ませた**補正後の値**を返す。スキルは計算せず、この値をそのまま Step D で整形する。

- `today_start` 今日の始業時刻（打刻済みなら打刻値、未打刻なら現在時刻）
- `clock_out_estimate` 補正後の退勤打刻の目安。月初ペース補正・フレックス前借り・コアタイム下限を織り込み済み。**生の均等割り値ではない。この値をそのまま使う**
- `work_end` 実働終端（`clock_out_estimate` − `wind_down_minutes`）。補正後
- `break_minutes` / `wind_down_minutes` 休憩分・退勤準備・片付け枠
- `pace_diff` 月初ペース差（正=貯金 負=不足）
- `actual_cumul` / `ideal_cumul` 月初ペースの実績・理想（2行目の表示に使う）
- `flex_carryover_hours` 今日に上乗せしたフレックス前借り（h）。前借りがある場合のみ
- `flex_deficit_hours` フレックス予定の前借り総量 D（h）。前借りがある場合のみ
- `capped_12h` 不足で12h上限に丸めたか（true なら「今日だけでは挽回不可」）
- `core_time_floored` コアタイム下限16:00に切り上げたか

`/check-kintai` はカレンダーの予定から不在時刻を渡さない。

---

**Step D: 出力**

退勤目安の計算（月初ペース補正・フレックス前借り・コアタイム下限・不在上限）はツールが済ませて `today_plan` に補正後の値を返す。スキルはここで計算しない。Step C で受け取ったフィールドを次のフォーマットに整形して出すだけ。

退勤目安を自分で計算し直したり、生の均等割り値を作り直したりしない。`today_plan.clock_out_estimate` がそのまま今日の退勤目安。過去に「生の値を使って退勤目安を過ぎたと誤判定する」事故があったため、計算はツールに任せて値を受け取るだけにする。

補正ロジックの詳細（式・配分の考え方）は、`type tasks`で確認した実体の`_pace_correction`・`_flex_carryover`・`_today_plan`にある。仕様を知りたいときはそちらを読む。計算はツールに集約し、スキル側では計算し直さない。

勤務ルールは保存データの`meta`へ明示的に設定する。未設定項目のエラーが出たら、`~/.agents/docs/work/tasks.md`を参照し、既存値を保持して不足分だけ設定する。

### D-3: 出力フォーマット

時間数はすべて小数点第一位まで表示（整数値も `.0` を付ける）。

値はすべて `work summary` の戻り値をそのまま使う（下の対応どおり）。

**1行目: 月次進捗**
```
今月 X.Xh / 目標 Y.Yh（所定 V.Vh）・残 N日
```
- `X.Xh` = `today_plan.actual_cumul`（今日の実績推定込み）
- `Y.Yh` = `target_hours`
- `V.Vh` = `target_hours`（所定勤務時間）
- `N` = `remaining_workdays`

**2行目: 月初ペース**
```
月初ペース: 実績 X.Xh / 理想 Y.Yh（+Z.Zh 貯金）   ← pace_diff > 0
月初ペース: 実績 X.Xh / 理想 Y.Yh（−Z.Zh 不足）   ← pace_diff < 0
月初ペース: 実績 X.Xh / 理想 Y.Yh（ぴったり）      ← pace_diff = 0
```
- `X.Xh` = `today_plan.actual_cumul`
- `Y.Yh` = `today_plan.ideal_cumul`
- `Z.Zh` = `|today_plan.pace_diff|`

**3行目: 今日の退勤目安（補正後）**
```
今日 <today_start> 開始 → 退勤目安 <clock_out_estimate>（ペース加味・休憩 Xmin 込み）
```
- 退勤目安は `today_plan.clock_out_estimate` をそのまま入れる。
- `today_plan.core_time_floored` が true: `→ 退勤目安 16:00（コアタイム下限・本来はもっと早くてよい）`
- `today_plan.capped_12h` が true: `→ 退勤目安 <clock_out_estimate>（12h 上限・今日だけでは挽回不可、明日以降も継続）`
- `today_plan.flex_carryover_hours` があれば末尾に添える: `（＋フレックス前借り <flex_carryover_hours>h・早上がり予定分）`

Step B で当日以外に始業のみの日が見つかったら、`/todo` に続けて終業時刻を入力してもらう。
