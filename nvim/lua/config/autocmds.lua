-- Autocmds are automatically loaded on the VeryLazy event
-- Default autocmds that are always set: https://github.com/LazyVim/LazyVim/blob/main/lua/lazyvim/config/autocmds.lua
--
-- Add any additional autocmds here
-- with `vim.api.nvim_create_autocmd`
--
-- Or remove existing autocmds by their group name (which is prefixed with `lazyvim_` for the defaults)
-- e.g. vim.api.nvim_del_augroup_by_name("lazyvim_wrap_spell")

-- LazyVimのlazyvim_wrap_spellはmarkdown等でspellを有効にするが、日本語は辞書に無く
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
-- 一度も終了しないと記録されず、開いただけのworktree等が一覧に出なかった。
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

-- Claude/Codex/terminal/projectの起動時セットアップ。
-- 以前はplugins/claude.lua・codex.lua・terminal.lua・project.lua がそれぞれ
-- "folke/snacks.nvim" のinitでVimEnter登録やコマンド登録をしていたが、
-- lazy.nvimは同名プラグインの複数initを後勝ちで上書きするため、
-- project.lua側のVimEnter処理(chdir含む)が実行されず起動時のディレクトリ移動が効かなくなっていた。
require("util.claude").setup_command()
require("util.codex").setup_command()
require("util.terminal").open_on_startup()
require("util.project").open_on_startup()
require("util.copy-path").setup()
require("util.trash-file").setup()
require("util.ime").setup()
require("util.ai-usage").setup()
require("util.time-difference").setup()

-- CSI u形式のエスケープシーケンス(例: Ctrl+jが`\27[27;5;106~`)が生文字として
-- バッファに混入する事象が発生した(2026-08-05、Ctrl+Vでのvisual block中)。
-- 「nvimがどんな生バイトを受け取ったか」「実際にバッファへ何が混入したか」が
-- 分からないため、次回の再現に備えて怪しい経路を横断的に記録する。
do
  local debug_log_path = vim.fs.joinpath(vim.fn.stdpath("state"), "keyboard-debug.log")

  local function debug_log(tag, fields)
    local file = io.open(debug_log_path, "a")
    if not file then
      return
    end
    local parts = { os.date("%Y-%m-%d %H:%M:%S"), ("tag=%-20s"):format(tag) }
    for _, kv in ipairs(fields) do
      table.insert(parts, kv)
    end
    file:write(table.concat(parts, " ") .. "\n")
    file:close()
  end

  -- 1. nvimが受け取った生のキー入力ストリームを監視する。矢印キー等の正しく解釈された
  --    特殊キーは`\128ku`のような内部エンコーディングになりESC(0x1b)を含まないため、
  --    `\27[`(ESCに続けてCSI開始の`[`)を含む場合だけを「解釈しきれず生のまま来た」
  --    疑いのある入力として拾う。単発の<Esc>キー押下(ESC 1バイトのみ)は除外される。
  vim.on_key(function(key, typed)
    if key:find("\27%[") then
      local hex = {}
      for i = 1, #key do
        table.insert(hex, string.format("%02x", key:byte(i)))
      end
      debug_log("on_key", {
        ("mode=%s"):format(vim.api.nvim_get_mode().mode),
        ("bytes=%s"):format(table.concat(hex, " ")),
        ("typed_len=%d"):format(typed and #typed or -1),
      })
    end
  end, vim.api.nvim_create_namespace("dotfiles_keyboard_debug"))

  -- 2. on_keyで拾いきれない経路(貼り付け・IME確定等)を補うため、実際にバッファへ
  --    混入した内容を直接見る。変更のあった行にESC文字が残っていれば記録する。
  vim.api.nvim_create_autocmd({ "TextChangedI", "TextChanged" }, {
    group = vim.api.nvim_create_augroup("dotfiles_keyboard_debug_buffer", { clear = true }),
    callback = function(args)
      local lnum = vim.api.nvim_win_get_cursor(0)[1]
      local line = vim.api.nvim_buf_get_lines(args.buf, lnum - 1, lnum, false)[1]
      if line and line:find("\27", 1, true) then
        debug_log("buffer_contamination", {
          ("event=%s"):format(args.event),
          ("file=%s"):format(vim.api.nvim_buf_get_name(args.buf)),
          ("lnum=%d"):format(lnum),
          ("line=%q"):format(line),
        })
      end
    end,
  })
end
