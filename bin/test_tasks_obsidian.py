"""`tasks` CLIのObsidian連携とGitバックアップを検証する。
保存先のGitバックアップ（_backup_to_git）、コミットメッセージ、
日次ノートの書き込み、タスクページの同期、保管庫のGitバックアップを対象とする。
`tasks`フィクスチャはconftest.pyで定義する。
"""

import json
import subprocess
from datetime import date

import pytest
from _test_helpers import _load_tasks_module

# ---------- Gitへの保存（_backup_to_git） ----------


def test_backup_to_git_commits_and_pushes(tmp_path, monkeypatch):
    """一時的なGitリポジトリで実際の_backup_to_gitを実行する。"""
    import subprocess as real_subprocess

    repo = tmp_path / "store"
    repo.mkdir()
    real_subprocess.run(["git", "init", "-q", str(repo)], check=True)
    store = repo / "tasks.json"
    store.write_text('{"tasks": [], "work_log": {}, "daily_logs": [], "meta": {}}')

    monkeypatch.setenv("TASKS_STORE", str(store))
    mod = _load_tasks_module()
    mod.STORE = store

    # 実際のネットワークへのpushを防ぐため、pushのPopenだけを置き換える。
    calls = {"push": False}
    orig_popen = real_subprocess.Popen

    def fake_popen(cmd, *a, **k):
        if "push" in cmd:
            calls["push"] = True

            class _P:  # 最小限の代替オブジェクト
                pass

            return _P()
        return orig_popen(cmd, *a, **k)

    monkeypatch.setattr("subprocess.Popen", fake_popen)

    mod._backup_to_git()
    # tasks.jsonを変更するコミットが作成されていることを確認する。
    log = real_subprocess.run(
        ["git", "-C", str(repo), "log", "--oneline"],
        check=True,
        capture_output=True,
        text=True,
    )
    assert log.stdout.strip()  # コミットが少なくとも一つ存在する。
    assert calls["push"] is True


def test_backup_to_git_skips_non_repo(tmp_path, monkeypatch):
    store = tmp_path / "tasks.json"
    store.write_text("{}")
    monkeypatch.setenv("TASKS_STORE", str(store))
    mod = _load_tasks_module()
    mod.STORE = store
    # Gitリポジトリでなければ、例外を出さずに戻る。
    mod._backup_to_git()


def test_backup_to_git_no_diff_noop(tmp_path, monkeypatch):
    import subprocess as real_subprocess

    repo = tmp_path / "store"
    repo.mkdir()
    real_subprocess.run(["git", "init", "-q", str(repo)], check=True)
    store = repo / "tasks.json"
    store.write_text("{}")
    # 未コミット差分が残らないよう、先にファイルをコミットする。
    real_subprocess.run(["git", "-C", str(repo), "add", "tasks.json"], check=True)
    real_subprocess.run(
        [
            "git",
            "-C",
            str(repo),
            "-c",
            "user.name=t",
            "-c",
            "user.email=t@t",
            "commit",
            "-q",
            "-m",
            "init",
        ],
        check=True,
    )

    monkeypatch.setenv("TASKS_STORE", str(store))
    mod = _load_tasks_module()
    mod.STORE = store
    # 差分がなければPopenによるpushの前に戻る。pushを実行すると
    # 実際のリモートへ接続するため、処理が正常に終わり、
    # コミット数が1のままであることを検証する。
    mod._backup_to_git()
    log = real_subprocess.run(
        ["git", "-C", str(repo), "log", "--oneline"],
        check=True,
        capture_output=True,
        text=True,
    )
    assert (
        len(log.stdout.strip().splitlines()) == 1
    )  # 初期化時のコミット一つだけが残る。


# ---------- コミットメッセージ（機能A） ----------


def test_commit_message_add(tasks):
    m = tasks.module._commit_message("add", "コスト試算の仕組みを作る")
    assert m == 'chore: タスク追加 "コスト試算の仕組みを作る"'


def test_commit_message_done_cancel_delete_snooze(tasks):
    cm = tasks.module._commit_message
    assert cm("done", "x") == 'chore: タスク完了 "x"'
    assert cm("cancel", "x") == 'chore: タスクキャンセル "x"'
    assert cm("delete", "x") == 'chore: タスク削除 "x"'
    assert cm("snooze", "x") == 'chore: タスクスヌーズ "x"'
    assert cm("update", "x") == 'chore: タスク更新 "x"'


def test_commit_message_none_action_falls_back(tasks):
    """action なし・未知の action は None を返し、呼び先が既定文言に落とす。"""
    assert tasks.module._commit_message(None, "x") is None
    assert tasks.module._commit_message("reorder", "x") is None


def test_commit_message_empty_title(tasks):
    """title が空ならラベルだけ。"""
    assert tasks.module._commit_message("add", "") == "chore: タスク追加"
    assert tasks.module._commit_message("add", None) == "chore: タスク追加"


def test_commit_message_long_title_truncated(tasks):
    long = "あ" * 100
    m = tasks.module._commit_message("add", long)
    assert m.startswith('chore: タスク追加 "')
    assert m.endswith('…"')
    # 引用符の内側は57文字と省略記号になる。
    assert "あ" * 57 + "…" in m


