-- markdownlint-cli2 の設定探索は対象ファイルのディレクトリから cwd までしか遡らないため、
-- ホーム直下に置いた設定はリポジトリ内のファイルには効かない。パスを明示的に渡す。
local markdownlint_config = vim.fn.expand("~/.markdownlint-cli2.yaml")

return {
  {
    "mfussenegger/nvim-lint",
    optional = true,
    opts = function(_, opts)
      opts.linters_by_ft = opts.linters_by_ft or {}
      opts.linters_by_ft.markdown = {}
      local linter = require("lint").linters["markdownlint-cli2"]
      linter.args = { "--config", markdownlint_config, "-" }
      return opts
    end,
  },
  {
    "stevearc/conform.nvim",
    optional = true,
    opts = {
      formatters = {
        ["markdownlint-cli2"] = {
          prepend_args = { "--config", markdownlint_config },
        },
      },
    },
  },
  {
    "iamcco/markdown-preview.nvim",
    enabled = false,
  },
  {
    "MeanderingProgrammer/render-markdown.nvim",
    optional = true,
    opts = {
      pipe_table = {
        enabled = false,
      },
    },
  },
}
