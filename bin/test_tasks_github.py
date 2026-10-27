"""`tasks` CLIのGitHub連携を検証する。
_gh_state / _gh_self_login / _gh_comment_resolved、待機理由の解消、
長期間更新のない待機タスクの処理、不正なJSONへの対応を対象とする。
`tasks`フィクスチャはconftest.pyで定義する。
"""

import datetime as _datetime
import json
from types import SimpleNamespace


def _fake_run(stdout="", returncode=0):
    """用意したCompletedProcess相当の結果を返すsubprocess.runの代替を作る。"""

    def run(*args, **kwargs):
        return SimpleNamespace(returncode=returncode, stdout=stdout, stderr="")

    return run


# ---------- GitHubの補助関数（子プロセスをモック化） ----------


def test_gh_notif_key_variants(tasks):
    m = tasks.module
    assert m._gh_notif_key("https://github.com/o/r/pull/12") == "o/r#12"
    assert m._gh_notif_key("https://github.com/o/r/pulls/12") == "o/r#12"
    assert m._gh_notif_key("https://github.com/o/r/issues/5") == "o/r#5"
    assert m._gh_notif_key("https://github.com/o/r/pull/12#discussion_r99") == "o/r#12"
    assert m._gh_notif_key("not a url") is None
    assert m._gh_notif_key("") is None


def test_gh_state_merged(tasks, monkeypatch):
    monkeypatch.setattr(
        "subprocess.run",
        _fake_run(stdout='{"state": "MERGED", "mergedAt": "2026-06-01T00:00:00Z"}'),
    )
    st = tasks.module._gh_state("https://github.com/o/r/pull/1")
    assert st == {"state": "MERGED", "merged": True}


def test_gh_state_open(tasks, monkeypatch):
    monkeypatch.setattr(
        "subprocess.run", _fake_run(stdout='{"state": "OPEN", "mergedAt": null}')
    )
    st = tasks.module._gh_state("https://github.com/o/r/pull/1")
    assert st == {"state": "OPEN", "merged": False}


def test_gh_state_non_github_url(tasks):
    assert tasks.module._gh_state("https://example.com/x") is None


def test_gh_state_command_fails(tasks, monkeypatch):
    monkeypatch.setattr("subprocess.run", _fake_run(returncode=1))
    assert tasks.module._gh_state("https://github.com/o/r/pull/1") is None


def test_gh_state_gh_missing(tasks, monkeypatch):
    def boom(*a, **k):
        raise FileNotFoundError

    monkeypatch.setattr("subprocess.run", boom)
    assert tasks.module._gh_state("https://github.com/o/r/pull/1") is None


def test_resolve_blocked_unblocks_merged_pr(tasks, capsys, monkeypatch):
    tasks.run("add", "blocked", "--blocked-by", "https://github.com/o/r/pull/1")
    capsys.readouterr()
    monkeypatch.setattr(
        tasks.module, "_gh_state", lambda url: {"state": "MERGED", "merged": True}
    )
    tasks.run("list", "--resolve-blocked")
    out = json.loads(capsys.readouterr().out)
    assert any(u["blocker_state"] == "MERGED" for u in out.get("_unblocked", []))
    assert tasks.by_title("blocked")["status"] == "open"


def test_resolve_blocked_keeps_open_pr_blocked(tasks, capsys, monkeypatch):
    tasks.run("add", "blocked", "--blocked-by", "https://github.com/o/r/pull/1")
    capsys.readouterr()
    monkeypatch.setattr(
        tasks.module, "_gh_state", lambda url: {"state": "OPEN", "merged": False}
    )
    tasks.run("list", "--resolve-blocked")
    capsys.readouterr()
    assert tasks.by_title("blocked")["status"] == "pending"


def test_resolve_blocked_comment_ball_returned(tasks, capsys, monkeypatch):
    url = "https://github.com/o/r/pull/1#issuecomment-555"
    tasks.run("add", "waiting", "--blocked-by", url)
    capsys.readouterr()
    monkeypatch.setattr(tasks.module, "_gh_comment_resolved", lambda u: "teammate")
    tasks.run("list", "--resolve-blocked")
    out = json.loads(capsys.readouterr().out)
    assert any(
        u["blocker_state"] == "REPLIED_BY:teammate" for u in out.get("_unblocked", [])
    )
    assert tasks.by_title("waiting")["status"] == "open"


