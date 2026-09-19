local M = {}

local function is_wsl_kernel()
  local file = io.open("/proc/version", "r")
  if not file then
    return false
  end
  local version = file:read("*a")
  file:close()
  return version:lower():find("microsoft", 1, true) ~= nil
end

function M.is_windows()
  return vim.fn.has("win32") == 1
end

function M.is_wsl()
  return vim.fn.has("wsl") == 1 or vim.env.WSL_DISTRO_NAME ~= nil or is_wsl_kernel()
end

return M
