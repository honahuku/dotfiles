"""CRUD, ordering, filtering, dependency, snooze, and migration tests for the
`tasks` CLI. The `tasks` fixture comes from conftest.py.
"""

import datetime as _datetime
import json

import pytest

# ---------- add ----------


@pytest.mark.parametrize("option", ["--normalize", "--by-tier"])
def test_reorder_unchanged_preserves_store_and_skips_backups(
    tasks, capsys, monkeypatch, option
):
    tasks.run("add", "implementation")
    capsys.readouterr()
    before = tasks.store_path.read_bytes()
    backups = []
    monkeypatch.setattr(tasks.module, "now_iso", lambda: "2099-01-01T00:00:00")
    monkeypatch.setattr(
        tasks.module, "_backup_to_git", lambda **kwargs: backups.append("store")
    )
    monkeypatch.setattr(
        tasks.module, "_sync_obsidian", lambda data: backups.append("sync")
    )
    tasks.run("reorder", option)
    assert tasks.store_path.read_bytes() == before
    assert backups == []
    assert json.loads(capsys.readouterr().out)["changed"] is False


def test_reorder_changes_only_moved_task_timestamps(tasks, capsys, monkeypatch):
    tasks.run("add", "first", "--queue-pos", "10")
    tasks.run("add", "second", "--queue-pos", "55")
    capsys.readouterr()
    first_timestamp = tasks.by_title("first")["updated_at"]
    monkeypatch.setattr(tasks.module, "now_iso", lambda: "2099-01-01T00:00:00")
    tasks.run("reorder", "--normalize")
    assert tasks.positions() == [("first", 10), ("second", 20)]
    assert tasks.by_title("first")["updated_at"] == first_timestamp
    assert tasks.by_title("second")["updated_at"] == "2099-01-01T00:00:00"
    assert json.loads(capsys.readouterr().out)["changed"] is True


def test_add_defaults_to_me_at_tail(tasks, capsys):
    tasks.run("add", "first")
    capsys.readouterr()
    t = tasks.by_title("first")
    assert t["from"] == "me"
    assert t["queue_pos"] == 10  # first task starts at 10, not 0
    assert t["due"] is None


def test_add_from_others(tasks, capsys):
    tasks.run("add", "task from boss", "--from", "others")
    capsys.readouterr()
    assert tasks.by_title("task from boss")["from"] == "others"


def test_add_from_me(tasks, capsys):
    tasks.run("add", "self-initiated task", "--from", "me")
    capsys.readouterr()
    assert tasks.by_title("self-initiated task")["from"] == "me"


def test_add_invalid_from_value_rejected(tasks, capsys):
    import pytest

    with pytest.raises(SystemExit):
        tasks.run("add", "bad task", "--from", "must")


def test_add_appends_in_steps_of_ten(tasks, capsys):
    tasks.run("add", "A", "--from", "others")
    tasks.run("add", "B", "--from", "others")
    tasks.run("add", "C", "--from", "me")
    capsys.readouterr()
    assert tasks.positions() == [("A", 10), ("B", 20), ("C", 30)]


def test_add_explicit_queue_pos(tasks, capsys):
    tasks.run("add", "A", "--queue-pos", "55")
    capsys.readouterr()
    assert tasks.by_title("A")["queue_pos"] == 55


def test_add_with_due(tasks, capsys):
    tasks.run("add", "deadline task", "--from", "others", "--due", "2026-06-30")
    capsys.readouterr()
    assert tasks.by_title("deadline task")["due"] == "2026-06-30"


def test_add_blocked_by_sets_pending(tasks, capsys):
    tasks.run("add", "blocked", "--blocked-by", "https://github.com/o/r/pull/1")
    capsys.readouterr()
    assert tasks.by_title("blocked")["status"] == "pending"


# ---------- list / sort ----------


def test_list_sorts_by_queue_pos(tasks, capsys):
    tasks.run("add", "A", "--queue-pos", "30")
    tasks.run("add", "B", "--queue-pos", "10")
    tasks.run("add", "C", "--queue-pos", "20")
    capsys.readouterr()
    tasks.run("list")
    out = json.loads(capsys.readouterr().out)
    assert [t["title"] for t in out["tasks"]] == ["B", "C", "A"]


def test_overdue_bubbles_to_front(tasks, capsys, monkeypatch):
    # Freeze "today" so the test is deterministic.
    monkeypatch.setattr(tasks.module, "today_str", lambda: "2026-06-08")
    tasks.run("add", "normal", "--queue-pos", "10")
    tasks.run("add", "overdue", "--queue-pos", "999", "--due", "2026-06-01")
    capsys.readouterr()
    tasks.run("list")
    out = json.loads(capsys.readouterr().out)
    # overdue task should come first despite a much larger queue_pos
    assert out["tasks"][0]["title"] == "overdue"


def test_dated_task_beats_undated(tasks, capsys, monkeypatch):
    # A task with any due date (even far in the future) sorts ahead of an
    # undated one, regardless of queue_pos. Having a deadline outranks tier.
    monkeypatch.setattr(tasks.module, "today_str", lambda: "2026-06-08")
    tasks.run("add", "dated", "--queue-pos", "20", "--due", "2026-12-31")
    tasks.run("add", "undated", "--queue-pos", "10")
    capsys.readouterr()
    tasks.run("list")
    out = json.loads(capsys.readouterr().out)
    assert [t["title"] for t in out["tasks"]] == ["dated", "undated"]


def test_dated_tasks_sort_by_date_ascending(tasks, capsys, monkeypatch):
    # Among dated tasks, overdue and future alike order by date ascending, so
    # overdue naturally comes first and nearer deadlines precede farther ones.
    monkeypatch.setattr(tasks.module, "today_str", lambda: "2026-06-08")
    tasks.run("add", "future-far", "--queue-pos", "10", "--due", "2026-12-31")
    tasks.run("add", "overdue", "--queue-pos", "20", "--due", "2026-06-01")
    tasks.run("add", "future-near", "--queue-pos", "30", "--due", "2026-06-20")
    capsys.readouterr()
    tasks.run("list")
    out = json.loads(capsys.readouterr().out)
    assert [t["title"] for t in out["tasks"]] == [
        "overdue",
        "future-near",
        "future-far",
    ]


def test_list_from_filter_others(tasks, capsys):
    tasks.run("add", "external task", "--from", "others")
    tasks.run("add", "self task", "--from", "me")
    capsys.readouterr()
    tasks.run("list", "--from", "others")
    out = json.loads(capsys.readouterr().out)
    assert [t["title"] for t in out["tasks"]] == ["external task"]


def test_list_from_filter_me(tasks, capsys):
    tasks.run("add", "external task", "--from", "others")
    tasks.run("add", "self task", "--from", "me")
    capsys.readouterr()
    tasks.run("list", "--from", "me")
    out = json.loads(capsys.readouterr().out)
    assert [t["title"] for t in out["tasks"]] == ["self task"]


# ---------- update ----------


def test_update_from_and_due(tasks, capsys):
    tasks.run("add", "x", "--from", "me")
    capsys.readouterr()
    tid = tasks.by_title("x")["id"]
    tasks.run("update", tid, "--from", "others", "--due", "2026-07-01")
    capsys.readouterr()
    t = tasks.by_title("x")
    assert t["from"] == "others"
    assert t["due"] == "2026-07-01"


def test_update_from_me_to_others(tasks, capsys):
    tasks.run("add", "x", "--from", "me")
    capsys.readouterr()
    tid = tasks.by_title("x")["id"]
    tasks.run("update", tid, "--from", "others")
    capsys.readouterr()
    assert tasks.by_title("x")["from"] == "others"


def test_update_clears_due_with_empty_string(tasks, capsys):
    tasks.run("add", "x", "--due", "2026-07-01")
    capsys.readouterr()
    tid = tasks.by_title("x")["id"]
    tasks.run("update", tid, "--due", "")
    capsys.readouterr()
    assert tasks.by_title("x")["due"] is None


# ---------- reorder ----------


