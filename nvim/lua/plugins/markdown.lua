return {
  {
    "mfussenegger/nvim-lint",
    optional = true,
    opts = function(_, opts)
      opts.linters_by_ft = opts.linters_by_ft or {}
      opts.linters_by_ft.markdown = {}
      return opts
    end,
  },
  {
    "stevearc/conform.nvim",
    optional = true,
    opts = function(_, opts)
      -- Markdown用のCLIを導入し直さないよう、LazyVimから継承した対象も外す。
      for _, ft in ipairs({ "markdown", "markdown.mdx" }) do
        opts.formatters_by_ft[ft] = vim.tbl_filter(function(formatter)
          return formatter ~= "markdown-toc" and formatter ~= "markdownlint-cli2"
        end, opts.formatters_by_ft[ft] or {})
      end
      opts.formatters["markdown-toc"] = nil
      opts.formatters["markdownlint-cli2"] = nil
    end,
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