def test_commit_message_newline_flattened(tasks):
    m = tasks.module._commit_message("add", "line1\nline2")
    assert m == 'chore: タスク追加 "line1 line2"'


def _capture_commit_message(tasks, monkeypatch):
    """save() が _backup_to_git に渡す message をキャプチャするリストを返す。"""
    seen = []
    monkeypatch.setattr(
        tasks.module,
        "_backup_to_git",
        lambda message=None: seen.append(message),
    )
    return seen


def test_add_passes_commit_message(tasks, capsys, monkeypatch):
    seen = _capture_commit_message(tasks, monkeypatch)
    tasks.run("add", "買い物")
    capsys.readouterr()
    assert seen[-1] == 'chore: タスク追加 "買い物"'


def test_done_passes_commit_message(tasks, capsys, monkeypatch):
    tasks.run("add", "レビュー対応")
    tid = json.loads(capsys.readouterr().out)["id"]
    seen = _capture_commit_message(tasks, monkeypatch)
    tasks.run("update", tid, "--status", "done")
    capsys.readouterr()
    assert seen[-1] == 'chore: タスク完了 "レビュー対応"'


def test_delete_passes_commit_message(tasks, capsys, monkeypatch):
    tasks.run("add", "消すやつ")
    tid = json.loads(capsys.readouterr().out)["id"]
    seen = _capture_commit_message(tasks, monkeypatch)
    tasks.run("delete", tid)
    capsys.readouterr()
    assert seen[-1] == 'chore: タスク削除 "消すやつ"'


def test_reorder_uses_fallback_message(tasks, capsys, monkeypatch):
    tasks.run("add", "a")
    tasks.run("add", "b")
    tid = tasks.by_title("b")["id"]
    seen = _capture_commit_message(tasks, monkeypatch)
    tasks.run("reorder", tid, "--head")
    capsys.readouterr()
    # reorderは操作名を渡さないため、messageがNoneとなり呼び出し元が既定値を使う。
    assert seen[-1] is None


# ---------- 日次保存時の状態スコア（機能C） ----------


def test_daily_save_stores_condition_scores(tasks, capsys):
    tasks.run(
        "daily",
        "save",
        "--focus",
        "4",
        "--sleepiness",
        "3",
        "--start-mood",
        "5",
        "--output-feel",
        "2",
    )
    out = json.loads(capsys.readouterr().out)
    assert out["focus"] == 4
    assert out["sleepiness"] == 3
    assert out["start_mood"] == 5
    assert out["output_feel"] == 2


def test_daily_save_condition_merges_without_clobber(tasks, capsys):
    """/todo の途中申告と夕方 furikaeri が互いのスコアを消さない。"""
    tasks.run("daily", "save", "--focus", "4")
    capsys.readouterr()
    tasks.run("daily", "save", "--sleepiness", "2")
    out = json.loads(capsys.readouterr().out)
    assert out["focus"] == 4  # 前回の値が残る
    assert out["sleepiness"] == 2  # 今回の値が入る


def test_daily_save_out_of_range_score_rejected(tasks, capsys):
    with pytest.raises(SystemExit):
        tasks.run("daily", "save", "--focus", "9")


def test_daily_save_without_scores_leaves_none(tasks, capsys):
    tasks.run("daily", "save", "--good", "順調")
    out = json.loads(capsys.readouterr().out)
    assert out["good"] == "順調"
    assert out["focus"] is None
    assert out["sleepiness"] is None


# ---------- ラベル付き行の追加・更新補助 ----------


def test_upsert_labeled_line_adds_to_new_section(tasks):
    """セクションが無ければ `## ふりかえり` を新設してラベル行を足す。"""
    f = tasks.module._upsert_labeled_line
    out = f("", "ふりかえり", "よかったこと", "レビューを返せた")
    assert "## ふりかえり" in out
    assert "- よかったこと: レビューを返せた" in out


def test_upsert_labeled_line_replaces_existing_label(tasks):
    """同じラベル行があれば値を差し替える（重複させない）。"""
    f = tasks.module._upsert_labeled_line
    text = "## ふりかえり\n- よかったこと: 旧\n"
    out = f(text, "ふりかえり", "よかったこと", "新")
    assert "- よかったこと: 新" in out
    assert "旧" not in out
    assert out.count("- よかったこと:") == 1


def test_upsert_labeled_line_preserves_other_labels(tasks):
    """自分のラベル行だけ触り、他のラベル行は残す。"""
    f = tasks.module._upsert_labeled_line
    text = "## ふりかえり\n- 今日の本丸: TASK-102\n- 課題: 溜まった\n"
    out = f(text, "ふりかえり", "よかったこと", "進んだ")
    assert "- 今日の本丸: TASK-102" in out
    assert "- 課題: 溜まった" in out
    assert "- よかったこと: 進んだ" in out


def test_upsert_labeled_line_does_not_touch_other_sections(tasks):
    """`## ふりかえり` 以外のセクションは変えない。"""
    f = tasks.module._upsert_labeled_line
    text = "## 今日の予定\n| a | b |\n\n## 一言メモ\n- メモ\n"
    out = f(text, "ふりかえり", "よかったこと", "x")
    assert "## 今日の予定" in out
    assert "## 一言メモ" in out
    assert "- メモ" in out
    assert "- よかったこと: x" in out