def _add_three(tasks, capsys):
    tasks.run("add", "A", "--from", "others")
    tasks.run("add", "B", "--from", "others")
    tasks.run("add", "C", "--from", "others")
    capsys.readouterr()


def test_reorder_head_takes_min_minus_one(tasks, capsys):
    _add_three(tasks, capsys)  # 10, 20, 30
    cid = tasks.by_title("C")["id"]
    tasks.run("reorder", cid, "--head")
    capsys.readouterr()
    assert tasks.by_title("C")["queue_pos"] == 9
    assert tasks.positions()[0][0] == "C"


def test_reorder_head_never_goes_below_one(tasks, capsys):
    _add_three(tasks, capsys)
    # Force the head task down to pos=1 so there's no integer gap before it.
    cid = tasks.by_title("C")["id"]
    tasks.run("update", cid, "--queue-pos", "1")
    capsys.readouterr()
    # Now head-move B: min is 1, 1-1=0 (<1) → renumber, B lands positive at front.
    bid = tasks.by_title("B")["id"]
    tasks.run("reorder", bid, "--head")
    capsys.readouterr()
    assert tasks.by_title("B")["queue_pos"] >= 1
    assert tasks.positions()[0][0] == "B"
    # No task should ever hold a non-positive queue_pos.
    assert all(p >= 1 for _, p in tasks.positions())


def test_reorder_tail_takes_max_plus_one(tasks, capsys):
    _add_three(tasks, capsys)  # 10, 20, 30
    aid = tasks.by_title("A")["id"]
    tasks.run("reorder", aid, "--tail")
    capsys.readouterr()
    assert tasks.by_title("A")["queue_pos"] == 31
    assert tasks.positions()[-1][0] == "A"


def test_reorder_before_inserts_between(tasks, capsys):
    _add_three(tasks, capsys)  # 10, 20, 30
    aid = tasks.by_title("A")["id"]
    cid = tasks.by_title("C")["id"]
    tasks.run("reorder", aid, "--before", cid)
    capsys.readouterr()
    # A should now sit between B (20) and C (30): order B, A, C
    assert [t for t, _ in tasks.positions()] == ["B", "A", "C"]


def test_reorder_after_inserts_between(tasks, capsys):
    _add_three(tasks, capsys)  # 10, 20, 30
    aid = tasks.by_title("A")["id"]
    cid = tasks.by_title("C")["id"]
    tasks.run("reorder", aid, "--after", cid)
    capsys.readouterr()
    # A moves to just after C: order B, C, A
    assert [t for t, _ in tasks.positions()] == ["B", "C", "A"]


def test_reorder_before_renumbers_when_no_gap(tasks, capsys):
    _add_three(tasks, capsys)
    # Make B and C adjacent integers so there's no gap to slot A before C.
    bid = tasks.by_title("B")["id"]
    cid = tasks.by_title("C")["id"]
    tasks.run("update", bid, "--queue-pos", "9")
    tasks.run("update", cid, "--queue-pos", "10")
    capsys.readouterr()
    aid = tasks.by_title("A")["id"]
    tasks.run("reorder", aid, "--before", cid)
    capsys.readouterr()
    # After renumber + insert, A must end up directly before C in order.
    order = [t for t, _ in tasks.positions()]
    assert order.index("A") + 1 == order.index("C")


def test_normalize_starts_at_ten(tasks, capsys):
    tasks.run("add", "A", "--queue-pos", "3")
    tasks.run("add", "B", "--queue-pos", "7")
    tasks.run("add", "C", "--queue-pos", "99")
    capsys.readouterr()
    tasks.run("reorder", "--normalize")
    capsys.readouterr()
    assert tasks.positions() == [("A", 10), ("B", 20), ("C", 30)]


def test_normalize_preserves_order(tasks, capsys):
    tasks.run("add", "X", "--queue-pos", "50")
    tasks.run("add", "Y", "--queue-pos", "5")
    capsys.readouterr()
    tasks.run("reorder", "--normalize")
    capsys.readouterr()
    assert [t for t, _ in tasks.positions()] == ["Y", "X"]


# ---------- tier classification ----------


def test_task_tier_classifies_by_title_and_source(tasks):
    tier = tasks.module._task_tier
    # tier3: Renovate dependency-update review.
    assert (
        tier(
            {
                "title": "cloudflare v5 依存更新 レビュー (project #1)",
                "from": "others",
                "source": "github",
                "status": "open",
            }
        )
        == 3
    )
    # tier2: human PR review request.
    assert (
        tier(
            {
                "title": "PR #2: カタログ追加 — レビュー (Reviewer)",
                "from": "others",
                "source": "github",
                "status": "open",
            }
        )
        == 2
    )
    # tier1: own PR reply — from=others but title carries a tier1 marker.
    assert (
        tier(
            {
                "title": "PR #3: 管理方針 — 返信",
                "from": "others",
                "source": "github",
                "status": "open",
            }
        )
        == 1
    )
    # tier1: self-initiated / non-github real work.
    assert (
        tier(
            {
                "title": "20期目標を練り直す",
                "from": "others",
                "source": "local",
                "status": "open",
            }
        )
        == 1
    )
    # tier0: in-progress bubbles ahead of every tier regardless of title.
    assert (
        tier(
            {
                "title": "cloudflare v5 依存更新 レビュー (project #1)",
                "from": "others",
                "source": "github",
                "status": "in-progress",
            }
        )
        == 0
    )


def test_task_tier_renovate_beats_reviewer_suffix(tasks):
    # A title that happens to carry both markers must resolve to tier3
    # (dependency-update is evaluated first, so it wins over the Reviewer suffix).
    tier = tasks.module._task_tier
    t = {
        "title": "x 依存更新 レビュー (project #9) — レビュー (Reviewer)",
        "from": "others",
        "source": "github",
        "status": "open",
    }
    assert tier(t) == 3


# ---------- reorder --by-tier ----------


def _add_github(tasks, title):
    tasks.run(
        "add",
        title,
        "--from",
        "others",
        "--source",
        "github",
        "--source-url",
        "https://github.com/o/r/pull/1",
    )


def test_reorder_by_tier_orders_groups(tasks, capsys):
    # Add in a deliberately scrambled order; --by-tier must regroup 1 → 2 → 3.
    _add_github(tasks, "keda v2 依存更新 レビュー (project #1)")  # tier3
    _add_github(tasks, "PR #2: 基盤追加 — レビュー (Reviewer)")  # tier2
    _add_github(tasks, "PR #3: 自分のPR — 返信")  # tier1
    capsys.readouterr()
    tasks.run("reorder", "--by-tier")
    capsys.readouterr()
    titles = [t for t, _ in tasks.positions()]
    assert titles == [
        "PR #3: 自分のPR — 返信",
        "PR #2: 基盤追加 — レビュー (Reviewer)",
        "keda v2 依存更新 レビュー (project #1)",
    ]
    # Positions are renumbered in steps of 10 starting at 10.
    assert [p for _, p in tasks.positions()] == [10, 20, 30]


def test_reorder_by_tier_preserves_intra_tier_manual_order(tasks, capsys):
    # Two tier3 tasks; flip their manual order, then --by-tier must keep that
    # flipped order within the tier (manual reorder is not clobbered).
    _add_github(tasks, "a v1 依存更新 レビュー (project #1)")
    _add_github(tasks, "b v1 依存更新 レビュー (project #2)")
    bid = tasks.by_title("b v1 依存更新 レビュー (project #2)")["id"]
    tasks.run("reorder", bid, "--head")  # b moved before a manually
    capsys.readouterr()
    tasks.run("reorder", "--by-tier")
    capsys.readouterr()
    titles = [t for t, _ in tasks.positions()]
    assert titles == [
        "b v1 依存更新 レビュー (project #2)",
        "a v1 依存更新 レビュー (project #1)",
    ]


def test_reorder_by_tier_reviewee_beats_renovate(tasks, capsys):
    # Regression for the c9748037 case: an own-PR reply (— 返信) registered
    # AFTER a pile of Renovate reviews must still sort ahead of them.
    for i in range(3):
        _add_github(tasks, f"dep{i} 依存更新 レビュー (project #{i})")
    _add_github(tasks, "PR #356: プロジェクト削除 — 返信")  # tier1, added last
    capsys.readouterr()
    tasks.run("reorder", "--by-tier")
    capsys.readouterr()
    assert tasks.positions()[0][0] == "PR #356: プロジェクト削除 — 返信"


