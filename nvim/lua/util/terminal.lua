-- VSCode の統合ターミナル相当。下部固定パネルとして常時表示する
local M = {}

---@param buf integer
---@return integer?
local function get_job_pid(buf)
  local ok, job_id = pcall(function()
    return vim.b[buf].terminal_job_id
  end)
  if not ok or not job_id then
    return nil
  end
  local ok2, pid = pcall(vim.fn.jobpid, job_id)
  if not ok2 or pid == nil or pid <= 0 then
    return nil
  end
  return pid
end

-- シェルの子プロセスが残っているかで「フォアグラウンドで何か実行中」を判定する。
-- シェル自身以外の子プロセスが無ければ、プロンプトで待機中とみなせる
---@param pid integer
---@return boolean
local function has_running_child(pid)
  if vim.fn.executable("ps") ~= 1 then
    return false
  end
  local out = vim.fn.system({ "ps", "--ppid", tostring(pid), "-o", "comm=" })
  return vim.v.shell_error == 0 and vim.trim(out) ~= ""
end

-- Claude Codeは実行中だけ画面下部に"esc to interrupt"を表示するため、
-- それが無ければユーザー入力待ちとみなす
---@param buf integer
---@return boolean
local function claude_is_waiting_for_input(buf)
  local lines = vim.api.nvim_buf_get_lines(buf, -15, -1, false)
  for _, line in ipairs(lines) do
    if line:find("esc to interrupt", 1, true) then
      return false
    end
  end
  return true
end

-- ターミナルバッファを閉じてよいか確認する。ターミナル以外は常に許可する。
-- Claude Codeはユーザー入力待ちなら常駐プロセスでも確認せず許可し、
-- それ以外のターミナルはフォアグラウンドの子プロセスが無ければ許可する
---@param buf? integer
---@return boolean
function M.confirm_close(buf)
  buf = buf or vim.api.nvim_get_current_buf()
  if vim.bo[buf].buftype ~= "terminal" then
    return true
  end

  local is_busy
  if vim.b[buf].is_claude_terminal then
    is_busy = not claude_is_waiting_for_input(buf)
  else
    local pid = get_job_pid(buf)
    is_busy = pid ~= nil and has_running_child(pid)
  end
  if not is_busy then
    return true
  end

  local choice =
    vim.fn.confirm("実行中のコマンドがあります。ターミナルを閉じますか?", "&yes\n&no", 2)
  return choice == 1
end

function M.open_bottom_terminal()
  -- LazyVim初期化中(VeryLazy前)にautocmds.luaから直接呼ばれるため、グローバルSnacksは
  -- まだセットされていない。require経由ならlazy.nvimが未ロードでもここでロードしてくれる
  require("snacks").terminal(nil, { cwd = LazyVim.root(), win = { position = "bottom", height = 0.3 } })
end

-- 引数ありで起動したときだけ下部ターミナルを開く。
-- 引数なし起動はutil.projectのプロジェクト選択確定時にterminalを開くため、二重起動を避ける
function M.open_on_startup()
  if vim.fn.argc() == 0 then
    return
  end
  M.open_bottom_terminal()
  vim.cmd("wincmd p") -- ターミナルではなく元のウィンドウにフォーカスを戻す
end

return M
