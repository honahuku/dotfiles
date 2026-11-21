# dotfilesの配置

mise 2026.10.17以降と、[セットアップの前提](setup.md)が必要である。OSに応じて`linux/`または`windows/`を作業ディレクトリとして使う。

```sh
# Linux
mise -C linux run setup

# Windows（PowerShell）
mise -C windows run setup
```

各OSはネイティブのmiseタスクから設定を同期する。変更後も同じセットアップタスクを繰り返し実行する。Windowsでは初回だけの設定ファイルを生成せず、毎回chezmoiで現在の管理元と照合する。

スキルだけを導入・再配置する場合は`mise run skills:install`、設定全体は`mise run setup:files`を使う。取得物への独自編集は同期前に管理元へ取り込む。タスクを取り込む構成では、利用側で`skills:install`を定義して取得・配置・検査を行う。

## 通常更新

```sh
# Linux設定を更新する。
mise -C linux dot apply
```

削除やリンク先の置換を含む場合は、先に`mise run setup:check`で対象を確認する。`--force`・`--prune`は通常更新に使わない。

## 競合で停止したとき

- Linux側：`mise -C linux dot diff`で差分を確認する。必要な変更を管理元へ取り込み、同じセットアップタスクを再実行する。
- Windows側：`mise -C windows run windows:diff`で差分を確認する。既存ファイルを上書きせず、必要な変更を管理元へ取り込んでから`mise -C windows run windows:sync`を再実行する。

一部の配置後に停止しても、反映済みの設定は残る。変更を管理元へ取り込み、同じセットアップタスクを再実行して状態を確認する。

## 配置を変更する