def test_reorder_by_tier_puts_in_progress_first(tasks, capsys):
    # in-progress is tier0: its queue_pos becomes the smallest so Obsidian's
    # filename prefix (driven by queue_pos) also shows it first — matching the
    # list view where status_rank already floats it to the top.
    _add_github(tasks, "PR #1: 自分のPR — 返信")  # tier1
    _add_github(tasks, "dep 依存更新 レビュー (project #2)")  # tier3
    wid = tasks.by_title("dep 依存更新 レビュー (project #2)")["id"]
    tasks.run("update", wid, "--status", "in-progress")
    capsys.readouterr()
    tasks.run("reorder", "--by-tier")
    capsys.readouterr()
    # positions() only lists open/pending, so check queue_pos directly.
    wip = tasks.by_title("dep 依存更新 レビュー (project #2)")
    tier1 = tasks.by_title("PR #1: 自分のPR — 返信")
    assert wip["queue_pos"] < tier1["queue_pos"]


def test_reorder_by_tier_dated_beats_undated(tasks, capsys, monkeypatch):
    # --by-tier bakes the list order into queue_pos, so a dated task (even a
    # low-tier Renovate one) gets a smaller queue_pos than an undated tier1 task.
    # This keeps Obsidian's filename order identical to the list view.
    monkeypatch.setattr(tasks.module, "today_str", lambda: "2026-06-08")
    _add_github(tasks, "PR #1: 自分のPR — 返信")  # tier1, undated
    _add_github(tasks, "dep 依存更新 レビュー (project #2)")  # tier3, undated
    tasks.run(
        "add",
        "dep 依存更新 レビュー (project #3)",
        "--from",
        "others",
        "--source",
        "github",
        "--source-url",
        "https://github.com/o/r/pull/3",
        "--due",
        "2026-06-20",
    )  # tier3, dated
    capsys.readouterr()
    tasks.run("reorder", "--by-tier")
    capsys.readouterr()
    dated = tasks.by_title("dep 依存更新 レビュー (project #3)")
    undated_tier1 = tasks.by_title("PR #1: 自分のPR — 返信")
    # A dated tier3 task outranks an undated tier1 task in queue_pos.
    assert dated["queue_pos"] < undated_tier1["queue_pos"]


def test_reorder_by_tier_matches_list_order(tasks, capsys, monkeypatch):
    # The queue_pos order baked by --by-tier must equal the list display order:
    # list (via _task_sort_key) and --by-tier share one ordering rule.
    monkeypatch.setattr(tasks.module, "today_str", lambda: "2026-06-08")
    _add_github(tasks, "PR #1: 自分のPR — 返信")  # tier1, undated
    _add_github(tasks, "PR #2: 基盤 — レビュー (Reviewer)")  # tier2, undated
    _add_github(tasks, "dep 依存更新 レビュー (project #3)")  # tier3, undated
    tasks.run(
        "add", "締切あり作業", "--from", "others", "--due", "2026-06-20"
    )  # tier1, dated
    capsys.readouterr()
    tasks.run("reorder", "--by-tier")
    capsys.readouterr()
    # Order the store by queue_pos (what Obsidian filenames follow).
    by_qpos = [t for t, _ in tasks.positions()]
    tasks.run("list")
    by_list = [t["title"] for t in json.loads(capsys.readouterr().out)["tasks"]]
    assert by_qpos == by_list
    # And the head is the dated task, ahead of every undated tier.
    assert by_list[0] == "締切あり作業"


# ---------- delete ----------


def test_delete_removes_task(tasks, capsys):
    tasks.run("add", "doomed")
    capsys.readouterr()
    tid = tasks.by_title("doomed")["id"]
    tasks.run("delete", tid)
    capsys.readouterr()
    assert tasks.store()["tasks"] == []


# ---------- error paths (exit on not-found) ----------


def test_update_unknown_id_exits(tasks):
    with pytest.raises(SystemExit):
        tasks.run("update", "deadbeef", "--title", "x")


def test_delete_unknown_id_exits(tasks):
    with pytest.raises(SystemExit):
        tasks.run("delete", "deadbeef")


def test_get_unknown_id_exits(tasks):
    with pytest.raises(SystemExit):
        tasks.run("get", "deadbeef")


def test_get_returns_task(tasks, capsys):
    tasks.run("add", "gettable")
    capsys.readouterr()
    tid = tasks.by_title("gettable")["id"]
    tasks.run("get", tid)
    out = json.loads(capsys.readouterr().out)
    assert out["title"] == "gettable"


def test_reorder_unknown_id_exits(tasks, capsys):
    tasks.run("add", "A")
    capsys.readouterr()
    with pytest.raises(SystemExit):
        tasks.run("reorder", "deadbeef", "--head")


def test_reorder_before_unknown_ref_exits(tasks, capsys):
    tasks.run("add", "A")
    capsys.readouterr()
    aid = tasks.by_title("A")["id"]
    with pytest.raises(SystemExit):
        tasks.run("reorder", aid, "--before", "deadbeef")


def test_reorder_no_flag_exits(tasks, capsys):
    tasks.run("add", "A")
    capsys.readouterr()
    aid = tasks.by_title("A")["id"]
    with pytest.raises(SystemExit):
        tasks.run("reorder", aid)


def test_reorder_head_on_only_task(tasks, capsys):
    tasks.run("add", "solo")
    capsys.readouterr()
    sid = tasks.by_title("solo")["id"]
    tasks.run("reorder", sid, "--head")
    capsys.readouterr()
    assert tasks.by_title("solo")["queue_pos"] == 10


def test_reorder_tail_on_only_task(tasks, capsys):
    tasks.run("add", "solo")
    capsys.readouterr()
    sid = tasks.by_title("solo")["id"]
    tasks.run("reorder", sid, "--tail")
    capsys.readouterr()
    assert tasks.by_title("solo")["queue_pos"] == 10


def test_update_blocked_by_then_clear(tasks, capsys):
    tasks.run("add", "x")
    capsys.readouterr()
    tid = tasks.by_title("x")["id"]
    tasks.run("update", tid, "--blocked-by", "https://github.com/o/r/pull/9")
    capsys.readouterr()
    assert tasks.by_title("x")["status"] == "pending"
    tasks.run("update", tid, "--blocked-by", "", "--status", "open")
    capsys.readouterr()
    t = tasks.by_title("x")
    assert t["blocked_by"] is None
    assert t["status"] == "open"


def test_update_status_done_sets_completed_at(tasks, capsys):
    tasks.run("add", "x")
    capsys.readouterr()
    tid = tasks.by_title("x")["id"]
    tasks.run("update", tid, "--status", "done")
    capsys.readouterr()
    assert tasks.by_title("x")["completed_at"] is not None


def test_update_completed_at_explicit(tasks, capsys):
    tasks.run("add", "x")
    capsys.readouterr()
    tid = tasks.by_title("x")["id"]
    tasks.run(
        "update", tid, "--status", "done", "--completed-at", "2026-06-22T16:04:00"
    )
    out = json.loads(capsys.readouterr().out)
    assert out["completed_at"] == "2026-06-22T16:04:00"


def test_update_completed_at_without_status(tasks, capsys):
    # --completed-at alone (already done task) should update only the timestamp
    tasks.run("add", "x")
    capsys.readouterr()
    tid = tasks.by_title("x")["id"]
    tasks.run("update", tid, "--status", "done")
    capsys.readouterr()
    tasks.run("update", tid, "--completed-at", "2026-06-22T16:04:00")
    out = json.loads(capsys.readouterr().out)
    assert out["completed_at"] == "2026-06-22T16:04:00"
    assert out["status"] == "done"


