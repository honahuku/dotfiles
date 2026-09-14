return {
  {
    "folke/snacks.nvim",
    keys = {
      {
        "<leader>cc",
        function()
          require("util.claude").open_claude()
        end,
        desc = "Claude Code",
      },
    },
  },
}
