-- plenary.busted経由でheadlessテストを走らせるための最小init。
-- 通常のinit.lua（lazy.nvim起動）はプラグイン解決で待ちが発生し重いため使わない。
--
-- 実行は次の形（`-c "PlenaryBustedFile <path>"`ではない）を使うこと。
--   nvim --headless -u tests/minimal_init.lua \
--     -c 'lua require("plenary.busted").run("tests/util/foo_spec.lua")' -c qa
-- `:PlenaryBustedFile`はテストごとに新しい子プロセスを`-u`なしで起動するため、
-- この最小initが継承されず`~/.config/nvim`（=mainのdotfiles）を読んでしまう。
-- そのため見た目上テストが通っても、実際にはworktree内の変更を検証していない
-- ことがある（2026-08-05に発生）。
vim.opt.rtp:prepend(vim.fn.getcwd())
vim.opt.rtp:prepend(vim.fn.stdpath("data") .. "/lazy/plenary.nvim")
