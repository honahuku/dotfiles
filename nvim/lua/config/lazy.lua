local lazypath = vim.fn.stdpath("data") .. "/lazy/lazy.nvim"
if not (vim.uv or vim.loop).fs_stat(lazypath) then
    local lazyrepo = "https://github.com/folke/lazy.nvim.git"
    local out = vim.fn.system({ "git", "clone", "--filter=blob:none", "--branch=stable", lazyrepo, lazypath })
    if vim.v.shell_error ~= 0 then
        vim.api.nvim_echo({
            { "Failed to clone lazy.nvim:\n", "ErrorMsg" },
            { out,                            "WarningMsg" },
            { "\nPress any key to exit..." },
        }, true, {})
        vim.fn.getchar()
        os.exit(1)
    end
end
vim.opt.rtp:prepend(lazypath)

require("lazy").setup({
    spec = {
        -- LazyVimを追加し、付属のプラグインを読み込む。
        { "LazyVim/LazyVim",                                import = "lazyvim.plugins" },
        -- 追加の拡張モジュールはここで読み込む。
        { import = "lazyvim.plugins.extras.lang.terraform" },
        { import = "lazyvim.plugins.extras.lang.json" },
        { import = "lazyvim.plugins.extras.lang.yaml" },
        { import = "lazyvim.plugins.extras.lang.markdown" },
        { import = "lazyvim.plugins.extras.lang.git" },
        { import = "lazyvim.plugins.extras.editor.neo-tree" },
        -- ui.edgyはneo-tree等のwindowを自前のedgebarレイアウトで非同期に再配置し直す
        -- ため、util.activity-barが手動で組む固定split(左端バー+content window)と
        -- 衝突する。edgyの再配置がactivity-barのwindowを「普通の編集用window」と
        -- 誤認して幅・位置を奪い、ファイルを開いた先がずれる不具合が出ていた(2026-08-10)
        -- 自分のプラグインを読み込み、設定を上書きする。
        { import = "plugins" },
        -- CLIはaqua/miseで管理し、Masonによる導入・PATH変更がされないようにする。
        { "mason-org/mason.nvim",                           enabled = false },
        { "mason-org/mason-lspconfig.nvim",                 enabled = false },
    },
    defaults = {
        -- 既定ではLazyVimのプラグインだけを遅延読み込みし、自分のプラグインは起動時に読み込む。
        -- 動作を理解したうえでtrueにすると、自分のプラグインも既定で遅延読み込みする。
        lazy = false,
        -- バージョン指定に対応していてもリリースが古いプラグインが多く、
        -- Neovimの動作を壊すおそれがあるため、当面はversion=falseを推奨する。
        version = false, -- 常に最新のGitコミットを使う。
        -- version = "*", -- semver対応プラグインの最新安定版を使う場合の設定。
    },
    install = { colorscheme = { "tokyonight", "habamax" } },
    checker = {
        enabled = true, -- プラグインの更新を定期的に確認する。
        notify = false, -- 更新時に通知する。
    },              -- プラグインの更新を自動確認する。
    performance = {
        rtp = {
            -- 一部の標準プラグインを読み込み対象から外す。
            disabled_plugins = {
                "gzip",
                -- "matchit",
                -- "matchparen",
                -- "netrwPlugin",
                "tarPlugin",
                "tohtml",
                "tutor",
                "zipPlugin",
            },
        },
    },
})

