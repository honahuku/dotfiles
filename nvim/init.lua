-- トラブルシューティング用: lazy.nvim読み込み前に起動を記録する
-- (VimEnterイベントが起きない場合、起動自体の失敗かプラグイン読み込み失敗かを切り分けるため)
do
  local log_path = vim.fs.joinpath(vim.fn.stdpath("state"), "reload.log")
  local file = io.open(log_path, "a")
  if file then
    file:write(os.date("%Y-%m-%d %H:%M:%S ") .. "init.lua: nvim starting, argc=" .. vim.fn.argc() .. "\n")
    file:close()
  end
end

-- LazyGit から現在の Neovim にファイルを開けるようにする
do
  local server = vim.v.servername

  if server == "" then
    local ok, started_server =
      pcall(vim.fn.serverstart, vim.fs.joinpath(vim.fn.stdpath("run"), "nvim-" .. vim.fn.getpid() .. ".sock"))
    if ok then
      server = started_server
    end
  end

  if server ~= "" then
    vim.env.NVIM = server
  end
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
    elseif type(private.setup) == "function" then
      local setup_ok, err = pcall(private.setup)
      if not setup_ok then
        vim.notify("private設定の初期化に失敗しました: " .. tostring(err), vim.log.levels.WARN)
      end
    end
  end
end

-- bootstrap lazy.nvim, LazyVim and your plugins
require("config.lazy")
