# 💤 LazyVim

A starter template for [LazyVim](https://github.com/LazyVim/LazyVim).
Refer to the [documentation](https://lazyvim.github.io/installation) to get started.

## 時刻差分計算

ノーマルモードで`<leader>ct`を押すと入力欄が開きます。式を入力してEnterを押すと、結果をWindowsクリップボードへコピーします。

```text
12:00 - 10:07       → 01:53
12:00 + 01:07       → 13:07
10:07 - 12:00       → -01:53
12:00:30 - 10:07:15 → 01:53:15
24:30 - 23:45       → 00:45
```

日付をまたぐ場合は、翌日の時刻を24時間以上の値で入力します。例えば、翌日0時30分は`24:30`です。Escで入力をキャンセルできます。

アンインストールは、この設定を削除してNeovimを再起動します。設定全体を削除する場合は、`nvim`ディレクトリとNeovimの設定シンボリックリンクを削除します。
