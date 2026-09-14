-- bufdelete.luaの純粋関数（判定・パス正規化）だけを対象にする。
-- Snacks.bufdelete呼び出し・vim.ui.input・vim.api.nvim_buf_callを含む
-- close()はheadlessテストで検証しづらいため対象外（ai-usage_specと同じ判断基準）。
---@diagnostic disable: undefined-global, undefined-field
local bufdelete = require("util.bufdelete")

describe("bufdelete", function()
  describe("needs_save_as", function()
    it("名前なしバッファに変更があればtrue", function()
      assert.is_true(bufdelete.needs_save_as("", true))
    end)

    it("名前なしバッファでも変更がなければfalse", function()
      assert.is_false(bufdelete.needs_save_as("", false))
    end)

    it("名前があれば変更の有無にかかわらずfalse", function()
      assert.is_false(bufdelete.needs_save_as("/tmp/foo.txt", true))
    end)
  end)

  describe("select_idx_to_action", function()
    it("idx=1(名前を付けて保存)はsave_as", function()
      assert.are.same("save_as", bufdelete.select_idx_to_action(1))
    end)

    it("idx=2(保存せず閉じる)はdiscard", function()
      assert.are.same("discard", bufdelete.select_idx_to_action(2))
    end)

    it("idx=3(キャンセル)はcancel", function()
      assert.are.same("cancel", bufdelete.select_idx_to_action(3))
    end)

    it("idx=nil(Escでの選択キャンセル)もcancel", function()
      assert.are.same("cancel", bufdelete.select_idx_to_action(nil))
    end)
  end)

  describe("normalize_save_path", function()
    it("前後の空白を取り除く", function()
      assert.are.same("/tmp/foo.txt", bufdelete.normalize_save_path("  /tmp/foo.txt  "))
    end)

    it("nilならnil（入力キャンセル）", function()
      assert.is_nil(bufdelete.normalize_save_path(nil))
    end)

    it("空文字ならnil", function()
      assert.is_nil(bufdelete.normalize_save_path(""))
    end)

    it("空白のみならnil", function()
      assert.is_nil(bufdelete.normalize_save_path("   "))
    end)
  end)
end)
