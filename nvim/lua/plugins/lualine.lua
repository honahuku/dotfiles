return {
  {
    "nvim-lualine/lualine.nvim",
    opts = function(_, opts)
      -- LazyVim標準のlualine_x[2]はnoiceのコマンド表示(Statement色固定)、[3]は
      -- モード表示(Constant色固定)で、どちらもvisual選択時等に赤系で常時表示され、
      -- IME全角時の警告色と紛らわしい。赤くするのはIME表示自体だけにしたいため、
      -- ここは色指定を外して他のlualine_xコンポーネントと同じデフォルト色にする。
      for _, idx in ipairs({ 2, 3 }) do
        local noice_component = opts.sections.lualine_x[idx]
        if noice_component then
          noice_component.color = nil
        end
      end

      table.insert(opts.sections.lualine_x, 1, {
        function()
          return require("util.ime").statusline()
        end,
        color = function()
          return require("util.ime").statusline_color()
        end,
      })
      -- 色は利用率で変えず、他のlualine_xコンポーネントと同じデフォルト色に揃える。
      table.insert(opts.sections.lualine_x, 1, {
        function()
          return require("util.ai-usage").statusline()
        end,
      })
    end,
  },
}