# ---------- デイリーノートの書き込み（機能C） ----------


def _set_vault(tasks, tmp_path, capsys=None):
    """meta に obsidian_vault_dir をセットして vault の Path を返す。"""
    vault = tmp_path / "vault"
    vault.mkdir()
    tasks.run("meta", "set", "obsidian_vault_dir", json.dumps(str(vault)))
    if capsys is not None:
        capsys.readouterr()  # meta set の出力を捨てる
    return vault


def test_daily_note_written_with_report_and_condition(tasks, capsys, tmp_path):
    vault = _set_vault(tasks, tmp_path, capsys)
    tasks.run(
        "daily",
        "save",
        "--date",
        "2026-07-03",
        "--good",
        "本丸を進めた",
        "--issues",
        "レビューが溜まった",
        "--focus",
        "4",
        "--sleepiness",
        "3",
    )
    capsys.readouterr()
    note = (vault / "daily" / "2026-07-03.md").read_text(encoding="utf-8")
    assert "## ふりかえり" in note
    assert "- よかったこと: 本丸を進めた" in note
    assert "- 課題: レビューが溜まった" in note
    # コンディションは記録のあるスコアだけを1行に集約する。分母付きで
    # 記録時点のレンジ(1-5)を残し、値のスラッシュと区切りが紛れないよう
    # 区切りはアンダースコアにする。
    assert "- コンディション: 集中度4/5 _ 眠気3/5" in note
    # 記録の無いスコアは出ない。
    assert "業務開始" not in note
    # 廃止したセクションは書かない。
    assert "## 日報" not in note
    assert "## コンディション" not in note


def test_daily_note_skips_empty_sections(tasks, capsys, tmp_path):
    vault = _set_vault(tasks, tmp_path, capsys)
    # good/issues も scores も無い → どのラベル行も書かない。
    tasks.run("daily", "save", "--date", "2026-07-03", "--notes", "x")
    capsys.readouterr()
    note = vault / "daily" / "2026-07-03.md"
    text = note.read_text(encoding="utf-8") if note.exists() else ""
    assert "- よかったこと:" not in text
    assert "- 課題:" not in text
    assert "- コンディション:" not in text


def test_daily_note_preserves_other_sections(tasks, capsys, tmp_path):
    """既存の todo 由来セクションや手書きを壊さない。"""
    vault = _set_vault(tasks, tmp_path, capsys)
    daily_dir = vault / "daily"
    daily_dir.mkdir(parents=True, exist_ok=True)
    note = daily_dir / "2026-07-03.md"
    note.write_text(
        "# 2026-07-03 (金)\n\n## 今日の予定\n| a | b |\n\n## 一言メモ\n- メモ\n",
        encoding="utf-8",
    )
    tasks.run("daily", "save", "--date", "2026-07-03", "--good", "よかった")
    capsys.readouterr()
    text = note.read_text(encoding="utf-8")
    assert "## 今日の予定" in text
    assert "## 一言メモ" in text
    assert "- メモ" in text
    assert "## ふりかえり" in text
    assert "- よかったこと: よかった" in text


def test_daily_note_preserves_honmaru_label(tasks, capsys, tmp_path):
    """daily save は todo が書いた `- 今日の本丸:` 行を消さない。"""
    vault = _set_vault(tasks, tmp_path, capsys)
    daily_dir = vault / "daily"
    daily_dir.mkdir(parents=True, exist_ok=True)
    note = daily_dir / "2026-07-03.md"
    note.write_text(
        "## ふりかえり\n- 今日の本丸: TASK-102 実装\n",
        encoding="utf-8",
    )
    tasks.run("daily", "save", "--date", "2026-07-03", "--good", "よかった")
    capsys.readouterr()
    text = note.read_text(encoding="utf-8")
    assert "- 今日の本丸: TASK-102 実装" in text
    assert "- よかったこと: よかった" in text
    # ふりかえりセクションは1つのまま。
    assert text.count("## ふりかえり") == 1


def test_daily_note_writes_standup_section(tasks, capsys, tmp_path):
    """--standup はデイリーノートの `## 朝会メモ` セクションに複数行のまま書かれる。"""
    vault = _set_vault(tasks, tmp_path, capsys)
    tasks.run(
        "daily",
        "save",
        "--date",
        "2026-07-09",
        "--standup",
        "- TASK-101: plan merge 済み、実装着手\n- Renovate #2262: レビュー待ち",
    )
    capsys.readouterr()
    note = (vault / "daily" / "2026-07-09.md").read_text(encoding="utf-8")
    assert "## 朝会メモ" in note
    assert "- TASK-101: plan merge 済み、実装着手" in note
    assert "- Renovate #2262: レビュー待ち" in note


