-- LazyVim標準の<C-s>(vim.cmd.write())は名前なしバッファ(VSCodeのUntitledに相当)で
-- E32: No file nameで落ちる。ファイル名を尋ねてから保存する薄いラッパを提供する。
local M = {}

---@param s string
---@return string
local function trim(s)
  return s:match("^%s*(.-)%s*$")
end

--- バッファに保存先ファイル名が必要か(=名前なしバッファか)を判定する
---@param name string vim.api.nvim_buf_get_name(buf)の戻り値
---@return boolean
function M.needs_filename(name)
  return name == ""
end

--- vim.ui.inputで受け取ったパスを正規化する。nil・空白のみは入力キャンセル扱い
---@param input string?
---@return string?
function M.normalize_save_path(input)
  if not input then
    return nil
  end
  local trimmed = trim(input)
  if trimmed == "" then
    return nil
  end
  return trimmed
end

--- pcallの戻り値から通知用のエラーメッセージを作る。書き込みが成功していればnil
---@param ok boolean pcallの1番目の戻り値
---@param err any pcallの2番目の戻り値(失敗時のエラー内容)
---@return string?
function M.format_write_error(ok, err)
  if ok then
    return nil
  end
  return "保存に失敗しました: " .. tostring(err)
end

--- 現在のバッファを保存する。名前なしバッファなら保存先を尋ねてから保存する。
--- readonlyバッファなど書き込みに失敗した場合は、エラーで落とさず通知するだけにする。
function M.save_current_buffer()
  local buf = vim.api.nvim_get_current_buf()
  if not M.needs_filename(vim.api.nvim_buf_get_name(buf)) then
    local ok, err = pcall(vim.cmd.write)
    local message = M.format_write_error(ok, err)
    if message then
      vim.notify(message, vim.log.levels.ERROR)
    end
    return
  end

  vim.ui.input({ prompt = "保存先のファイル名: ", completion = "file" }, function(input)
    local path = M.normalize_save_path(input)
    if not path then
      return
    end
    local ok, err = pcall(vim.api.nvim_buf_call, buf, function()
      vim.cmd.write(path)
    end)
    local message = M.format_write_error(ok, err)
    if message then
      vim.notify(message, vim.log.levels.ERROR)
    end
  end)
end

return M
