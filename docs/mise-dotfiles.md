# dotfilesの配置

mise 2026.10.17以降と、[セットアップの前提](setup.md)が必要である。公開だけなら公開リポジトリ、private併用ならprivate側を作業ディレクトリにする。

```sh
# 配置予定と競合を確認してから、設定と管理対象ツールを導入する。
mise run setup
```

Windows連携があれば初回だけ保存先を確認する。承認した設定は`~/.local/share/dotfiles/windows/chezmoi.toml`へ保存する。

## 通常更新

```sh
# Windows側の未取り込み編集があれば上書きせず停止する。
mise dot apply
```

削除やリンク先の置換を含む場合は、先に`mise run setup:check`で対象を確認する。`--force`・`--prune`は通常更新に使わない。

## 競合で停止したとき

- Linux側：既存ファイルやリンク元を確認し、必要な内容を管理元へ取り込む。不要と判断した旧リンクだけを手動で削除し、再実行する。`.bashrc`・`.profile`の実ファイルと`~/.codex/skills/.system`は削除しない。
- Windows側：`mise run windows:diff`で差分を確認し、変更対象と差分の内容をユーザーに示して判断を求める。原本へ取り込む、共通設定を適用する、適用を保留する、のどれにするかユーザーが決めるまで、原本の編集やWindows側への適用は行わない。判断を受けて必要な変更を原本へ反映した後、`mise dot apply`を実行する。差が残る場合もユーザーの判断を確認し、適用する場合は対話端末で`mise run windows:resolve`を使う。

Windows側で停止しても、先行する配置は完了している場合がある。設定編集を終えてから適用し、終了状態と差分を確認する。中間ファイルは再生成されるため、直接編集しない。

## 配置を変更する

取得元と配置先は[`mise.toml`](../mise.toml)、処理は[`mise-tasks.toml`](../mise-tasks.toml)で管理する。private併用時はprivate側から公開設定を参照し、同名スキルは片方のグループで除外する。設定方法は[miseの管理ファイル](https://mise.jdx.dev/dotfiles/managed.html)と[グループ](https://mise.jdx.dev/dotfiles/groups.html)を参照する。

Windowsの対象はCodex共通指示とインストール済みのTerminal設定である。保存先はWindowsホーム配下に限る。Codexの保存先を変える場合は、初回セットアップ時に環境変数`DOTFILES_WINDOWS_CODEX_HOME`で指定する。設定済みの対象や保存先を変更する場合は、移行先と既存ファイルを確認してから適用する。

## 共通指示・スキル・非公開資料

汎用手順と自作スキルは公開側で管理し、社内情報と個人情報は非公開リポジトリの資料に分ける。内容を生成してホームにだけ保存せず、リンク元を必ずいずれかのリポジトリにコミットする。

| 配置先                              | 管理元                                                                          |
| ----------------------------------- | ------------------------------------------------------------------------------- |
| `~/.codex/AGENTS.md`                | 公開側の`.agents/AGENTS.md`                                                     |
| `~/.agents/docs/common/`             | 公開側の`docs/agents/`。miseの`public-agent-docs`グループでファイル単位にリンク |
| `~/.agents/skills/`                 | 公開側の自作スキル・vendir取得先と、非公開側の社内取得スキル                    |
| `~/.agents/hooks/`                  | 公開側の共通判定。登録方法と確認手順は[共通hook](../.agents/hooks/README.md)を参照 |
| `~/.agents/prh/`                    | 公開側の技術日本語ルール                                                        |
| `~/.agents/docs/work/context.md`     | 非公開側の業務・環境資料                                                        |
| `~/.agents/docs/personal/context.md` | 非公開側の個人資料                                                              |
| `~/.codex/config.toml`              | 公開側の汎用設定、または非公開側の環境別設定                                    |

非公開資料はファイル単位で`[dotfiles]`に登録する。自作スキルには資料を読む条件とセクション名だけを書き、個人情報・社内情報をスキル本体へ戻さない。取得スキルと自作版の名前が衝突する場合は、自作版を別名にする。

自作スキルの説明文と参照文書は日本語にする。コード・識別子・正式な出典名は維持する。Lefthookは公開候補のパスと内容全体に対して禁止語を検査し、自作スキルには日本語の検査も行う。`vendir.yml`と`vendir.lock.yml`の両方で定義された取得先は、この二つの検査から除外して上流の原文を保つ。秘密情報の検査は継続する。

禁止語の定義は`~/.config/dotfiles/public-forbidden-patterns.txt`へmiseで配置する。別の定義を使う場合だけ`DOTFILES_FORBIDDEN_PATTERNS_FILE`で指定する。定義が未配置・空なら検査は失敗する。

手動検査は`./bin/check-public-candidate.sh --all`、変更範囲だけなら`--worktree`を使う。日本語の自動検査は英語だけの説明行を検出する補助であり、翻訳の正確さは原文と照合する。

Codex設定は任意の別ファイルを自動結合する構成にせず、実際に読み込む`config.toml`を一つ選ぶ。社内MCP・信頼済みパスなどが必要な環境では非公開版を使い、汎用設定との差分を見て更新する。

共通資料・判定処理は`.agents`へ集約する。ツールが読む`~/.codex/AGENTS.md`は共通指示へのリンク、`~/.codex/config.toml`は固有の設定入口として残す。[指示ファイルの探索仕様](https://developers.openai.com/codex/guides/agents-md)に合わせ、公開版のfallback設定は空にする。別名の指示ファイルに依存する既存環境の互換設定は非公開版で保持し、内容を引き継いでから整理する。
