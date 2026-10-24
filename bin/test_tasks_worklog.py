"""`tasks` CLIの勤務記録、退勤目安の補正、today_plan、work-summaryを検証する。
`tasks`フィクスチャはconftest.pyで定義する。
"""

import datetime as _datetime
import json

import pytest


class _FrozenDate(_datetime.date):
    """date(y,m,d)による生成を保ち、.today()だけを固定するdateの派生クラス。

    cmd_work_summaryはdate.today()とdate(year, mon, 1)を呼ぶ。
    tasks_cli.dateをこのクラスに置き換え、日付の生成を保ったまま今日の日付を固定する。
    """

    _frozen = None

    def __new__(cls, *args, **kwargs):
        # date(2026, 6, 1)など、通常の日付生成は許可する。
        return _datetime.date.__new__(_datetime.date, *args, **kwargs)

    @classmethod
    def today(cls):
        return cls._frozen


def _frozen_date(year, month, day):
    _FrozenDate._frozen = _datetime.date(year, month, day)
    return _FrozenDate


class _FrozenDatetime(_datetime.datetime):
    """生成処理を保ち、.now()だけを固定するdatetimeの派生クラス。

    _today_planはdatetime.now()で現在時刻を取得する。
    時刻を固定して、remaining_work_minutes / today_startの値を正確に検証する。
    """

    _frozen = None

    @classmethod
    def now(cls, tz=None):
        return cls._frozen


def _frozen_now(year, month, day, hour, minute):
    _FrozenDatetime._frozen = _datetime.datetime(year, month, day, hour, minute)
    return _FrozenDatetime


# ---------- 作業記録 ----------


def test_summary_includes_unfilled_without_writing(tasks, capsys, monkeypatch):
    monkeypatch.setattr(tasks.module, "date", _frozen_date(2026, 6, 10))
    monkeypatch.setattr(tasks.module, "datetime", _frozen_now(2026, 6, 10, 10, 0))
    tasks.run(
        "meta",
        "set",
        "workdays_2026-06",
        '["2026-06-08", "2026-06-09", "2026-06-10", "2026-06-11"]',
    )
    tasks.run("work", "set", "--date", "2026-06-08", "--segment", "09:00-18:00")
    tasks.run("work", "set", "--date", "2026-06-09", "--segment", "09:00")
    capsys.readouterr()
    before = tasks.store_path.read_bytes()
    tasks.run("work", "summary", "--include-unfilled")
    summary = json.loads(capsys.readouterr().out)
    assert summary["unfilled_entries"] == [
        {"date": "2026-06-09", "status": "start_only", "start": "09:00"},
        {"date": "2026-06-10", "status": "missing"},
    ]
    assert summary["today_plan"]["clock_out_estimate"]
    assert tasks.store_path.read_bytes() == before
    tasks.run(
        "work",
        "show",
        "unfilled-entries",
        "--month",
        "2026-06",
        "--through",
        "2026-06-10",
    )
    assert (
        json.loads(capsys.readouterr().out)["unfilled_entries"]
        == (summary["unfilled_entries"])
    )


def test_work_set_single_segment_deducts_break(tasks, capsys):
    tasks.run("meta", "set", "break_default_minutes", "60")
    capsys.readouterr()
    tasks.run("work", "set", "--date", "2026-06-08", "--segment", "09:00-18:00")
    out = json.loads(capsys.readouterr().out)
    entry = out["2026-06-08"]
    assert entry["hours"] == 8.0  # 9h span minus 60min break
    assert entry["start"] == "09:00"
    assert entry["end"] == "18:00"


def test_work_set_multi_segment_sums(tasks, capsys):
    tasks.run(
        "work",
        "set",
        "--date",
        "2026-06-08",
        "--segment",
        "09:00-12:00",
        "--segment",
        "13:00-18:00",
    )
    out = json.loads(capsys.readouterr().out)
    entry = out["2026-06-08"]
    assert entry["hours"] == 8.0  # 3h + 5h, gap is the break
    assert entry["break_minutes_inferred"] == 60


def test_work_set_start_only(tasks, capsys):
    tasks.run("work", "set", "--date", "2026-06-08", "--segment", "0900")
    out = json.loads(capsys.readouterr().out)
    entry = out["2026-06-08"]
    assert entry["start"] == "09:00"
    assert entry["end"] is None
    assert entry["hours"] is None


def test_work_punches_keep_overnight_end_and_next_day_start(tasks, capsys):
    tasks.run(
        "work",
        "punches",
        "--punch",
        "start:2026/10/08 09:46:28",
        "--punch",
        "end:2026/10/09 00:55:45",
        "--punch",
        "start:2026/10/09 09:10:28",
    )

    entries = json.loads(capsys.readouterr().out)
    oct_8 = entries["2026-10-08"]
    oct_9 = entries["2026-10-09"]
    assert oct_8["segments"] == [{"start": "09:46", "end": "24:55"}]
    assert oct_8["hours"] == 14.15
    assert oct_8["break_minutes_inferred"] == 60
    assert oct_9["segments"] == [{"start": "09:10", "end": None}]
    assert oct_9["hours"] is None
    plan = tasks.module._today_plan({}, oct_9, 8.0, None, 0.0, [], [])
    assert plan["today_start"] == "09:10"
    assert plan["clock_out_estimate"] == "18:10"


def test_work_set_break_override(tasks, capsys):
    tasks.run(
        "work",
        "set",
        "--date",
        "2026-06-08",
        "--segment",
        "09:00-18:00",
        "--break",
        "30",
    )
    out = json.loads(capsys.readouterr().out)
    assert out["2026-06-08"]["hours"] == 8.5  # 9h minus 30min


