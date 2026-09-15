-- 右クリックの標準PopUpメニュー(Cut/Copy/Paste等)にパスコピー項目を追加する。
-- VSCodeのCopy Path/Copy Relative Pathに相当。neo-treeバッファ上ではカーソル下のノードを、
-- それ以外のバッファでは開いているファイルを対象にする
local M = {}

function M.get_target_path()
  if vim.bo.filetype == "neo-tree" then
    local ok, manager = pcall(require, "neo-tree.sources.manager")
    if ok then
      local state = manager.get_state_for_window()
      if state then
        local node = state.tree:get_node()
        if node then
          return node:get_id()
        end
      end
    end
  end
  return vim.fn.expand("%:p")
end

function M.copy(absolute)
  local path = M.get_target_path()
  if path == "" then
    vim.notify("コピー対象のパスがありません", vim.log.levels.WARN)
    return
  end
  if not absolute then
    path = vim.fn.fnamemodify(path, ":.")
  end
  vim.fn.setreg("+", path)
  vim.notify("コピーしました: " .. path)
end

function M.setup()
  vim.api.nvim_create_user_command("CopyRelativePath", function()
    M.copy(false)
  end, {})
  vim.api.nvim_create_user_command("CopyAbsolutePath", function()
    M.copy(true)
  end, {})
  vim.cmd([[
    anoremenu PopUp.-3-                     <Nop>
    anoremenu PopUp.相対パスをコピー        <Cmd>CopyRelativePath<CR>
    anoremenu PopUp.絶対パスをコピー        <Cmd>CopyAbsolutePath<CR>
  ]])
end

return M
