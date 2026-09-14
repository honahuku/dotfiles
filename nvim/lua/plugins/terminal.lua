-- VSCode の統合ターミナル相当。下部固定パネルとして常時表示する
return {
  {
    "folke/snacks.nvim",
    keys = {
      {
        "<c-`>",
        function()
          require("util.terminal").open_bottom_terminal()
        end,
        desc = "ターミナル(下部)",
        mode = { "n", "t" },
      },
      -- VSCodeのCtrl+J(パネルトグル)相当。下部ターミナルのトグルと同じ役割。
      -- terminalモードでCtrl+Jを拾うと、外側端末がCtrl+Jを改行と区別するために
      -- modifyOtherKeys相当のCSIエンコードを要求する状態になり、貼り付けたテキスト中の
      -- 改行がそのCSIシーケンス(ESC[27;5;106~)として子プロセス(Claude Code等)に
      -- 渡ってしまい、貼り付け内容に生の制御シーケンスが混入する不具合があった。
      -- normalモードだけに絞り、terminalモード中は素の改行を通す
      {
        "<C-j>",
        function()
          require("util.terminal").open_bottom_terminal()
        end,
        desc = "パネルの表示切り替え",
        mode = { "n" },
      },
      -- VSCodeのCtrl+Shift+`(新規ターミナル)相当。openは毎回新規インスタンスを作る
      {
        "<C-S-`>",
        function()
          Snacks.terminal.open(nil, { cwd = LazyVim.root(), win = { position = "bottom", height = 0.3 } })
        end,
        desc = "新しいターミナル",
        mode = { "n", "t" },
      },
    },
  },
}
