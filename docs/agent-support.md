# Coding Agentsの対応方針

## 2026年11月17日の決定

このdotfilesで導入・バージョン管理するCoding AgentはOpenCodeとする。共通指示とスキルはOpenCodeから利用できる形で配置する。

共通指示の実体は`.agents/AGENTS.md`、スキルの実体は`.agents/skills/`で管理する。miseでOpenCodeのグローバル指示先へ配置し、OpenCodeは`.agents/skills`のグローバル互換探索先からスキルを読み込む。

ツール固有の機能は、それぞれの設定として維持する。共通指示やスキルと異なるイベント形式を持つhookを、同一の登録設定で使えるとは扱わない。