def test_resolve_blocked_comment_still_waiting(tasks, capsys, monkeypatch):
    url = "https://github.com/o/r/pull/1#issuecomment-555"
    tasks.run("add", "waiting", "--blocked-by", url)
    capsys.readouterr()
    monkeypatch.setattr(tasks.module, "_gh_comment_resolved", lambda u: None)
    tasks.run("list", "--resolve-blocked")
    capsys.readouterr()
    assert tasks.by_title("waiting")["status"] == "pending"


def test_resolve_blocked_state_unknown_stays(tasks, capsys, monkeypatch):
    tasks.run("add", "blocked", "--blocked-by", "https://github.com/o/r/pull/1")
    capsys.readouterr()
    monkeypatch.setattr(tasks.module, "_gh_state", lambda url: None)
    tasks.run("list", "--resolve-blocked")
    capsys.readouterr()
    assert tasks.by_title("blocked")["status"] == "pending"


def test_resolve_blocked_skips_open_tasks(tasks, capsys, monkeypatch):
    # 待ち先のないopenタスクは、--resolve-blockedで変更してはならない。
    tasks.run("add", "free")
    capsys.readouterr()
    tasks.run("list", "--resolve-blocked")
    capsys.readouterr()
    assert tasks.by_title("free")["status"] == "open"


# ---------- 長期停滞したpendingの再開（すべてのlist呼び出し） ----------
#
# updated_atが1週間変わらないpendingタスクは、待ち先ではなく
# 本人側で停滞している可能性がある。listの呼び出し時にopenへ戻して
# 再表示し、停滞期間を_stale_unblockedへ記録して、
# 本人が次の行動を判断できるようにする。--resolve-blockedの指定時だけでなく、
# すべてのlist呼び出しで実行する。


def _age_pending(tasks, title, days, blocked_by="https://github.com/o/r/pull/1"):
    """既存タスクをpendingにし、updated_atを`days`日前に設定する。"""
    data = tasks.store()
    old = (_datetime.datetime.now() - _datetime.timedelta(days=days)).isoformat(
        timespec="seconds"
    )
    for t in data["tasks"]:
        if t["title"] == title:
            t["status"] = "pending"
            t["blocked_by"] = blocked_by
            t["updated_at"] = old
    tasks.store_path.write_text(json.dumps(data))


def test_stale_pending_flipped_to_open_on_plain_list(tasks, capsys):
    tasks.run("add", "stuck review", "--from", "others")
    _age_pending(tasks, "stuck review", days=8)
    capsys.readouterr()
    tasks.run("list")
    out = json.loads(capsys.readouterr().out)
    assert tasks.by_title("stuck review")["status"] == "open"
    stale = out.get("_stale_unblocked", [])
    assert any(s["title"] == "stuck review" and s["stale_days"] >= 7 for s in stale)


def test_stale_pending_recent_stays_pending(tasks, capsys):
    tasks.run("add", "fresh wait", "--from", "others")
    _age_pending(tasks, "fresh wait", days=3)
    capsys.readouterr()
    tasks.run("list")
    out = json.loads(capsys.readouterr().out)
    assert tasks.by_title("fresh wait")["status"] == "pending"
    assert "_stale_unblocked" not in out


def test_stale_pending_boundary_seven_days(tasks, capsys):
    # ちょうど7日でも停滞と判定する。秒単位の丸めを避けるため、わずかに余裕を加える。
    tasks.run("add", "borderline", "--from", "others")
    _age_pending(tasks, "borderline", days=7)
    capsys.readouterr()
    tasks.run("list")
    out = json.loads(capsys.readouterr().out)
    assert tasks.by_title("borderline")["status"] == "open"
    assert any(s["title"] == "borderline" for s in out.get("_stale_unblocked", []))


def test_stale_pending_handles_utc_z_timestamp(tasks, capsys):
    # GitHub由来のupdated_atに含まれるUTCの末尾Zを解析できることを確認する。
    tasks.run("add", "gh stuck", "--from", "others")
    data = tasks.store()
    old = _datetime.datetime.now() - _datetime.timedelta(days=10)
    for t in data["tasks"]:
        if t["title"] == "gh stuck":
            t["status"] = "pending"
            t["blocked_by"] = "https://github.com/o/r/pull/1"
            t["updated_at"] = old.strftime("%Y-%m-%dT%H:%M:%SZ")
    tasks.store_path.write_text(json.dumps(data))
    capsys.readouterr()
    tasks.run("list")
    out = json.loads(capsys.readouterr().out)
    assert tasks.by_title("gh stuck")["status"] == "open"
    assert any(s["title"] == "gh stuck" for s in out.get("_stale_unblocked", []))


