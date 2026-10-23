"""GitHub-integration tests for the `tasks` CLI: _gh_state / _gh_self_login /
_gh_comment_resolved, blocker resolution, stale-pending sweep, and
malformed-JSON handling. The `tasks` fixture comes from conftest.py.
"""

import datetime as _datetime
import json
from types import SimpleNamespace


def _fake_run(stdout="", returncode=0):
    """Build a subprocess.run replacement returning a canned CompletedProcess-like."""

    def run(*args, **kwargs):
        return SimpleNamespace(returncode=returncode, stdout=stdout, stderr="")

    return run


# ---------- GitHub helpers (subprocess mocked) ----------


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
    # An open task with no blocker must be left untouched by --resolve-blocked.
    tasks.run("add", "free")
    capsys.readouterr()
    tasks.run("list", "--resolve-blocked")
    capsys.readouterr()
    assert tasks.by_title("free")["status"] == "open"


# ---------- stale pending sweep (any list call) ----------
#
# A pending task that hasn't moved (updated_at) for a week is probably stuck on
# the user's side, not the blocker's. Any `list` call flips it back to open so
# it re-surfaces, and reports it under _stale_unblocked with how long it sat —
# so the user can decide what to do. This runs on every list, not just
# --resolve-blocked.


def _age_pending(tasks, title, days, blocked_by="https://github.com/o/r/pull/1"):
    """Make an existing task pending with updated_at set `days` ago."""
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
    # Exactly 7 days (plus a hair, to dodge second-level rounding) counts as stale.
    tasks.run("add", "borderline", "--from", "others")
    _age_pending(tasks, "borderline", days=7)
    capsys.readouterr()
    tasks.run("list")
    out = json.loads(capsys.readouterr().out)
    assert tasks.by_title("borderline")["status"] == "open"
    assert any(s["title"] == "borderline" for s in out.get("_stale_unblocked", []))


def test_stale_pending_handles_utc_z_timestamp(tasks, capsys):
    # GitHub-sourced tasks carry a trailing-Z UTC updated_at; it must parse.
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
    # An old but already-open task is not a pending sweep target.
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
    # No updated_at to anchor age on → leave it pending rather than guess.
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


# ---------- _gh_state JSON edge ----------


def test_gh_state_bad_json(tasks, monkeypatch):
    monkeypatch.setattr("subprocess.run", _fake_run(stdout="not json"))
    assert tasks.module._gh_state("https://github.com/o/r/pull/1") is None


def test_gh_state_issue_url(tasks, monkeypatch):
    monkeypatch.setattr("subprocess.run", _fake_run(stdout='{"state": "CLOSED"}'))
    st = tasks.module._gh_state("https://github.com/o/r/issues/7")
    assert st == {"state": "CLOSED", "merged": False}


# ---------- _gh_self_login ----------


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


# ---------- _gh_comment_resolved ----------


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
    """Return a fake subprocess.run that answers the gh api calls
    _gh_comment_resolved makes, keyed by the path argument.

    Serves both blocker kinds: an #issuecomment-<id> blocker's body comes from
    repos/.../issues/comments/<id>, while a #discussion_r<id> (PR review comment)
    blocker's body comes from repos/.../pulls/comments/<id>. The same router
    answers both; review_comments injects the PR review-comment thread that the
    discussion path reads on top of the issue-comments timeline.

    Any of issue_comments / reviews / commits / review_comments / comment_raw
    may be a raw string to inject a malformed-JSON response for that endpoint;
    otherwise the value is JSON-encoded as normal.
    """
    issue_comments = issue_comments if issue_comments is not None else []
    reviews = reviews if reviews is not None else []
    commits = commits if commits is not None else []
    review_comments = review_comments if review_comments is not None else []

    def _dump(v):
        return v if isinstance(v, str) else json.dumps(v)

    def run(cmd, *args, **kwargs):
        # cmd looks like ["gh", "api", "--method", "GET", <path>, ...]
        path = cmd[4] if len(cmd) > 4 else ""
        # _gh_self_login uses ["gh", "api", "user", ...]
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
            # The .user.login jq is requested; emulate jq output (just the login).
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
    router = _comment_api_router()  # no comments/reviews/commits after
    monkeypatch.setattr("subprocess.run", router)
    assert tasks.module._gh_comment_resolved(url) is None


def test_gh_comment_resolved_not_a_comment_url(tasks):
    # No #issuecomment- fragment → returns None without any API call.
    assert tasks.module._gh_comment_resolved("https://github.com/o/r/pull/1") is None


def test_gh_comment_resolved_no_created_at(tasks, monkeypatch):
    # Comment has no created_at → can't anchor "after", so bail out.
    url = "https://github.com/o/r/pull/1#issuecomment-555"
    router = _comment_api_router(comment_created="")
    monkeypatch.setattr("subprocess.run", router)
    assert tasks.module._gh_comment_resolved(url) is None