def test_update_status_back_to_open_clears_completed_at(tasks, capsys):
    """done → open に戻したら completed_at も消す（誤って done にした後の巻き戻し）。"""
    tasks.run("add", "x")
    capsys.readouterr()
    tid = tasks.by_title("x")["id"]
    tasks.run("update", tid, "--status", "done")
    capsys.readouterr()
    tasks.run("update", tid, "--status", "open")
    out = json.loads(capsys.readouterr().out)
    assert out["status"] == "open"
    assert out["completed_at"] is None


def test_update_status_to_in_progress_clears_completed_at(tasks, capsys):
    tasks.run("add", "x")
    capsys.readouterr()
    tid = tasks.by_title("x")["id"]
    tasks.run("update", tid, "--status", "done")
    capsys.readouterr()
    tasks.run("update", tid, "--status", "in-progress")
    out = json.loads(capsys.readouterr().out)
    assert out["completed_at"] is None


def test_update_status_done_with_explicit_completed_at_not_cleared(tasks, capsys):
    """--status done と --completed-at を同時指定した場合は明示値を尊重する。"""
    tasks.run("add", "x")
    capsys.readouterr()
    tid = tasks.by_title("x")["id"]
    tasks.run(
        "update", tid, "--status", "done", "--completed-at", "2026-06-22T16:04:00"
    )
    out = json.loads(capsys.readouterr().out)
    assert out["completed_at"] == "2026-06-22T16:04:00"


def test_update_created_at_explicit(tasks, capsys):
    tasks.run("add", "x")
    capsys.readouterr()
    tid = tasks.by_title("x")["id"]
    tasks.run("update", tid, "--created-at", "2026-06-20T09:00:00")
    out = json.loads(capsys.readouterr().out)
    assert out["created_at"] == "2026-06-20T09:00:00"


def test_update_created_at_and_completed_at_together(tasks, capsys):
    tasks.run("add", "x")
    capsys.readouterr()
    tid = tasks.by_title("x")["id"]
    tasks.run(
        "update",
        tid,
        "--status",
        "done",
        "--created-at",
        "2026-06-20T09:00:00",
        "--completed-at",
        "2026-06-22T16:04:00",
    )
    out = json.loads(capsys.readouterr().out)
    assert out["created_at"] == "2026-06-20T09:00:00"
    assert out["completed_at"] == "2026-06-22T16:04:00"


def test_update_title_and_notes(tasks, capsys):
    tasks.run("add", "old")
    capsys.readouterr()
    tid = tasks.by_title("old")["id"]
    tasks.run("update", tid, "--title", "new", "--append-notes", "a note")
    out = json.loads(capsys.readouterr().out)
    assert out["title"] == "new"
    assert out["notes"] == "a note"


def test_update_notes_appends_explicitly(tasks, capsys):
    # --append-notes appends to existing notes (separated by a blank line), so prior
    # context is never silently lost.
    tasks.run("add", "t", "--notes", "first")
    capsys.readouterr()
    tid = tasks.by_title("t")["id"]
    tasks.run("update", tid, "--append-notes", "second")
    out = json.loads(capsys.readouterr().out)
    assert out["notes"] == "first\n\nsecond"


def test_update_notes_overwrite_replaces(tasks, capsys):
    # --replace-all-notes is the explicit (dangerous) opt-in to discard existing notes.
    tasks.run("add", "t", "--notes", "first")
    capsys.readouterr()
    tid = tasks.by_title("t")["id"]
    tasks.run("update", tid, "--replace-all-notes", "fresh")
    out = json.loads(capsys.readouterr().out)
    assert out["notes"] == "fresh"


def test_update_notes_append_when_empty(tasks, capsys):
    # Appending onto empty notes yields just the new text (no leading separator).
    tasks.run("add", "t")
    capsys.readouterr()
    tid = tasks.by_title("t")["id"]
    tasks.run("update", tid, "--append-notes", "only")
    out = json.loads(capsys.readouterr().out)
    assert out["notes"] == "only"


@pytest.mark.parametrize(
    "options",
    [
        ["--notes", "new"],
        ["--overwrite-notes"],
        ["--append-notes", "new", "--replace-all-notes", "new"],
    ],
)
def test_update_notes_rejects_ambiguous_options(tasks, capsys, options):
    tasks.run("add", "t", "--notes", "keep")
    capsys.readouterr()
    tid = tasks.by_title("t")["id"]
    with pytest.raises(SystemExit) as exc:
        tasks.run("update", tid, *options)
    assert exc.value.code == 2
    assert tasks.by_title("t")["notes"] == "keep"


@pytest.mark.parametrize(
    "option, expected",
    [
        ("--append-notes", "keep"),
        ("--replace-all-notes", ""),
    ],
)
def test_update_notes_empty_text(tasks, capsys, option, expected):
    tasks.run("add", "t", "--notes", "keep")
    capsys.readouterr()
    tasks.run("update", tasks.by_title("t")["id"], option, "")
    assert tasks.by_title("t")["notes"] == expected


def test_update_source_url(tasks, capsys):
    tasks.run(
        "add", "t", "--source", "notion", "--source-url", "https://example.com/old"
    )
    capsys.readouterr()
    tid = tasks.by_title("t")["id"]
    tasks.run("update", tid, "--source-url", "https://example.com/new")
    out = json.loads(capsys.readouterr().out)
    assert out["source_url"] == "https://example.com/new"


def test_update_source_url_clear(tasks, capsys):
    tasks.run(
        "add", "t", "--source", "notion", "--source-url", "https://example.com/old"
    )
    capsys.readouterr()
    tid = tasks.by_title("t")["id"]
    tasks.run("update", tid, "--source-url", "")
    out = json.loads(capsys.readouterr().out)
    assert out["source_url"] is None


def test_update_source_does_not_overwrite_source_url(tasks, capsys):
    # Regression: `--source slack` was matched by argparse as an abbreviation of
    # `--source-url`, clobbering the URL with the literal string "slack".
    tasks.run(
        "add", "t", "--source", "notion", "--source-url", "https://example.com/original"
    )
    capsys.readouterr()
    tid = tasks.by_title("t")["id"]
    tasks.run("update", tid, "--source", "slack")
    out = json.loads(capsys.readouterr().out)
    assert out["source"] == "slack"
    assert out["source_url"] == "https://example.com/original"


def test_update_source_and_source_url_independently(tasks, capsys):
    # Both --source and --source-url can be updated in one call without interference.
    tasks.run(
        "add", "t", "--source", "notion", "--source-url", "https://example.com/old"
    )
    capsys.readouterr()
    tid = tasks.by_title("t")["id"]
    tasks.run(
        "update", tid, "--source", "slack", "--source-url", "https://example.com/new"
    )
    out = json.loads(capsys.readouterr().out)
    assert out["source"] == "slack"
    assert out["source_url"] == "https://example.com/new"


# ---------- list variants ----------


def test_list_all_includes_done(tasks, capsys):
    tasks.run("add", "live")
    tasks.run("add", "gone")
    capsys.readouterr()
    gid = tasks.by_title("gone")["id"]
    tasks.run("update", gid, "--status", "done")
    capsys.readouterr()
    tasks.run("list")
    open_only = json.loads(capsys.readouterr().out)
    assert {t["title"] for t in open_only["tasks"]} == {"live"}
    tasks.run("list", "--all")
    everything = json.loads(capsys.readouterr().out)
    assert {t["title"] for t in everything["tasks"]} == {"live", "gone"}


def test_list_status_filter(tasks, capsys):
    tasks.run("add", "a")
    tasks.run("add", "b")
    capsys.readouterr()
    bid = tasks.by_title("b")["id"]
    tasks.run("update", bid, "--status", "done")
    capsys.readouterr()
    tasks.run("list", "--status", "done")
    out = json.loads(capsys.readouterr().out)
    assert [t["title"] for t in out["tasks"]] == ["b"]


def test_list_source_filter(tasks, capsys):
    tasks.run(
        "add",
        "gh",
        "--source",
        "github",
        "--source-url",
        "https://github.com/o/r/pull/1",
    )
    tasks.run("add", "loc")
    capsys.readouterr()
    tasks.run("list", "--source", "github")
    out = json.loads(capsys.readouterr().out)
    assert [t["title"] for t in out["tasks"]] == ["gh"]


