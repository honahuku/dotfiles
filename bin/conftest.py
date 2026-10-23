"""Shared pytest fixtures for the `tasks` CLI script (claude-companion local store).

The suite is split by domain so a single area can be run without loading the
whole file (this keeps concurrent edits in different areas from colliding):
    test_tasks_crud.py      add / list / update / reorder / delete / meta /
                            snooze / migration / dependency
    test_tasks_worklog.py   work log / pace correction / flex / today_plan /
                            work summary
    test_tasks_github.py    _gh_* helpers / stale-pending sweep / malformed JSON
    test_tasks_obsidian.py  page sync / daily note / commit message / vault backup
    test_tasks_daily.py     daily logs / notif-keys

Run the complete suite every time:
    uv run --with pytest pytest .

Non-fixture helpers shared across files live in _test_helpers.py; helpers used
by only one domain stay local to that file. Every test points
CLAUDE_COMPANION_STORE at a pytest tmp_path, so the real store
(~/.claude-companion/tasks.json) is never touched.

The `tasks` script has no .py extension, so it's loaded as a module via
importlib. `_backup_to_git` is neutralized because the tmp store is not a git
repo (and we don't want tests pushing anything).
"""

import json

import pytest
from _test_helpers import _load_tasks_module


@pytest.fixture
def tasks(tmp_path, monkeypatch):
    """A freshly-loaded tasks module wired to a throwaway store.

    Returns a helper object exposing `.run(*argv)` to invoke CLI commands and
    `.store()` to read back the raw JSON.
    """
    store = tmp_path / "tasks.json"
    monkeypatch.setenv("CLAUDE_COMPANION_STORE", str(store))

    mod = _load_tasks_module()
    # The module read STORE at import time from the env var we just set, so it
    # already points at tmp_path. Belt and suspenders: re-point it explicitly.
    mod.STORE = store
    # Don't let tests touch git. save() now calls _backup_to_git(message=...),
    # so the stub must accept args. _backup_vault_to_git is NOT stubbed: it
    # early-returns when the vault is unset (most tests) or not a git repo
    # (tests that set obsidian_vault_dir at a plain tmp dir), so it never runs
    # git on its own. Feature-D tests exercise the real function directly on a
    # git-initialized tmp vault.
    monkeypatch.setattr(mod, "_backup_to_git", lambda *a, **k: None)

    class Harness:
        def __init__(self):
            self.module = mod
            self.store_path = store

        def run(self, *argv):
            args = mod.build_parser().parse_args(list(argv))
            args.func(args)

        def store(self):
            return json.loads(store.read_text())

        def active(self):
            """Active tasks sorted by queue_pos (the queue order)."""
            data = self.store()
            act = [t for t in data["tasks"] if t["status"] in ("open", "pending")]
            act.sort(key=lambda t: t.get("queue_pos") or 0)
            return act

        def by_title(self, title):
            for t in self.store()["tasks"]:
                if t["title"] == title:
                    return t
            raise KeyError(title)

        def positions(self):
            """List of (title, queue_pos) in queue order."""
            return [(t["title"], t["queue_pos"]) for t in self.active()]

    return Harness()