def test_work_set_note_and_source(tasks, capsys):
    tasks.run(
        "work",
        "set",
        "--date",
        "2026-06-08",
        "--segment",
        "09:00-18:00",
        "--note",
        "remote",
        "--source",
        "manual",
    )
    out = json.loads(capsys.readouterr().out)
    entry = out["2026-06-08"]
    assert entry["note"] == "remote"
    assert entry["source"] == "manual"


def test_work_delete(tasks, capsys):
    tasks.run("work", "set", "--date", "2026-06-08", "--segment", "09:00-18:00")
    capsys.readouterr()
    tasks.run("work", "delete", "2026-06-08")
    capsys.readouterr()
    assert "2026-06-08" not in tasks.store()["work_log"]


def test_work_delete_missing_exits(tasks):
    with pytest.raises(SystemExit):
        tasks.run("work", "delete", "2099-01-01")


def test_work_show_by_date(tasks, capsys):
    tasks.run("work", "set", "--date", "2026-06-08", "--segment", "09:00-18:00")
    capsys.readouterr()
    tasks.run("work", "show", "log", "--date", "2026-06-08")
    out = json.loads(capsys.readouterr().out)
    assert out["start"] == "09:00"


def test_work_show_by_month(tasks, capsys):
    tasks.run("work", "set", "--date", "2026-06-08", "--segment", "09:00-18:00")
    tasks.run("work", "set", "--date", "2026-07-01", "--segment", "09:00-18:00")
    capsys.readouterr()
    tasks.run("work", "show", "log", "--month", "2026-06")
    out = json.loads(capsys.readouterr().out)
    assert list(out.keys()) == ["2026-06-08"]


def test_work_unfilled_entries(tasks, capsys):
    tasks.run(
        "meta", "set", "workdays_2026-06", '["2026-06-08", "2026-06-09", "2026-06-10"]'
    )
    tasks.run("work", "set", "--date", "2026-06-08", "--segment", "09:00-18:00")
    tasks.run(
        "work", "set", "--date", "2026-06-09", "--segment", "0900"
    )  # 開始時刻のみ
    capsys.readouterr()
    tasks.run(
        "work",
        "show",
        "unfilled-entries",
        "--month",
        "2026-06",
        "--through",
        "2026-06-10",
    )
    out = json.loads(capsys.readouterr().out)
    statuses = {e["date"]: e["status"] for e in out["unfilled_entries"]}
    assert statuses["2026-06-09"] == "start_only"
    assert statuses["2026-06-10"] == "missing"
    assert "2026-06-08" not in statuses  # 必要項目をすべて入力済み


def test_work_summary_behind_pace(tasks, capsys, monkeypatch):
    monkeypatch.setattr(tasks.module, "date", _frozen_date(2026, 6, 15))
    tasks.run("meta", "set", "target_hours_2026-06", "160")
    tasks.run("meta", "set", "holidays_2026-06", "[]")
    tasks.run(
        "work", "set", "--date", "2026-06-01", "--segment", "09:00-15:00"
    )  # 6h span - 1h break = 5h
    capsys.readouterr()
    tasks.run("work", "summary", "--month", "2026-06")
    out = json.loads(capsys.readouterr().out)
    assert out["target_hours"] == 160
    assert out["pace"] in ("behind", "on_track")
    assert out["cumulative_hours"] == 5.0
    assert out["remaining_hours"] == 155.0


def test_work_summary_past_month(tasks, capsys, monkeypatch):
    monkeypatch.setattr(tasks.module, "date", _frozen_date(2026, 7, 15))
    tasks.run("meta", "set", "target_hours_2026-06", "160")
    capsys.readouterr()
    tasks.run("work", "summary", "--month", "2026-06")
    out = json.loads(capsys.readouterr().out)
    assert out["remaining_workdays"] == 0


def test_work_summary_december_rollover(tasks, capsys, monkeypatch):
    monkeypatch.setattr(tasks.module, "date", _frozen_date(2026, 12, 15))
    tasks.run("meta", "set", "target_hours_2026-12", "160")
    capsys.readouterr()
    tasks.run("work", "summary", "--month", "2026-12")
    out = json.loads(capsys.readouterr().out)
    assert out["month"] == "2026-12"


def test_work_summary_future_month(tasks, capsys, monkeypatch):
    monkeypatch.setattr(tasks.module, "date", _frozen_date(2026, 5, 1))
    tasks.run("meta", "set", "target_hours_2026-06", "160")
    capsys.readouterr()
    tasks.run("work", "summary", "--month", "2026-06")
    out = json.loads(capsys.readouterr().out)
    # 対象月が未来の場合、その月の全営業日を残営業日として扱う。
    assert out["remaining_workdays"] == out["workdays_in_month"]


# ---------- 退勤目安の補正: 段ごとの純粋関数 ----------
#
# 退勤目安の計算はツールに集約する。補正は段に分けて純粋関数にし、段ごとに検証する。
#   _pace_correction: 月初ペースの貯金/不足で今日ノルマを補正（コアタイム下限・12h上限）
#   _flex_carryover:  未来のフレックス退勤予定の不足を今日に前借りする分（分）を返す
# ツールの既定定数（所定8h・月バッファ1h・コアタイム16:00・フレキシブルタイム終了22:00・
# 12h上限・標準09:30/18:30）は meta で上書きできる。テストは meta 既定でも上書きでも検証する。

# --- ペース補正（_pace_correction） ---
# 入力: pace_diff（正=貯金 負=不足）, even_norma（均等割りノルマ h）, meta
# 返り: {norma, core_time_floored, capped_12h} など。norma は補正後の今日ノルマ h。


