---@diagnostic disable: undefined-global, undefined-field
local project = require("util.project")
local ime = require("util.ime")

describe("public settings", function()
  it("個人環境に依存しないプロジェクトのデフォルト値を使う", function()
    assert.are.same(vim.fn.getcwd(), project.DEFAULT_PROJECT_DIR)
  end)

  it("ZENHAN_PATH環境変数を最優先する", function()
    local is_executable = function()
      return 0
    end
    assert.are.same("/custom/zenhan.exe", ime.resolve_zenhan_path(is_executable, "/tmp/TestUser", "/custom/zenhan.exe"))
  end)

  it("PATHになければWindowsユーザープロファイルのbinから解決する", function()
    local userprofile = "/tmp/TestUser"
    local expected = vim.fs.joinpath(userprofile, "bin", "zenhan.exe")
    local is_executable = function(path)
      return path == expected and 1 or 0
    end
    assert.are.same(expected, ime.resolve_zenhan_path(is_executable, userprofile, nil))
  end)

  it("USERPROFILEが空でも検出したユーザープロファイルから解決する", function()
    local userprofile = "/tmp/TestUser"
    local expected = vim.fs.joinpath(userprofile, "bin", "zenhan.exe")
    local is_executable = function(path)
      return path == expected and 1 or 0
    end
    local discover_userprofile = function()
      return userprofile
    end
    assert.are.same(expected, ime.resolve_zenhan_path(is_executable, nil, nil, discover_userprofile))
  end)

  it("zenhanの英数状態を解釈する", function()
    assert.are.equal(0, ime.parse_status("0\n", 0))
  end)

  it("zenhanの日本語入力状態を解釈する", function()
    assert.are.equal(1, ime.parse_status("1\n", 0))
  end)

  it("zenhanの実行失敗を解釈できない状態として扱う", function()
    assert.is_nil(ime.parse_status("", 1))
  end)
end)