def test_list_completed_on_filter(tasks, capsys, monkeypatch):
    monkeypatch.setattr(tasks.module, "now_iso", lambda: "2026-06-08T12:00:00")
    tasks.run("add", "done-today")
    capsys.readouterr()
    tid = tasks.by_title("done-today")["id"]
    tasks.run("update", tid, "--status", "done")
    capsys.readouterr()
    tasks.run("list", "--status", "done", "--completed-on", "2026-06-08")
    out = json.loads(capsys.readouterr().out)
    assert [t["title"] for t in out["tasks"]] == ["done-today"]


def test_list_format_hint_warns(tasks, capsys):
    tasks.run("add", "a")
    capsys.readouterr()
    tasks.run("list", "--format", "table")
    out = json.loads(capsys.readouterr().out)
    assert "_warning" in out


# ---------- meta ----------


def test_meta_set_get_string(tasks, capsys):
    tasks.run("meta", "set", "notion_tasks_db", "abc123")
    capsys.readouterr()
    tasks.run("meta", "get", "notion_tasks_db")
    assert json.loads(capsys.readouterr().out.strip()) == "abc123"


def test_meta_set_parses_json(tasks, capsys):
    tasks.run("meta", "set", "target_hours_2026-06", "160")
    capsys.readouterr()
    tasks.run("meta", "get", "target_hours_2026-06")
    assert json.loads(capsys.readouterr().out.strip()) == 160


def test_meta_set_parses_array(tasks, capsys):
    tasks.run("meta", "set", "holidays_2026-06", '["2026-06-01"]')
    capsys.readouterr()
    assert tasks.store()["meta"]["holidays_2026-06"] == ["2026-06-01"]


def test_meta_get_all(tasks, capsys):
    tasks.run("meta", "set", "k", "v")
    capsys.readouterr()
    tasks.run("meta", "get")
    out = json.loads(capsys.readouterr().out)
    assert out["k"] == "v"


def test_meta_unset(tasks, capsys):
    tasks.run("meta", "set", "k", "v")
    capsys.readouterr()
    tasks.run("meta", "unset", "k")
    capsys.readouterr()
    assert "k" not in tasks.store()["meta"]


# ---------- task-to-task dependency (blocked_by=task_id / --blocks / --unblocks) ----------
#
# Tasks can block each other without a GitHub URL.  Two directions:
#   B-side: tasks update B --blocked-by <A_id>   → B waits for A
#   A-side: tasks update A --blocks <B_id>        → A declares it blocks B
#
# When A reaches done or cancelled the script auto-opens every dependent task.
# `list --resolve-blocked` also detects done/cancelled blockers and opens them.


def test_is_task_id_helper(tasks):
    m = tasks.module
    assert m._is_task_id("ab06e0e8") is True
    assert m._is_task_id("ABCDEF12") is False  # uppercase not accepted
    assert m._is_task_id("ab06e0e") is False  # 7 chars
    assert m._is_task_id("ab06e0e88") is False  # 9 chars
    assert m._is_task_id("https://github.com/o/r/pull/1") is False
    assert m._is_task_id("") is False
    assert m._is_task_id(None) is False


def test_blocked_by_task_id_sets_pending(tasks, capsys):
    tasks.run("add", "A")
    tasks.run("add", "B")
    capsys.readouterr()
    aid = tasks.by_title("A")["id"]
    bid = tasks.by_title("B")["id"]
    tasks.run("update", bid, "--blocked-by", aid)
    capsys.readouterr()
    b = tasks.by_title("B")
    assert b["status"] == "pending"
    assert b["blocked_by"] == aid


def test_resolve_blocked_by_task_id_done(tasks, capsys):
    tasks.run("add", "A")
    tasks.run("add", "B")
    capsys.readouterr()
    aid = tasks.by_title("A")["id"]
    bid = tasks.by_title("B")["id"]
    tasks.run("update", bid, "--blocked-by", aid)
    capsys.readouterr()
    # Mark A as done directly in the store to test _resolve_blocked independently
    # (bypassing cmd_update's auto-unblock so B stays pending until list runs).
    data = tasks.store()
    for t in data["tasks"]:
        if t["id"] == aid:
            t["status"] = "done"
    tasks.store_path.write_text(json.dumps(data))
    tasks.run("list", "--resolve-blocked")
    out = json.loads(capsys.readouterr().out)
    assert tasks.by_title("B")["status"] == "open"
    assert any(u["id"] == bid for u in out.get("_unblocked", []))


def test_resolve_blocked_by_task_id_not_done_stays_pending(tasks, capsys):
    tasks.run("add", "A")
    tasks.run("add", "B")
    capsys.readouterr()
    aid = tasks.by_title("A")["id"]
    bid = tasks.by_title("B")["id"]
    tasks.run("update", bid, "--blocked-by", aid)
    capsys.readouterr()
    tasks.run("list", "--resolve-blocked")
    capsys.readouterr()
    assert tasks.by_title("B")["status"] == "pending"


def test_resolve_blocked_by_task_id_missing_stays_pending(tasks, capsys):
    tasks.run("add", "B")
    capsys.readouterr()
    bid = tasks.by_title("B")["id"]
    tasks.run("update", bid, "--blocked-by", "deadbeef")
    capsys.readouterr()
    tasks.run("list", "--resolve-blocked")
    capsys.readouterr()
    assert tasks.by_title("B")["status"] == "pending"


def test_update_done_auto_unblocks_blocked_by_task_id(tasks, capsys):
    tasks.run("add", "A")
    tasks.run("add", "B")
    capsys.readouterr()
    aid = tasks.by_title("A")["id"]
    bid = tasks.by_title("B")["id"]
    tasks.run("update", bid, "--blocked-by", aid)
    capsys.readouterr()
    tasks.run("update", aid, "--status", "done")
    out = json.loads(capsys.readouterr().out)
    assert tasks.by_title("B")["status"] == "open"
    assert any(u["id"] == bid for u in out.get("_auto_unblocked", []))


def test_update_cancelled_auto_unblocks_blocked_by_task_id(tasks, capsys):
    tasks.run("add", "A")
    tasks.run("add", "B")
    capsys.readouterr()
    aid = tasks.by_title("A")["id"]
    bid = tasks.by_title("B")["id"]
    tasks.run("update", bid, "--blocked-by", aid)
    capsys.readouterr()
    tasks.run("update", aid, "--status", "cancelled")
    out = json.loads(capsys.readouterr().out)
    assert tasks.by_title("B")["status"] == "open"
    assert any(u["id"] == bid for u in out.get("_auto_unblocked", []))


def test_blocks_flag_makes_target_pending(tasks, capsys):
    tasks.run("add", "A")
    tasks.run("add", "B")
    capsys.readouterr()
    aid = tasks.by_title("A")["id"]
    bid = tasks.by_title("B")["id"]
    tasks.run("update", aid, "--blocks", bid)
    capsys.readouterr()
    a = tasks.by_title("A")
    b = tasks.by_title("B")
    assert bid in (a.get("blocks") or [])
    assert b["status"] == "pending"
    assert b["blocked_by"] == aid


def test_blocks_flag_done_auto_unblocks_via_blocks_list(tasks, capsys):
    tasks.run("add", "A")
    tasks.run("add", "B")
    capsys.readouterr()
    aid = tasks.by_title("A")["id"]
    bid = tasks.by_title("B")["id"]
    tasks.run("update", aid, "--blocks", bid)
    capsys.readouterr()
    tasks.run("update", aid, "--status", "done")
    out = json.loads(capsys.readouterr().out)
    assert tasks.by_title("B")["status"] == "open"
    assert any(u["id"] == bid for u in out.get("_auto_unblocked", []))


