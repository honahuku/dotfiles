return {
  {
    "nvim-lualine/lualine.nvim",
    opts = function(_, opts)
      local function add_coding_agents_usage_component(sections)
        sections.lualine_x = sections.lualine_x or {}
        table.insert(sections.lualine_x, 1, {
          function()
            return require("util.coding-agents-usage").statusline()
          end,
        })
      end

      local function resolve_extension(extension)
        if type(extension) ~= "string" then
          return extension
        end

        local ok, resolved = pcall(require, "lualine.extensions." .. extension)
        return ok and resolved or extension
      end

      table.insert(opts.sections.lualine_x, 1, {
        function()
          return require("util.coding-agents-usage").statusline()
        end,
      })

      for index, extension in ipairs(opts.extensions or {}) do
        extension = resolve_extension(extension)
        if type(extension) == "table" and type(extension.sections) == "table" then
          extension = vim.deepcopy(extension)
          add_coding_agents_usage_component(extension.sections)
          if extension.inactive_sections then
            add_coding_agents_usage_component(extension.inactive_sections)
          end
          opts.extensions[index] = extension
        end
      end
    end,
  },
}
