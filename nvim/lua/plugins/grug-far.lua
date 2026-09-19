-- VSCodeのCtrl+H(現在ファイル内置換)/Ctrl+Shift+H(ワークスペース置換)相当
return {
  "MagicDuck/grug-far.nvim",
  opts = {
    openTargetWindow = {
      -- 検索結果は左側のgrug-farから見て右隣のコード編集用windowへ開く
      preferredLocation = "right",
      exclude = { "activity-bar", "neo-tree", "grug-far", "grug-far-history", "grug-far-help" },
    },
  },
  keys = {
    {
      "<C-h>",
      function()
        require("util.activity-bar").open_search({
          prefills = { paths = vim.fn.expand("%") },
          transient = true,
        })
      end,
      mode = { "n", "v" },
      desc = "ファイル内を置換",
    },
    {
      "<C-S-h>",
      function()
        require("util.activity-bar").open_search({ transient = true })
      end,
      mode = { "n", "v" },
      desc = "ワークスペース全体を置換",
    },
  },
}
