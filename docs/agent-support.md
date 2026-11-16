# Coding Agentsの対応方針

## 2026年11月17日の決定

このdotfilesはCodexとOpenCodeの両方で共通指示とスキルを使える状態を目指す。どちらか一方に限定する必要が生じた場合は、OpenCode向けを優先する。

共通指示の実体は`agents/AGENTS.md`、スキルの実体は`.agents/skills/`で管理する。miseで各ツールのグローバル探索先へ配置し、ツールごとの設定はそれぞれの形式で管理する。OpenCodeは[`~/.config/opencode/AGENTS.md`とグローバルスキル探索先](https://opencode.ai/docs/instructions/)をサポートし、Codexは[AGENTS.mdと共通スキルの配置](https://developers.openai.com/codex/skills)をサポートする。

ツール固有の機能は、それぞれの設定として維持する。共通指示やスキルと異なるイベント形式を持つhookを、同一の登録設定で使えるとは扱わない。