def test_pace_correction_surplus_keeps_even_norma(tasks):
    # 貯金（pace_diff>0）は均等割りのまま。急いで消化しない。
    r = tasks.module._pace_correction(5.0, 7.0, {})
    assert r["norma"] == 7.0
    assert r["capped_12h"] is False


def test_pace_correction_shortfall_adds_full_deficit(tasks):
    # 不足（pace_diff<0）は不足を今日に全額上乗せする。
    r = tasks.module._pace_correction(-2.0, 7.0, {})
    assert r["norma"] == 9.0
    assert r["capped_12h"] is False


def test_pace_correction_shortfall_caps_at_12h(tasks):
    # 補正後ノルマが 12h を超えたら 12h に丸め、フラグを立てる。
    r = tasks.module._pace_correction(-10.0, 7.0, {})
    assert r["norma"] == 12.0
    assert r["capped_12h"] is True


def test_pace_correction_zero_keeps_even_norma(tasks):
    # ちょうど（pace_diff=0）は補正なし。
    r = tasks.module._pace_correction(0.0, 7.5, {})
    assert r["norma"] == 7.5


def test_pace_correction_max_daily_hours_meta_override(tasks):
    # 12h 上限は meta.max_daily_hours で上書きできる。
    r = tasks.module._pace_correction(-10.0, 7.0, {"max_daily_hours": 10})
    assert r["norma"] == 10.0
    assert r["capped_12h"] is True


# --- フレックス繰越（_flex_carryover） ---
# 入力: planned_days（[(date_str, 退勤希望min)]）, today_start_min, today_started(bool),
#       future_workdays（今日〜最遠予定日の普通日 date_str の集合）, today_str, meta
# 返り: {D, a_today_min, T_min, ...}。a_today_min は今日に上乗せする前借り（分）。


def _hhmm(h, m):
    return h * 60 + m


def test_flex_carryover_none_when_no_planned(tasks):
    # フレックス予定が無ければ前借りゼロ。
    r = tasks.module._flex_carryover([], _hhmm(9, 18), True, set(), {})
    assert r["a_today_min"] == 0
    assert r["D"] == 0


def test_flex_carryover_surplus_days_cancel_deficit(tasks):
    # 7/9 退勤17:15（1.25h不足）を 7/10 18:50（0.33h貯金）・7/23 18:35（0.08h貯金）が相殺。
    # D = 1.25 - 0.33 - 0.08 = 0.84h。前借りが要る。
    planned = [
        ("2026-07-09", _hhmm(17, 15)),
        ("2026-07-10", _hhmm(18, 50)),
        ("2026-07-23", _hhmm(18, 35)),
    ]
    # 今日7/8始業済み(残業のみ日)、対称ズレ日=7/13,14,15,16,17,21,22 の7日
    future = {
        "2026-07-13",
        "2026-07-14",
        "2026-07-15",
        "2026-07-16",
        "2026-07-17",
        "2026-07-21",
        "2026-07-22",
    }
    r = tasks.module._flex_carryover(planned, _hhmm(9, 18), True, future, {})
    assert abs(r["D"] - 0.84) < 0.01
    # 今日の前借りは約15分（a_today = T - base_today）
    assert 13 <= r["a_today_min"] <= 17


def test_flex_carryover_zero_when_all_surplus(tasks):
    # フレックス予定が全部貯金側なら D<=0 で前借りゼロ。
    planned = [("2026-07-10", _hhmm(18, 50)), ("2026-07-23", _hhmm(18, 35))]
    future = {"2026-07-13", "2026-07-14"}
    r = tasks.module._flex_carryover(planned, _hhmm(9, 18), True, future, {})
    assert r["D"] <= 0
    assert r["a_today_min"] == 0


def test_flex_carryover_conserves_total(tasks):
    # 配分の合計（今日 + 対称ズレ日×m）が D に一致する（分配の保存）。
    planned = [("2026-07-09", _hhmm(17, 15))]  # 1.25h 不足のみ
    future = {"2026-07-13", "2026-07-14", "2026-07-15"}
    r = tasks.module._flex_carryover(planned, _hhmm(9, 18), True, future, {})
    total = r["a_today_min"] + r["a_sym_min"] * len(future)
    assert abs(total - r["D"] * 60) < 0.5


# ---------- today_plan (今日の退勤打刻時刻・実働終端) ----------
#
# 仕様: 決め打ちの退勤時刻（18:10 / 18:30 等）は持たない。すべて始業時刻と
# today_target_hours から毎日計算する。
#   clock_out_estimate（退勤打刻目安）= 始業 + ノルマ実働 + 休憩
#   work_end（実働終端 = タスクを置ける最後）= clock_out_estimate − wind_down
#   不在予定（off_start）があれば、それを退勤打刻の上限にする（min）


def _clock_out_from_target(start_min, target_hours, break_min=60):
    """期待される退勤打刻（分）= 始業 + ノルマ実働 + 休憩。
    フレキシブルタイム終了(22:00)を超えない。テストの検証用。"""
    raw = start_min + round(target_hours * 60) + break_min
    return min(raw, 22 * 60)


