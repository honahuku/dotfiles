# Personal agent guidance

## 共通ルール

- Git コミットは Conventional Commits 形式を使い、本文は可能な限り日本語にする。
- このファイルは dotfiles/.agents/AGENTS.md で管理し、各環境の Codex home からリンクする。
- 以下の環境別ルールは、コマンドを実行する環境に応じて適用する。

## Linux / WSL

- Do not add throwaway helper scripts or ad hoc programs unless the user explicitly approves them.
- This includes repository scripts and inline CI programs written in Bash, Ruby, Python, Node, or similar languages.
- Prefer built-in CI features and well-maintained existing Actions before adding custom logic.
- If custom logic is genuinely needed, explain why and ask for explicit approval before adding it.

- Do not request elevated permissions, broader tool access, authentication scope changes, or other privilege escalation unless the user explicitly instructs you to do so.
- If a task cannot be completed with the currently available permissions, stop and ask the user how to proceed before attempting any escalation.
- Treat unintended privilege escalation as dangerous; never assume approval from context or convenience.

## Windows / PowerShell

The following rules apply only when executing on native Windows.

### Python

When a Python command is needed in Codex on this machine, prefer the bundled Codex runtime executable instead of `python` or `py`. The global `python` currently resolves to the Microsoft Store app execution alias, and `py` may be unavailable inside the sandbox.

Use this executable:

`C:\Users\hona-desk\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe`

In PowerShell commands, invoke it like this:

`& 'C:\Users\hona-desk\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'`

### GitHub CLI (`gh`)

When using the GitHub CLI (`gh`), run it outside the Codex sandbox by requesting escalation (`sandbox_permissions: "require_escalated"`). The sandbox may not be able to read the host GitHub authentication state, so `gh` commands inside the sandbox can fail even when the user is already authenticated on the machine.

Prefer escalating the needed `gh` command with a concise justification over re-authenticating inside the sandbox. Use a narrowly scoped `prefix_rule` only when it matches the specific repeated workflow.

### File edits on Windows (`apply_patch` fallback)

On native Windows Codex sessions, `apply_patch` may fail before editing because of Windows sandbox issues, especially with `workspace-write`, `unelevated` restricted-token sandboxing, and split writable roots. Known related symptoms include:

- `failed to prepare windows sandbox wrapper`
- `windows unelevated restricted-token sandbox cannot enforce split writable root sets directly`
- `refusing to run unsandboxed`

When `apply_patch` fails this way, do not keep retrying it. Prefer this fallback order for ordinary text file edits:

1. Try a unified diff with `git apply --check`, then `git apply` if the check succeeds. This can modify untracked files and can also work outside a Git repository when used only against the working tree, as long as Git is available.
2. If `git apply` is unsuitable, use a small exact-match script that reads the file, verifies the target text occurs exactly as expected, writes the edited content, and then re-reads or diffs the result.
3. Avoid broad PowerShell regex replacements for non-trivial edits. `Set-Content` can change encoding, CRLF/LF, or add unwanted EOF blank lines, so verify with `git diff`, `git diff --check`, or an equivalent check after editing.

Keep edits minimal and local to the requested files. If a fallback requires writing outside the workspace, request escalation with a concise justification.

### Gitコミットメッセージ

- Conventional Commits形式を使う。
- prefix は英語でよいが、メッセージ本文は可能な限り日本語にする。
