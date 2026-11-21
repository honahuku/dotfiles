"""Renovate PR分析ワークフローの安全策を確認する。"""

import re
import tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "renovate-review.yml"


class RenovateReviewWorkflowTest(unittest.TestCase):
    def test_only_runs_for_same_repository_renovate_pull_requests(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")

        self.assertIn("pull_request_target:", workflow)
        self.assertIn("opened", workflow)
        self.assertIn("synchronize", workflow)
        self.assertIn("reopened", workflow)
        self.assertIn("ready_for_review", workflow)
        self.assertIn("github.event.pull_request.user.login == 'renovate[bot]'", workflow)
        self.assertIn(
            "github.event.pull_request.head.repo.full_name == github.repository",
            workflow,
        )
        self.assertIn("github.event.pull_request.draft == false", workflow)

    def test_codex_and_comment_jobs_use_separate_least_privilege_tokens(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")

        self.assertIn(
            "openai/codex-action@306c6a196a99dcc6582530c396a19d2672d5e9ec",
            workflow,
        )
        self.assertIn("permission-profile: renovate-readonly", workflow)
        self.assertIn("safety-strategy: drop-sudo", workflow)
        self.assertIn("contents: read", workflow)
        self.assertIn("issues: write", workflow)
        self.assertIn("pull-requests: read", workflow)
        self.assertNotIn("pull-requests: write", workflow)
        self.assertIn("needs: analyze", workflow)
        self.assertIn("secrets.OPENAI_API_KEY", workflow)

    def test_comment_is_scoped_to_head_sha_and_replaced_on_rerun(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")

        self.assertIn("head.sha", workflow)
        self.assertIn("renovate-review -->", workflow)
        self.assertIn("listComments", workflow)
        self.assertIn("updateComment", workflow)
        self.assertIn("createComment", workflow)

    def test_workflow_avoids_pull_request_target_and_shell_expression_injection(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")

        self.assertIn("pull_request_target:", workflow)
        self.assertIn("persist-credentials: false", workflow)
        self.assertIn('git fetch --no-tags origin "$PR_BASE_SHA" "$PR_HEAD_SHA"', workflow)
        self.assertIn("PR_TITLE: ${{ github.event.pull_request.title }}", workflow)
        self.assertIn("PR_BODY: ${{ github.event.pull_request.body }}", workflow)
        self.assertIn("CODEX_REVIEW: ${{ needs.analyze.outputs.review }}", workflow)
        self.assertNotIn('run: echo "${{ github.event.pull_request.title }}"', workflow)
        self.assertNotIn('run: echo "${{ github.event.pull_request.body }}"', workflow)

    def test_network_profile_is_read_only_and_has_no_wildcard_allow(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        config = re.search(
            r"cat > \"\$CODEX_HOME/config.toml\" <<'EOF'\n(.*?)\n\s+EOF",
            workflow,
            re.DOTALL,
        )
        self.assertIsNotNone(config)
        parsed = tomllib.loads(config.group(1))
        profile = parsed["permissions"]["renovate-readonly"]

        self.assertEqual(profile["extends"], ":read-only")
        self.assertTrue(profile["network"]["enabled"])
        self.assertNotIn("*", profile["network"]["domains"])

    def test_prompt_requires_japanese_summary_with_sources_and_limitations(self):
        prompt = (ROOT / ".github" / "prompts" / "renovate-review.md").read_text(
            encoding="utf-8"
        )

        for section in ("更新の概要", "互換性", "このリポジトリへの影響", "参照URL", "未検証"):
            with self.subTest(section=section):
                self.assertIn(section, prompt)

    def test_prompt_treats_pull_request_content_as_untrusted_and_forbids_writes(self):
        prompt = (ROOT / ".github" / "prompts" / "renovate-review.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("信頼できないデータ", prompt)
        self.assertIn("ファイルの作成・変更", prompt)
        self.assertIn("実行しない", prompt)


if __name__ == "__main__":
    unittest.main()
