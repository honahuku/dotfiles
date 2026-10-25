-- オプションはlazy.nvimの起動前に自動的に読み込まれる。
-- 常に設定される既定のオプション: https://github.com/LazyVim/LazyVim/blob/main/lua/lazyvim/config/options.lua
-- 追加のオプションはここで設定する。

vim.opt.wrap = true
vim.opt.linebreak = true

-- VSCode同様、行番号は絶対値のみ表示する
vim.opt.relativenumber = false

-- マウスドラッグでウィンドウ境界(サイドバー幅など)をリサイズできるようにする
vim.opt.mouse = "a"
vim.opt.mousemoveevent = true

local platform = require("platform")

-- WSL上のnvimからWindowsクリップボードへyank/pasteするためwin32yankを使う。
-- Windows nativeではNeovimの標準clipboard providerを使う。
if platform.is_wsl() and vim.fn.executable("win32yank.exe") == 1 then
  vim.g.clipboard = {
    name = "win32yank",
    copy = {
      ["+"] = "win32yank.exe -i --crlf",
      ["*"] = "win32yank.exe -i --crlf",
    },
    paste = {
      ["+"] = "win32yank.exe -o --lf",
      ["*"] = "win32yank.exe -o --lf",
    },
    cache_enabled = 0,
  }
end
vim.opt.clipboard = "unnamedplus"