def test_daily_note_standup_replaces_not_duplicates(tasks, capsys, tmp_path):
    """standup を再保存するとセクションごと置き換わり、旧内容は残らない。"""
    vault = _set_vault(tasks, tmp_path, capsys)
    tasks.run("daily", "save", "--date", "2026-07-09", "--standup", "旧メモ")
    tasks.run("daily", "save", "--date", "2026-07-09", "--standup", "新メモ")
    capsys.readouterr()
    note = (vault / "daily" / "2026-07-09.md").read_text(encoding="utf-8")
    assert note.count("## 朝会メモ") == 1
    assert "新メモ" in note
    assert "旧メモ" not in note


def test_daily_note_standup_empty_writes_nothing(tasks, capsys, tmp_path):
    """standup 未指定・空文字ならセクションを書かない。"""
    vault = _set_vault(tasks, tmp_path, capsys)
    tasks.run("daily", "save", "--date", "2026-07-09", "--good", "x")
    tasks.run("daily", "save", "--date", "2026-07-10", "--standup", "")
    capsys.readouterr()
    note9 = (vault / "daily" / "2026-07-09.md").read_text(encoding="utf-8")
    note10 = vault / "daily" / "2026-07-10.md"
    text10 = note10.read_text(encoding="utf-8") if note10.exists() else ""
    assert "## 朝会メモ" not in note9
    assert "## 朝会メモ" not in text10


def test_daily_note_standup_preserves_furikaeri(tasks, capsys, tmp_path):
    """standup の書き込みは既存の `## ふりかえり` や手書きセクションを壊さない。"""
    vault = _set_vault(tasks, tmp_path, capsys)
    daily_dir = vault / "daily"
    daily_dir.mkdir(parents=True, exist_ok=True)
    note = daily_dir / "2026-07-09.md"
    note.write_text(
        "## ふりかえり\n- 今日の本丸: TASK-101 実装\n- よかったこと: 進んだ\n",
        encoding="utf-8",
    )
    tasks.run("daily", "save", "--date", "2026-07-09", "--standup", "- 共有事項")
    capsys.readouterr()
    text = note.read_text(encoding="utf-8")
    assert "- 今日の本丸: TASK-101 実装" in text
    assert "- よかったこと: 進んだ" in text
    assert "## 朝会メモ" in text
    assert text.count("## ふりかえり") == 1


def test_daily_note_upsert_replaces_not_duplicates(tasks, capsys, tmp_path):
    """同じ日に2回叩いてもラベル行が重複せず、ふりかえりは1セクションのまま。"""
    vault = _set_vault(tasks, tmp_path, capsys)
    tasks.run("daily", "save", "--date", "2026-07-03", "--good", "初回")
    capsys.readouterr()
    tasks.run("daily", "save", "--date", "2026-07-03", "--good", "更新後")
    capsys.readouterr()
    text = (vault / "daily" / "2026-07-03.md").read_text(encoding="utf-8")
    assert text.count("## ふりかえり") == 1
    assert text.count("- よかったこと:") == 1
    assert "更新後" in text
    assert "初回" not in text


def test_daily_note_skipped_when_vault_unset(tasks, capsys, tmp_path):
    """vault 未設定なら書き込みは走らず、daily save 自体は成功する。"""
    tasks.run("daily", "save", "--date", "2026-07-03", "--good", "x")
    out = json.loads(capsys.readouterr().out)
    assert out["good"] == "x"
    # vault ディレクトリは作られない。
    assert not (tmp_path / "vault").exists()


# ---------- Obsidianのタスクページ同期（機能B） ----------


def test_sync_writes_page_for_open_task(tasks, capsys, tmp_path):
    vault = _set_vault(tasks, tmp_path, capsys)
    tasks.run("add", "コスト試算を作る", "--from", "me")
    tid = json.loads(capsys.readouterr().out)["id"]
    # ファイル名は queue_pos prefix + title。初回 add は queue_pos=10。
    page = vault / "tasks" / "010_コスト試算を作る.md"
    assert page.exists()
    text = page.read_text(encoding="utf-8")
    assert f"id: {tid}" in text
    assert "# コスト試算を作る" in text
    assert "managed_by: tasks" in text
    assert "status: open" in text


def test_sync_page_filename_sanitizes_special_chars(tasks, capsys, tmp_path):
    """title の使えない記号は _ に置換してファイル名にする。"""
    vault = _set_vault(tasks, tmp_path, capsys)
    tasks.run("add", "#alerts-project-* を整理する: 前半")
    capsys.readouterr()
    files = list((vault / "tasks").glob("*.md"))
    assert len(files) == 1
    name = files[0].name
    # / \ : * ? " < > | # ^ [ ] は含まれない。
    assert not any(c in name for c in '/\\:*?"<>|#^[]')
    assert "alerts-project" in name  # 使える文字は残る