def test_stale_pending_open_task_untouched(tasks, capsys):
    # 古くても既にopenのタスクは、pendingの再開処理の対象にしない。
    tasks.run("add", "old open")
    data = tasks.store()
    old = (_datetime.datetime.now() - _datetime.timedelta(days=30)).isoformat(
        timespec="seconds"
    )
    for t in data["tasks"]:
        if t["title"] == "old open":
            t["updated_at"] = old
    tasks.store_path.write_text(json.dumps(data))
    capsys.readouterr()
    tasks.run("list")
    out = json.loads(capsys.readouterr().out)
    assert "_stale_unblocked" not in out
    assert tasks.by_title("old open")["status"] == "open"


def test_stale_pending_missing_updated_at_stays_pending(tasks, capsys):
    # updated_atがなく経過時間を判断できない場合は、推測せずpendingに保つ。
    tasks.run("add", "no stamp", "--from", "others")
    data = tasks.store()
    for t in data["tasks"]:
        if t["title"] == "no stamp":
            t["status"] = "pending"
            t["blocked_by"] = "https://github.com/o/r/pull/1"
            t["updated_at"] = ""
    tasks.store_path.write_text(json.dumps(data))
    capsys.readouterr()
    tasks.run("list")
    out = json.loads(capsys.readouterr().out)
    assert "_stale_unblocked" not in out
    assert tasks.by_title("no stamp")["status"] == "pending"


# ---------- _gh_stateのJSON境界条件 ----------


def test_gh_state_bad_json(tasks, monkeypatch):
    monkeypatch.setattr("subprocess.run", _fake_run(stdout="not json"))
    assert tasks.module._gh_state("https://github.com/o/r/pull/1") is None


def test_gh_state_issue_url(tasks, monkeypatch):
    monkeypatch.setattr("subprocess.run", _fake_run(stdout='{"state": "CLOSED"}'))
    st = tasks.module._gh_state("https://github.com/o/r/issues/7")
    assert st == {"state": "CLOSED", "merged": False}


# ---------- ログイン名の取得（_gh_self_login） ----------


def test_gh_self_login_ok(tasks, monkeypatch):
    monkeypatch.setattr("subprocess.run", _fake_run(stdout="example-user\n"))
    assert tasks.module._gh_self_login() == "example-user"


def test_gh_self_login_empty(tasks, monkeypatch):
    monkeypatch.setattr("subprocess.run", _fake_run(stdout="\n"))
    assert tasks.module._gh_self_login() is None


def test_gh_self_login_fails(tasks, monkeypatch):
    monkeypatch.setattr("subprocess.run", _fake_run(returncode=1))
    assert tasks.module._gh_self_login() is None


def test_gh_self_login_gh_missing(tasks, monkeypatch):
    def boom(*a, **k):
        raise FileNotFoundError

    monkeypatch.setattr("subprocess.run", boom)
    assert tasks.module._gh_self_login() is None


# ---------- コメントへの応答判定（_gh_comment_resolved） ----------


