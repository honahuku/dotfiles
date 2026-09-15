local theme = require("platform.theme")

theme.setup()

return {
  { "projekt0n/github-nvim-theme", lazy = false, priority = 1000 },
  {
    "LazyVim/LazyVim",
    opts = {
      colorscheme = require("platform.theme").colorscheme_for(vim.o.background) or "github_dark_dimmed",
    },
  },
}
