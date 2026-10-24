"""単体のtasksコマンドを外部から検証する。"""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

TASKS = Path(
    os.environ.get(
        "TASKS_EXECUTABLE",
        str(Path(__file__).resolve().parents[1] / "bin" / "tasks"),
    )
)


@pytest.fixture
def isolated_tasks(tmp_path):
    """独立した保存先を使い、保管庫を未設定にしてCLIを実行する。"""
    env = os.environ.copy()
    store = tmp_path / "tasks.json"
    env["TASKS_STORE"] = str(store)

    def run(*args):
        return subprocess.run(
            [sys.executable, str(TASKS), *args],
            capture_output=True,
            text=True,
            check=False,
            env=env,
        )

    return run, store


def test_standalone_cli_keeps_existing_store_shape(isolated_tasks):
    run, store = isolated_tasks
    added = run("add", "sample task")
    assert added.returncode == 0, added.stderr

    listed = run("list")
    assert listed.returncode == 0, listed.stderr
    assert json.loads(listed.stdout)["tasks"][0]["title"] == "sample task"
    assert set(json.loads(store.read_text(encoding="utf-8"))) == {
        "tasks",
        "work_log",
        "daily_logs",
        "meta",
    }


def test_work_summary_requires_explicit_work_rules(isolated_tasks):
    run, _ = isolated_tasks
    summarized = run("work", "summary", "--month", "2026-10")
    assert summarized.returncode != 0
    assert "daily_norma_hours" in summarized.stderr