def _comment_api_router(
    comment_created="2026-06-01T00:00:00Z",
    comment_body="@teammate please look",
    pr_author="someone",
    issue_comments=None,
    reviews=None,
    commits=None,
    review_comments=None,
    comment_raw=None,
):
    """_gh_comment_resolvedによるgh api呼び出しに、パス引数に応じて応答する
    subprocess.runの代替を返す。

    #issuecomment-<id>の本文はrepos/.../issues/comments/<id>、
    #discussion_r<id>のPRレビューコメント本文は
    repos/.../pulls/comments/<id>から取得する。両方を同じルーターで扱う。
    review_commentsでは、discussion側がIssueコメントの時系列に加えて読み込む
    PRレビューコメントのスレッドを渡す。

    issue_comments / reviews / commits / review_comments / comment_rawに
    文字列を渡すと、その取得先から不正なJSONが返る状況を再現できる。
    それ以外の値は通常どおりJSONに変換する。
    """
    issue_comments = issue_comments if issue_comments is not None else []
    reviews = reviews if reviews is not None else []
    commits = commits if commits is not None else []
    review_comments = review_comments if review_comments is not None else []

    def _dump(v):
        return v if isinstance(v, str) else json.dumps(v)

    def run(cmd, *args, **kwargs):
        # cmdは["gh", "api", "--method", "GET", <path>, ...]の形式になる。
        path = cmd[4] if len(cmd) > 4 else ""
        # _gh_self_loginは["gh", "api", "user", ...]を使う。
        if path == "user":
            return SimpleNamespace(returncode=0, stdout="me\n", stderr="")
        if "issues/comments/" in path or "pulls/comments/" in path:
            body = (
                comment_raw
                if comment_raw is not None
                else json.dumps({"created_at": comment_created, "body": comment_body})
            )
        elif (
            path.endswith("/pulls/1")
            or "/pulls/1?" in path
            or path == "repos/o/r/pulls/1"
        ):
            # .user.loginを求めるjq出力を再現し、ログイン名だけを返す。
            body = pr_author
        elif "/issues/1/comments" in path:
            body = _dump(issue_comments)
        elif "/pulls/1/reviews" in path:
            body = _dump(reviews)
        elif "/pulls/1/commits" in path:
            body = _dump(commits)
        elif "/pulls/1/comments" in path:
            body = _dump(review_comments)
        else:
            body = ""
        return SimpleNamespace(returncode=0, stdout=body, stderr="")

    return run


def test_gh_comment_resolved_via_issue_comment(tasks, monkeypatch):
    url = "https://github.com/o/r/pull/1#issuecomment-555"
    router = _comment_api_router(
        issue_comments=[
            {"created_at": "2026-06-02T00:00:00Z", "user": {"login": "teammate"}}
        ],
    )
    monkeypatch.setattr("subprocess.run", router)
    assert tasks.module._gh_comment_resolved(url) == "teammate"


def test_gh_comment_resolved_via_review(tasks, monkeypatch):
    url = "https://github.com/o/r/pull/1#issuecomment-555"
    router = _comment_api_router(
        reviews=[
            {"submitted_at": "2026-06-03T00:00:00Z", "user": {"login": "teammate"}}
        ],
    )
    monkeypatch.setattr("subprocess.run", router)
    assert tasks.module._gh_comment_resolved(url) == "teammate"


def test_gh_comment_resolved_via_commit(tasks, monkeypatch):
    url = "https://github.com/o/r/pull/1#issuecomment-555"
    router = _comment_api_router(
        commits=[
            {
                "commit": {"committer": {"date": "2026-06-04T00:00:00Z"}},
                "author": {"login": "teammate"},
            }
        ],
    )
    monkeypatch.setattr("subprocess.run", router)
    assert tasks.module._gh_comment_resolved(url) == "teammate"


def test_gh_comment_resolved_no_activity(tasks, monkeypatch):
    url = "https://github.com/o/r/pull/1#issuecomment-555"
    router = _comment_api_router()  # 後続のコメント・レビュー・コミットはない。
    monkeypatch.setattr("subprocess.run", router)
    assert tasks.module._gh_comment_resolved(url) is None


def test_gh_comment_resolved_not_a_comment_url(tasks):
    # #issuecomment-のフラグメントがなければ、APIを呼ばずNoneを返す。
    assert tasks.module._gh_comment_resolved("https://github.com/o/r/pull/1") is None


def test_gh_comment_resolved_no_created_at(tasks, monkeypatch):
    # コメントにcreated_atがなければ前後を判断できないため、処理を中止する。
    url = "https://github.com/o/r/pull/1#issuecomment-555"
    router = _comment_api_router(comment_created="")
    monkeypatch.setattr("subprocess.run", router)
    assert tasks.module._gh_comment_resolved(url) is None


def test_gh_comment_resolved_no_other_side(tasks, monkeypatch):
    # 本文にメンションがなく、PR作成者も自分（me）の場合は、
    # 応答を待つ相手がいないためNoneを返す。
    url = "https://github.com/o/r/pull/1#issuecomment-555"
    router = _comment_api_router(comment_body="just a note, no pings", pr_author="me")
    monkeypatch.setattr("subprocess.run", router)
    assert tasks.module._gh_comment_resolved(url) is None


