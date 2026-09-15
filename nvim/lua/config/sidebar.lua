-- 左サイドバー(neo-tree)をVSCode同様に常時表示で固定する仕組み。
-- 誤操作で閉じた場合は開き直し、toggle経由の明示的な操作だけ閉じたままにする。
local M = {}

-- toggle実行中だけ立てるフラグ。WinClosedはtoggleの中で発火するため、
-- 復帰処理はこれを見て意図した閉じ方と誤操作を区別する
local closing_on_purpose = false

---@param args string|nil :Neotreeへ渡す追加引数。dir=cwd等
function M.toggle(args)
  closing_on_purpose = true
  vim.cmd("Neotree toggle " .. (args or ""))
  vim.schedule(function()
    closing_on_purpose = false
  end)
end

local function is_sidebar(win)
  if not vim.api.nvim_win_is_valid(win) then
    return false
  end
  -- git commitの入力ポップアップなどフロートは復帰対象にしない
  if vim.api.nvim_win_get_config(win).relative ~= "" then
    return false
  end
  return vim.bo[vim.api.nvim_win_get_buf(win)].filetype == "neo-tree"
end

-- サイドバーのウィンドウが閉じたら開き直すautocmdを登録する
function M.enable_guard()
  vim.api.nvim_create_autocmd("WinClosed", {
    callback = function(ev)
      local win = tonumber(ev.match)
      if not win or closing_on_purpose or not is_sidebar(win) then
        return
      end
      vim.schedule(function()
        -- nvim終了中は開き直さない
        if vim.v.exiting ~= vim.NIL then
          return
        end
        -- showはフォーカスを移さないので、編集中のカーソル位置は保たれる
        vim.cmd("Neotree show")
      end)
    end,
  })
end

return M