def test_page_filename_helper(tasks):
    """_page_filename の変換規則を直接検証する。

    queue_pos があるとゼロ埋め3桁の prefix + アンダースコアが頭に付く。
    """
    pf = tasks.module._page_filename
    # queue_pos ありは 3桁ゼロ埋め prefix + _ が頭に付く。
    assert (
        pf({"id": "x", "title": "普通のタスク", "queue_pos": 10}) == "010_普通のタスク"
    )
    # / と : は _ に。( ) は使えるので残る。
    assert (
        pf({"id": "x", "title": "feat(gke/prod): 廃止", "queue_pos": 20})
        == "020_feat(gke_prod)_ 廃止"
    )
    # 連続する記号は _ 1つにまとめる（prefix の _ は保つ）。
    assert pf({"id": "x", "title": "a::b", "queue_pos": 100}) == "100_a_b"
    # queue_pos 1000 以上は 3桁を超えてそのまま出す。
    assert pf({"id": "x", "title": "先", "queue_pos": 1230}) == "1230_先"
    # queue_pos が無ければ prefix 無し（フォールバック）。
    assert pf({"id": "x", "title": "prefix なし"}) == "prefix なし"
    # 空 title は id にフォールバック（prefix は付く）。
    assert pf({"id": "fallback99", "title": "", "queue_pos": 30}) == "030_fallback99"
    # 記号だけの title も id にフォールバック（strip で空になる）。
    assert pf({"id": "fallback99", "title": "::", "queue_pos": 40}) == "040_fallback99"


def test_sync_page_prefixes_queue_pos(tasks, capsys, tmp_path):
    """複数タスクは queue_pos 順にゼロ埋め3桁 prefix が付く。"""
    vault = _set_vault(tasks, tmp_path, capsys)
    tasks.run("add", "一番目")
    tasks.run("add", "二番目")
    tasks.run("add", "三番目")
    capsys.readouterr()
    names = sorted(p.name for p in (vault / "tasks").glob("*.md"))
    assert names == ["010_一番目.md", "020_二番目.md", "030_三番目.md"]


def test_sync_page_prefix_changes_on_move(tasks, capsys, tmp_path):
    """move で queue_pos が変わると prefix も変わり、旧ファイルは消える。"""
    vault = _set_vault(tasks, tmp_path, capsys)
    tasks.run("add", "先頭に上げる")
    tid = json.loads(capsys.readouterr().out)["id"]
    tasks.run("add", "元は先頭")
    capsys.readouterr()
    # 初期状態: 010_先頭に上げる.md, 020_元は先頭.md
    assert (vault / "tasks" / "010_先頭に上げる.md").exists()
    tasks.run("reorder", tid, "--head")
    capsys.readouterr()
    names = {p.name for p in (vault / "tasks").glob("*.md")}
    # 「先頭に上げる」が先頭 (queue_pos が最小) に来て prefix が変わる。
    top = tasks.by_title("先頭に上げる")["queue_pos"]
    other = tasks.by_title("元は先頭")["queue_pos"]
    assert top < other
    assert f"{top:03d}_先頭に上げる.md" in names
    # 旧ファイル名 (020_先頭に上げる.md のような別 prefix) は残らない。
    stale = [
        n
        for n in names
        if n.endswith("先頭に上げる.md") and not n.startswith(f"{top:03d}_")
    ]
    assert stale == []


def test_sync_removes_page_on_done(tasks, capsys, tmp_path):
    vault = _set_vault(tasks, tmp_path, capsys)
    tasks.run("add", "終わらせるタスク")
    tid = json.loads(capsys.readouterr().out)["id"]
    page = vault / "tasks" / "010_終わらせるタスク.md"
    assert page.exists()
    tasks.run("update", tid, "--status", "done")
    capsys.readouterr()
    assert not page.exists()


def test_sync_removes_page_on_delete(tasks, capsys, tmp_path):
    vault = _set_vault(tasks, tmp_path, capsys)
    tasks.run("add", "消すタスク")
    tid = json.loads(capsys.readouterr().out)["id"]
    page = vault / "tasks" / "010_消すタスク.md"
    assert page.exists()
    tasks.run("delete", tid)
    capsys.readouterr()
    assert not page.exists()


def test_sync_removes_page_with_long_title_and_url(tasks, capsys, tmp_path):
    """title と source_url が長く managed_by が先頭付近に無くても削除される。"""
    vault = _set_vault(tasks, tmp_path, capsys)
    long_title = (
        "daily-cockpit Argo CD Application 追加 (project #2140) — レビュー (Reviewer)"
    )
    tasks.run(
        "add",
        long_title,
        "--from",
        "others",
        "--source",
        "github",
        "--source-url",
        "https://github.com/example/project/pull/2140#pullrequestreview-4614579819",
    )
    tid = json.loads(capsys.readouterr().out)["id"]
    files_before = list((vault / "tasks").glob("*.md"))
    assert len(files_before) == 1
    tasks.run("update", tid, "--status", "done")
    capsys.readouterr()
    # done でページが消える（managed_by が先頭 400 文字より後ろでも拾える）。
    assert list((vault / "tasks").glob("*.md")) == []


def test_sync_keeps_pending_page(tasks, capsys, tmp_path):
    vault = _set_vault(tasks, tmp_path, capsys)
    tasks.run("add", "ブロック中", "--blocked-by", "https://example.com/pr/1")
    capsys.readouterr()
    # blocked-by で pending になる。pending もページを出す。
    page = vault / "tasks" / "010_ブロック中.md"
    assert page.exists()
    assert "status: pending" in page.read_text(encoding="utf-8")


