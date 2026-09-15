local platform = require("platform")

local M = {}

local registry_key = "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize"
local scheme_by_mode = {
  dark = "github_dark_dimmed",
  light = "github_light",
}

local function registry_executable()
  if platform.is_windows() then
    local windows_reg = [[C:\Windows\system32\reg.exe]]
    if vim.fn.executable(windows_reg) == 1 then
      return windows_reg
    end
  end
  if vim.fn.executable("reg.exe") == 1 then
    return "reg.exe"
  end
  if platform.is_wsl() then
    local wsl_reg = "/mnt/c/Windows/system32/reg.exe"
    if vim.fn.filereadable(wsl_reg) == 1 then
      return wsl_reg
    end
  end
  return nil
end

function M.parse_apps_use_light_theme(output)
  local value = output:match("AppsUseLightTheme%s+REG_DWORD%s+0x([%da-fA-F]+)")
  if not value then
    return nil
  end
  local number = tonumber(value, 16)
  if number == 0 then
    return "dark"
  elseif number == 1 then
    return "light"
  end
  return nil
end

function M.colorscheme_for(mode)
  return scheme_by_mode[mode]
end

local function apply_mode(mode)
  if mode == nil or mode == vim.o.background then
    return
  end
  vim.o.background = mode
  local colorscheme = M.colorscheme_for(mode)
  if colorscheme then
    pcall(vim.cmd.colorscheme, colorscheme)
  end
end

local function handle_output(output)
  apply_mode(M.parse_apps_use_light_theme(output))
end

local function query_with_system()
  local executable = registry_executable()
  if not executable then
    return false
  end
  local ok = pcall(
    vim.system,
    { executable, "query", registry_key, "/v", "AppsUseLightTheme" },
    { text = true },
    function(result)
      if result.code == 0 then
        vim.schedule(function()
          handle_output(result.stdout or "")
        end)
      end
    end
  )
  if not ok then
    return false
  end
  return true
end

local function query_with_jobstart()
  local executable = registry_executable()
  if not executable then
    return
  end
  local output = {}
  vim.fn.jobstart({ executable, "query", registry_key, "/v", "AppsUseLightTheme" }, {
    stdout_buffered = true,
    on_stdout = function(_, data)
      if data then
        vim.list_extend(output, data)
      end
    end,
    on_exit = function(_, code)
      if code == 0 then
        handle_output(table.concat(output, "\n"))
      end
    end,
  })
end

function M.sync()
  if not (platform.is_windows() or platform.is_wsl()) or vim.g.neovide or not registry_executable() then
    return
  end
  if vim.system and query_with_system() then
    return
  end
  query_with_jobstart()
end

function M.setup()
  if vim.g.neovide then
    vim.g.neovide_theme = "auto"
    vim.api.nvim_create_autocmd("OptionSet", {
      group = vim.api.nvim_create_augroup("dotfiles_neovide_theme", { clear = true }),
      pattern = "background",
      callback = function()
        local colorscheme = M.colorscheme_for(vim.o.background)
        if colorscheme then
          pcall(vim.cmd.colorscheme, colorscheme)
        end
      end,
    })
    return
  end

  if not (platform.is_windows() or platform.is_wsl()) then
    return
  end
  vim.api.nvim_create_autocmd({ "VimEnter", "FocusGained", "VimResume" }, {
    group = vim.api.nvim_create_augroup("dotfiles_windows_theme", { clear = true }),
    callback = M.sync,
  })
  vim.api.nvim_create_autocmd("User", {
    group = "dotfiles_windows_theme",
    pattern = "VeryLazy",
    callback = M.sync,
  })
end

return M
