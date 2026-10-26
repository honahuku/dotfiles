-- LazyGit から現在の Neovim にファイルを開けるようにする
do
  local server = vim.v.servername

  if server == "" then
    server = vim.fn.serverstart(vim.fs.joinpath(vim.fn.stdpath("run"), "nvim-" .. vim.fn.getpid() .. ".sock"))
  end

  vim.env.NVIM = server
end

vim.env.EDITOR = "nvim"
vim.env.VISUAL = "nvim"

-- lazy.nvim・LazyVim・自分のプラグインを初期化する。
require("config.lazy")
