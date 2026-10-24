"""`tasks` CLIの日次記録とnotif-keysを検証する。
`tasks`フィクスチャはconftest.pyで定義する。
"""

import json

# ---------- 日次記録 ----------


def test_daily_save_and_show(tasks, capsys):
    tasks.run(
        "daily",
        "save",
        "--date",
        "2026-06-08",
        "--good",
        "shipped",
        "--issues",
        "tired",
        "--completed-task-ids",
        "aaa,bbb",
    )
    capsys.readouterr()
    tasks.run("daily", "show", "--date", "2026-06-08")
    out = json.loads(capsys.readouterr().out)
    assert out["good"] == "shipped"
    assert out["completed_task_ids"] == ["aaa", "bbb"]


def test_daily_save_updates_specified_field_same_date(tasks, capsys):
    tasks.run("daily", "save", "--date", "2026-06-08", "--good", "first")
    tasks.run("daily", "save", "--date", "2026-06-08", "--good", "second")
    capsys.readouterr()
    tasks.run("daily", "show", "--date", "2026-06-08")
    out = json.loads(capsys.readouterr().out)
    assert out["good"] == "second"
    assert len(tasks.store()["daily_logs"]) == 1


def test_daily_save_merges_unspecified_fields_same_date(tasks, capsys):
    # /todo の途中で issues を記録し、夕方の furikaeri が good を保存しても
    # 互いの記録が消えないこと（未指定フィールドは保持される）。
    tasks.run("daily", "save", "--date", "2026-06-08", "--issues", "頭が痛い")
    tasks.run("daily", "save", "--date", "2026-06-08", "--good", "レビューを返せた")
    capsys.readouterr()
    tasks.run("daily", "show", "--date", "2026-06-08")
    out = json.loads(capsys.readouterr().out)
    assert out["issues"] == "頭が痛い"
    assert out["good"] == "レビューを返せた"
    assert len(tasks.store()["daily_logs"]) == 1


def test_daily_save_empty_string_clears_field_same_date(tasks, capsys):
    # 空文字を明示したフィールドは更新（クリア）される。None（未指定）との区別。
    tasks.run("daily", "save", "--date", "2026-06-08", "--good", "first")
    tasks.run("daily", "save", "--date", "2026-06-08", "--good", "")
    capsys.readouterr()
    tasks.run("daily", "show", "--date", "2026-06-08")
    out = json.loads(capsys.readouterr().out)
    assert out["good"] == ""


def test_daily_save_merges_completed_task_ids_as_union(tasks, capsys):
    tasks.run(
        "daily", "save", "--date", "2026-06-08", "--completed-task-ids", "aaa,bbb"
    )
    tasks.run(
        "daily", "save", "--date", "2026-06-08", "--completed-task-ids", "bbb,ccc"
    )
    capsys.readouterr()
    tasks.run("daily", "show", "--date", "2026-06-08")
    out = json.loads(capsys.readouterr().out)
    assert out["completed_task_ids"] == ["aaa", "bbb", "ccc"]


def test_daily_save_preserves_created_at_on_merge(tasks, capsys):
    tasks.run("daily", "save", "--date", "2026-06-08", "--good", "first")
    first_created = tasks.store()["daily_logs"][0]["created_at"]
    tasks.run("daily", "save", "--date", "2026-06-08", "--issues", "later")
    assert tasks.store()["daily_logs"][0]["created_at"] == first_created


def test_daily_show_missing_returns_null(tasks, capsys):
    tasks.run("daily", "show", "--date", "2099-01-01")
    assert json.loads(capsys.readouterr().out) is None


def test_daily_list_with_month_and_limit(tasks, capsys):
    tasks.run("daily", "save", "--date", "2026-06-01", "--good", "a")
    tasks.run("daily", "save", "--date", "2026-06-02", "--good", "b")
    tasks.run("daily", "save", "--date", "2026-07-01", "--good", "c")
    capsys.readouterr()
    tasks.run("daily", "list", "--month", "2026-06", "--limit", "1")
    out = json.loads(capsys.readouterr().out)
    # 日付の降順で6月に絞り、1件だけ取得すると2026-06-02になる。
    assert len(out) == 1
    assert out[0]["date"] == "2026-06-02"


# ---------- 通知キー ----------


def test_notif_keys(tasks, capsys):
    tasks.run(
        "add",
        "gh-done",
        "--source",
        "github",
        "--source-url",
        "https://github.com/example/project/pull/2000",
    )
    capsys.readouterr()
    tid = tasks.by_title("gh-done")["id"]
    tasks.run("update", tid, "--status", "done")
    capsys.readouterr()
    tasks.run("notif-keys")
    out = json.loads(capsys.readouterr().out)
    assert "example/project#2000" in out["keys"]


def test_notif_keys_skips_open_and_non_github(tasks, capsys):
    tasks.run(
        "add",
        "still-open",
        "--source",
        "github",
        "--source-url",
        "https://github.com/o/r/pull/1",
    )
    tasks.run("add", "local-done")
    capsys.readouterr()
    lid = tasks.by_title("local-done")["id"]
    tasks.run("update", lid, "--status", "done")
    capsys.readouterr()
    tasks.run("notif-keys")
    out = json.loads(capsys.readouterr().out)
    assert out["keys"] == []  # openのGitHubタスクとローカルタスクをどちらも除外する。


# ---------- daily list: エントリなし ----------


def test_daily_list_empty_returns_empty_list(tasks, capsys):
    tasks.run("daily", "list")
    out = json.loads(capsys.readouterr().out)
    assert out == []


def test_daily_list_month_filter_no_match_returns_empty(tasks, capsys):
    tasks.run("daily", "save", "--date", "2026-06-01", "--good", "x")
    capsys.readouterr()
    tasks.run("daily", "list", "--month", "2099-01")
    out = json.loads(capsys.readouterr().out)
    assert out == []


# ---------- standup（朝会メモ） ----------


def test_daily_save_standup_stored(tasks, capsys):
    tasks.run(
        "daily",
        "save",
        "--date",
        "2026-07-09",
        "--standup",
        "- TASK-101: plan merge 済み、実装着手",
    )
    capsys.readouterr()
    tasks.run("daily", "show", "--date", "2026-07-09")
    out = json.loads(capsys.readouterr().out)
    assert out["standup"] == "- TASK-101: plan merge 済み、実装着手"


def test_daily_save_standup_merges_without_clobber(tasks, capsys):
    # standup と他フィールドは同一日付でマージされ、未指定側は保持される。
    tasks.run("daily", "save", "--date", "2026-07-09", "--good", "進んだ")
    tasks.run("daily", "save", "--date", "2026-07-09", "--standup", "TASK-101 実装着手")
    capsys.readouterr()
    tasks.run("daily", "show", "--date", "2026-07-09")
    out = json.loads(capsys.readouterr().out)
    assert out["good"] == "進んだ"
    assert out["standup"] == "TASK-101 実装着手"
    assert len(tasks.store()["daily_logs"]) == 1


def test_daily_save_standup_absent_in_old_entry_defaults_empty(tasks, capsys):
    # standup フィールドの無い旧エントリをマージしても KeyError にならず空で補われる。
    tasks.run("daily", "save", "--date", "2026-07-09", "--good", "x")
    store = tasks.store()
    del store["daily_logs"][0]["standup"]
    tasks.store_path.write_text(json.dumps(store))
    tasks.run("daily", "save", "--date", "2026-07-09", "--issues", "y")
    capsys.readouterr()
    tasks.run("daily", "show", "--date", "2026-07-09")
    out = json.loads(capsys.readouterr().out)
    assert out["standup"] == ""
