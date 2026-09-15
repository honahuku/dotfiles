-- save.luaの純粋関数（保存先パスの正規化）だけを対象にする。
-- vim.ui.input・vim.cmd.writeを含むsave_current_buffer()はheadlessテストで
-- 検証しづらいため対象外（bufdelete_specと同じ判断基準）。
---@diagnostic disable: undefined-global, undefined-field
local save = require("util.save")

describe("save", function()
  describe("normalize_save_path", function()
    it("前後の空白を取り除く", function()
      assert.are.same("/tmp/foo.txt", save.normalize_save_path("  /tmp/foo.txt  "))
    end)

    it("nilならnil(入力キャンセル)", function()
      assert.is_nil(save.normalize_save_path(nil))
    end)

    it("空文字ならnil", function()
      assert.is_nil(save.normalize_save_path(""))
    end)

    it("空白のみならnil", function()
      assert.is_nil(save.normalize_save_path("   "))
    end)
  end)

  describe("needs_filename", function()
    it("名前なしバッファならtrue", function()
      assert.is_true(save.needs_filename(""))
    end)

    it("名前があればfalse", function()
      assert.is_false(save.needs_filename("/tmp/foo.txt"))
    end)
  end)

  describe("format_write_error", function()
    it("okならnil(通知不要)", function()
      assert.is_nil(save.format_write_error(true, nil))
    end)

    it("失敗ならエラー内容を含む通知文字列", function()
      local message = save.format_write_error(false, "Vim:E45: 'readonly' option is set (add ! to override)")
      assert.is_not_nil(message:find("E45", 1, true))
    end)
  end)
end)
