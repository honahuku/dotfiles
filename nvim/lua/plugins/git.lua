-- VSCode の GitLens / Git History / Git Graph 相当
return {
  {
    "sindrets/diffview.nvim",
    cmd = { "DiffviewOpen", "DiffviewFileHistory" },
    keys = {
      { "<leader>gd", "<cmd>DiffviewOpen<cr>", desc = "差分を表示" },
      { "<leader>gh", "<cmd>DiffviewFileHistory %<cr>", desc = "ファイルの履歴" },
    },
  },
}
