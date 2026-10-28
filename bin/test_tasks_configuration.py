"""設定がない環境や不正な勤務ルールで、実データに触れず失敗することを確認する。"""

import json
from pathlib import Path

import pytest
from _test_helpers import _load_tasks_module


def test_default_store_uses_shared_data_directory(tmp_path, monkeypatch):
    monkeypatch.delenv("TASKS_STORE", raising=False)
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    module = _load_tasks_module(configured=False)
    assert module.STORE == tmp_path / ".local" / "share" / "tasks" / "tasks.json"


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("daily_norma_hours", None),
        ("daily_norma_hours", 0),
        ("daily_norma_hours", True),
        ("daily_norma_hours", float("nan")),
        ("max_daily_hours", -1),
        ("core_time_floor", "25:00"),
        ("core_time_floor", "16:60"),
        ("break_default_minutes", "60"),
    ],
)
def test_invalid_work_rule_is_rejected(key, value):
    module = _load_tasks_module(configured=False)
    with pytest.raises(ValueError, match=key):
        module._work_rule({key: value}, key)


def test_missing_rules_do_not_change_existing_store(tmp_path, monkeypatch):
    store = tmp_path / "tasks.json"
    original = '{"tasks": [], "work_log": {}, "daily_logs": [], "meta": {}}'
    store.write_text(original, encoding="utf-8")
    monkeypatch.setenv("TASKS_STORE", str(store))
    module = _load_tasks_module(configured=False)
    args = module.build_parser().parse_args(["work", "summary", "--month", "2026-10"])
    with pytest.raises(ValueError, match="daily_norma_hours"):
        args.func(args)
    assert store.read_text(encoding="utf-8") == original
    module._release_store_lock()


def test_explicit_leave_times_override_sample_rules(tasks, capsys):
    tasks.run("meta", "set", "leave_start", "08:00")
    tasks.run("meta", "set", "leave_end", "17:00")
    capsys.readouterr()
    tasks.run("work", "leave", "set", "--date", "2026-10-22", "--type", "paid")
    entry = json.loads(capsys.readouterr().out)["2026-10-22"]
    assert entry["segments"] == [{"start": "08:00", "end": "17:00"}]
