return {
  {
    -- VSCode同様フォルダ単位でセッションを分ける(gitブランチ単位の既定は使わない)
    "folke/persistence.nvim",
    opts = { branch = false },
    init = function()
      -- sessionoptionsが特殊バッファを保存できずゴーストウィンドウが残るため、
      -- 保存前にサイドバー・ターミナルを閉じる(復元時はutil.projectのpick_project側で開き直す)
      vim.api.nvim_create_autocmd("User", {
        pattern = "PersistenceSavePre",
        callback = function()
          pcall(vim.cmd, "Neotree close")
          for _, win in ipairs(vim.api.nvim_list_wins()) do
            local buf = vim.api.nvim_win_get_buf(win)
            if vim.bo[buf].buftype == "terminal" then
              pcall(vim.api.nvim_win_close, win, true)
            end
          end
        end,
      })

      -- VSCodeのReload Window相当。VimLeavePreの自動保存に任せず明示的に保存し、
      -- 復元先を引き継ぎファイルに書いてから終了する。
      -- :restartはnoice.nvim等のUI再アタッチ処理と相性が悪くsegfaultするため使わない。
      -- 終了後は手動でnvimを起動し直す必要があり、util.project.open_on_startupが
      -- 引き継ぎファイルを見てセッションを復元する
      vim.api.nvim_create_user_command("Reload", function()
        local project = require("util.project")
        local persistence = require("persistence")
        persistence.fire("SavePre")
        persistence.save()
        local cwd = vim.fn.getcwd()
        local session = persistence.current()
        vim.fn.writefile({ cwd, session }, project.reload_marker)
        project.log("reload: cwd=" .. cwd .. " session=" .. session)
        vim.cmd("qa")
      end, {
        desc = "Neovimを再起動(セッションを保存して終了。再度nvimを起動すると復元する)",
      })
    end,
  },

  {
    "folke/snacks.nvim",
    keys = {
      {
        "<leader>fp",
        function()
          require("util.project").pick_project()
        end,
        desc = "プロジェクト",
      },
      {
        "<C-r>",
        function()
          require("util.project").pick_project()
        end,
        desc = "最近のプロジェクト",
      },
    },
    opts = function(_, opts)
      -- dashboardの自動起動を止め、引数なし起動時はutil.project.open_on_startupの
      -- pick_project(直近順のディレクトリ一覧)だけを表示する。
      -- 自動起動しないだけで、手動でのSnacks.dashboard()呼び出しやpreset自体は残す
      opts.dashboard.enabled = false
      table.insert(opts.dashboard.preset.keys, 3, {
        action = function()
          require("util.project").pick_project()
        end,
        desc = "プロジェクト",
        icon = " ",
        key = "P",
      })
    end,
  },
}