def test_blocks_flag_multiple_targets(tasks, capsys):
    tasks.run("add", "A")
    tasks.run("add", "B")
    tasks.run("add", "C")
    capsys.readouterr()
    aid = tasks.by_title("A")["id"]
    bid = tasks.by_title("B")["id"]
    cid = tasks.by_title("C")["id"]
    tasks.run("update", aid, "--blocks", bid)
    tasks.run("update", aid, "--blocks", cid)
    capsys.readouterr()
    tasks.run("update", aid, "--status", "done")
    out = json.loads(capsys.readouterr().out)
    assert tasks.by_title("B")["status"] == "open"
    assert tasks.by_title("C")["status"] == "open"
    unblocked_ids = {u["id"] for u in out.get("_auto_unblocked", [])}
    assert {bid, cid} == unblocked_ids


def test_unblocks_flag_clears_dependency(tasks, capsys):
    tasks.run("add", "A")
    tasks.run("add", "B")
    capsys.readouterr()
    aid = tasks.by_title("A")["id"]
    bid = tasks.by_title("B")["id"]
    tasks.run("update", aid, "--blocks", bid)
    capsys.readouterr()
    tasks.run("update", aid, "--unblocks", bid)
    capsys.readouterr()
    a = tasks.by_title("A")
    b = tasks.by_title("B")
    assert bid not in (a.get("blocks") or [])
    assert b["status"] == "open"
    assert b.get("blocked_by") is None


def test_blocks_on_add(tasks, capsys):
    tasks.run("add", "B")
    capsys.readouterr()
    bid = tasks.by_title("B")["id"]
    tasks.run("add", "A", "--blocks", bid)
    capsys.readouterr()
    a = tasks.by_title("A")
    b = tasks.by_title("B")
    assert bid in (a.get("blocks") or [])
    assert b["status"] == "pending"
    assert b["blocked_by"] == a["id"]


def test_blocks_flag_idempotent(tasks, capsys):
    tasks.run("add", "A")
    tasks.run("add", "B")
    capsys.readouterr()
    aid = tasks.by_title("A")["id"]
    bid = tasks.by_title("B")["id"]
    tasks.run("update", aid, "--blocks", bid)
    tasks.run("update", aid, "--blocks", bid)  # second call is a no-op
    capsys.readouterr()
    a = tasks.by_title("A")
    assert (a.get("blocks") or []).count(bid) == 1  # not duplicated


def test_auto_unblock_no_output_when_none(tasks, capsys):
    tasks.run("add", "solo")
    capsys.readouterr()
    sid = tasks.by_title("solo")["id"]
    tasks.run("update", sid, "--status", "done")
    out = json.loads(capsys.readouterr().out)
    assert "_auto_unblocked" not in out


def test_blocked_by_task_id_cancel_clears_blocked_by(tasks, capsys):
    # After auto-unblock the blocked_by field on B should be cleared.
    tasks.run("add", "A")
    tasks.run("add", "B")
    capsys.readouterr()
    aid = tasks.by_title("A")["id"]
    bid = tasks.by_title("B")["id"]
    tasks.run("update", bid, "--blocked-by", aid)
    tasks.run("update", aid, "--status", "cancelled")
    capsys.readouterr()
    b = tasks.by_title("B")
    assert b["status"] == "open"
    assert b.get("blocked_by") is None


# ---------- add: title なし（argparse 必須引数） ----------


def test_add_without_title_exits(tasks):
    with pytest.raises(SystemExit):
        tasks.run("add")


# ---------- list: 空ストア ----------


def test_list_empty_store_returns_empty_tasks(tasks, capsys):
    tasks.run("list")
    out = json.loads(capsys.readouterr().out)
    assert out["tasks"] == []


def test_list_all_empty_store_returns_empty_tasks(tasks, capsys):
    tasks.run("list", "--all")
    out = json.loads(capsys.readouterr().out)
    assert out["tasks"] == []


# ---------- update: --source に無効値で SystemExit ----------


def test_update_source_invalid_value_exits(tasks, capsys):
    tasks.run("add", "t")
    capsys.readouterr()
    tid = tasks.by_title("t")["id"]
    with pytest.raises(SystemExit):
        tasks.run("update", tid, "--source", "invalid_source")


# ---------- meta: 存在しないキーの get / unset ----------


def test_meta_get_missing_key_returns_null(tasks, capsys):
    tasks.run("meta", "get", "no_such_key")
    out = json.loads(capsys.readouterr().out)
    assert out is None


def test_meta_unset_missing_key_is_silent_ok(tasks, capsys):
    # unset on a non-existent key silently succeeds (no SystemExit, no error)
    tasks.run("meta", "unset", "no_such_key")
    assert capsys.readouterr().out.strip() == "ok"


# ---------- add: --source-url が正しく保存される ----------


def test_add_with_source_url(tasks, capsys):
    tasks.run(
        "add",
        "linked",
        "--source",
        "notion",
        "--source-url",
        "https://notion.so/abc123",
    )
    capsys.readouterr()
    t = tasks.by_title("linked")
    assert t["source"] == "notion"
    assert t["source_url"] == "https://notion.so/abc123"


def test_add_without_source_url_defaults_to_none(tasks, capsys):
    tasks.run("add", "plain")
    capsys.readouterr()
    t = tasks.by_title("plain")
    assert t["source_url"] is None


# ---------- get: 正常系の対として、存在するタスクの全フィールドが揃うか ----------


def test_get_task_has_required_fields(tasks, capsys):
    tasks.run(
        "add",
        "full",
        "--from",
        "others",
        "--due",
        "2026-12-31",
        "--source",
        "notion",
        "--source-url",
        "https://notion.so/x",
        "--notes",
        "some note",
    )
    capsys.readouterr()
    tid = tasks.by_title("full")["id"]
    tasks.run("get", tid)
    out = json.loads(capsys.readouterr().out)
    for field in (
        "id",
        "title",
        "from",
        "due",
        "status",
        "source",
        "source_url",
        "notes",
        "created_at",
        "updated_at",
        "queue_pos",
        "tags",
    ):
        assert field in out, f"missing field: {field}"


# ---------- snooze (date-triggered pending) ----------
#
# snooze は「この日まで脇に置く」操作。status=pending + snooze_until=YYYY-MM-DD を
# セットし、list 既定（open のみ）から隠す。snooze_until <= today になった list で
# 自動的に open に戻り、_snooze_expired に載って報告される。
# 誰か/何かを待つ blocked_by 由来の pending とは別軸。7日 stale-sweep は
# snooze_until を持つタスクをスキップする（自分で寝かせたものを勝手に起こさない）。


def test_snooze_sets_pending_with_snooze_until(tasks, capsys):
    tasks.run("add", "later")
    tid = tasks.by_title("later")["id"]
    capsys.readouterr()
    tasks.run("snooze", tid, "--until", "2026-07-06")
    t = tasks.by_title("later")
    assert t["status"] == "pending"
    assert t["snooze_until"] == "2026-07-06"


def test_snoozed_task_hidden_from_default_list(tasks, capsys, monkeypatch):
    # today を snooze 期限より前に凍結する。凍結しないと実行日が 07-06 以降のとき
    # snooze が切れて list に現れ、テストが実行日依存で落ちる。
    monkeypatch.setattr(tasks.module, "today_str", lambda: "2026-07-05")
    tasks.run("add", "later")
    tid = tasks.by_title("later")["id"]
    tasks.run("snooze", tid, "--until", "2026-07-06")
    capsys.readouterr()
    tasks.run("list")
    out = json.loads(capsys.readouterr().out)
    assert all(t["title"] != "later" for t in out["tasks"])


def test_snooze_expires_on_list_when_date_reached(tasks, capsys, monkeypatch):
    monkeypatch.setattr(tasks.module, "today_str", lambda: "2026-07-06")
    tasks.run("add", "wake me")
    tid = tasks.by_title("wake me")["id"]
    tasks.run("snooze", tid, "--until", "2026-07-06")
    capsys.readouterr()
    tasks.run("list")
    out = json.loads(capsys.readouterr().out)
    assert tasks.by_title("wake me")["status"] == "open"
    assert tasks.by_title("wake me")["snooze_until"] is None
    assert any(s["title"] == "wake me" for s in out.get("_snooze_expired", []))