def _setup_june_today(tasks, monkeypatch, hour, minute, target=160, wind_down=20):
    """today を 2026-06-08(月) に、現在時刻を hour:minute に固定する共通段取り。

    today_target_hours は target / 残営業日(今日〜月末) で決まるので、検証側は
    out["today_target_hours"] を読んで期待値を組み立てる（決め打ちにしない）。
    """
    monkeypatch.setattr(tasks.module, "date", _frozen_date(2026, 6, 8))
    monkeypatch.setattr(tasks.module, "datetime", _frozen_now(2026, 6, 8, hour, minute))
    tasks.run("meta", "set", "target_hours_2026-06", str(target))
    tasks.run("meta", "set", "holidays_2026-06", "[]")
    tasks.run("meta", "set", "break_default_minutes", "60")
    if wind_down is not None:
        tasks.run("meta", "set", "wind_down_default_minutes", str(wind_down))


def test_today_plan_default_wind_down_is_five_minutes(tasks, capsys, monkeypatch):
    _setup_june_today(tasks, monkeypatch, 10, 0, wind_down=None)
    capsys.readouterr()
    tasks.run("work", "summary", "--month", "2026-06")
    out = json.loads(capsys.readouterr().out)
    assert out["today_plan"]["wind_down_minutes"] == 5


def test_today_plan_present_for_current_month(tasks, capsys, monkeypatch):
    _setup_june_today(tasks, monkeypatch, 10, 0)
    capsys.readouterr()
    tasks.run("work", "summary", "--month", "2026-06")
    out = json.loads(capsys.readouterr().out)
    assert "today_plan" in out
    plan = out["today_plan"]
    # 未打刻なので始業=現在時刻 10:00
    assert plan["today_start"] == "10:00"
    assert plan["break_minutes"] == 60
    assert plan["wind_down_minutes"] == 20
    # 決め打ち時刻フィールドは廃止
    assert "work_end_cap" not in plan
    assert "norma_work_end" not in plan


def _corrected_norma(tasks, out):
    """out（work summary）から補正後の今日ノルマ h を実装と同じロジックで出す。

    退勤目安は補正込みなので、テストの期待値も _pace_correction を通して組む。
    _setup_june_today はフレックス予定を入れないので前借りは効かない。
    """
    even = out["today_target_hours"]
    pace_diff = out["today_plan"].get("pace_diff", 0.0)
    return tasks.module._pace_correction(pace_diff, even, {})["norma"]


def test_today_plan_clock_out_includes_break(tasks, capsys, monkeypatch):
    _setup_june_today(tasks, monkeypatch, 9, 30)
    # 始業 09:30 を打刻済みにする（end 無し = start only）
    tasks.run("work", "set", "--date", "2026-06-08", "--segment", "09:30")
    capsys.readouterr()
    tasks.run("work", "summary", "--month", "2026-06")
    out = json.loads(capsys.readouterr().out)
    plan = out["today_plan"]
    norma = _corrected_norma(tasks, out)
    assert plan["today_start"] == "09:30"
    # 退勤打刻 = 始業09:30 + 補正後ノルマ実働 + 休憩60分
    co_min = _clock_out_from_target(9 * 60 + 30, norma)
    assert plan["clock_out_estimate"] == f"{co_min // 60:02d}:{co_min % 60:02d}"
    # 実働終端 = 退勤打刻 − wind_down 20分
    we_min = co_min - 20
    assert plan["work_end"] == f"{we_min // 60:02d}:{we_min % 60:02d}"


def test_today_plan_no_fixed_clock_out_time(tasks, capsys, monkeypatch):
    # 退勤打刻はノルマ次第で変わる（18:10 / 18:30 の決め打ちが無いことの確認）。
    # 始業を後ろにずらせば退勤打刻も同じだけ後ろにずれる。
    _setup_june_today(tasks, monkeypatch, 11, 0)
    tasks.run("work", "set", "--date", "2026-06-08", "--segment", "11:00")
    capsys.readouterr()
    tasks.run("work", "summary", "--month", "2026-06")
    out = json.loads(capsys.readouterr().out)
    plan = out["today_plan"]
    norma = _corrected_norma(tasks, out)
    co_min = _clock_out_from_target(11 * 60, norma)
    assert plan["clock_out_estimate"] == f"{co_min // 60:02d}:{co_min % 60:02d}"
    # 11:00 始業ぶん遅い退勤打刻になっており、18:30 固定ではない
    assert co_min > 18 * 60 + 30


def test_today_plan_off_start_caps_clock_out(tasks, capsys, monkeypatch):
    _setup_june_today(tasks, monkeypatch, 10, 0)
    capsys.readouterr()
    # 不在 17:05 開始 → 退勤打刻は不在開始 17:05 が上限、実働終端 = 17:05 − 20分 = 16:45
    tasks.run("work", "summary", "--month", "2026-06", "--off-start", "17:05")
    out = json.loads(capsys.readouterr().out)
    plan = out["today_plan"]
    assert plan["clock_out_estimate"] == "17:05"
    assert plan["work_end"] == "16:45"


def test_today_plan_off_start_ignored_when_later_than_norma(tasks, capsys, monkeypatch):
    # 不在開始がノルマ退勤打刻より後なら、退勤打刻はノルマ側を使う（早い方）。
    # ノルマを低くして退勤打刻を早め、不在 23:00 を確実に後にする。
    _setup_june_today(tasks, monkeypatch, 9, 30, target=17)  # 17h / 17営業日 = 1.0h/日
    tasks.run("work", "set", "--date", "2026-06-08", "--segment", "09:30")
    capsys.readouterr()
    tasks.run("work", "summary", "--month", "2026-06", "--off-start", "23:00")
    out = json.loads(capsys.readouterr().out)
    plan = out["today_plan"]
    norma = _corrected_norma(tasks, out)
    co_min = _clock_out_from_target(9 * 60 + 30, norma)
    assert co_min < 23 * 60  # ノルマ退勤打刻は不在より前
    assert plan["clock_out_estimate"] == f"{co_min // 60:02d}:{co_min % 60:02d}"


