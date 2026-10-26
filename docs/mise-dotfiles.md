# dotfilesの配置

mise 2026.10.17以降と、[セットアップの前提](setup.md)が必要である。このrepoを作業ディレクトリにする。

```sh
# 配置予定と競合を確認してから、設定と管理対象ツールを導入する。
mise run setup
```

Windows同期は最後に`mise run windows:sync`で行う。初回に確認した保存先は`~/.local/share/dotfiles/windows/chezmoi.toml`へ保存する。

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
| `~/.agents/docs/common/`             | 公開側の`docs/agents/`。miseの`public-agent-docs`グループでファイル単位にリンク |
| `~/.agents/skills/` | 自作スキルとvendir取得先 |
| `~/.agents/hooks/`                  | 公開側の共通判定。登録方法と確認手順は[共通hook](../.agents/hooks/README.md)を参照 |
| `~/.agents/prh/`                    | 公開側の技術日本語ルール                                                        |
| `~/.codex/config.toml` | このrepoの汎用設定 |

取得スキルと自作版の名前が衝突する場合は、自作版を別名にする。

自作スキルの説明文と参照文書は日本語にする。コード・識別子・正式な出典名は維持する。Lefthookは公開候補のパスと内容全体に対して禁止語を検査し、自作スキルには日本語の検査も行う。`vendir.yml`と`vendir.lock.yml`の両方で定義された取得先は、この二つの検査から除外して上流の原文を保つ。秘密情報の検査は継続する。

禁止語の定義は`config/public-forbidden-patterns.txt`を常に読む。追加の定義は`DOTFILES_FORBIDDEN_PATTERNS_FILE`で指定できる。指定した定義の欠落・空ファイルは検査失敗とする。

手動検査は`./bin/check-public-candidate.sh --all`、変更範囲だけなら`--worktree`を使う。日本語の自動検査は英語だけの説明行を検出する補助であり、翻訳の正確さは原文と照合する。

Codex設定は任意の別ファイルを自動結合せず、このrepoの`config.toml`を使う。

共通資料・判定処理は`.agents`へ集約する。ツールが読む`~/.codex/AGENTS.md`は共通指示へのリンク、`~/.codex/config.toml`は固有の設定入口とする。[指示ファイルの探索仕様](https://developers.openai.com/codex/guides/agents-md)に合わせ、fallback設定は空にする。
