local M = {}

local function append_blank_line(event)
  local buf = event.buf
  if vim.bo[buf].buftype ~= "" or vim.bo[buf].binary or not vim.bo[buf].modifiable then
    return
  end

  local last_line = vim.api.nvim_buf_get_lines(buf, -2, -1, false)[1]
  if last_line ~= "" then
    vim.api.nvim_buf_set_lines(buf, -1, -1, false, { "" })
    vim.bo[buf].endofline = true
  end
end

function M.setup()
  local function register()
    vim.api.nvim_create_autocmd("BufWritePre", {
      group = vim.api.nvim_create_augroup("dotfiles_final_blank_line", { clear = true }),
      desc = "保存時に末尾の空行を補う",
      callback = append_blank_line,
    })
  end

  register()
  -- LazyVimはconfig.autocmdsの後に保存時の整形を登録するため、その後に登録し直す。
  vim.schedule(register)
end

return M
