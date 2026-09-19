-- 右クリックの標準PopUpメニューに、対象ファイルをゴミ箱へ移動する項目を追加する。
-- 対象の決め方はutil.copy-pathと同じで、neo-treeバッファ上ではカーソル下のノード、
-- それ以外のバッファでは開いているファイルを使う
local M = {}
local platform = require("platform")

-- bash -i はttyが無い環境でジョブ制御の警告をstderrへ出す。trash本体のエラーだけを残す
local function shell_error(stderr)
  local lines = {}
  for _, line in ipairs(vim.split(stderr or "", "\n", { trimempty = true })) do
    if not line:match("cannot set terminal process group") and not line:match("no job control in this shell") then
      table.insert(lines, line)
    end
  end
  return table.concat(lines, " ")
end

local function refresh_after_delete(path)
  -- 消えたファイルのバッファが残るとwriteで復活するため先に破棄する
  local bufnr = vim.fn.bufnr(path)
  if bufnr ~= -1 then
    vim.api.nvim_buf_delete(bufnr, { force = true })
  end
  pcall(function()
    require("neo-tree.sources.manager").refresh("filesystem")
  end)
end

function M.trash()
  local path = require("util.copy-path").get_target_path()
  if path == "" then
    vim.notify("削除対象のパスがありません", vim.log.levels.WARN)
    return
  end

  local display = vim.fn.fnamemodify(path, ":.")
  local prompt = "ゴミ箱へ移動しますか?: " .. display
  if vim.fn.isdirectory(path) == 1 then
    prompt = "ディレクトリを中身ごとゴミ箱へ移動しますか?: " .. display
  end
  if vim.fn.confirm(prompt, "&yes\n&no", 2) ~= 1 then
    return
  end

  -- trashは~/.bashrc内のシェル関数で、非対話bashでは.bashrcが読まれない。
  -- -iで対話シェルとして起動して関数を定義させる
  local result = vim.system({ "bash", "-ic", 'trash -r -- "$1"', "bash", path }, { text = true }):wait()
  if result.code ~= 0 then
    vim.notify("ゴミ箱へ移動できませんでした: " .. shell_error(result.stderr), vim.log.levels.ERROR)
    return
  end

  refresh_after_delete(path)
  vim.notify("ゴミ箱へ移動しました: " .. display)
end

function M.setup()
  if not platform.is_wsl() then
    return
  end
  vim.api.nvim_create_user_command("TrashFile", function()
    M.trash()
  end, {})
  vim.cmd([[
    anoremenu PopUp.-4-                     <Nop>
    anoremenu PopUp.ゴミ箱へ移動            <Cmd>TrashFile<CR>
  ]])
end

return M