def test_sync_keeps_in_progress_page(tasks, capsys, tmp_path):
    vault = _set_vault(tasks, tmp_path, capsys)
    tasks.run("add", "着手中タスク")
    tid = json.loads(capsys.readouterr().out)["id"]
    tasks.run("update", tid, "--status", "in-progress")
    capsys.readouterr()
    page = vault / "tasks" / "010_着手中タスク.md"
    assert page.exists()
    assert "status: in-progress" in page.read_text(encoding="utf-8")


def test_page_tags_in_frontmatter(tasks):
    """tags を持つタスクはフロントマターに tags を出す（グラフの辺の源泉）。

    add コマンドはタグを付けないので、ページ生成関数を直接検証する。
    """
    page = tasks.module._obsidian_page(
        {
            "id": "abcd1234",
            "title": "タグ付き",
            "status": "open",
            "from": "me",
            "source": "notion",
            "source_url": None,
            "due": None,
            "queue_pos": 10,
            "snooze_until": None,
            "notes": "",
            "blocked_by": None,
            "blocks": [],
            "created_at": "2026-07-03T09:00:00",
            "updated_at": "2026-07-03T09:00:00",
            "tags": ["TASK-103", "onboarding"],
        }
    )
    assert "tags:" in page
    assert "- TASK-103" in page
    assert "- onboarding" in page


def test_page_aliases_include_id(tasks):
    """aliases に id を入れる（クイックスイッチャー・`[[` 補完での検索用）。

    Obsidian のウィキリンクはファイル名でのみ解決され、aliases では解決されない。
    デイリーノートからは `[[tasks/<ファイル名>|<id>]]` 形式でリンクする（todo
    スキル参照）。alias の id は `[[` の入力補完で id からこのページを探せる
    ようにするためのもの。
    """
    page = tasks.module._obsidian_page(
        {
            "id": "abcd1234",
            "title": "エイリアス確認",
            "status": "open",
            "from": "me",
            "source": "notion",
            "source_url": None,
            "due": None,
            "queue_pos": 10,
            "snooze_until": None,
            "notes": "",
            "blocked_by": None,
            "blocks": [],
            "created_at": "2026-07-03T09:00:00",
            "updated_at": "2026-07-03T09:00:00",
            "tags": [],
        }
    )
    # aliases は title と id の2つ。id は生の8桁でそのまま alias にする。
    assert "aliases:" in page
    assert '  - "エイリアス確認"' in page
    assert "  - abcd1234" in page


def test_page_title_with_special_chars_yaml_safe(tasks):
    """title に # : [ を含んでも YAML が壊れないようクオートされる。"""
    page = tasks.module._obsidian_page(
        {
            "id": "abcd1234",
            "title": "#alerts: 整理 [WIP]",
            "status": "open",
            "from": "me",
            "source": "local",
            "source_url": None,
            "due": None,
            "queue_pos": 10,
            "snooze_until": None,
            "notes": "",
            "blocked_by": None,
            "blocks": [],
            "created_at": "2026-07-03T09:00:00",
            "updated_at": "2026-07-03T09:00:00",
            "tags": [],
        }
    )
    assert 'title: "#alerts: 整理 [WIP]"' in page
    assert "# #alerts: 整理 [WIP]" in page  # H1 は生の title


def test_sync_skipped_when_vault_unset(tasks, capsys, tmp_path):
    """vault 未設定なら同期は走らない。"""
    tasks.run("add", "同期されないタスク")
    capsys.readouterr()
    assert not (tmp_path / "vault").exists()


def test_sync_does_not_touch_handwritten_notes(tasks, capsys, tmp_path):
    """tasks/ 配下だけ掃除し、vault の他ファイルは残す。"""
    vault = _set_vault(tasks, tmp_path, capsys)
    welcome = vault / "ようこそ.md"
    welcome.write_text("手書き", encoding="utf-8")
    tasks.run("add", "何か")
    tid = json.loads(capsys.readouterr().out)["id"]
    tasks.run("delete", tid)
    capsys.readouterr()
    # tasks 配下は掃除されるが、vault 直下の手書きは無事。
    assert welcome.exists()
    assert welcome.read_text(encoding="utf-8") == "手書き"


# ---------- vaultのGitバックアップ（機能D） ----------


def _git(vault, *argv):
    return subprocess.run(
        ["git", "-C", str(vault), *argv], check=False, capture_output=True, text=True
    )


def _init_vault_repo(tmp_path):
    vault = tmp_path / "vault"
    vault.mkdir()
    _git(vault, "init")
    _git(vault, "config", "user.name", "test")
    _git(vault, "config", "user.email", "test@example.com")
    # push が origin 無しで失敗しても握りつぶされる。commit だけ検証する。
    return vault


def _commit_count(vault):
    r = _git(vault, "rev-list", "--count", "HEAD")
    return int(r.stdout.strip()) if r.returncode == 0 else 0


def test_vault_backup_commits_changes(tasks, tmp_path):
    vault = _init_vault_repo(tmp_path)
    (vault / "daily").mkdir()
    (vault / "daily" / "2026-07-03.md").write_text("x", encoding="utf-8")
    tasks.module._backup_vault_to_git(vault)
    assert _commit_count(vault) == 1
    r = _git(vault, "log", "-1", "--pretty=%s")
    # コミットメッセージは代表ファイル名 + 件数で決定論的に組む。1ファイルなら
    # そのファイル名だけを名指しする。
    assert r.stdout.strip() == "chore: 2026-07-03.md を更新する"


