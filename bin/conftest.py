"""tasks CLIのテストで共有するpytestフィクスチャ（tasksのローカル保存先）。

分野ごとにテストを分け、別分野の同時編集が衝突しにくくする。
    test_tasks_crud.py      追加・一覧・更新・順序変更・削除・メタデータ・
                           snooze・移行・依存関係
    test_tasks_worklog.py   作業記録・ペース補正・フレックス・今日の予定・時間集計
    test_tasks_github.py    _gh_*の補助関数・長期停滞の再開・不正なJSON
    test_tasks_obsidian.py  ページ同期・デイリーノート・コミットメッセージ・vault保存
    test_tasks_daily.py     日次記録・通知キー

毎回、全テストを実行する。
    uv run --with pytest pytest .

分野をまたぐ補助関数は_test_helpers.pyに置き、一分野でしか使わない関数は
各テストファイルに置く。すべてのテストでTASKS_STOREを
pytestのtmp_pathへ向け、実際の~/.local/share/tasks/tasks.jsonには触れない。

tasksには.py拡張子がないため、importlibでモジュールとして読み込む。
一時保存先はGitリポジトリではなく、テストからpushも行わないため、
_backup_to_gitを無効化する。
"""

import json

import pytest
from _test_helpers import _load_tasks_module


@pytest.fixture
def tasks(tmp_path, monkeypatch):
    """一時的な保存先につないだ、新しく読み込んだtasksモジュール。

    .run(*argv)でCLIを呼び出し、.store()で保存されたJSONを読み出す
    補助オブジェクトを返す。
    """
    store = tmp_path / "tasks.json"
    monkeypatch.setenv("TASKS_STORE", str(store))

    mod = _load_tasks_module()
    # モジュールは読み込み時に設定済みの環境変数からSTOREを取得するため、
    # 既にtmp_pathを参照しているが、念のため参照先を明示的に設定する。
    mod.STORE = store
    # テスト中のGit操作を防ぐ。save()は_backup_to_git(message=...)を呼ぶため、
    # スタブでも引数を受け取る。_backup_vault_to_gitはスタブ化しない。
    # vault未設定の場合（大半のテスト）やGitリポジトリではない場合には
    # 途中で戻る（obsidian_vault_dirに通常の一時ディレクトリを設定するテスト）。
    # そのため、この関数からGit操作は実行されない。機能Dのテストでは、
    # Git初期化済みの一時vaultで実際の関数を直接検証する。
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
            """進行可能なタスクをqueue_posの昇順で返す。"""
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
            """キューの順序で(title, queue_pos)の一覧を返す。"""
            return [(t["title"], t["queue_pos"]) for t in self.active()]

    return Harness()