def test_gh_comment_resolved_comment_fetch_fails(tasks, monkeypatch):
    url = "https://github.com/o/r/pull/1#issuecomment-555"
    monkeypatch.setattr("subprocess.run", _fake_run(returncode=1))
    assert tasks.module._gh_comment_resolved(url) is None


# ---------- PRレビューコメントへの応答判定（_gh_comment_resolved・#discussion_r<id>） ----------
#
# 末尾が#discussion_r<id>の待ち先URLは、Issueコメントの時系列ではなく
# PRの行コメントを指す。本文は
# repos/.../pulls/comments/<id>にあり、相手からの返信はPRの
# レビュースレッド（repos/.../pulls/1/comments）に投稿される。
# Issueコメントの時系列には現れないが、待ちの解除条件は
# #issuecomment-と同じく、相手からの応答があったこととする。


def test_gh_comment_resolved_discussion_reply_in_review_thread(tasks, monkeypatch):
    # 自分のコメント後に、相手がレビュースレッドへ返信している。
    url = "https://github.com/o/r/pull/1#discussion_r3346035452"
    router = _comment_api_router(
        review_comments=[
            {"created_at": "2026-06-04T00:00:00Z", "user": {"login": "teammate"}}
        ],
    )
    monkeypatch.setattr("subprocess.run", router)
    assert tasks.module._gh_comment_resolved(url) == "teammate"


def test_gh_comment_resolved_discussion_no_reply(tasks, monkeypatch):
    # 最新の活動が待ちの起点となる自分のコメントで、その後の返信がない。
    # PR #1973と同様に、スレッドがレビューを受ける側の発言で終わっている。
    url = "https://github.com/o/r/pull/1#discussion_r3346035452"
    router = _comment_api_router(
        review_comments=[
            {"created_at": "2026-05-30T00:00:00Z", "user": {"login": "teammate"}}
        ],  # 自分のコメントより前
    )
    monkeypatch.setattr("subprocess.run", router)
    assert tasks.module._gh_comment_resolved(url) is None


def test_gh_comment_resolved_discussion_reply_by_self_ignored(tasks, monkeypatch):
    # コメント後の返信が自分（me）による補足の場合は、
    # 自分の待ちを自動解除してはならない。
    url = "https://github.com/o/r/pull/1#discussion_r3346035452"
    router = _comment_api_router(
        comment_body="@teammate please look",
        pr_author="someone",
        review_comments=[
            {"created_at": "2026-06-04T00:00:00Z", "user": {"login": "me"}}
        ],
    )
    monkeypatch.setattr("subprocess.run", router)
    assert tasks.module._gh_comment_resolved(url) is None


def test_gh_comment_resolved_discussion_review_comments_malformed_warns(
    tasks, monkeypatch, capsys
):
    url = "https://github.com/o/r/pull/1#discussion_r3346035452"
    router = _comment_api_router(review_comments="{broken")
    monkeypatch.setattr("subprocess.run", router)
    result = tasks.module._gh_comment_resolved(url)
    err = capsys.readouterr().err
    assert result is None
    assert "review comments list" in err


def test_resolve_blocked_discussion_ball_returned(tasks, capsys, monkeypatch):
    url = "https://github.com/o/r/pull/1#discussion_r999"
    tasks.run("add", "discussion reply", "--from", "others", "--blocked-by", url)
    capsys.readouterr()
    router = _comment_api_router(
        review_comments=[
            {"created_at": "2026-06-05T00:00:00Z", "user": {"login": "teammate"}}
        ],
    )
    monkeypatch.setattr("subprocess.run", router)
    tasks.run("list", "--resolve-blocked")
    out = json.loads(capsys.readouterr().out)
    assert any(
        u["id"] == tasks.by_title("discussion reply")["id"]
        for u in out.get("_unblocked", [])
    )
    assert tasks.by_title("discussion reply")["status"] == "open"


def test_resolve_blocked_discussion_still_waiting(tasks, capsys, monkeypatch):
    url = "https://github.com/o/r/pull/1#discussion_r999"
    tasks.run("add", "discussion reply", "--from", "others", "--blocked-by", url)
    capsys.readouterr()
    router = _comment_api_router()  # 自分のコメント後に返信はない。
    monkeypatch.setattr("subprocess.run", router)
    tasks.run("list", "--resolve-blocked")
    out = json.loads(capsys.readouterr().out)
    assert "_unblocked" not in out
    assert tasks.by_title("discussion reply")["status"] == "pending"


