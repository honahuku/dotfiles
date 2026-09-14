---@diagnostic disable: undefined-global, undefined-field
local theme = require("platform.theme")

describe("platform.theme", function()
  describe("parse_apps_use_light_theme", function()
    it("レジストリの0をdarkとして解釈する", function()
      assert.are.equal("dark", theme.parse_apps_use_light_theme("AppsUseLightTheme    REG_DWORD    0x0"))
    end)

    it("レジストリの1をlightとして解釈する", function()
      assert.are.equal("light", theme.parse_apps_use_light_theme("AppsUseLightTheme    REG_DWORD    0x1"))
    end)

    it("不正な出力ではnilを返す", function()
      assert.is_nil(theme.parse_apps_use_light_theme("ERROR: The system was unable to find the specified registry key"))
    end)
  end)

  describe("colorscheme_for", function()
    it("lightとdarkに対応するcolorschemeを返す", function()
      assert.are.equal("github_light", theme.colorscheme_for("light"))
      assert.are.equal("github_dark_dimmed", theme.colorscheme_for("dark"))
    end)
  end)
end)
