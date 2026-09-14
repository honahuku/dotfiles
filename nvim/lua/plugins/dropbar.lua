-- VSCodeのブレッドクラム相当。クリック可能なシンボルパスをwinbarに表示する
return {
  "Bekaboo/dropbar.nvim",
  event = "VeryLazy",
  opts = {
    bar = {
      -- neo-treeのsource_selectorやedgyの管理ウィンドウ、ターミナルなど
      -- 既存winbarを使うウィンドウ・特殊バッファには重ねない
      enable = function(buf, win)
        if not vim.api.nvim_buf_is_valid(buf) or not vim.api.nvim_win_is_valid(win) then
          return false
        end
        if vim.fn.win_gettype(win) ~= "" then
          return false
        end
        if vim.wo[win].winbar ~= "" then
          return false
        end
        if vim.bo[buf].buftype ~= "" then
          return false
        end
        local exclude_ft = { "neo-tree", "edgy", "trouble", "grug-far", "snacks_terminal", "snacks_picker_list" }
        return not vim.tbl_contains(exclude_ft, vim.bo[buf].filetype)
      end,
    },
  },
}
