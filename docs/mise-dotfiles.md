# miseで複数のdotfilesリポジトリを使う

公開設定とprivate設定を別々のGitリポジトリで編集し、ホームへのリンクをmiseで管理する。公開側のファイルをprivate側へコピーする必要はない。

この手順はLinux / WSLの標準配置（`~/.config`、`~/.codex`）を対象とする。別の配置先を使う場合は、適用前に`mise.toml`の対象パスを変更する。

## 公開リポジトリだけを使う

[miseの公式手順](https://mise.jdx.dev/installing-mise.html)で2026.10.15以降を導入し、このリポジトリを`~/git/honahuku/dotfiles`へcloneする。既存環境では、先に[競合する旧設定の確認](#既存のリンクスクリプトから移行する)を行う。

```sh
cd ~/git/honahuku/dotfiles
mise trust
./bin/slink.sh --dry-run
./bin/slink.sh
mise dot status
```

[`mise.toml`](../mise.toml)がシェル、mise、lazygit、aqua、Neovim、共通指示の配置を定義する。`bin/slink.sh`はjqとmiseを使って差分と競合を検査してから適用する。実ファイルに加え、取得元が異なる既存リンクも停止対象になるため、適用にはこの入口を使う。

`.bashrc`と`.profile`は既存の実ファイルを残し、[管理ブロック](https://mise.jdx.dev/dotfiles/edits.html#blocks)にdotfilesを読み込む処理を追加する。再適用でブロックは重複しない。既存設定を先に読み、その後dotfilesを読み込むため、同名のaliasや変数は後者の値が優先される。端末固有の上書きは`~/.bashrc.local`に置く。

シェル設定の本体は次のファイルで管理する。リポジトリ直下の`.bashrc`は旧リンク向けの互換入口である。

| 用途              | 公開側             | private側          |
| ----------------- | ------------------ | ------------------ |
| 環境変数・PATH    | `shell/profile.sh` | `shell/profile.sh` |
| Bashのalias・補完 | `shell/bashrc.sh`  | `shell/bashrc.sh`  |

公開側を`~/git/honahuku/dotfiles`へcloneする。private側も使う場合は、`DOTFILES_PRIVATE_ROOT`にそのrepoの絶対パスを指定し、公開設定の読み込み前にexportする。既存環境で自動検出を使う場合は、`shell/profile.sh`の検索条件を確認する。privateがなくても公開側だけで動く。対話Bashでは、公開設定、private設定、miseの有効化、`~/.bashrc.local`の順に適用する。非対話シェルではaliasや補完の初期化を行わない。以下では`DOTFILES_PRIVATE_ROOT`が設定済みであることを前提とする。

## privateリポジトリと組み合わせる

private側に、両リポジトリを参照する`mise.toml`を置く。シェルの管理ブロックは公開側と同じ入口を使う。次の例では、Neovimを公開側から使い、個人設定も配置する。

```toml
min_version = "2026.10.15"

[dotfiles]
"~/.bashrc/dotfiles-shell" = { block = '''
if [ -n "${BASH_VERSION:-}" ]; then
  . "$HOME/git/honahuku/dotfiles/shell/bashrc.sh"
fi
''' }
"~/.config/nvim" = "~/git/honahuku/dotfiles/nvim"
"~/.config/nvim-private" = "nvim"
```

[Managed files | mise-en-place](https://mise.jdx.dev/dotfiles/managed.html)

`source`の相対パスは[設定ファイルのディレクトリを基準に解決される](https://mise.jdx.dev/dotfiles/managed.html#whole-file-entries)。上の`nvim`はprivate側を参照する。`.profile`のブロックも公開側の`mise.toml`と同じものを定義する。

両方をcloneした後、private側で実行する。

```sh
cd "$DOTFILES_PRIVATE_ROOT"
mise trust
DOTFILES="$PWD" ~/git/honahuku/dotfiles/bin/slink.sh --dry-run
DOTFILES="$PWD" ~/git/honahuku/dotfiles/bin/slink.sh
mise dot status
```

以後はprivate側の設定を入口にする。公開側の設定を別途適用すると、lazygitなどのリンク元が公開側へ変わるため、組み合わせ用の設定だけを適用する。

### スキルを同じディレクトリに配置する

両リポジトリのスキルを`~/.agents/skills`に置く場合は、[グループごとに取得元のディレクトリを指定する](https://mise.jdx.dev/dotfiles/groups.html)。`symlink-each`はファイル単位でリンクする。

```toml
[dotfile_groups.public-skills]
root = "~/git/honahuku/dotfiles/.agents/skills"
target = "~/.agents/skills"
mode = "symlink-each"
exclude = ["__pycache__", "*.pyc"]

[dotfile_groups.private-skills]
root = "/path/to/private-config/.agents/skills"
target = "~/.agents/skills"
mode = "symlink-each"
exclude = ["__pycache__", "*.pyc"]
```

[Groups | mise-en-place](https://mise.jdx.dev/dotfiles/groups.html)

上の`/path/to/private-config`は、実際の非公開repoの絶対パスに置き換える。

両グループに同じ配置先のファイルがあると[適用前に競合となる](https://mise.jdx.dev/dotfiles/groups.html#selecting-groups)。片方の`exclude`に重複するスキルのディレクトリ名を追加し、使う版を選ぶ。`root`の相対パスは設定ファイル基準ではなく`dotfiles.root`基準になるため、この例ではホームからのパスを使う。

## 既存のリンクスクリプトから移行する

通常の実ファイルの`.bashrc`と`.profile`は削除しない。旧スクリプトでこれらをリンクしていた場合、管理ブロックをリンクへ書き込めないため停止する。リンク元を確認し、不要なリンクだけを手動で削除してから再実行する。

実ファイルとリンク元を確認する。

```sh
ls -ld "$HOME/.bashrc"
ls -ld "$HOME/.agents/skills"
find -L "$HOME/.agents/skills" -type f -print
```

以下は、`.bashrc`が旧リンクであり、内容を確認して不要なリンクと判断した場合だけ実行する。

```sh
rm -- "$HOME/.bashrc"
```

専用設定やスキルが競合した場合も、必要な内容を管理元へ引き継いでから、表示された対象だけを手動で削除する。`~/.codex/skills/.system`は削除対象に含めない。削除後は`./bin/slink.sh --dry-run`で競合が解消したことを確認し、`./bin/slink.sh`を実行する。`--force`・`--prune`・`--backup`は受け付けない。

## 設定を更新する

### 共通指示・スキル・非公開資料

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

禁止語の定義は非公開repoの`config/public-forbidden-patterns.txt`で管理する。Lefthookと手動検査の実行環境では、`DOTFILES_PRIVATE_ROOT`にそのrepoの絶対パスを設定する。定義が未配置・空、または環境変数が未設定なら検査は失敗する。

手動検査は`./bin/check-public-candidate.sh --all`、変更範囲だけなら`--worktree`を使う。日本語の自動検査は英語だけの説明行を検出する補助であり、翻訳の正確さは原文と照合する。

Codex設定は任意の別ファイルを自動結合する構成にせず、実際に読み込む`config.toml`を一つ選ぶ。社内MCP・信頼済みパスなどが必要な環境では非公開版を使い、汎用設定との差分を見て更新する。

共通資料・判定処理は`.agents`へ集約する。ツールが読む`~/.codex/AGENTS.md`は共通指示へのリンク、`~/.codex/config.toml`は固有の設定入口として残す。[指示ファイルの探索仕様](https://developers.openai.com/codex/guides/agents-md)に合わせ、公開版のfallback設定は空にする。別名の指示ファイルに依存する既存環境の互換設定は非公開版で保持し、内容を引き継いでから整理する。

既存リンクを通した編集はリンク元のリポジトリへ反映される。配置するファイルを追加した場合は、組み合わせ用の`mise.toml`を更新し、同じ適用手順を繰り返す。スキルのグループ配下にファイルを追加した場合は、一覧への追記は不要である。

`symlink-each`は[取得元から削除したファイルのリンクも次回適用時に削除する](https://mise.jdx.dev/dotfiles/managed.html#modes)。更新後もdry-runで削除対象を確認する。`--prune`は通常の適用手順に含めない。

リポジトリの取得もmiseへ任せる場合は、別途[`[bootstrap.repos]`](https://mise.jdx.dev/bootstrap/repos.html)を定義する。`mise dot apply`はローカルのファイルを配置し、リポジトリのcloneや更新は行わない。
