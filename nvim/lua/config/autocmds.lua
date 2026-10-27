-- 自動コマンドはVeryLazyイベントで自動的に読み込まれる。
-- 常に設定される既定の自動コマンド: https://github.com/LazyVim/LazyVim/blob/main/lua/lazyvim/config/autocmds.lua
--
-- 追加の自動コマンドは、ここで
-- vim.api.nvim_create_autocmdを使って設定する。
--
-- 既存の自動コマンドはグループ名で削除できる。既定のグループ名はlazyvim_で始まる。
-- 例: vim.api.nvim_del_augroup_by_name("lazyvim_wrap_spell")

-- LazyVimのlazyvim_wrap_spellはMarkdownなどでspellを有効にするが、日本語は辞書になく
-- 全単語が赤波線になって読めなくなる。wrapは残したいのでspellだけ切る。
vim.api.nvim_create_autocmd("FileType", {
  group = vim.api.nvim_create_augroup("dotfiles_no_spell_ja", { clear = true }),
  pattern = { "markdown", "markdown.mdx", "text", "gitcommit" },
  callback = function()
    vim.opt_local.spell = false
  end,
})

-- LazyVimのlazyvim_checktimeはFocusGained・TermClose・TermLeaveでしかディスクを
-- 点検しないため、nvim内のタブ移動では別セッションの編集が反映されない。
-- タブ・ウィンドウ・バッファへ入った時点で点検を足す。
vim.api.nvim_create_autocmd({ "TabEnter", "WinEnter", "BufEnter" }, {
  group = vim.api.nvim_create_augroup("dotfiles_checktime", { clear = true }),
  callback = function()
    if vim.o.buftype == "" then
      vim.cmd("checktime")
    end
  end,
})

-- :cdでグローバルカレントディレクトリが変わるたびに、そのディレクトリを
-- プロジェクト一覧(util.project.pick_project)に記録する。以前はセッションを
-- 一度も終了しないと記録されず、開いただけのworktreeなどが一覧に出なかった。
-- 起動時のchdir(下のopen_on_startup)分も拾うため、requireより前に登録する
vim.api.nvim_create_autocmd("DirChanged", {
  group = vim.api.nvim_create_augroup("dotfiles_project_record_cwd", { clear = true }),
  pattern = "global",
  callback = function()
    require("util.project").record_cwd()
  end,
})

-- activity-barはVSCodeのアクティビティバー相当で、常時表示のため引数の有無に
-- かかわらず起動時に開く。project.open_on_startupのopen_workspaceが
-- activity-bar経由でNeotreeを開くため、それより前に呼ぶ必要がある
require("util.activity-bar").open_on_startup()

-- terminal/projectの起動時セットアップ。
-- 以前はplugins/terminal.lua・project.luaがそれぞれ
-- "folke/snacks.nvim" のinitでVimEnter登録やコマンド登録をしていたが、
-- lazy.nvimは同名プラグインの複数initを後勝ちで上書きするため、
-- project.lua側のVimEnter処理(chdir含む)が実行されず起動時のディレクトリ移動が効かなくなっていた。
require("util.terminal").open_on_startup()
require("util.project").open_on_startup()
require("util.copy-path").setup()
require("util.trash-file").setup()
require("util.ime").setup()
require("util.time-difference").setup()
require("util.final-blank-line").setup()
