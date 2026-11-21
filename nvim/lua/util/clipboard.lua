local M = {}

function M.resolve(is_windows, is_wsl, is_ssh, executable)
  if is_ssh then
    return "osc52"
  end

  if is_wsl and executable("win32yank.exe") then
    return {
      name = "win32yank",
      copy = {
        ["+"] = "win32yank.exe -i --crlf",
        ["*"] = "win32yank.exe -i --crlf",
      },
      paste = {
        ["+"] = "win32yank.exe -o --lf",
        ["*"] = "win32yank.exe -o --lf",
      },
      cache_enabled = 0,
    }
  end

  if is_windows and executable("clip.exe") and executable("powershell.exe") then
    return {
      name = "Windows",
      copy = {
        ["+"] = "clip.exe",
        ["*"] = "clip.exe",
      },
      paste = {
        ["+"] = "powershell.exe -NoProfile -Command Get-Clipboard -Raw",
        ["*"] = "powershell.exe -NoProfile -Command Get-Clipboard -Raw",
      },
      cache_enabled = 0,
    }
  end
end

return M