def test_gh_comment_resolved_no_other_side(tasks, monkeypatch):
    # No @mentions in the body and the PR author is ourselves ("me"), so the
    # "other side" set is empty — nobody to wait on, return None.
    url = "https://github.com/o/r/pull/1#issuecomment-555"
    router = _comment_api_router(comment_body="just a note, no pings", pr_author="me")
    monkeypatch.setattr("subprocess.run", router)
    assert tasks.module._gh_comment_resolved(url) is None


def test_gh_comment_resolved_comment_fetch_fails(tasks, monkeypatch):
    url = "https://github.com/o/r/pull/1#issuecomment-555"
    monkeypatch.setattr("subprocess.run", _fake_run(returncode=1))
    assert tasks.module._gh_comment_resolved(url) is None


# ---------- _gh_comment_resolved: #discussion_r<id> (PR review comment) ----------
#
# A blocker URL ending in #discussion_r<id> points at an inline PR review
# comment, not the issue-comment timeline. Its body lives at
# repos/.../pulls/comments/<id>, and a reply by the other side lands in the PR
# review-comment thread (repos/.../pulls/1/comments) — which the issue-comments
# timeline does not surface. Resolution otherwise follows the same "ball came
# back" rule as #issuecomment-.


def test_gh_comment_resolved_discussion_reply_in_review_thread(tasks, monkeypatch):
    # The other side replied in the review-comment thread after our comment.
    url = "https://github.com/o/r/pull/1#discussion_r3346035452"
    router = _comment_api_router(
        review_comments=[
            {"created_at": "2026-06-04T00:00:00Z", "user": {"login": "teammate"}}
        ],
    )
    monkeypatch.setattr("subprocess.run", router)
    assert tasks.module._gh_comment_resolved(url) == "teammate"


def test_gh_comment_resolved_discussion_no_reply(tasks, monkeypatch):
    # Latest activity is our own comment (the blocker); nobody replied after.
    # Mirrors PR #1973: the thread ends on the reviewee's own message.
    url = "https://github.com/o/r/pull/1#discussion_r3346035452"
    router = _comment_api_router(
        review_comments=[
            {"created_at": "2026-05-30T00:00:00Z", "user": {"login": "teammate"}}
        ],  # before our comment
    )
    monkeypatch.setattr("subprocess.run", router)
    assert tasks.module._gh_comment_resolved(url) is None


def test_gh_comment_resolved_discussion_reply_by_self_ignored(tasks, monkeypatch):
    # A reply after the comment, but it's us ("me") — our own follow-up must not
    # auto-resolve our own block.
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
    router = _comment_api_router()  # no reply after our comment
    monkeypatch.setattr("subprocess.run", router)
    tasks.run("list", "--resolve-blocked")
    out = json.loads(capsys.readouterr().out)
    assert "_unblocked" not in out
    assert tasks.by_title("discussion reply")["status"] == "pending"


# ---------- malformed-JSON handling: warn on stderr, stay safe, exit 0 ----------
#
# With no error-tracking service behind the CLI, stderr is the only trace a
# swallowed bad response leaves. These tests pin the contract:
#   - a one-line "[tasks] warning: ..." goes to stderr
#   - stdout stays clean JSON / the helper returns the safe value
#   - the command never raises (i.e. would exit 0)


def test_gh_state_malformed_warns_and_returns_none(tasks, monkeypatch, capsys):
    monkeypatch.setattr("subprocess.run", _fake_run(stdout="{not json"))
    result = tasks.module._gh_state("https://github.com/o/r/pull/1")
    err = capsys.readouterr().err
    assert result is None  # safe: state unknown
    assert "[tasks] warning:" in err
    assert "o/r#1" in err


def test_comment_blocker_body_malformed_warns_and_stays_blocked(
    tasks, monkeypatch, capsys
):
    url = "https://github.com/o/r/pull/1#issuecomment-555"
    # The blocker comment itself is unreadable → cannot judge → leave blocked.
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
    # issue-comments list is garbage, but a later source (reviews) has the reply.
    router = _comment_api_router(
        issue_comments="{broken",
        reviews=[
            {"submitted_at": "2026-06-03T00:00:00Z", "user": {"login": "teammate"}}
        ],
    )
    monkeypatch.setattr("subprocess.run", router)
    result = tasks.module._gh_comment_resolved(url)
    err = capsys.readouterr().err
    assert result == "teammate"  # fell through to reviews, still resolved
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
    """End-to-end through the CLI: a malformed gh response must NOT crash the
    command, must leave the task blocked, and must surface a stderr warning
    while keeping stdout valid JSON."""
    url = "https://github.com/o/r/pull/1#issuecomment-555"
    tasks.run("add", "review reply", "--from", "others", "--blocked-by", url)
    capsys.readouterr()
    router = _comment_api_router(comment_raw="{broken")
    monkeypatch.setattr("subprocess.run", router)
    # No exception == exit 0 for this code path.
    tasks.run("list", "--resolve-blocked")
    captured = capsys.readouterr()
    out = json.loads(captured.out)  # stdout is still parseable JSON
    assert out["tasks"] == []  # pending task excluded from the open list
    assert "_unblocked" not in out  # nothing was wrongly unblocked
    assert "[tasks] warning:" in captured.err  # but the anomaly was reported
    assert tasks.by_title("review reply")["status"] == "pending"