def test_snooze_expires_when_date_passed(tasks, capsys, monkeypatch):
    # today past the snooze_until date also expires.
    monkeypatch.setattr(tasks.module, "today_str", lambda: "2026-07-10")
    tasks.run("add", "overdue snooze")
    tid = tasks.by_title("overdue snooze")["id"]
    tasks.run("snooze", tid, "--until", "2026-07-06")
    capsys.readouterr()
    tasks.run("list")
    out = json.loads(capsys.readouterr().out)
    assert tasks.by_title("overdue snooze")["status"] == "open"
    assert any(s["title"] == "overdue snooze" for s in out.get("_snooze_expired", []))


def test_snooze_stays_pending_before_date(tasks, capsys, monkeypatch):
    monkeypatch.setattr(tasks.module, "today_str", lambda: "2026-07-05")
    tasks.run("add", "still sleeping")
    tid = tasks.by_title("still sleeping")["id"]
    tasks.run("snooze", tid, "--until", "2026-07-06")
    capsys.readouterr()
    tasks.run("list")
    out = json.loads(capsys.readouterr().out)
    assert tasks.by_title("still sleeping")["status"] == "pending"
    assert "_snooze_expired" not in out


def test_snooze_via_add_snooze_until(tasks, capsys):
    # add で --snooze-until を渡しても snooze 状態で作れる。
    tasks.run("add", "born asleep", "--snooze-until", "2026-07-06")
    capsys.readouterr()
    t = tasks.by_title("born asleep")
    assert t["status"] == "pending"
    assert t["snooze_until"] == "2026-07-06"


def test_update_snooze_until(tasks, capsys):
    # update でも snooze_until をセットでき、pending に倒れる。
    tasks.run("add", "to snooze")
    tid = tasks.by_title("to snooze")["id"]
    capsys.readouterr()
    tasks.run("update", tid, "--snooze-until", "2026-07-06")
    t = tasks.by_title("to snooze")
    assert t["status"] == "pending"
    assert t["snooze_until"] == "2026-07-06"


def test_update_clear_snooze_until_with_empty_string(tasks, capsys):
    # 空文字で snooze を解除して open に戻す。
    tasks.run("add", "wake early", "--snooze-until", "2026-07-06")
    tid = tasks.by_title("wake early")["id"]
    capsys.readouterr()
    tasks.run("update", tid, "--snooze-until", "")
    t = tasks.by_title("wake early")
    assert t["snooze_until"] is None
    assert t["status"] == "open"


def test_snooze_not_swept_by_stale_pending(tasks, capsys, monkeypatch):
    # snooze_until を持つ pending は、7日 stale-sweep の対象外。
    # updated_at を 30 日前にしても、snooze_until が未来なら起こされない。
    monkeypatch.setattr(tasks.module, "today_str", lambda: "2026-07-05")
    tasks.run("add", "long snooze", "--snooze-until", "2026-07-06")
    data = tasks.store()
    old = (_datetime.datetime.now() - _datetime.timedelta(days=30)).isoformat(
        timespec="seconds"
    )
    for t in data["tasks"]:
        if t["title"] == "long snooze":
            t["updated_at"] = old
    tasks.store_path.write_text(json.dumps(data))
    capsys.readouterr()
    tasks.run("list")
    out = json.loads(capsys.readouterr().out)
    assert tasks.by_title("long snooze")["status"] == "pending"
    assert "_stale_unblocked" not in out


def test_snooze_unknown_id_exits(tasks):
    with pytest.raises(SystemExit):
        tasks.run("snooze", "deadbeef", "--until", "2026-07-06")


def test_snoozed_task_shown_with_status_pending_filter(tasks, capsys, monkeypatch):
    # snooze 中でも --status pending で明示すれば list に出る（隠れるのは既定だけ）。
    monkeypatch.setattr(tasks.module, "today_str", lambda: "2026-07-05")
    tasks.run("add", "hidden but findable", "--snooze-until", "2026-07-06")
    capsys.readouterr()
    tasks.run("list", "--status", "pending")
    out = json.loads(capsys.readouterr().out)
    assert any(t["title"] == "hidden but findable" for t in out["tasks"])


# ---------- migration: kind(must/will) → from(others/me) ----------


def _inject_old_tasks(tasks, capsys, tasks_data):
    """kind フィールドを持つ旧形式のタスクをストアに直接書き込む。"""
    tasks.run("add", "_init")
    capsys.readouterr()
    data = tasks.store()
    data["tasks"] = tasks_data
    tasks.store_path.write_text(json.dumps(data))


def test_migrate_must_to_others(tasks, capsys):
    """kind=must のタスクが from=others に変換される。"""
    _inject_old_tasks(
        tasks,
        capsys,
        [
            {
                "id": "aabb1122",
                "title": "external task",
                "kind": "must",
                "status": "open",
                "queue_pos": 10,
                "due": None,
                "tags": [],
                "source": "local",
                "source_url": None,
                "blocked_by": None,
                "blocks": [],
                "snooze_until": None,
                "notes": "",
                "created_at": "2026-06-01T09:00:00",
                "updated_at": "2026-06-01T09:00:00",
                "completed_at": None,
            },
        ],
    )
    tasks.run("migrate")
    t = tasks.by_title("external task")
    assert "from" in t
    assert t["from"] == "others"
    assert "kind" not in t


def test_migrate_will_to_me(tasks, capsys):
    """kind=will のタスクが from=me に変換される。"""
    _inject_old_tasks(
        tasks,
        capsys,
        [
            {
                "id": "ccdd3344",
                "title": "self task",
                "kind": "will",
                "status": "open",
                "queue_pos": 10,
                "due": None,
                "tags": [],
                "source": "local",
                "source_url": None,
                "blocked_by": None,
                "blocks": [],
                "snooze_until": None,
                "notes": "",
                "created_at": "2026-06-01T09:00:00",
                "updated_at": "2026-06-01T09:00:00",
                "completed_at": None,
            },
        ],
    )
    tasks.run("migrate")
    t = tasks.by_title("self task")
    assert t["from"] == "me"
    assert "kind" not in t


def test_migrate_multiple_tasks(tasks, capsys):
    """複数タスクが混在していても全件変換される。"""
    _inject_old_tasks(
        tasks,
        capsys,
        [
            {
                "id": "aa000001",
                "title": "A",
                "kind": "must",
                "status": "open",
                "queue_pos": 10,
                "due": None,
                "tags": [],
                "source": "local",
                "source_url": None,
                "blocked_by": None,
                "blocks": [],
                "snooze_until": None,
                "notes": "",
                "created_at": "2026-06-01T09:00:00",
                "updated_at": "2026-06-01T09:00:00",
                "completed_at": None,
            },
            {
                "id": "bb000002",
                "title": "B",
                "kind": "will",
                "status": "done",
                "queue_pos": 20,
                "due": None,
                "tags": [],
                "source": "github",
                "source_url": "https://github.com/o/r/pull/1",
                "blocked_by": None,
                "blocks": [],
                "snooze_until": None,
                "notes": "",
                "created_at": "2026-06-02T09:00:00",
                "updated_at": "2026-06-02T09:00:00",
                "completed_at": "2026-06-03T09:00:00",
            },
            {
                "id": "cc000003",
                "title": "C",
                "kind": "must",
                "status": "cancelled",
                "queue_pos": 30,
                "due": "2026-07-01",
                "tags": ["foo"],
                "source": "notion",
                "source_url": None,
                "blocked_by": None,
                "blocks": [],
                "snooze_until": None,
                "notes": "some note",
                "created_at": "2026-06-03T09:00:00",
                "updated_at": "2026-06-03T09:00:00",
                "completed_at": None,
            },
        ],
    )
    tasks.run("migrate")
    data = tasks.store()
    froms = {t["title"]: t["from"] for t in data["tasks"]}
    assert froms == {"A": "others", "B": "me", "C": "others"}
    assert all("kind" not in t for t in data["tasks"])


