-- Snacks.bufdelete()は保存確認で「Yes」を選ぶとvim.cmd.writeをそのまま呼ぶため、
-- 未保存の新規バッファ(名前なし。VSCodeのUntitledに相当)を閉じようとすると
-- E32: No file nameで落ちる。ファイル名を尋ねてから保存し閉じる薄いラッパを提供する。
-- 何も考えずEnterを押しても保存フロー(名前を付けて保存)に進むだけで閉じないよう、
-- 選択肢の先頭を「名前を付けて保存」にする(誤操作で保存せず閉じてしまう事故を防ぐ安全側デフォルト)。
local M = {}

---@param s string
---@return string
local function trim(s)
  return s:match("^%s*(.-)%s*$")
end

--- vim.ui.selectに渡す選択肢。並び順がそのままカーソルの初期位置(先頭=デフォルト)になる。
M.SELECT_ITEMS = { "名前を付けて保存", "保存せず閉じる", "キャンセル" }

--- 名前なしバッファに未保存の変更があるかを判定する
---@param name string vim.api.nvim_buf_get_name(buf)の戻り値
---@param modified boolean
---@return boolean
function M.needs_save_as(name, modified)
  return name == "" and modified
end

--- vim.ui.selectの選択結果(idx)をアクションに変換する
---@param idx integer? SELECT_ITEMS内のインデックス。nilはEscなどでの選択キャンセル
---@return "save_as"|"discard"|"cancel"
function M.select_idx_to_action(idx)
  if idx == 1 then
    return "save_as"
  elseif idx == 2 then
    return "discard"
  else
    return "cancel"
  end
end

--- vim.ui.inputで受け取ったパスを正規化する。nil・空白のみは入力キャンセル扱い
--- (空文字で保存先なしのまま閉じてしまわないよう、キャンセル側に倒す)
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

--- バッファを閉じる。名前なしで未保存の変更があれば、まず「名前を付けて保存」/「保存せず閉じる」/
--- 「キャンセル」をカーソルで選ばせる(デフォルトは名前を付けて保存)。名前を付けて保存を選んだ場合のみ保存先を尋ねる。
--- それ以外はSnacks.bufdelete()にそのまま委ねる(保存確認・forceなどの挙動を保つ)。
---@param buf? integer
function M.close(buf)
  buf = buf or vim.api.nvim_get_current_buf()

  if not M.needs_save_as(vim.api.nvim_buf_get_name(buf), vim.bo[buf].modified) then
    Snacks.bufdelete({ buf = buf })
    return
  end

  vim.ui.select(
    M.SELECT_ITEMS,
    { prompt = "名前のないバッファの変更を保存しますか?" },
    function(_, idx)
      local action = M.select_idx_to_action(idx)

      if action == "cancel" then
        return
      elseif action == "discard" then
        Snacks.bufdelete({ buf = buf, force = true })
        return
      end

      vim.ui.input({ prompt = "保存先のファイル名: ", completion = "file" }, function(input)
        local path = M.normalize_save_path(input)
        if not path then
          return
        end
        vim.api.nvim_buf_call(buf, function()
          vim.cmd.write(path)
        end)
        Snacks.bufdelete({ buf = buf, force = true })
      end)
    end
  )
end

return M