def test_today_plan_remaining_minutes(tasks, capsys, monkeypatch):
    _setup_june_today(tasks, monkeypatch, 10, 0)
    tasks.run("work", "set", "--date", "2026-06-08", "--segment", "09:30")
    capsys.readouterr()
    tasks.run("work", "summary", "--month", "2026-06")
    out = json.loads(capsys.readouterr().out)
    plan = out["today_plan"]
    norma = _corrected_norma(tasks, out)
    we_min = _clock_out_from_target(9 * 60 + 30, norma) - 20
    # remaining = work_end − now(10:00 = 600分)
    assert plan["remaining_work_minutes"] == we_min - 600


def test_today_plan_absent_for_past_month(tasks, capsys, monkeypatch):
    monkeypatch.setattr(tasks.module, "date", _frozen_date(2026, 7, 15))
    monkeypatch.setattr(tasks.module, "datetime", _frozen_now(2026, 7, 15, 10, 0))
    tasks.run("meta", "set", "target_hours_2026-06", "160")
    capsys.readouterr()
    tasks.run("work", "summary", "--month", "2026-06")
    out = json.loads(capsys.readouterr().out)
    assert "today_plan" not in out


# ---------- today_plan: 補正の統合（work summary 経由） ----------


def test_today_plan_core_time_floor_applied(tasks, capsys, monkeypatch):
    # 貯金があり退勤目安が 16:00 より前になる → コアタイム下限で 16:00 に切り上げ。
    # 会社規定の終業可能時間は 16:00 以降（17:00 ではない）。
    # 月初ペースの理想を下げる（daily_norma_hours=1）ことで貯金を作りやすくする。
    # あわせて daily_norma_hours の meta 上書きが効くことも確認する。
    monkeypatch.setattr(tasks.module, "date", _frozen_date(2026, 6, 8))
    monkeypatch.setattr(tasks.module, "datetime", _frozen_now(2026, 6, 8, 9, 30))
    tasks.run("meta", "set", "target_hours_2026-06", "40")
    tasks.run("meta", "set", "holidays_2026-06", "[]")
    tasks.run("meta", "set", "break_default_minutes", "60")
    tasks.run("meta", "set", "wind_down_default_minutes", "20")
    tasks.run("meta", "set", "daily_norma_hours", "1")  # 理想を下げて貯金にする
    tasks.run("meta", "set", "month_buffer_hours", "0")
    # 過去営業日 6/1-6/5 に 8h ずつ働いた実績（貯金）。ideal は 6日×1=6h、実績は 40h。
    for d in ["2026-06-01", "2026-06-02", "2026-06-03", "2026-06-04", "2026-06-05"]:
        tasks.run("work", "set", "--date", d, "--segment", "09:00-18:00")
    tasks.run("work", "set", "--date", "2026-06-08", "--segment", "09:30")
    capsys.readouterr()
    tasks.run("work", "summary", "--month", "2026-06")
    out = json.loads(capsys.readouterr().out)
    plan = out["today_plan"]
    # 貯金が大きく素の退勤目安が 16:00 より前 → 16:00 に切り上げ
    assert plan["clock_out_estimate"] == "16:00"
    assert plan.get("core_time_floored") is True


def test_today_plan_core_time_floor_after_monthly_target_exceeded(tasks):
    plan = tasks.module._today_plan(
        {"wind_down_default_minutes": 20},
        {"start": "09:34"},
        today_target_hours=-3.03,
        off_start=None,
        pace_diff=-1.0,
        planned_days=[],
        future_workdays=set(),
    )
    assert plan["clock_out_estimate"] == "16:00"
    assert plan["work_end"] == "15:40"
    assert plan["core_time_floored"] is True


def test_today_plan_flex_time_end_caps_clock_out(tasks):
    # フレキシブルタイム終了(22:00)は退勤目安の絶対上限。会社規定でこれを超える
    # 勤務は認められない。12h上限を緩めても 22:00 は超えない。
    meta = {"max_daily_hours": 20}
    today_entry = {"start": "09:00"}
    plan = tasks.module._today_plan(
        meta,
        today_entry,
        today_target_hours=1.0,
        off_start=None,
        pace_diff=-12.0,
        planned_days=[],
        future_workdays=set(),
    )
    assert plan["clock_out_estimate"] == "22:00"
    assert plan.get("flex_time_capped") is True


def test_today_plan_flex_time_end_not_capped_when_within_range(tasks):
    # フレキシブルタイム内に収まっていればフラグは立たない。
    meta = {}
    today_entry = {"start": "09:30"}
    plan = tasks.module._today_plan(
        meta,
        today_entry,
        today_target_hours=8.0,
        off_start=None,
        pace_diff=0.0,
        planned_days=[],
        future_workdays=set(),
    )
    assert plan["clock_out_estimate"] < "22:00"
    assert "flex_time_capped" not in plan