def test_migrate_preserves_other_fields(tasks, capsys):
    """from 以外のフィールドはそのまま保持される。"""
    _inject_old_tasks(
        tasks,
        capsys,
        [
            {
                "id": "dd000004",
                "title": "check fields",
                "kind": "must",
                "status": "pending",
                "queue_pos": 55,
                "due": "2026-08-01",
                "tags": ["important"],
                "source": "slack",
                "source_url": "https://chat.example.invalid/archives/C123/p456",
                "blocked_by": "https://github.com/o/r/pull/2",
                "blocks": [],
                "snooze_until": None,
                "notes": "keep this note",
                "created_at": "2026-06-10T10:00:00",
                "updated_at": "2026-06-20T10:00:00",
                "completed_at": None,
            },
        ],
    )
    tasks.run("migrate")
    t = tasks.by_title("check fields")
    assert t["status"] == "pending"
    assert t["queue_pos"] == 55
    assert t["due"] == "2026-08-01"
    assert t["tags"] == ["important"]
    assert t["notes"] == "keep this note"
    assert t["blocked_by"] == "https://github.com/o/r/pull/2"


def test_migrate_idempotent(tasks, capsys):
    """すでに from フィールドがあるストアに対して実行しても壊れない。"""
    _inject_old_tasks(
        tasks,
        capsys,
        [
            {
                "id": "ee000005",
                "title": "already done",
                "from": "others",
                "status": "open",
                "queue_pos": 10,
                "due": None,
                "tags": [],
                "source": "local",
                "source_url": None,
                "blocked_by": None,
                "blocks": [],
                "snooze_until": None,
                "notes": "",
                "created_at": "2026-06-01T09:00:00",
                "updated_at": "2026-06-01T09:00:00",
                "completed_at": None,
            },
        ],
    )
    tasks.run("migrate")
    t = tasks.by_title("already done")
    assert t["from"] == "others"
    assert "kind" not in t


def test_migrate_creates_backup(tasks, capsys):
    """マイグレーション前に .bak ファイルを作成する。"""
    _inject_old_tasks(
        tasks,
        capsys,
        [
            {
                "id": "ff000006",
                "title": "backup test",
                "kind": "will",
                "status": "open",
                "queue_pos": 10,
                "due": None,
                "tags": [],
                "source": "local",
                "source_url": None,
                "blocked_by": None,
                "blocks": [],
                "snooze_until": None,
                "notes": "",
                "created_at": "2026-06-01T09:00:00",
                "updated_at": "2026-06-01T09:00:00",
                "completed_at": None,
            },
        ],
    )
    original_text = tasks.store_path.read_text()
    tasks.run("migrate")
    bak = tasks.store_path.with_suffix(".json.bak")
    assert bak.exists()
    assert bak.read_text() == original_text


def test_migrate_dry_run_does_not_write(tasks, capsys):
    """--dry-run では実ファイルを変更しない。"""
    _inject_old_tasks(
        tasks,
        capsys,
        [
            {
                "id": "gg000007",
                "title": "dry run test",
                "kind": "must",
                "status": "open",
                "queue_pos": 10,
                "due": None,
                "tags": [],
                "source": "local",
                "source_url": None,
                "blocked_by": None,
                "blocks": [],
                "snooze_until": None,
                "notes": "",
                "created_at": "2026-06-01T09:00:00",
                "updated_at": "2026-06-01T09:00:00",
                "completed_at": None,
            },
        ],
    )
    before = tasks.store_path.read_text()
    tasks.run("migrate", "--dry-run")
    capsys.readouterr()
    assert tasks.store_path.read_text() == before
    bak = tasks.store_path.with_suffix(".json.bak")
    assert not bak.exists()


def test_migrate_reports_count(tasks, capsys):
    """変換件数が出力に含まれる。"""
    _inject_old_tasks(
        tasks,
        capsys,
        [
            {
                "id": "hh000008",
                "title": "count test 1",
                "kind": "must",
                "status": "open",
                "queue_pos": 10,
                "due": None,
                "tags": [],
                "source": "local",
                "source_url": None,
                "blocked_by": None,
                "blocks": [],
                "snooze_until": None,
                "notes": "",
                "created_at": "2026-06-01T09:00:00",
                "updated_at": "2026-06-01T09:00:00",
                "completed_at": None,
            },
            {
                "id": "ii000009",
                "title": "count test 2",
                "kind": "will",
                "status": "open",
                "queue_pos": 20,
                "due": None,
                "tags": [],
                "source": "local",
                "source_url": None,
                "blocked_by": None,
                "blocks": [],
                "snooze_until": None,
                "notes": "",
                "created_at": "2026-06-01T09:00:00",
                "updated_at": "2026-06-01T09:00:00",
                "completed_at": None,
            },
        ],
    )
    tasks.run("migrate")
    out = json.loads(capsys.readouterr().out)
    assert out["migrated"] == 2


# ---------- in-progress status ----------


def test_update_to_in_progress(tasks, capsys):
    tasks.run("add", "x")
    capsys.readouterr()
    tid = tasks.by_title("x")["id"]
    tasks.run("update", tid, "--status", "in-progress")
    capsys.readouterr()
    assert tasks.by_title("x")["status"] == "in-progress"


def test_list_shows_in_progress_by_default(tasks, capsys):
    tasks.run("add", "active")
    capsys.readouterr()
    tid = tasks.by_title("active")["id"]
    tasks.run("update", tid, "--status", "in-progress")
    capsys.readouterr()
    tasks.run("list")
    out = json.loads(capsys.readouterr().out)
    assert {t["title"] for t in out["tasks"]} == {"active"}


def test_in_progress_sorts_before_open(tasks, capsys):
    # in-progress bubbles to the front even with a larger queue_pos than an open task.
    tasks.run("add", "open-task", "--queue-pos", "10")
    tasks.run("add", "wip-task", "--queue-pos", "999")
    capsys.readouterr()
    wid = tasks.by_title("wip-task")["id"]
    tasks.run("update", wid, "--status", "in-progress")
    capsys.readouterr()
    tasks.run("list")
    out = json.loads(capsys.readouterr().out)
    assert out["tasks"][0]["title"] == "wip-task"


def test_in_progress_over_limit_signal_and_warning(tasks, capsys):
    # Marking a 6th task in-progress (limit is 5) puts _in_progress_over on the
    # update result and prints a warning to stderr.
    for i in range(6):
        tasks.run("add", f"t{i}")
    capsys.readouterr()
    ids = [tasks.by_title(f"t{i}")["id"] for i in range(6)]
    for tid in ids[:5]:
        tasks.run("update", tid, "--status", "in-progress")
    capsys.readouterr()
    tasks.run("update", ids[5], "--status", "in-progress")
    cap = capsys.readouterr()
    out = json.loads(cap.out)
    assert out["_in_progress_over"]["count"] == 6
    assert out["_in_progress_over"]["limit"] == 5
    assert "6" in cap.err


def test_in_progress_at_limit_no_signal(tasks, capsys):
    # Exactly 5 in-progress is at the limit, not over it: no signal, no warning.
    for i in range(5):
        tasks.run("add", f"t{i}")
    capsys.readouterr()
    ids = [tasks.by_title(f"t{i}")["id"] for i in range(5)]
    for tid in ids[:4]:
        tasks.run("update", tid, "--status", "in-progress")
    capsys.readouterr()
    tasks.run("update", ids[4], "--status", "in-progress")
    cap = capsys.readouterr()
    out = json.loads(cap.out)
    assert "_in_progress_over" not in out
    assert cap.err == ""


def _mark_n_in_progress(tasks, n):
    for i in range(n):
        tasks.run("add", f"t{i}")
    for i in range(n):
        tid = tasks.by_title(f"t{i}")["id"]
        tasks.run("update", tid, "--status", "in-progress")


def test_list_in_progress_over_limit_signal(tasks, capsys):
    # list surfaces _in_progress_over when in-progress count exceeds the limit.
    _mark_n_in_progress(tasks, 6)
    capsys.readouterr()
    tasks.run("list")
    out = json.loads(capsys.readouterr().out)
    assert out["_in_progress_over"]["count"] == 6
    assert out["_in_progress_over"]["limit"] == 5


def test_list_no_in_progress_over_when_under_limit(tasks, capsys):
    _mark_n_in_progress(tasks, 3)
    capsys.readouterr()
    tasks.run("list")
    out = json.loads(capsys.readouterr().out)
    assert "_in_progress_over" not in out
