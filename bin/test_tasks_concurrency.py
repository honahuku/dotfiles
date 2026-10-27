"""複数の`tasks` CLIプロセスが同じ保存先へ同時に書き込んでも、
JSONの破損や更新の欠落が起きないことを検証する。

2026-08-07に発生した事象では、シェルの`&`で10個の
`tasks reorder <id> --tail`を並列実行すると、tasks.jsonに余分な末尾の`}`が
混入し、10件中8件の更新が通知なく失われた。load()/save()に排他制御がなく、
読み取り・変更・保存の処理が競合していた。
"""

import json
import subprocess
import sys
from pathlib import Path

TASKS_SCRIPT = Path(__file__).parent / "tasks"


def _env(store):
    return {"TASKS_STORE": str(store), "PATH": "/usr/bin:/bin"}


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

    # 保存ファイルをJSONとして解析できることを確認する。書き込みの競合で
    # 閉じ括弧が余分に残るなど、破損していればここで例外になる。
    data = json.loads(store.read_text())

    updated = {t["id"]: t["queue_pos"] for t in data["tasks"]}
    assert len(updated) == 10
    # すべてのIDが残り、queue_posが重複しないことを確認する。
    # 競合するプロセスに更新を上書きされると、二つのIDが同じ
    # queue_posになったり、末尾へ移動した操作が失われたりする。
    assert set(updated) == set(ids)
    assert len(set(updated.values())) == 10
