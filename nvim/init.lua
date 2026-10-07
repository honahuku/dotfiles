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

-- privateは任意のruntimepath拡張として読み込む。public設定だけでも起動できるようにする。
do
  local private_root = vim.fn.stdpath("config") .. "-private"

  if vim.fn.isdirectory(private_root) == 1 then
    vim.opt.rtp:append(private_root)

    local ok, private = pcall(require, "private")
    if not ok then
      vim.notify("private設定の読み込みに失敗しました: " .. tostring(private), vim.log.levels.WARN)
    elseif type(private) ~= "table" or type(private.setup) ~= "function" then
      vim.notify("private設定はsetup関数を持つテーブルを返す必要があります", vim.log.levels.WARN)
    else
      local setup_ok, err = pcall(private.setup)
      if not setup_ok then
        vim.notify("private設定の初期化に失敗しました: " .. tostring(err), vim.log.levels.WARN)
      end
    end
  end
end

-- bootstrap lazy.nvim, LazyVim and your plugins
require("config.lazy")
