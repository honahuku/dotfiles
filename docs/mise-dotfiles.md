# miseで複数のdotfilesリポジトリを使う

公開設定とprivate設定を別々のGitリポジトリで編集し、ホームへのリンクをmiseで管理する。公開側のファイルをprivate側へコピーする必要はない。

この手順はLinux / WSLの標準配置（`~/.config`、`~/.codex`）を対象とする。別の配置先を使う場合は、適用前に`mise.toml`の対象パスを変更する。

## 公開リポジトリだけを使う

[miseの公式手順](https://mise.jdx.dev/installing-mise.html)で2026.10.15以降を導入し、このリポジトリを`~/git/honahuku/dotfiles`へcloneする。既存環境では、先に[競合する旧設定の確認](#既存のリンクスクリプトから移行する)を行う。

```sh
cd ~/git/honahuku/dotfiles
mise trust
mise dot apply --dry-run
mise dot apply
mise dot status
```

[`mise.toml`](../mise.toml)がシェル、mise、lazygit、aqua、Neovim、共通指示の配置を定義する。`bin/slink.sh`も同じ設定を使うため、リンクを追加するときにスクリプトを編集する必要はない。

## privateリポジトリと組み合わせる

private側に、両リポジトリを参照する`mise.toml`を置く。次の例では、Neovimを公開側から、シェルをprivate側から使う。

```toml
min_version = "2026.10.15"

[dotfiles]
"~/.bashrc" = ".bashrc"
"~/.config/nvim" = "~/git/honahuku/dotfiles/nvim"
"~/.config/nvim-private" = "nvim"
```

[Managed files | mise-en-place](https://mise.jdx.dev/dotfiles/managed.html)

`source`の相対パスは[設定ファイルのディレクトリを基準に解決される](https://mise.jdx.dev/dotfiles/managed.html#whole-file-entries)。上の`.bashrc`と`nvim`はprivate側を参照する。公開側の`source`はホームディレクトリを起点にしたパスで指定する。

両方をcloneした後、private側で実行する。

```sh
cd ~/src/dotfiles-private
mise trust
mise dot apply --dry-run
mise dot apply
mise dot status
```

以後はprivate側の設定を入口にする。公開側の設定を別途適用すると、`.bashrc`などが公開側へ向き直るため、組み合わせ用の設定だけを適用する。

### スキルを同じディレクトリに配置する

両リポジトリのスキルを`~/.agents/skills`に置く場合は、[グループごとに取得元のディレクトリを指定する](https://mise.jdx.dev/dotfiles/groups.html)。`symlink-each`はファイル単位でリンクする。

```toml
[dotfile_groups.public-skills]
root = "~/git/honahuku/dotfiles/.agents/skills"
target = "~/.agents/skills"
mode = "symlink-each"
exclude = ["__pycache__", "*.pyc"]

[dotfile_groups.private-skills]
root = "~/src/dotfiles-private/.agents/skills"
target = "~/.agents/skills"
mode = "symlink-each"
exclude = ["__pycache__", "*.pyc"]
```

[Groups | mise-en-place](https://mise.jdx.dev/dotfiles/groups.html)

両グループに同じ配置先のファイルがあると[適用前に競合となる](https://mise.jdx.dev/dotfiles/groups.html#selecting-groups)。片方の`exclude`に重複するスキルのディレクトリ名を追加し、使う版を選ぶ。`root`の相対パスは設定ファイル基準ではなく`dotfiles.root`基準になるため、この例ではホームからのパスを使う。

## 既存のリンクスクリプトから移行する

miseのリンク設定は[既存の実ファイルや実ディレクトリと競合すると停止する](https://mise.jdx.dev/dotfiles/managed.html#conflicts)。`--force`で置き換えず、必要な内容を管理元へ引き継いでから、不要と判断した競合対象を手動の`rm`で削除する。既存のシンボリックリンクは別のリンク元へ変更されるため、dry-runで配置先を確認する。

実ファイルとリンク元を確認する。

```sh
ls -ld "$HOME/.bashrc"
ls -ld "$HOME/.agents/skills"
find -L "$HOME/.agents/skills" -type f -print
```

以下は、内容を確認し、必要な設定や独自スキルの引き継ぎを終え、両方を不要と判断した場合だけ実行する。

```sh
rm -- "$HOME/.bashrc"
rm -r -- "$HOME/.agents/skills"
```

`~/.codex/skills/.system`は削除対象に含めない。削除後は`mise dot apply --dry-run`で競合が解消したことを確認し、`mise dot apply`を実行する。`bin/slink.sh --backup`は廃止した。

## 設定を更新する

既存リンクを通した編集はリンク元のリポジトリへ反映される。配置するファイルを追加した場合は、組み合わせ用の`mise.toml`を更新し、同じ適用手順を繰り返す。スキルのグループ配下にファイルを追加した場合は、一覧への追記は不要である。

`symlink-each`は[取得元から削除したファイルのリンクも次回適用時に削除する](https://mise.jdx.dev/dotfiles/managed.html#modes)。更新後もdry-runで削除対象を確認する。`--prune`は通常の適用手順に含めない。

リポジトリの取得もmiseへ任せる場合は、別途[`[bootstrap.repos]`](https://mise.jdx.dev/bootstrap/repos.html)を定義する。`mise dot apply`はローカルのファイルを配置し、リポジトリのcloneや更新は行わない。
