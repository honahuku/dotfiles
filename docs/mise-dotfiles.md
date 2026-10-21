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

| 用途 | 公開側 | private側 |
| --- | --- | --- |
| 環境変数・PATH | `shell/profile.sh` | `shell/profile.sh` |
| Bashのalias・補完 | `shell/bashrc.sh` | `shell/bashrc.sh` |

公開側を`~/git/honahuku/dotfiles`へcloneする。private側も使う場合は、`~/git/your-namespace/dotfiles-private`へcloneする。公開側のシェル設定は、この場所にprivate repoが1つだけあれば自動で読み込む。複数ある場合は`DOTFILES_PRIVATE_ROOT`に使うrepoのパスを指定する。privateがなくても公開側だけで動く。対話Bashでは、公開設定、private設定、miseの有効化、`~/.bashrc.local`の順に適用する。非対話シェルではaliasや補完の初期化を行わない。以下の`your-namespace`は実際のclone先に置き換える。

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
cd "$HOME/git/your-namespace/dotfiles-private"
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
root = "~/git/your-namespace/dotfiles-private/.agents/skills"
target = "~/.agents/skills"
mode = "symlink-each"
exclude = ["__pycache__", "*.pyc"]
```

[Groups | mise-en-place](https://mise.jdx.dev/dotfiles/groups.html)

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

既存リンクを通した編集はリンク元のリポジトリへ反映される。配置するファイルを追加した場合は、組み合わせ用の`mise.toml`を更新し、同じ適用手順を繰り返す。スキルのグループ配下にファイルを追加した場合は、一覧への追記は不要である。

`symlink-each`は[取得元から削除したファイルのリンクも次回適用時に削除する](https://mise.jdx.dev/dotfiles/managed.html#modes)。更新後もdry-runで削除対象を確認する。`--prune`は通常の適用手順に含めない。

リポジトリの取得もmiseへ任せる場合は、別途[`[bootstrap.repos]`](https://mise.jdx.dev/bootstrap/repos.html)を定義する。`mise dot apply`はローカルのファイルを配置し、リポジトリのcloneや更新は行わない。
