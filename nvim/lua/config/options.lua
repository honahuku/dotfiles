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

-- WSLではwin32yank、Windows nativeでは標準コマンドでクリップボードを扱う。
local clipboard = require("util.clipboard")
local provider = clipboard.resolve(platform.is_windows(), platform.is_wsl(), function(command)
  return vim.fn.executable(command) == 1
end)
if provider then
  vim.g.clipboard = provider
end
vim.opt.clipboard = "unnamedplus"