def test_today_plan_flex_carryover_pushes_clock_out(tasks, capsys, monkeypatch):
    # 未来のフレックス予定（早上がり）があると今日の退勤目安が前借り分だけ後ろへ動く。
    # 月初ペースの不足補正が乗ると 22:00 のフレキシブルタイム終了キャップに
    # 張り付いて前借りの効果が見えなくなるため、経過営業日ぶんの実績を先に
    # 埋めて pace_diff をゼロ近辺にしておく（テストの狙いは前借りの効果の
    # 検証で、月初ペース補正の大小ではない。daily_norma_hours は変えない
    # — _flex_carryover の不足計算も daily_norma_hours を使うため、下げると
    # 前借り判定そのものが変わってしまう）。
    monkeypatch.setattr(tasks.module, "date", _frozen_date(2026, 7, 8))
    monkeypatch.setattr(tasks.module, "datetime", _frozen_now(2026, 7, 8, 9, 18))
    tasks.run("meta", "set", "target_hours_2026-07", "40")
    tasks.run("meta", "set", "holidays_2026-07", '["2026-07-20"]')
    tasks.run("meta", "set", "break_default_minutes", "60")
    tasks.run("meta", "set", "wind_down_default_minutes", "20")
    cur = _datetime.date(2026, 7, 1)
    today_date = _datetime.date(2026, 7, 8)
    while cur < today_date:
        if cur.weekday() < 5:
            tasks.run(
                "work", "set", "--date", cur.isoformat(), "--segment", "09:00-18:00"
            )
        cur += _datetime.timedelta(days=1)
    tasks.run("work", "set", "--date", "2026-07-08", "--segment", "09:18")
    # フレックス前借りなしの退勤目安を先に取る
    capsys.readouterr()
    tasks.run("work", "summary", "--month", "2026-07")
    base = json.loads(capsys.readouterr().out)["today_plan"]["clock_out_estimate"]
    # 7/9 早上がり(17:15)を登録 → 前借りが乗って退勤目安が後ろへ
    tasks.run(
        "work", "set", "--date", "2026-07-09", "--segment", "09:30-17:15", "--planned"
    )
    capsys.readouterr()
    tasks.run("work", "summary", "--month", "2026-07")
    withflex = json.loads(capsys.readouterr().out)["today_plan"]
    assert withflex["clock_out_estimate"] > base  # HH:MM 文字列比較で後ろへ
    assert withflex.get("flex_carryover_hours", 0) > 0


def test_today_plan_no_flex_when_all_surplus(tasks, capsys, monkeypatch):
    # フレックス予定が貯金側だけなら前借りは乗らない（退勤目安が動かない）。
    monkeypatch.setattr(tasks.module, "date", _frozen_date(2026, 7, 8))
    monkeypatch.setattr(tasks.module, "datetime", _frozen_now(2026, 7, 8, 9, 18))
    tasks.run("meta", "set", "target_hours_2026-07", "160")
    tasks.run("meta", "set", "holidays_2026-07", '["2026-07-20"]')
    tasks.run("work", "set", "--date", "2026-07-08", "--segment", "09:18")
    capsys.readouterr()
    tasks.run("work", "summary", "--month", "2026-07")
    base = json.loads(capsys.readouterr().out)["today_plan"]["clock_out_estimate"]
    # 7/10 遅め退勤(18:50)＝貯金側だけ登録
    tasks.run(
        "work", "set", "--date", "2026-07-10", "--segment", "09:30-18:50", "--planned"
    )
    capsys.readouterr()
    tasks.run("work", "summary", "--month", "2026-07")
    withflex = json.loads(capsys.readouterr().out)["today_plan"]
    assert withflex["clock_out_estimate"] == base
    assert "flex_carryover_hours" not in withflex


def test_today_plan_returns_work_available_minutes(tasks, capsys, monkeypatch):
    # 実働可能時間（分）をツールが返す。= clock_out_estimate − today_start − break。
    # todo.md の本丸割合の分母がこれを手計算していたのをツール側に一元化する。
    _setup_june_today(tasks, monkeypatch, 9, 30)
    tasks.run("work", "set", "--date", "2026-06-08", "--segment", "09:30")
    capsys.readouterr()
    tasks.run("work", "summary", "--month", "2026-06")
    plan = json.loads(capsys.readouterr().out)["today_plan"]
    co = tasks.module._time_to_minutes(plan["clock_out_estimate"])
    st = tasks.module._time_to_minutes(plan["today_start"])
    assert plan["work_available_minutes"] == co - st - plan["break_minutes"]


# ---------- 内部の補助関数: 時間・営業日 ----------


def test_calc_hours_empty_segments(tasks):
    assert tasks.module._calc_hours_from_segments([], 60) == (None, 60)


def test_calc_hours_single_incomplete_segment(tasks):
    # 開始時刻しかない区間は、時間を計算できない。
    assert tasks.module._calc_hours_from_segments(
        [{"start": "09:00", "end": None}], 60
    ) == (None, 60)


def test_calc_hours_multi_incomplete_segment(tasks):
    segs = [{"start": "09:00", "end": "12:00"}, {"start": "13:00", "end": None}]
    assert tasks.module._calc_hours_from_segments(segs, 60) == (None, 60)


def test_workdays_between_reversed_is_zero(tasks):
    d = tasks.module.date
    assert tasks.module._workdays_between(d(2026, 6, 10), d(2026, 6, 1), set()) == 0


def test_parse_time_colon_and_compact(tasks):
    assert tasks.module.parse_time("9:5") == "09:05"
    assert tasks.module.parse_time("0900") == "09:00"


# ---------- work_summaryの境界条件 ----------


def test_work_summary_satisfied_when_target_met(tasks, capsys, monkeypatch):
    # 過去月で累計時間が目標以上なら、month_over_satisfiedになる。
    monkeypatch.setattr(tasks.module, "date", _frozen_date(2026, 7, 1))
    tasks.run("meta", "set", "target_hours_2026-06", "5")
    tasks.run("meta", "set", "holidays_2026-06", "[]")
    tasks.run("work", "set", "--date", "2026-06-01", "--segment", "09:00-15:00")  # 5h
    # 対象月外の記録とhours=Noneの記録で、集計を飛ばす分岐を検証する。
    tasks.run("work", "set", "--date", "2026-05-30", "--segment", "09:00-18:00")
    tasks.run(
        "work", "set", "--date", "2026-06-02", "--segment", "0900"
    )  # 開始時刻のみのため、時間はNoneになる。
    capsys.readouterr()
    tasks.run("work", "summary", "--month", "2026-06")
    out = json.loads(capsys.readouterr().out)
    assert out["pace"] == "month_over_satisfied"


