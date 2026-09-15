-- Claude Codeをファイルタブと同じbufferlineに1枚として開く
local M = {}

function M.open_claude()
  vim.cmd("enew")
  -- 閉じる前の確認(util.terminal.confirm_close)で、他の一般的なターミナルと
  -- 判定基準を分けるための目印
  vim.b.is_claude_terminal = true
  vim.fn.jobstart("claude --permission-mode auto", { cwd = LazyVim.root(), term = true })
  vim.cmd("startinsert")
end

-- コマンドラインから ":Claude" で起動できるようにする(キーマップを覚えていなくてもよい)
function M.setup_command()
  vim.api.nvim_create_user_command("Claude", M.open_claude, { desc = "Claude Code" })
end

return M
