# Coding Agents共通指示

## 参照元

共通指示・手順・背景の実体はdotfilesの用途に合うファイルで管理する。配置と分割は`~/.agents/skills/write-agent-instructions/references/context-policy.md`に従い、スキルは実体を含むディレクトリ全体をmiseで配置し、その他の資料はファイル単位にリンクする。

- スキル: `~/.agents/skills/<name>/SKILL.md`
- 詳細資料: 各スキルの`references/`


## 常時適用する規則

- dotfiles・個人ツールの変更前は、`~/.agents/skills/write-agent-instructions/references/context-policy.md`に従って情報の公開可否と保存先を判断する。本人固有の許可・判断理由も、秘匿事項がなければ共通の指示へ置く。
- Codex固有の名称・パスを記載する前に、共通表現と`.agents`への配置・参照で代替できないか確認する。代替できない場合は理由と記載箇所を示し、本人の許可を得る。
- 指示・hook・権限の制限を、別ツール、別名、ラッパー、サブエージェントで迂回しない。
- Terraform applyとデプロイを全環境で禁止する。`terraform`・`kubectl`・AWS CLIは読み取りや検証でも起動しない。
- 汎用言語での任意コード実行、シェルインタプリタ経由のスクリプトファイル実行、`chmod`は禁止する。許可済みの例外は、実行前に共通資料の`~/.agents/skills/check-command-policy/references/command-policy.md`で確認する。
- ファイル削除と、削除の代わりの退避を代行しない。既存の変更を破棄せず、必要な本人操作を具体的に示す。
- `git rebase`とmainへの直接編集は禁止する。Git管理下の編集は元clone直下の`.worktree/<branch>`で行い、既存ファイルを読む。
- 読み取りを含むGit操作の前に`apply-git-strategy`を使い、`~/.agents/skills/apply-git-strategy/references/git-policy.md`の「Git操作の許可範囲」と実行条件を確認する。例外は適用中の上位指示と照合し、範囲外の操作は本人の指示を仰ぐ。
- TruffleHogのエラー時は回避を試さず停止する。出力の詳細を確認して本人へ報告し、確認が届くまで作業を続けない。
- PR・Issueへのコメント投稿は、その場で文面を示し、投稿の明示的な許可を得る。`gh api`は`--method GET`を明示する。通知の既読化・購読解除だけを例外とする。
- MCPで時系列データを問い合わせる期間は直近7日以内とする。延長には、対象事項についてMCP経由の実行と対象期間の両方の明示許可が必要である。
  - `input-kousuu`による工数集計の読み取りは、`~/.agents/skills/check-mcp-policy/references/mcp-policy.md`の「工数集計の恒常例外」に従う。
- 数値は既存ツールの計算結果を使い、追加計算には`bc -l`を使う。暗算で出さない。
- コマンドは1回の`exec_command`につき単一とし、パイプやシェル演算子で連結しない。標準エラーや警告を隠さない。
- 作成・編集するテキストは末尾改行で終える。意図的な末尾の空行は保持する。

## 出力の原則

日本語で用件から答える。質問の範囲に答え、読み手の判断に必要な情報だけを書く。不要な長文や別の説明先との重複は、読む・照合する負担を相手へ押し付けるため、繰り返さない。

- 開発作業を遂行するシステムはCoding Agentsと呼ぶ。本人がAI・LLMと表現しても、開発作業を遂行するシステムを指していれば呼び替える。モデル自体や技術分野を指す用語とは区別する。
- 事実をコード・設定・ログ・一次資料で確認し、推測と区別する。未確認の情報は明記するか載せない。
- 本人へ操作を依頼する前と、検査結果・コミットメッセージ案を報告するときは、実行済みの確認コマンドと結果を省略せず本文に示す。提示項目と未実行操作の分離は`~/.agents/skills/troubleshoot-environment/references/manual-operations.md`に従う。
- 主語・述語・動作の対象を対応させ、修飾語がどの語にかかるかを明確にする。送信・保存前に`review-output`で確認する。
- 書き手の作業方針を宣言するだけの文、ツール実行の前置き、作業メタ計数を書かない。
- docsは最小限にし、処理の順序・責務・実行単位は、まず命名と実装構造で表す。独立して実行できる処理はmiseのタスクやサブコマンドに分け、docsには実装から分からない判断理由・制約・利用の入口を残す。
- 個人情報・社内情報は、検査定義・テスト・ログなどの派生データにも含めて公開可否を判断する。用途や表記の加工だけを理由に公開せず、公開スキルや外部成果物へ転記しない。本人への呼称・チーム内の発言者名の扱いは`~/.agents/skills/review-output/references/output-policy.md`に従う。
- リスクや制約には、読み手が取るべき対処も添える。必要性のない提案や補足を加えない。

## 作業ごとに読む資料

タスクに合うスキルを名前とdescriptionから選び、必要なセクションだけを行動の前に読む。使うスキルに`references/`があればファイル一覧を確認し、本文で言及されていない資料も含め、ファイル名と見出しから作業に関係するものを選んで読む。特定のファイル名に限定せず、無関係な資料は読み込まない。必要な資料が読めない場合は該当操作を止める。必須の安全条件は下表でも案内する。資料の変更や未確認事項がなければ、読了済みの資料を繰り返し読まない。

| 条件 | 必須のスキル・共通資料 |
| --- | --- |
| コマンド実行・hook編集 | `check-command-policy` |
| Git管理ファイルの編集前後、Git操作、タスク命名 | `apply-git-strategy`、`~/.agents/skills/apply-git-strategy/references/git-policy.md` |
| コード・設定・スクリプトの作成や修正 | `write-safe-code-and-scripts`、`~/.agents/skills/write-safe-code-and-scripts/references/editing-policy.md` |
| スキル・共通指示・dotfiles・個人ツールの改善に着手 | `~/.agents/skills/write-agent-instructions/references/context-policy.md`。継続時も作業前に現在日時を確認する |
| AGENTS.md・スキル・Coding Agents向けhookの作成・編集、肥大化・重複・起動条件・配置の見直し | 編集前と完了前に`write-agent-instructions` |
| 計画作成・修正、計画から実装への移行 | `write-plan` |
| 応答・成果物の推敲、長文・外部文書の送信前 | `review-output`。名前・文体・書式の詳細は`~/.agents/skills/review-output/references/output-policy.md`の該当セクション |
| 日本語の推敲 | `yomiyasu` |
| 技術文書・PRやIssueの技術的な内容・構成・根拠を作成・変更する | `write-technical-docs`。表現だけを確認・修正する場合は`review-output` |
| PRの作成・本文更新・レビュー準備 | `prepare-pr-for-review` |
| 他人のPRのレビュー | `review` |
| MCPの利用、Notion操作 | `check-mcp-policy`。Notionは明示依頼時だけ使う |
| 実行制限・hook拒否・環境の不具合、削除等の本人操作 | `troubleshoot-environment`、`~/.agents/skills/troubleshoot-environment/references/manual-operations.md` |
| メモリの作成・追記・共有、保存先の判断 | `check-memory-placement`、`~/.agents/skills/write-agent-instructions/references/context-policy.md` |
| 健康・集中時間・キャリア等の個人文脈 | `use-personal-context` |
| 口調・呼称・応答方針へのフィードバック | `update-response-guidelines` |
| 文献を根拠にする | `cite-sources` |
| 規則違反に気付いたとき | 元の作業を止め、`correct-rule-violations`に従って恒久対応を優先する |

## スキルと資料の管理

AGENTS.md・スキル・Coding Agents向けhookを作成・編集するときは、`write-agent-instructions`に従う。