def test_work_summary_unfilled_break_past_through(tasks, capsys):
    # 営業日の一覧が--throughより先まで続く場合、ループを途中で終了する。
    tasks.run("meta", "set", "workdays_2026-06", '["2026-06-08", "2026-06-30"]')
    capsys.readouterr()
    tasks.run(
        "work",
        "show",
        "unfilled-entries",
        "--month",
        "2026-06",
        "--through",
        "2026-06-09",
    )
    out = json.loads(capsys.readouterr().out)
    dates = {e["date"] for e in out["unfilled_entries"]}
    assert "2026-06-30" not in dates  # --throughを過ぎるため、breakで処理を打ち切る。


# ---------- work show: 存在しない日付は null / 空 dict ----------


def test_work_show_missing_date_returns_null(tasks, capsys):
    tasks.run("work", "show", "log", "--date", "2099-01-01")
    out = json.loads(capsys.readouterr().out)
    assert out is None


def test_work_show_missing_month_returns_empty(tasks, capsys):
    tasks.run("work", "show", "log", "--month", "2099-01")
    out = json.loads(capsys.readouterr().out)
    assert out == {}


# ---------- work set: 不正なセグメントフォーマット ----------


def test_work_set_invalid_segment_raises(tasks):
    # parse_time("abc")はValueErrorを送出し、現状では回復処理を行わない。
    with pytest.raises((ValueError, SystemExit)):
        tasks.run("work", "set", "--date", "2026-06-08", "--segment", "abc-xyz")


# ---------- work set: start > end のセグメントは負の hours ----------


def test_work_set_end_before_start_clamps_to_zero(tasks, capsys):
    # 終了が開始より前の区間では、_calc_hours_from_segmentsがmax(0, ...)で下限を設ける。
    # そのため、時間は負の値やNoneではなく0.0になる。
    tasks.run("work", "set", "--date", "2026-06-08", "--segment", "18:00-09:00")
    out = json.loads(capsys.readouterr().out)
    assert out["2026-06-08"]["hours"] == 0.0


# ---------- parse_time: 境界値 ----------


def test_parse_time_midnight(tasks):
    assert tasks.module.parse_time("00:00") == "00:00"
    assert tasks.module.parse_time("0000") == "00:00"


def test_parse_time_end_of_day(tasks):
    assert tasks.module.parse_time("23:59") == "23:59"
    assert tasks.module.parse_time("2359") == "23:59"


# ---------- work summary: target_hours 未設定 ----------


def test_work_summary_no_target_uses_zero(tasks, capsys, monkeypatch):
    # target_hours_YYYY-MMが未設定なら、summaryは目標を0とみなし、
    # 累計0が目標0以上のためmonth_over_satisfiedを返す。
    monkeypatch.setattr(tasks.module, "date", _frozen_date(2026, 7, 1))
    # target_hours_2026-06を意図的に設定しない。
    capsys.readouterr()
    tasks.run("work", "summary", "--month", "2026-06")
    out = json.loads(capsys.readouterr().out)
    assert out["target_hours"] == 0.0
    assert out["pace"] == "month_over_satisfied"


# ---------- 作業時間の集計: target_hours_no_buffer ----------


def test_work_summary_no_buffer_used_when_few_workdays_remain(
    tasks, capsys, monkeypatch
):
    # 残り営業日が3以下のとき target_hours_no_buffer を使う。
    # 2026-06-29(月): 残り営業日 = 29, 30 の2日。
    monkeypatch.setattr(tasks.module, "date", _frozen_date(2026, 6, 29))
    monkeypatch.setattr(tasks.module, "datetime", _frozen_now(2026, 6, 29, 10, 0))
    tasks.run("meta", "set", "target_hours_2026-06", "179")
    tasks.run("meta", "set", "target_hours_no_buffer_2026-06", "176")
    tasks.run("meta", "set", "holidays_2026-06", "[]")
    capsys.readouterr()
    tasks.run("work", "summary", "--month", "2026-06")
    out = json.loads(capsys.readouterr().out)
    # バッファなしの 176 が使われる
    assert out["target_hours"] == 176


def test_work_summary_buffer_used_when_many_workdays_remain(tasks, capsys, monkeypatch):
    # 残り営業日が4以上のとき通常の target_hours を使う。
    # 2026-06-22(月): 残り営業日 = 22〜30 の7日。
    monkeypatch.setattr(tasks.module, "date", _frozen_date(2026, 6, 22))
    monkeypatch.setattr(tasks.module, "datetime", _frozen_now(2026, 6, 22, 10, 0))
    tasks.run("meta", "set", "target_hours_2026-06", "179")
    tasks.run("meta", "set", "target_hours_no_buffer_2026-06", "176")
    tasks.run("meta", "set", "holidays_2026-06", "[]")
    capsys.readouterr()
    tasks.run("work", "summary", "--month", "2026-06")
    out = json.loads(capsys.readouterr().out)
    # バッファ込みの 179 が使われる
    assert out["target_hours"] == 179