def test_vault_backup_no_commit_when_clean(tasks, tmp_path):
    vault = _init_vault_repo(tmp_path)
    (vault / "a.md").write_text("x", encoding="utf-8")
    tasks.module._backup_vault_to_git(vault)
    n1 = _commit_count(vault)
    # 変化が無ければ空 commit を作らない。
    tasks.module._backup_vault_to_git(vault)
    assert _commit_count(vault) == n1


def test_vault_backup_pushes_clean_repo(tasks, tmp_path):
    vault = _init_vault_repo(tmp_path)
    remote = tmp_path / "remote.git"
    subprocess.run(["git", "init", "--bare", str(remote)], check=True)
    (vault / "a.md").write_text("backup", encoding="utf-8")
    assert _git(vault, "add", "a.md").returncode == 0
    assert _git(vault, "commit", "-m", "initial").returncode == 0
    assert _git(vault, "remote", "add", "origin", str(remote)).returncode == 0
    branch = _git(vault, "branch", "--show-current").stdout.strip()
    assert _git(vault, "config", f"branch.{branch}.remote", "origin").returncode == 0
    assert (
        _git(
            vault, "config", f"branch.{branch}.merge", f"refs/heads/{branch}"
        ).returncode
        == 0
    )
    assert tasks.module._backup_vault_to_git(vault) is True
    assert (
        _git(remote, "rev-parse", f"refs/heads/{branch}").stdout
        == _git(vault, "rev-parse", "HEAD").stdout
    )


def test_vault_backup_reports_push_failure(tasks, tmp_path, capsys):
    vault = _init_vault_repo(tmp_path)
    (vault / "a.md").write_text("backup", encoding="utf-8")
    assert tasks.module._backup_vault_to_git(vault) is False
    assert "No configured push destination" in capsys.readouterr().err


def test_vault_backup_does_not_remove_existing_index_lock_by_default(
    tasks, tmp_path, capsys
):
    vault = _init_vault_repo(tmp_path)
    lock = vault / ".git" / "index.lock"
    lock.write_text("active Git operation", encoding="utf-8")

    assert tasks.module._backup_vault_to_git(vault) is False

    assert lock.exists()
    err = capsys.readouterr().err
    assert "index.lock" in err
    assert "--remove-index-lock" in err


def test_vault_backup_reports_when_explicitly_removing_index_lock(
    tasks, tmp_path, capsys
):
    vault = _init_vault_repo(tmp_path)
    remote = tmp_path / "remote.git"
    subprocess.run(["git", "init", "--bare", str(remote)], check=True)
    (vault / "base.md").write_text("base", encoding="utf-8")
    assert _git(vault, "add", "base.md").returncode == 0
    assert _git(vault, "commit", "-m", "init").returncode == 0
    branch = _git(vault, "branch", "--show-current").stdout.strip()
    assert _git(vault, "remote", "add", "origin", str(remote)).returncode == 0
    assert _git(vault, "push", "-u", "origin", branch).returncode == 0

    lock = vault / ".git" / "index.lock"
    lock.write_text("stale lock", encoding="utf-8")

    assert tasks.module._backup_vault_to_git(vault, remove_index_lock=True) is True

    assert not lock.exists()
    assert "削除しました" in capsys.readouterr().err


def test_vault_backup_parser_exposes_explicit_lock_removal(tasks):
    args = tasks.module.build_parser().parse_args(
        ["vault-backup", "--remove-index-lock"]
    )

    assert args.remove_index_lock is True


def test_vault_backup_skips_uninitialized(tasks, tmp_path):
    vault = tmp_path / "vault"
    vault.mkdir()
    (vault / "a.md").write_text("x", encoding="utf-8")
    # git 未初期化 → 何もしない・例外を投げない。
    tasks.module._backup_vault_to_git(vault)
    assert not (vault / ".git").exists()


def test_vault_backup_skips_when_none(tasks):
    # vault 未設定（None）→ 何もしない。
    tasks.module._backup_vault_to_git(None)


def test_vault_backup_stages_all_files(tasks, tmp_path):
    """diff 問わず全ステージ（新規ファイルも拾う）。"""
    vault = _init_vault_repo(tmp_path)
    (vault / "tasks").mkdir()
    (vault / "tasks" / "abc.md").write_text("task", encoding="utf-8")
    (vault / "Inbox.md").write_text("inbox", encoding="utf-8")
    tasks.module._backup_vault_to_git(vault)
    tracked = _git(vault, "ls-files").stdout.split()
    assert "tasks/abc.md" in tracked
    assert "Inbox.md" in tracked


# ---------- Day Plannerの出勤時刻検査（機能E） ----------


def _frozen_date(year, month, day):
    class _D(date):
        @classmethod
        def today(cls):
            return cls(year, month, day)

    return _D