# ---------- 不正なJSONの処理: 標準エラーへの警告・安全な値・終了コード0 ----------
#
# CLIの背後にエラー追跡サービスがないため、不正な応答を処理した痕跡は
# 標準エラー出力だけに残る。次の動作をテストで保証する。
#   - 標準エラー出力に「[tasks] warning: ...」の形式で警告を1行出す。
#   - 標準出力はJSONだけを維持し、補助関数は安全な値を返す。
#   - コマンドは例外を送出せず、終了コード0で終わる。


def test_gh_state_malformed_warns_and_returns_none(tasks, monkeypatch, capsys):
    monkeypatch.setattr("subprocess.run", _fake_run(stdout="{not json"))
    result = tasks.module._gh_state("https://github.com/o/r/pull/1")
    err = capsys.readouterr().err
    assert result is None  # 状態不明の場合の安全な値
    assert "[tasks] warning:" in err
    assert "o/r#1" in err


def test_comment_blocker_body_malformed_warns_and_stays_blocked(
    tasks, monkeypatch, capsys
):
    url = "https://github.com/o/r/pull/1#issuecomment-555"
    # 待ちの起点となるコメントを読めない場合は判断せず、待ちを維持する。
    router = _comment_api_router(comment_raw="{broken")
    monkeypatch.setattr("subprocess.run", router)
    result = tasks.module._gh_comment_resolved(url)
    err = capsys.readouterr().err
    assert result is None
    assert "[tasks] warning:" in err
    assert "leaving the task blocked" in err


def test_comment_comments_list_malformed_warns_then_checks_next_source(
    tasks, monkeypatch, capsys
):
    url = "https://github.com/o/r/pull/1#issuecomment-555"
    # Issueコメントの一覧が不正でも、後から調べるレビューに返信がある。
    router = _comment_api_router(
        issue_comments="{broken",
        reviews=[
            {"submitted_at": "2026-06-03T00:00:00Z", "user": {"login": "teammate"}}
        ],
    )
    monkeypatch.setattr("subprocess.run", router)
    result = tasks.module._gh_comment_resolved(url)
    err = capsys.readouterr().err
    assert result == "teammate"  # レビューまで調べて応答を検出する。
    assert "skipping that source" in err
    assert "comments list" in err


def test_comment_reviews_list_malformed_warns(tasks, monkeypatch, capsys):
    url = "https://github.com/o/r/pull/1#issuecomment-555"
    router = _comment_api_router(reviews="{broken")
    monkeypatch.setattr("subprocess.run", router)
    result = tasks.module._gh_comment_resolved(url)
    err = capsys.readouterr().err
    assert result is None
    assert "reviews list" in err


def test_comment_commits_list_malformed_warns(tasks, monkeypatch, capsys):
    url = "https://github.com/o/r/pull/1#issuecomment-555"
    router = _comment_api_router(commits="{broken")
    monkeypatch.setattr("subprocess.run", router)
    result = tasks.module._gh_comment_resolved(url)
    err = capsys.readouterr().err
    assert result is None
    assert "commits list" in err


def test_resolve_blocked_malformed_keeps_pending_and_exits_clean(
    tasks, capsys, monkeypatch
):
    """CLI経由で、不正なgh応答でも異常終了せず、タスクの待機状態を維持することを検証する。
    stderrに警告を出し、stdoutは有効なJSONのままにする。
    """
    url = "https://github.com/o/r/pull/1#issuecomment-555"
    tasks.run("add", "review reply", "--from", "others", "--blocked-by", url)
    capsys.readouterr()
    router = _comment_api_router(comment_raw="{broken")
    monkeypatch.setattr("subprocess.run", router)
    # この処理経路では例外がなければ終了コード0になる。
    tasks.run("list", "--resolve-blocked")
    captured = capsys.readouterr()
    out = json.loads(captured.out)  # 標準出力は引き続きJSONとして解析できる。
    assert out["tasks"] == []  # pendingのタスクはopenの一覧から除外する。
    assert "_unblocked" not in out  # 誤って待ちを解除したタスクはない。
    assert "[tasks] warning:" in captured.err  # 異常は警告で報告する。
    assert tasks.by_title("review reply")["status"] == "pending"