def test_work_summary_no_buffer_key_absent_uses_target_hours(
    tasks, capsys, monkeypatch
):
    # target_hours_no_buffer が未設定のとき、残り日数に関わらず target_hours を使う。
    monkeypatch.setattr(tasks.module, "date", _frozen_date(2026, 6, 29))
    monkeypatch.setattr(tasks.module, "datetime", _frozen_now(2026, 6, 29, 10, 0))
    tasks.run("meta", "set", "target_hours_2026-06", "176")
    tasks.run("meta", "set", "holidays_2026-06", "[]")
    capsys.readouterr()
    tasks.run("work", "summary", "--month", "2026-06")
    out = json.loads(capsys.readouterr().out)
    assert out["target_hours"] == 176


# ---------- 作業時間の集計: 残営業日0の場合のtoday_plan ----------


def test_today_plan_absent_when_no_remaining_workdays(tasks, capsys, monkeypatch):
    # 今日が月の最終営業日で、すべての時間を記録済みなら、
    # remaining_workdaysは0、today_target_hoursはNoneになるが、
    # 当月であるためtoday_planは引き続き存在する。
    # KeyErrorが発生せず、予定のフィールドが存在することを保証する。
    monkeypatch.setattr(tasks.module, "date", _frozen_date(2026, 6, 30))
    monkeypatch.setattr(tasks.module, "datetime", _frozen_now(2026, 6, 30, 10, 0))
    tasks.run("meta", "set", "target_hours_2026-06", "160")
    tasks.run("meta", "set", "holidays_2026-06", "[]")
    capsys.readouterr()
    tasks.run("work", "summary", "--month", "2026-06")
    out = json.loads(capsys.readouterr().out)
    assert "today_plan" in out


# ---------- work set --planned（フレックス退勤予定） ----------
#
# フレックス退勤予定を先に登録するための予定エントリ。
#   --planned を付けると entry に planned: true と source: flex_plan が立つ。
#   前借りの配分計算はスキル層が行い、ツールは保存・読み出しだけ担当する。
#   planned な未来日は work summary の cumulative（実績）に混ざらない。


def test_work_set_planned_flags_entry(tasks, capsys):
    # --planned を付けると planned: true と source: flex_plan が立つ。
    tasks.run(
        "work", "set", "--date", "2026-07-09", "--segment", "09:30-17:15", "--planned"
    )
    out = json.loads(capsys.readouterr().out)
    entry = out["2026-07-09"]
    assert entry["planned"] is True
    assert entry["source"] == "flex_plan"
    assert entry["start"] == "09:30"
    assert entry["end"] == "17:15"


def test_work_set_planned_appears_in_show(tasks, capsys):
    # planned entry は work show log の出力に含まれる。
    tasks.run(
        "work", "set", "--date", "2026-07-09", "--segment", "09:30-17:15", "--planned"
    )
    capsys.readouterr()
    tasks.run("work", "show", "log", "--date", "2026-07-09")
    out = json.loads(capsys.readouterr().out)
    assert out["planned"] is True
    assert out["end"] == "17:15"


def test_work_set_real_clock_overwrites_planned(tasks, capsys):
    # 実打刻で set し直す（--planned なし）と planned が外れて実績になる。
    tasks.run(
        "work", "set", "--date", "2026-07-09", "--segment", "09:30-17:15", "--planned"
    )
    capsys.readouterr()
    tasks.run(
        "work",
        "set",
        "--date",
        "2026-07-09",
        "--segment",
        "09:24-18:45",
        "--source",
        "slack_clock",
    )
    out = json.loads(capsys.readouterr().out)
    entry = out["2026-07-09"]
    assert entry.get("planned") in (False, None)
    assert entry["source"] == "slack_clock"
    assert entry["end"] == "18:45"


def test_work_summary_excludes_planned_from_cumulative(tasks, capsys, monkeypatch):
    # planned な未来日は cumulative（実績）に入らない。月次に影響しないこと。
    monkeypatch.setattr(tasks.module, "date", _frozen_date(2026, 7, 8))
    monkeypatch.setattr(tasks.module, "datetime", _frozen_now(2026, 7, 8, 10, 0))
    tasks.run("meta", "set", "target_hours_2026-07", "160")
    tasks.run("meta", "set", "holidays_2026-07", "[]")
    # 実績（過去日）8h と、未来日の planned を入れる。
    tasks.run("work", "set", "--date", "2026-07-07", "--segment", "09:00-18:00")
    tasks.run(
        "work", "set", "--date", "2026-07-09", "--segment", "09:30-17:15", "--planned"
    )
    capsys.readouterr()
    tasks.run("work", "summary", "--month", "2026-07")
    out = json.loads(capsys.readouterr().out)
    # cumulative は過去日の 8h のみ。planned な 7/9 は含まれない。
    assert out["cumulative_hours"] == 8.0


def test_work_summary_excludes_planned_even_on_past_day(tasks, capsys, monkeypatch):
    # 過去日に planned が入っていても cumulative から除外する（予定は実績ではない）。
    monkeypatch.setattr(tasks.module, "date", _frozen_date(2026, 7, 8))
    monkeypatch.setattr(tasks.module, "datetime", _frozen_now(2026, 7, 8, 10, 0))
    tasks.run("meta", "set", "target_hours_2026-07", "160")
    tasks.run("meta", "set", "holidays_2026-07", "[]")
    tasks.run(
        "work", "set", "--date", "2026-07-06", "--segment", "09:30-17:15", "--planned"
    )
    capsys.readouterr()
    tasks.run("work", "summary", "--month", "2026-07")
    out = json.loads(capsys.readouterr().out)
    assert out["cumulative_hours"] == 0.0
