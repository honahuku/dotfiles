"""勤務記録の有給休暇と代休を検証する。"""

import json

import pytest


def test_full_day_leave_records_standard_workday(tasks, capsys):
    tasks.run("work", "leave", "set", "--date", "2026-06-08", "--type", "paid")

    entry = json.loads(capsys.readouterr().out)["2026-06-08"]

    assert entry["start"] == "10:00"
    assert entry["end"] == "19:00"
    assert entry["hours"] == 8.0
    assert entry["work_hours"] == 0.0
    assert entry["leave"] == {"type": "paid", "hours": 8.0}


@pytest.mark.parametrize("period", ["am", "pm"])
def test_half_day_paid_leave_records_period(tasks, capsys, period):
    tasks.run(
        "work",
        "leave",
        "set",
        "--date",
        "2026-06-08",
        "--type",
        "paid",
        "--period",
        period,
    )

    entry = json.loads(capsys.readouterr().out)["2026-06-08"]

    assert entry["hours"] == 4.0
    assert entry["work_hours"] == 0.0
    assert entry["leave"] == {"type": "paid", "hours": 4.0, "period": period}


def test_half_day_compensatory_leave_records_period(tasks, capsys):
    tasks.run(
        "work",
        "leave",
        "set",
        "--date",
        "2026-06-08",
        "--type",
        "comp",
        "--period",
        "pm",
    )

    entry = json.loads(capsys.readouterr().out)["2026-06-08"]

    assert entry["hours"] == 4.0
    assert entry["leave"] == {"type": "comp", "hours": 4.0, "period": "pm"}


def test_half_day_leave_rejects_hourly_amount(tasks, capsys):
    with pytest.raises(SystemExit):
        tasks.run(
            "work",
            "leave",
            "set",
            "--date",
            "2026-06-08",
            "--type",
            "paid",
            "--period",
            "am",
            "--hours",
            "4",
        )

    capsys.readouterr()


def test_hourly_leave_adds_to_work_hours(tasks, capsys):
    tasks.run(
        "work",
        "set",
        "--date",
        "2026-06-08",
        "--segment",
        "09:00-18:00",
    )
    capsys.readouterr()

    tasks.run(
        "work",
        "leave",
        "set",
        "--date",
        "2026-06-08",
        "--type",
        "paid",
        "--hours",
        "1",
    )
    entry = json.loads(capsys.readouterr().out)["2026-06-08"]

    assert entry["work_hours"] == 8.0
    assert entry["hours"] == 9.0
    assert entry["leave"] == {"type": "paid", "hours": 1.0}


def test_work_set_after_hourly_leave_keeps_leave_credit(tasks, capsys):
    tasks.run(
        "work",
        "leave",
        "set",
        "--date",
        "2026-06-08",
        "--type",
        "paid",
        "--hours",
        "1",
    )
    capsys.readouterr()

    tasks.run(
        "work",
        "set",
        "--date",
        "2026-06-08",
        "--segment",
        "10:00-17:00",
    )
    entry = json.loads(capsys.readouterr().out)["2026-06-08"]

    assert entry["work_hours"] == 6.0
    assert entry["hours"] == 7.0
    assert entry["leave"] == {"type": "paid", "hours": 1.0}


def test_hourly_leave_without_work_is_counted(tasks, capsys):
    tasks.run(
        "work",
        "leave",
        "set",
        "--date",
        "2026-06-08",
        "--type",
        "paid",
        "--hours",
        "1",
    )

    entry = json.loads(capsys.readouterr().out)["2026-06-08"]

    assert entry["work_hours"] == 0.0
    assert entry["hours"] == 1.0
    assert entry["leave"] == {"type": "paid", "hours": 1.0}


def test_hourly_leave_rejects_half_hour_units(tasks, capsys):
    with pytest.raises(SystemExit):
        tasks.run(
            "work",
            "leave",
            "set",
            "--date",
            "2026-06-08",
            "--type",
            "paid",
            "--hours",
            "1.5",
        )

    capsys.readouterr()


def test_compensatory_leave_is_annotated(tasks, capsys):
    tasks.run(
        "work",
        "leave",
        "set",
        "--date",
        "2026-06-08",
        "--type",
        "comp",
    )

    entry = json.loads(capsys.readouterr().out)["2026-06-08"]
    assert entry["hours"] == 8.0
    assert entry["leave"]["type"] == "comp"


def test_full_day_leave_is_not_unfilled(tasks, capsys):
    tasks.run(
        "meta",
        "set",
        "workdays_2026-06",
        '["2026-06-08", "2026-06-09"]',
    )
    tasks.run("work", "leave", "set", "--date", "2026-06-08", "--type", "paid")
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
    entries = json.loads(capsys.readouterr().out)["unfilled_entries"]

    assert entries == [{"date": "2026-06-09", "status": "missing"}]


def test_hourly_leave_without_work_is_not_unfilled(tasks, capsys):
    tasks.run(
        "meta",
        "set",
        "workdays_2026-06",
        '["2026-06-08"]',
    )
    tasks.run(
        "work",
        "leave",
        "set",
        "--date",
        "2026-06-08",
        "--type",
        "paid",
        "--hours",
        "1",
    )
    capsys.readouterr()

    tasks.run(
        "work",
        "show",
        "unfilled-entries",
        "--month",
        "2026-06",
        "--through",
        "2026-06-08",
    )
    entries = json.loads(capsys.readouterr().out)["unfilled_entries"]

    assert entries == []
