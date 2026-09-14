---@diagnostic disable: undefined-global, undefined-field
local minimap = require("util.minimap")

describe("minimap", function()
  describe("should_show", function()
    it("折り返し表示中は本文を隠さないため非表示にする", function()
      assert.is_false(minimap.should_show("", true))
    end)

    it("折り返しなしのファイルバッファでは表示する", function()
      assert.is_true(minimap.should_show("", false))
    end)

    it("ファイル以外のバッファでは表示しない", function()
      assert.is_false(minimap.should_show("nofile", false))
    end)
  end)
end)
