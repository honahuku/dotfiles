# dotfilesの配置

mise 2026.10.17以降と、[セットアップの前提](setup.md)が必要である。このrepoを作業ディレクトリにする。

```sh
# 配置予定と競合を確認してから、設定と管理対象ツールを導入する。
mise run setup
```

Windows同期は最後に`mise run windows:sync`で行う。初回に確認した保存先は`~/.local/share/dotfiles/windows/chezmoi.toml`へ保存する。

スキルだけを導入・再配置する場合は`mise run skills:install`、設定全体は`mise run setup:files`を使う。取得物への独自編集は同期前に管理元へ取り込む。タスクを取り込む構成では、利用側で`skills:install`を定義して取得・配置・検査を行う。

## 通常更新

```sh
# Linux / WSL側を更新する。
mise dot apply
```

削除やリンク先の置換を含む場合は、先に`mise run setup:check`で対象を確認する。`--force`・`--prune`は通常更新に使わない。

## 競合で停止したとき

- Linux側：既存ファイルやリンク元を確認し、必要な内容を管理元へ取り込む。不要と判断した旧リンクだけを手動で削除し、再実行する。`.bashrc`・`.profile`の実ファイルと`~/.codex/skills/.system`は削除しない。
- Windows側：`mise run windows:diff`で差分を確認し、変更対象と差分の内容をユーザーに示して判断を求める。原本へ取り込む、共通設定を適用する、適用を保留する、のどれにするかユーザーが決めるまで、原本の編集やWindows側への適用は行わない。判断を受けて必要な変更を原本へ反映した後、`mise dot apply`で同期元を更新し、`mise run windows:sync`を実行する。差が残る場合もユーザーの判断を確認し、適用する場合は対話端末で`mise run windows:resolve`を使う。

Windows側で停止しても、先行する配置は完了している場合がある。設定編集を終えてから適用し、終了状態と差分を確認する。中間ファイルは再生成されるため、直接編集しない。

## 配置を変更する

取得元と配置先は[`mise.toml`](../mise.toml)、処理は[`mise-tasks.toml`](../mise-tasks.toml)で管理する。設定方法は[miseの管理ファイル](https://mise.jdx.dev/dotfiles/managed.html)と[グループ](https://mise.jdx.dev/dotfiles/groups.html)を参照する。

Windowsの対象はCodex共通指示とインストール済みのTerminal設定である。保存先はWindowsホーム配下に限る。Codexの保存先を変える場合は、初回セットアップ時に環境変数`DOTFILES_WINDOWS_CODEX_HOME`で指定する。設定済みの対象や保存先を変更する場合は、移行先と既存ファイルを確認してから適用する。

## 共通指示・スキル

汎用手順と自作スキルはこのrepoで管理する。内容を生成してホームにだけ保存せず、リンク元をrepoにコミットする。

| 配置先                              | 管理元                                                                          |
| ----------------------------------- | ------------------------------------------------------------------------------- |
| `~/.codex/AGENTS.md`                | 公開側の`.agents/AGENTS.md`                                                     |
| `~/.agents/skills/` | 自作スキルとvendir取得先を含む`.agents/skills/`全体へのリンク |
| `~/.agents/hooks/`                  | 公開側の共通判定。登録方法と確認手順は[共通hook](../.agents/hooks/README.md)を参照 |
| `~/.agents/prh/`                    | 公開側の技術日本語ルール                                                        |
| `~/.codex/config.toml` | このrepoの汎用設定 |

取得スキルと自作版の名前が衝突する場合は、自作版を別名にする。

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

禁止語の基本定義は`config/public-forbidden-patterns.txt`を常に読む。追加定義はmiseで配置する`~/.config/dotfiles/public-forbidden-patterns.txt`を読み、別の定義を使う場合だけ`DOTFILES_FORBIDDEN_PATTERNS_FILE`で指定する。基本定義・追加定義の欠落や空ファイルは検査失敗とする。

手動検査は`./bin/check-public-candidate.sh --all`、変更範囲だけなら`--worktree`を使う。日本語の自動検査は英語だけの説明行を検出する補助であり、翻訳の正確さは原文と照合する。

Codex設定は任意の別ファイルを自動結合せず、このrepoの`config.toml`を使う。

共通資料・判定処理は`.agents`へ集約する。ツールが読む`~/.codex/AGENTS.md`は共通指示へのリンク、`~/.codex/config.toml`は固有の設定入口とする。[指示ファイルの探索仕様](https://developers.openai.com/codex/guides/agents-md)に合わせ、fallback設定は空にする。
