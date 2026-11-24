---@diagnostic disable: undefined-global, undefined-field
local clipboard = require("util.clipboard")

describe("clipboard", function()
  it("SSH接続ではホスト端末へ送るOSC 52を使う", function()
    local provider = clipboard.resolve(false, false, true, function()
      return false
    end)
    assert.are.equal("osc52", provider)
  end)

  it("Windows nativeではclip.exeとPowerShellを使う", function()
    local provider = clipboard.resolve(true, false, false, function(command)
      return command == "clip.exe" or command == "powershell.exe"
    end)

    assert.are.same("Windows", provider.name)
    assert.are.same("clip.exe", provider.copy["+"])
    assert.are.same("powershell.exe -NoProfile -Command Get-Clipboard -Raw", provider.paste["+"])
  end)

  it("WSLではwin32yank.exeを使う", function()
    local provider = clipboard.resolve(false, true, false, function(command)
      return command == "win32yank.exe"
    end)

    assert.are.same("win32yank", provider.name)
    assert.are.same("win32yank.exe -i --crlf", provider.copy["+"])
    assert.are.same("win32yank.exe -o --lf", provider.paste["+"])
  end)

  it("必要なコマンドがない場合はNeovim標準のproviderに任せる", function()
    assert.is_nil(clipboard.resolve(true, false, false, function()
      return false
    end))
  end)
end)
