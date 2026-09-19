-- WSL2側のNeovimプロセスにはWindowsのIME開閉状態が届かないため検知できない。
-- zenhan.exe(GetForegroundWindow + WM_IME_CONTROLでIMEを直接操作するツール)を
-- Windows側に配置し、WSL interop経由で呼ぶことで検知・切り替えの両方を行う。
-- im-select.exe(ActivateKeyboardLayoutベース)ではこの開閉状態を検知できなかった。
-- see https://github.com/iuchim/zenhan
local M = {}
local platform = require("platform")

local function discover_userprofile()
  local cmd_path = "/mnt/c/Windows/System32/cmd.exe"
  if vim.fn.executable(cmd_path) ~= 1 then
    return nil
  end

  local output = vim.fn.system({ cmd_path, "/d", "/c", "echo", "%HOMEDRIVE%%HOMEPATH%" })
  local cmd_error = vim.v.shell_error
  local windows_profile = output:match("([A-Za-z]:\\Users\\[^\\\r\n]+)")
  if cmd_error ~= 0 or not windows_profile then
    return nil
  end

  local wsl_profile = vim.fn.system({ "wslpath", "-u", windows_profile })
  local wsl_error = vim.v.shell_error
  local userprofile = vim.trim(wsl_profile)
  if wsl_error ~= 0 or userprofile == "" then
    return nil
  end
  return userprofile
end

---@param is_executable fun(path: string): integer
---@param userprofile string?
---@param configured_path string?
---@param fallback_userprofile fun(): string?
---@return string
local function resolve_zenhan_path(is_executable, userprofile, configured_path, fallback_userprofile)
  if configured_path and configured_path ~= "" then
    return configured_path
  end
  if is_executable("zenhan.exe") == 1 then
    return "zenhan.exe"
  end
  local resolved_userprofile = userprofile
  if not resolved_userprofile and fallback_userprofile then
    resolved_userprofile = fallback_userprofile()
  end
  if resolved_userprofile and resolved_userprofile ~= "" then
    local user_bin_path = vim.fs.joinpath(resolved_userprofile, "bin", "zenhan.exe")
    if is_executable(user_bin_path) == 1 then
      return user_bin_path
    end
  end
  return "zenhan.exe"
end

M.resolve_zenhan_path = resolve_zenhan_path
M.ZENHAN_PATH = resolve_zenhan_path(
  vim.fn.executable,
  vim.env.USERPROFILE,
  vim.env.ZENHAN_PATH,
  platform.is_wsl() and discover_userprofile or nil
)

---@param output string
---@param shell_error integer
---@return integer? 0=英数 1=日本語入力。取得失敗時はnil
local function parse_status(output, shell_error)
  if shell_error ~= 0 then
    return nil
  end
  local status = tonumber(vim.trim(output or ""))
  if status ~= 0 and status ~= 1 then
    return nil
  end
  return status
end

M.parse_status = parse_status

---@return integer? 0=英数 1=日本語入力。取得失敗時はnil
local function get_status()
  local out = vim.fn.system({ M.ZENHAN_PATH })
  return parse_status(out, vim.v.shell_error)
end

---@param status integer
local function set_status(status)
  vim.fn.system({ M.ZENHAN_PATH, tostring(status) })
end

local function refresh_statusline()
  local ok, lualine = pcall(require, "lualine")
  if ok then
    lualine.refresh()
  end
end

-- lualine表示用のキャッシュ。zenhan.exeをstatusline再描画のたびに呼ぶと
-- プロセス起動のオーバーヘッドが積み重なるため、タイマーでのみ更新する
M.display_status = 0

-- ノーマルモードでIMEが全角のまま残って操作できなくなる事故を防ぐため、
-- ノーマルモードに入ったら英数に切り替え、次に入力系モードへ入るときは
-- 抜けた時点の状態に戻す。InsertLeave/InsertEnterだとterminalモードを
-- <C-\><C-n>で抜けるケースを捕捉できないため、
-- モード遷移全般を見るModeChangedを使う
local last_insert_status = nil

function M.setup()
  if not platform.is_wsl() or vim.fn.executable(M.ZENHAN_PATH) ~= 1 then
    return
  end

  local group = vim.api.nvim_create_augroup("dotfiles_ime", { clear = true })

  vim.api.nvim_create_autocmd("ModeChanged", {
    group = group,
    pattern = "*:n",
    callback = function()
      local status = get_status()
      if status ~= nil then
        last_insert_status = status
      end
      set_status(0)
      M.display_status = 0
      refresh_statusline()
    end,
  })

  vim.api.nvim_create_autocmd("ModeChanged", {
    group = group,
    pattern = "n:i,n:ic,n:ix,n:R,n:Rc,n:Rx,n:Rv,n:t",
    callback = function()
      local restored = last_insert_status ~= nil
      if restored then
        set_status(last_insert_status)
        M.display_status = last_insert_status
        refresh_statusline()
      end
    end,
  })

  local timer = vim.uv.new_timer()
  timer:start(
    1000,
    1000,
    vim.schedule_wrap(function()
      local status = get_status()
      if status ~= nil then
        M.display_status = status
        refresh_statusline()
      end
    end)
  )
end

function M.statusline()
  return M.display_status == 1 and "あ" or "A"
end

-- ノーマルモードでは全角のままだとコマンドが打てず操作不能になるため、
-- 全角中は赤背景・太字で目立たせて気付きやすくする
function M.statusline_color()
  if M.display_status == 1 then
    return { fg = "#ffffff", bg = "#d70000", gui = "bold" }
  end
  return {}
end

return M
