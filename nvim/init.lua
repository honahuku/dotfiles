if vim.fn.has("win32") == 1 then
  -- Windowsの起動時はローダーが再有効化されるため、VimEnter後に止める。
  vim.api.nvim_create_autocmd("VimEnter", {
    once = true,
    callback = function()
      vim.loader.enable(false)
    end,
  })
end

require("config.bootstrap")
