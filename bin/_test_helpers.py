"""Shared, non-fixture helpers for the `tasks` CLI test suite.

Test files import from here (`from _test_helpers import _load_tasks_module`).
The `tasks` fixture lives in conftest.py and depends on `_load_tasks_module`
defined here.
"""

import importlib.util
from importlib.machinery import SourceFileLoader
from pathlib import Path

SCRIPT_PATH = Path(__file__).with_name("tasks")


SAMPLE_WORK_RULES = {
    "daily_norma_hours": 8,
    "max_daily_hours": 12,
    "core_time_floor": "16:00",
    "flex_time_end": "22:00",
    "std_start": "09:30",
    "std_end": "18:30",
    "break_default_minutes": 60,
    "wind_down_default_minutes": 5,
    "leave_start": "10:00",
    "leave_end": "19:00",
    "month_buffer_hours": 1,
}


def _load_tasks_module(configured=True):
    # The script has no .py extension, so spec_from_file_location can't infer a
    # loader on its own — pass a SourceFileLoader explicitly.
    loader = SourceFileLoader("tasks_cli", str(SCRIPT_PATH))
    spec = importlib.util.spec_from_loader("tasks_cli", loader)
    mod = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)
    if configured:
        # 既存の計算テストにはルールを明示し、本体には既定値を戻さない。
        work_rule = mod._work_rule
        mod._work_rule = lambda meta, key: work_rule({**SAMPLE_WORK_RULES, **meta}, key)
    return mod
