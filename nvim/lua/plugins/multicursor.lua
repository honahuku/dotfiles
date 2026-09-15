-- VSCodeのマルチカーソル相当(Ctrl+D/Ctrl+Shift+L/Alt+Click/Ctrl+Alt+Up/Down)
-- vim-visual-multiは既定のCtrl+Nが新規ファイル(keymaps.lua)と衝突し、マウス対応も無いため不採用
return {
  "jake-stewart/multicursor.nvim",
  event = "VeryLazy",
  config = function()
    local mc = require("multicursor-nvim")
    mc.setup()

    local set = vim.keymap.set
    set({ "n", "v" }, "<C-d>", function()
      mc.matchAddCursor(1)
    end, { desc = "次の一致箇所にカーソルを追加" })
    set({ "n", "v" }, "<C-S-l>", mc.matchAllAddCursors, { desc = "すべての一致箇所を選択" })
    set({ "n", "v" }, "<C-A-Up>", function()
      mc.lineAddCursor(-1)
    end, { desc = "上にカーソルを追加" })
    set({ "n", "v" }, "<C-A-Down>", function()
      mc.lineAddCursor(1)
    end, { desc = "下にカーソルを追加" })

    -- VSCodeのAlt+Click相当(Ctrl+Clickは定義ジャンプに使用済みのためAltを採用)
    set("n", "<M-LeftMouse>", mc.handleMouse)
    set("n", "<M-LeftDrag>", mc.handleMouseDrag)
    set("n", "<M-LeftRelease>", mc.handleMouseRelease)

    -- マルチカーソル中の補完メニュー確定はメインカーソルにのみ適用される制約がある
    -- (blink.cmp, https://github.com/jake-stewart/multicursor.nvim/issues/74)

    mc.addKeymapLayer(function(layerSet)
      layerSet("n", "<Esc>", function()
        if not mc.cursorsEnabled() then
          mc.enableCursors()
        else
          mc.clearCursors()
        end
      end)
    end)
  end,
}
