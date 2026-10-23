"""Concurrency tests: multiple `tasks` CLI processes writing to the same
store at once must not corrupt the JSON or drop updates.

Real-world incident (2026-08-07): ten `tasks reorder <id> --tail` processes
launched in parallel via shell `&` corrupted tasks.json (a stray trailing
`}`) and silently dropped 8 of the 10 updates. `load()`/`save()` had no
mutual exclusion, so concurrent read-modify-write cycles raced.
"""

import json
import subprocess
import sys
from pathlib import Path

TASKS_SCRIPT = Path(__file__).parent / "tasks"


def _env(store):
    return {"CLAUDE_COMPANION_STORE": str(store), "PATH": "/usr/bin:/bin"}


def _run_cli(store, *argv):
    return subprocess.run(
        [sys.executable, str(TASKS_SCRIPT), *argv],
        env=_env(store),
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )


def _start_cli(store, *argv):
    return subprocess.Popen(
        [sys.executable, str(TASKS_SCRIPT), *argv],
        env=_env(store),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def test_parallel_reorder_tail_does_not_corrupt_or_drop_updates(tmp_path):
    store = tmp_path / "tasks.json"
    for i in range(10):
        result = _run_cli(store, "add", f"task-{i}")
        assert result.returncode == 0, result.stderr

    data = json.loads(store.read_text())
    ids = [t["id"] for t in data["tasks"]]
    assert len(ids) == 10

    procs = [_start_cli(store, "reorder", task_id, "--tail") for task_id in ids]
    for p in procs:
        _out, err = p.communicate(timeout=30)
        assert p.returncode == 0, err

    # The store must still parse as JSON — a corrupted file (e.g. a stray
    # trailing brace from an interleaved write) raises here.
    data = json.loads(store.read_text())

    updated = {t["id"]: t["queue_pos"] for t in data["tasks"]}
    assert len(updated) == 10
    # Every id must still be present and every queue_pos distinct — a lost
    # update (overwritten by a racing process) would collapse two ids onto
    # the same queue_pos or silently drop an id's move to the tail.
    assert set(updated) == set(ids)
    assert len(set(updated.values())) == 10
