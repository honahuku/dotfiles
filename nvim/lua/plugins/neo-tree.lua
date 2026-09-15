-- VSCode のアクティビティバー相当。左パネルをfilesystem/buffers/git_statusで切り替える
return {
  {
    "nvim-neo-tree/neo-tree.nvim",
    opts = {
      source_selector = {
        winbar = true,
        statusline = false,
      },
      -- dotfileやgitignore対象を「N hidden items」に畳まず常に表示する
      filesystem = {
        -- LazyVimのデフォルトはfalse。:cd実行後もneo-treeのrootが起動時ディレクトリに固定されたままになるため、
        -- vimのcwdとneo-treeのrootを連動させる
        bind_to_cwd = true,
        filtered_items = {
          hide_dotfiles = false,
          hide_gitignored = false,
        },
      },
      -- デフォルトは"terminal"を含み、ファイルを開く際にターミナルウィンドウの上書きを避ける。
      -- その結果、他に開いているウィンドウが無いと新規splitが作られてしまうため外す。
      -- ターミナルバッファはファイルに置き換わって裏に残るだけで、再度ターミナルを開けば復帰する
      open_files_do_not_replace_types = { "Trouble", "qf" },
      window = {
        -- ファイルを開く操作(Enter・左シングル/ダブルクリック・中クリック)は
        -- すべてutil.activity-bar.open_in_editorへ差し替える。sidebar windowは
        -- position=currentで開いているため、既定の"open"だとそのまま
        -- ファイルに置き換わってツリーが消えてしまう。デフォルトの
        -- "<2-LeftMouse>"を見落として<LeftMouse>だけ差し替えていたため、
        -- ダブルクリック相当の入力で再発した(2026-08-10)。中クリックも
        -- VSCode同様bufferlineへ新規タブ追加する用途で残す
        mappings = {
          ["<cr>"] = function(state)
            require("util.activity-bar").open_in_editor(state)
          end,
          ["<LeftMouse>"] = function(state)
            require("util.activity-bar").open_in_editor(state)
          end,
          ["<2-LeftMouse>"] = function(state)
            require("util.activity-bar").open_in_editor(state)
          end,
          ["<MiddleMouse>"] = function(state)
            require("util.activity-bar").open_in_editor(state)
          end,
          -- デフォルトのrenameキー"r"に加え、VSCode同様F2でもリネームできるようにする
          ["<F2>"] = "rename",
        },
      },
    },
    -- LazyVim標準の<leader>e系はNeotree toggleを直に呼ぶが、activity-bar導入後は
    -- Explorerパネルへのフォーカスに意味を変える(常時表示のため開閉の概念が無い)
    keys = {
      {
        "<leader>e",
        function()
          require("util.activity-bar").select(1)
        end,
        desc = "エクスプローラー(ルートディレクトリ)",
      },
      {
        "<leader>fe",
        function()
          require("util.activity-bar").select(1)
        end,
        desc = "エクスプローラー(ルートディレクトリ)",
      },
      {
        "<leader>E",
        function()
          require("util.activity-bar").select(1, { dir = vim.uv.cwd() })
        end,
        desc = "エクスプローラー(作業ディレクトリ)",
      },
      {
        "<leader>fE",
        function()
          require("util.activity-bar").select(1, { dir = vim.uv.cwd() })
        end,
        desc = "エクスプローラー(作業ディレクトリ)",
      },
    },
    -- 起動時の常時表示はutil.activity-bar.open_on_startup(config/autocmds.lua経由)が
    -- Explorerパネルとして開くため、ここでのVimEnter起動処理は不要
    init = function()
      require("util.activity-bar").enable_guard()
    end,
  },
}
