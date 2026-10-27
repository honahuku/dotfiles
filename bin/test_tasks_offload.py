"""`tasks` CLIの移管候補の検出を検証する。

OFFLOAD_STALE_DAYSを超えて更新されていないfrom=meのタスクは、
タスク保存先からアイデアの保存先（Obsidian inbox / Notion）へ移す候補とする。
`list`は候補を`_offload_candidates`に含める。検出のみで、状態などは変更しない。
実際の移動は、ユーザーが保存する候補を選んだ後にoffloadスキルが行う。
`tasks`フィクスチャはconftest.pyで定義する。
"""

import datetime as _datetime
import json


def _age_task(tasks, title, days, *, from_="me", status="open"):
    """既存タスクのfrom/statusを設定し、updated_atを`days`日前に戻す。"""
    data = tasks.store()
    old = (_datetime.datetime.now() - _datetime.timedelta(days=days)).isoformat(
        timespec="seconds"
    )
    for t in data["tasks"]:
        if t["title"] == title:
            t["from"] = from_
            t["status"] = status
            t["updated_at"] = old
    tasks.store_path.write_text(json.dumps(data))


def test_offload_candidate_from_me_stale(tasks, capsys):
    tasks.run("add", "old idea", "--from", "me")
    _age_task(tasks, "old idea", days=20)
    capsys.readouterr()
    tasks.run("list")
    out = json.loads(capsys.readouterr().out)
    cands = out.get("_offload_candidates", [])
    assert any(c["title"] == "old idea" and c["stale_days"] >= 14 for c in cands)


def test_offload_candidate_carries_fields(tasks, capsys):
    tasks.run(
        "add",
        "detailed idea",
        "--from",
        "me",
        "--source",
        "notion",
        "--source-url",
        "https://notion.so/x",
    )
    _age_task(tasks, "detailed idea", days=20, status="open")
    capsys.readouterr()
    tasks.run("list")
    out = json.loads(capsys.readouterr().out)
    c = next(c for c in out["_offload_candidates"] if c["title"] == "detailed idea")
    assert c["source"] == "notion"
    assert c["source_url"] == "https://notion.so/x"
    assert "id" in c and "updated_at" in c


def test_offload_skips_from_others(tasks, capsys):
    tasks.run("add", "someone elses ask", "--from", "others")
    _age_task(tasks, "someone elses ask", days=20, from_="others")
    capsys.readouterr()
    tasks.run("list")
    out = json.loads(capsys.readouterr().out)
    assert "_offload_candidates" not in out


def test_offload_skips_in_progress(tasks, capsys):
    tasks.run("add", "active work", "--from", "me")
    _age_task(tasks, "active work", days=20, status="in-progress")
    capsys.readouterr()
    tasks.run("list", "--all")
    out = json.loads(capsys.readouterr().out)
    assert "_offload_candidates" not in out


def test_offload_skips_recent(tasks, capsys):
    tasks.run("add", "fresh idea", "--from", "me")
    _age_task(tasks, "fresh idea", days=5)
    capsys.readouterr()
    tasks.run("list")
    out = json.loads(capsys.readouterr().out)
    assert "_offload_candidates" not in out


def test_offload_boundary_fourteen_days(tasks, capsys):
    tasks.run("add", "borderline idea", "--from", "me")
    _age_task(tasks, "borderline idea", days=14)
    capsys.readouterr()
    tasks.run("list")
    out = json.loads(capsys.readouterr().out)
    assert any(
        c["title"] == "borderline idea" for c in out.get("_offload_candidates", [])
    )


def test_offload_detection_does_not_mutate_status(tasks, capsys):
    # 検出時にはタスクを取り消したり変更したりせず、後でスキルが操作する。
    tasks.run("add", "keep as is", "--from", "me")
    _age_task(tasks, "keep as is", days=20, status="open")
    capsys.readouterr()
    tasks.run("list")
    capsys.readouterr()
    assert tasks.by_title("keep as is")["status"] == "open"


def test_offload_includes_stale_pending_from_me(tasks, capsys):
    # 14日を超えたfrom=meのpendingタスクは、長期停滞の処理でopenへ戻り、
    # 同じlistの呼び出しで委譲候補にも該当する。
    tasks.run("add", "stuck mine", "--from", "me")
    _age_task(tasks, "stuck mine", days=20, status="pending")
    capsys.readouterr()
    tasks.run("list")
    out = json.loads(capsys.readouterr().out)
    assert any(c["title"] == "stuck mine" for c in out.get("_offload_candidates", []))
