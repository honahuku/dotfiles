-- Codexをファイルタブと同じbufferlineに1枚として開く
local M = {}

function M.open_codex()
  vim.cmd("enew")
  vim.fn.jobstart({ "codex" }, { cwd = LazyVim.root(), term = true })
  vim.cmd("startinsert")
end

-- コマンドラインから":Codex"で起動できるようにする
function M.setup_command()
  vim.api.nvim_create_user_command("Codex", M.open_codex, { desc = "Codex" })
end

return M