共通の取得元と配置先は[`mise.toml`](../mise.toml)、Linux固有設定は[`linux/mise.toml`](../linux/mise.toml)、Windows固有設定とタスクは[`windows/mise.toml`](../windows/mise.toml)・[`windows/mise-tasks.toml`](../windows/mise-tasks.toml)で管理する。設定方法は[miseの管理ファイル](https://mise.jdx.dev/dotfiles/managed.html)と[グループ](https://mise.jdx.dev/dotfiles/groups.html)を参照する。

Windows側は共通指示と、インストール済みWindows Terminalの設定を管理する。Windows固有のパス解決はPowerShellとchezmoiが行う。

## 共通指示・スキル

汎用手順と自作スキルはこのrepoで管理する。内容を生成してホームにだけ保存せず、リンク元をrepoにコミットする。

| 配置先                         | 管理元                                                                                   |
| ------------------------------ | ---------------------------------------------------------------------------------------- |
| `~/.codex/AGENTS.md`           | `.agents/AGENTS.md`                                                                      |
| `~/.config/opencode/AGENTS.md` | `.agents/AGENTS.md`                                                                      |
| `~/.agents/skills/`            | 自作スキルとvendir取得先を含む`.agents/skills/`全体へのリンク                            |
| `~/.agents/hooks/`             | `.agents/hooks/`の共通判定。登録方法と確認手順は[共通hook](../.agents/hooks/README.md)を参照 |
| `~/.agents/prh/`               | `.agents/prh/`の技術日本語ルール                                                          |

取得スキルと自作版の名前が衝突する場合は、自作版を別名にする。

OpenCodeの共通指示・スキル配置方針は[対応方針](agent-support.md)を参照する。

## スキルの配置と更新

スキルの編集元は`.agents/skills/`とする。`~/.agents/skills`はディレクトリ全体へのリンクとし、配下の`SKILL.md`は通常ファイルにする。取得物の更新はvendir定義とlockfileを一緒に反映する。初回の配置でホームの既存ディレクトリと競合した場合は、[競合で停止したとき](#競合で停止したとき)に従う。

## 外部スキルの取得範囲

追加・更新前に、取得する版のREADMEのInstall・Installationなどのセクションを読み、そのリポジトリが案内するインストール方法を選ぶ。手順だけでは配布範囲が分からない場合は、対応するインストーラーの実装、配布アーカイブ、プラグインのマニフェストを確認する。インストーラーを起動してホームを変更する必要はない。

vendirは、その方法で選択したスキルに配布されるファイル一式を取り込む。`SKILL.md`だけに限定せず、付属のagents定義・references・scripts・assets・ライセンスなども元の相対配置で保持する。ライセンス専用の取得先を別に作ることを既定にしない。配布範囲がスキルのディレクトリ全体なら、その配下をまとめて取得し、個々のファイル名を列挙しない。READMEがリポジトリ全体の配布を指定する場合は、その一式を保持する。

除外は、選んだインストール方法が除くファイルや、配布物に含まれないGit管理情報・生成キャッシュに限る。インストーラー側の除外を確認せずに独自の選別を増やさない。付属ファイルを省いて検査を通したり、ライセンスを削って取り込みを進めたりしない。取得版と配布範囲、元の相対パスをvendir定義とlockfileで対応させる。

現在の取得範囲は次の一次資料で確認した。`npx skills add`を選ぶ場合は、[コピー処理と除外定義](https://github.com/vercel-labs/skills/blob/a80e4c9d12d607631249d4d7d059f835d4b2f13a/src/installer.ts)も確認する。今後の更新時には、その時点の案内と実装を再確認する。

| 取得元 | 選んだ配布方法と範囲 |
| --- | --- |
| [mattpocock/skills](https://github.com/mattpocock/skills/blob/d81f3a183412e71a5b1e84ca21bc1a35eea03a60/README.md#installation-30-second-setup) | スキルを選択する`npx skills add`。選択したスキルのディレクトリ一式 |
| [nanaism/yomiyasu](https://github.com/nanaism/yomiyasu/blob/v1.1.2/README.md#インストール) | 推奨される`npx skills add`。`skills/yomiyasu/`一式 |
| [aws/agent-toolkit-for-aws](https://github.com/aws/agent-toolkit-for-aws#skills) | スキル導入用の`npx skills add`。選択したスキルのディレクトリ一式 |
| [wheresryan22/anatomy](https://github.com/wheresryan22/anatomy/blob/e6600ffc4e8e6620eeb45bf49bcdbd5e4b84163f/README.md#install) | `npx skills add`。examplesを含むリポジトリ一式 |
| [vercel-labs/skills](https://github.com/vercel-labs/skills/blob/13e4063a1cf913f5606d57d42ab83a86f5001e04/README.md#install-a-skill) | スキル選択用インストーラーの規則に従い、`skills/find-skills/`一式 |

## 取得物と自作スキルの検査

自作スキルの説明文と参照文書は日本語にする。コード・識別子・正式な出典名は維持する。Lefthookは公開候補のパスと内容全体に対して禁止語を検査し、自作スキルには日本語の検査も行う。`vendir.yml`と`vendir.lock.yml`の両方で定義された取得先は、この二つの検査から除外して上流の原文を保つ。秘密情報の検査は継続する。

禁止語の基本定義は`config/public-forbidden-patterns.txt`を常に読む。追加定義はmiseで配置する`~/.config/dotfiles/public-forbidden-patterns.txt`を読み、別の定義を使う場合だけ`DOTFILES_FORBIDDEN_PATTERNS_FILE`で指定する。基本定義は必須とし、追加定義が未配置なら基本定義だけで検査する。追加定義を明示指定した場合や配置済みの場合は、欠落・空ファイルを検査失敗とする。

手動検査は`./bin/check-public-candidate.sh --all`、変更範囲だけなら`--worktree`を使う。日本語の自動検査は英語だけの説明行を検出する補助であり、翻訳の正確さは原文と照合する。

共通資料・スキルは`.agents`へ集約し、OpenCodeは`~/.agents/skills`から読み込む。OpenCodeのグローバル権限設定は[設定ファイル](../.config/opencode/opencode.jsonc)で管理する。

旧配置の`~/.local/share/dotfiles/agents/skills`はmiseで撤去し、`.agents/skills`だけをスキルの管理元にする。
