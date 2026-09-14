return {
  {
    "folke/snacks.nvim",
    keys = {
      {
        "<leader>cx",
        function()
          require("util.codex").open_codex()
        end,
        desc = "Codex",
      },
    },
  },
}
