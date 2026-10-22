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
- Windows側：`mise run windows:diff`で差分を確認し、原本へ取り込むか保留する。原本への反映後に`mise dot apply`を実行する。統合後も差が残る場合は、対話端末で`mise run windows:resolve`を使う。

Windows側で停止しても、先行する配置は完了している場合がある。設定編集を終えてから適用し、終了状態と差分を確認する。中間ファイルは再生成されるため、直接編集しない。

## 配置を変更する

取得元と配置先は[`mise.toml`](../mise.toml)、処理は[`mise-tasks.toml`](../mise-tasks.toml)で管理する。private併用時はprivate側から公開設定を参照し、同名スキルは片方のグループで除外する。設定方法は[miseの管理ファイル](https://mise.jdx.dev/dotfiles/managed.html)と[グループ](https://mise.jdx.dev/dotfiles/groups.html)を参照する。

Windowsの対象はCodex共通指示とインストール済みのTerminal設定である。保存先はWindowsホーム配下に限る。Codexの保存先を変える場合は、初回セットアップ時に環境変数`DOTFILES_WINDOWS_CODEX_HOME`で指定する。設定済みの対象や保存先を変更する場合は、移行先と既存ファイルを確認してから適用する。