def _write_today_note(
    tasks, tmp_path, monkeypatch, capsys, body, year=2026, month=7, day=27
):
    vault = _set_vault(tasks, tmp_path, capsys)
    monkeypatch.setattr(tasks.module, "date", _frozen_date(year, month, day))
    daily_dir = vault / "daily"
    daily_dir.mkdir(parents=True, exist_ok=True)
    note = daily_dir / f"{year:04d}-{month:02d}-{day:02d}.md"
    note.write_text(body, encoding="utf-8")
    return vault, note


def test_update_done_blocked_when_clock_in_open(tasks, capsys, tmp_path, monkeypatch):
    """clock-in 中（end 無し）のタスクは done 化を拒否し、ステータスを変えない。"""
    tasks.run("add", "計測タスク")
    tid = json.loads(capsys.readouterr().out)["id"]
    body = (
        "## 今日の予定\n\n"
        f"- [ ] 15:00 - 15:30 計測タスク ({tid}・me・XL)\n"
        "  ```yaml\n"
        "  planner:\n"
        "    log:\n"
        "      - start: 2026-07-27 15:10:45\n"
        "  ```\n"
    )
    _write_today_note(tasks, tmp_path, monkeypatch, capsys, body)
    with pytest.raises(SystemExit):
        tasks.run("update", tid, "--status", "done")
    err = capsys.readouterr().err
    assert "clock-in" in err
    tasks.run("get", tid)
    got = json.loads(capsys.readouterr().out)
    assert got["status"] == "open"


def test_update_done_allowed_when_clock_out(tasks, capsys, tmp_path, monkeypatch):
    """clock-out 済み（end あり）なら done 化を通す。"""
    tasks.run("add", "計測タスク")
    tid = json.loads(capsys.readouterr().out)["id"]
    body = (
        "## 今日の予定\n\n"
        f"- [ ] 15:00 - 15:30 計測タスク ({tid}・me・XL)\n"
        "  ```yaml\n"
        "  planner:\n"
        "    log:\n"
        "      - start: 2026-07-27 15:10:45\n"
        "        end: 2026-07-27 15:11:57\n"
        "  ```\n"
    )
    _write_today_note(tasks, tmp_path, monkeypatch, capsys, body)
    tasks.run("update", tid, "--status", "done")
    out = json.loads(capsys.readouterr().out)
    assert out["status"] == "done"


def test_update_done_allowed_when_no_clock_block(tasks, capsys, tmp_path, monkeypatch):
    """打刻ブロックが無いタスク行は従来どおり done 化できる。"""
    tasks.run("add", "計測タスク")
    tid = json.loads(capsys.readouterr().out)["id"]
    body = f"## 今日の予定\n\n- [ ] 15:00 - 15:30 計測タスク ({tid}・me・XL)\n"
    _write_today_note(tasks, tmp_path, monkeypatch, capsys, body)
    tasks.run("update", tid, "--status", "done")
    out = json.loads(capsys.readouterr().out)
    assert out["status"] == "done"


def test_update_done_allowed_when_no_daily_note(tasks, capsys, tmp_path, monkeypatch):
    """今日のデイリーノートが無ければガード自体をスキップし done 化を通す。"""
    _set_vault(tasks, tmp_path, capsys)
    monkeypatch.setattr(tasks.module, "date", _frozen_date(2026, 7, 27))
    tasks.run("add", "計測タスク")
    tid = json.loads(capsys.readouterr().out)["id"]
    tasks.run("update", tid, "--status", "done")
    out = json.loads(capsys.readouterr().out)
    assert out["status"] == "done"


def test_update_done_allowed_when_vault_unset(tasks, capsys):
    """vault 未設定ならガード自体をスキップする。"""
    tasks.run("add", "計測タスク")
    tid = json.loads(capsys.readouterr().out)["id"]
    tasks.run("update", tid, "--status", "done")
    out = json.loads(capsys.readouterr().out)
    assert out["status"] == "done"


def test_find_open_clock_in_line_detects_missing_end(tasks):
    f = tasks.module._find_open_clock_in_line
    text = (
        "- [ ] 15:00 - 15:30 計測タスク (abcd1234・me・XL)\n"
        "  ```yaml\n"
        "  planner:\n"
        "    log:\n"
        "      - start: 2026-07-27 15:10:45\n"
        "  ```\n"
    )
    line = f(text, "abcd1234")
    assert line is not None
    assert "計測タスク" in line


def test_find_open_clock_in_line_none_when_closed(tasks):
    f = tasks.module._find_open_clock_in_line
    text = (
        "- [ ] 15:00 - 15:30 計測タスク (abcd1234・me・XL)\n"
        "  ```yaml\n"
        "  planner:\n"
        "    log:\n"
        "      - start: 2026-07-27 15:10:45\n"
        "        end: 2026-07-27 15:11:57\n"
        "  ```\n"
    )
    assert f(text, "abcd1234") is None


def test_find_open_clock_in_line_none_when_id_absent(tasks):
    f = tasks.module._find_open_clock_in_line
    text = "- [ ] 15:00 - 15:30 計測タスク (abcd1234・me・XL)\n"
    assert f(text, "abcd1234") is None
    assert f(text, "zzzz9999") is None
