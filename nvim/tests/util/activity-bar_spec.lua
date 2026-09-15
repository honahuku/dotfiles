-- activity-bar.luaの純粋関数(パネル定義に対する行変換・表示行生成)だけを対象にする。
-- window作成・vim.cmd呼び出し・ハイライト適用を含むopen()/select()はheadlessテストで
-- 検証しづらいため対象外(bufdelete_specと同じ判断基準)。
---@diagnostic disable: undefined-global, undefined-field
local activity_bar = require("util.activity-bar")

describe("activity-bar", function()
  describe("panel_index_for_key", function()
    it("定義済みキーは対応するパネルのインデックスを返す", function()
      assert.are.same(1, activity_bar.panel_index_for_key("1"))
      assert.are.same(2, activity_bar.panel_index_for_key("2"))
      assert.are.same(3, activity_bar.panel_index_for_key("3"))
    end)

    it("未定義キーはnil", function()
      assert.is_nil(activity_bar.panel_index_for_key("9"))
    end)

    it("nilはnil", function()
      assert.is_nil(activity_bar.panel_index_for_key(nil))
    end)
  end)

  describe("panel_index_for_line", function()
    it("パネルごとに割り当てた行からインデックスを返す", function()
      assert.are.same(1, activity_bar.panel_index_for_line(1))
      assert.are.same(1, activity_bar.panel_index_for_line(3))
      assert.are.same(3, activity_bar.panel_index_for_line(#activity_bar.PANELS * activity_bar.ROWS_PER_PANEL))
    end)

    it("範囲外の行はnil", function()
      assert.is_nil(activity_bar.panel_index_for_line(0))
      assert.is_nil(activity_bar.panel_index_for_line(#activity_bar.PANELS * activity_bar.ROWS_PER_PANEL + 1))
    end)
  end)

  describe("render_lines", function()
    it("パネル数と同じ行数を、アイコン付きの文字列で返す", function()
      local lines = activity_bar.render_lines()
      assert.are.same(#activity_bar.PANELS * activity_bar.ROWS_PER_PANEL, #lines)
      for i, panel in ipairs(activity_bar.PANELS) do
        local icon_line = (i - 1) * activity_bar.ROWS_PER_PANEL + 2
        assert.is_true(lines[icon_line]:find(panel.icon, 1, true) ~= nil)
      end
    end)
  end)
end)
