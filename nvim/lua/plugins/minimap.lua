-- VSCode右上のミニマップに相当。フォーカス可能なウィンドウにすることで
-- マウスのクリック・ドラッグでその位置にジャンプできる(codewindow.nvimはfocusable=false固定でこれができなかった)
return {
  {
    "nvim-mini/mini.map",
    event = "VeryLazy",
    opts = function()
      local map = require("mini.map")
      return {
        integrations = {
          map.gen_integration.builtin_search(),
          map.gen_integration.diagnostic(),
          map.gen_integration.diff(),
        },
        symbols = {
          encode = map.gen_encode_symbols.dot("4x2"),
        },
        window = {
          side = "right",
          width = 10,
          winblend = 0,
          focusable = true,
          show_integration_count = false,
        },
      }
    end,
    keys = {
      {
        "<leader>mm",
        function()
          local map = require("mini.map")
          local minimap = require("util.minimap")
          if minimap.should_show(vim.bo.buftype, vim.wo.wrap) then
            map.toggle()
          else
            map.close()
          end
        end,
        desc = "ミニマップの表示切り替え",
      },
      {
        "<leader>mf",
        function()
          require("mini.map").toggle_focus()
        end,
        desc = "ミニマップへのフォーカス切り替え",
      },
    },
    config = function(_, opts)
      local map = require("mini.map")
      local minimap = require("util.minimap")
      map.setup(opts)

      -- mini.mapは本文の上に浮くため、折り返し表示中は末尾の文字を隠さない。
      local function sync_visibility()
        if minimap.should_show(vim.bo.buftype, vim.wo.wrap) then
          map.open()
        else
          map.close()
        end
      end

      vim.api.nvim_create_autocmd({ "BufEnter", "WinEnter", "OptionSet" }, {
        group = vim.api.nvim_create_augroup("minimap_file_only", { clear = true }),
        pattern = "wrap",
        callback = sync_visibility,
      })

      -- event="VeryLazy"はVimEnterより後に適用されるため、VimEnterを待たずここで直接反映する
      sync_visibility()
    end,
  },
}
