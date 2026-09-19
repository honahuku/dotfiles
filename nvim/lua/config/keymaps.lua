-- Keymaps are automatically loaded on the VeryLazy event
-- Default keymaps that are always set: https://github.com/LazyVim/LazyVim/blob/main/lua/lazyvim/config/keymaps.lua
-- Add any additional keymaps here

local map = vim.keymap.set

-- vimデフォルトの<C-z>は:sus(サスペンド)なので、VSCode同様undoに上書きする
map("n", "<C-z>", "u", { desc = "元に戻す" })
map("i", "<C-z>", "<C-o>u", { desc = "元に戻す" })
map("n", "<C-y>", "<C-r>", { desc = "やり直す" })
map("i", "<C-y>", "<C-o><C-r>", { desc = "やり直す" })

-- 選択なしでの行カット・行コピー
map("n", "<C-x>", '"+dd', { desc = "行の切り取り" })
map("n", "<C-c>", '"+yy', { desc = "行のコピー" })
-- 選択範囲のカット・コピー(VSCode同様visual modeでも動くようにする)
map("v", "<C-x>", '"+d', { desc = "切り取り" })
map("v", "<C-c>", '"+y', { desc = "コピー" })

map("i", "<C-CR>", "<Esc>o", { desc = "下に行を挿入" })
map("i", "<C-S-CR>", "<Esc>O", { desc = "上に行を挿入" })

-- LazyVim標準のAlt+j/kと並存する矢印キー版の行移動・行コピー
map("n", "<A-Up>", "<cmd>execute 'move .-' . (v:count1 + 1)<cr>==", { desc = "行を上へ移動" })
map("n", "<A-Down>", "<cmd>execute 'move .+' . v:count1<cr>==", { desc = "行を下へ移動" })
map("v", "<A-Up>", ":<C-u>execute \"'<,'>move '<-\" . (v:count1 + 1)<cr>gv=gv", { desc = "行を上へ移動" })
map("v", "<A-Down>", ":<C-u>execute \"'<,'>move '>+\" . v:count1<cr>gv=gv", { desc = "行を下へ移動" })
map("n", "<S-A-Up>", "<cmd>t-1<cr>", { desc = "行を上へコピー" })
map("n", "<S-A-Down>", "<cmd>t.<cr>", { desc = "行を下へコピー" })
map("v", "<S-A-Up>", ":t-1<cr>gv", { desc = "選択範囲を上へコピー" })
map("v", "<S-A-Down>", ":t.<cr>gv", { desc = "選択範囲を下へコピー" })

map("n", "<C-Home>", "gg", { desc = "ファイルの先頭へ移動" })
map("n", "<C-End>", "G", { desc = "ファイルの末尾へ移動" })
map("n", "<C-g>", ":", { desc = "行へ移動" })

-- ターミナルフォーカス(LazyVim標準の<C-/>)はCtrl+`(bottom terminal)と役割が重複するため、コメントトグルへ差し替える
map("n", "<C-/>", "gcc", { remap = true, desc = "行コメントの切り替え" })
map("v", "<C-/>", "gc", { remap = true, desc = "行コメントの切り替え" })

map("n", "<C-p>", function()
  Snacks.picker.files()
end, { desc = "ファイルを検索" })
map("n", "<C-o>", function()
  Snacks.picker.files()
end, { desc = "ファイルを開く" })
map("n", "<C-S-p>", function()
  Snacks.picker.commands()
end, { desc = "コマンドパレット" })
map("n", "<C-S-f>", function()
  Snacks.picker.grep()
end, { desc = "ワークスペース全体を検索" })
map("n", "<C-S-o>", function()
  Snacks.picker.lsp_symbols()
end, { desc = "シンボルへ移動" })
map("n", "<C-t>", function()
  Snacks.picker.lsp_workspace_symbols()
end, { desc = "ワークスペース内のシンボルへ移動" })

map("n", "<F12>", vim.lsp.buf.definition, { desc = "定義へ移動" })
map("n", "<S-F12>", vim.lsp.buf.references, { desc = "参照へ移動" })
map("n", "<F2>", vim.lsp.buf.rename, { desc = "シンボル名の変更" })

map("n", "<C-\\>", "<C-w>v", { desc = "エディタの分割" })
map("n", "<C-b>", function()
  require("util.activity-bar").toggle()
end, { desc = "サイドバーの表示切り替え" })

map("n", "<leader>ct", function()
  require("util.time-difference").open()
end, { desc = "時刻差分を計算" })

map({ "n", "v" }, "<C-a>", "ggVG", { desc = "すべて選択" })
map("i", "<C-a>", "<Esc>ggVG", { desc = "すべて選択" })

map("n", "<C-Tab>", "<cmd>BufferLineCycleNext<cr>", { desc = "次のタブ" })
map("n", "<C-S-Tab>", "<cmd>BufferLineCyclePrev<cr>", { desc = "前のタブ" })
-- ターミナルモードではキーがそのまま中のアプリに渡り、上のマッピングが効かない。
-- Escはターミナル内のアプリが使うため、ノーマルモードへ抜ける操作込みで割り当てる
map("t", "<C-Tab>", "<C-\\><C-n><cmd>BufferLineCycleNext<cr>", { desc = "次のタブ" })
map("t", "<C-S-Tab>", "<C-\\><C-n><cmd>BufferLineCyclePrev<cr>", { desc = "前のタブ" })

-- vimデフォルトの<C-n>は下移動(j相当)だが、j/矢印で代替できるため上書きする
map("n", "<C-n>", "<cmd>enew<cr>", { desc = "新しいファイル" })

-- vimデフォルトの<C-w>プレフィックス(分割・削除等)は<leader>-/<leader>|/<leader>wdで代替できるため上書きする
-- ターミナルバッファは実行中のコマンドがあれば閉じる前に確認する(util.terminal.confirm_close)
-- バッファを閉じる処理自体はutil.bufdelete.closeに委ねる(名前なしバッファのE32対策)
map("n", "<C-w>", function()
  if require("util.terminal").confirm_close() then
    require("util.bufdelete").close()
  end
end, { desc = "バッファを閉じる" })
-- LazyVim標準の<leader>bdも同じ確認を通す
map("n", "<leader>bd", function()
  if require("util.terminal").confirm_close() then
    require("util.bufdelete").close()
  end
end, { desc = "バッファを削除" })

-- vimデフォルトの<C-f>は1画面下スクロールだが、<PageDown>で代替できるため上書きする
map({ "n", "v" }, "<C-f>", "/", { desc = "検索" })

-- ジャンプリストでの戻る/進む
map("n", "<A-Left>", "<C-o>", { desc = "戻る" })
map("n", "<A-Right>", "<C-i>", { desc = "進む" })
-- マウスの戻る/進むボタン。Alacrittyが該当ボタンを送信するかは実機未検証
map("n", "<X1Mouse>", "<C-o>", { desc = "戻る(マウス)" })
map("n", "<X2Mouse>", "<C-i>", { desc = "進む(マウス)" })

map({ "n", "v" }, "<C-.>", vim.lsp.buf.code_action, { desc = "クイックフィックス" })
map("n", "<C-S-m>", "<cmd>Trouble diagnostics toggle<cr>", { desc = "問題" })
map("n", "<F8>", function()
  vim.diagnostic.jump({ count = 1, float = true })
end, { desc = "次の問題" })
map("n", "<S-F8>", function()
  vim.diagnostic.jump({ count = -1, float = true })
end, { desc = "前の問題" })

map({ "n", "v" }, "<C-S-\\>", "%", { remap = true, desc = "対応する括弧へ移動" })

-- <C-LeftMouse>は既定でtagfunc経由のLSP定義ジャンプに使われるが、F12と挙動を揃えて明示する
map("n", "<C-LeftMouse>", "<LeftMouse><cmd>lua vim.lsp.buf.definition()<cr>", { desc = "定義へ移動(マウス)" })

map("n", "<C-PageDown>", "<cmd>BufferLineCycleNext<cr>", { desc = "次のタブ" })
map("n", "<C-PageUp>", "<cmd>BufferLineCyclePrev<cr>", { desc = "前のタブ" })

-- 閉じたバッファをスタックに積み、Ctrl+Shift+Tで再オープンする
local closed_buffers = {}
vim.api.nvim_create_autocmd("BufDelete", {
  callback = function(ev)
    local name = vim.api.nvim_buf_get_name(ev.buf)
    if vim.bo[ev.buf].buftype == "" and name ~= "" and vim.fn.filereadable(name) == 1 then
      for i = #closed_buffers, 1, -1 do
        if closed_buffers[i] == name then
          table.remove(closed_buffers, i)
        end
      end
      table.insert(closed_buffers, name)
    end
  end,
})
map("n", "<C-S-t>", function()
  local name = table.remove(closed_buffers)
  if name then
    vim.cmd.edit(vim.fn.fnameescape(name))
  end
end, { desc = "閉じたバッファを再度開く" })

-- 選択なしでの行削除(クリップボードを汚さないblackholeレジスタ)
map("n", "<C-S-k>", '"_dd', { desc = "行を削除" })
map("v", "<C-S-k>", '"_d', { desc = "選択範囲を削除" })

-- 押すたび1行ずつ拡張する行選択
map("n", "<C-l>", "V", { desc = "行を選択" })
map("v", "<C-l>", "j", { desc = "行選択を拡張" })

map("n", "<A-z>", "<cmd>set wrap!<cr>", { desc = "折り返しの切り替え" })

map({ "n", "v" }, "<S-A-f>", function()
  LazyVim.format({ force = true })
end, { desc = "ドキュメントのフォーマット" })

-- nvim 0.12ビルトインのtreesitter選択拡張(v_an/v_in)を利用する
map("n", "<S-A-Right>", "van", { remap = true, desc = "選択範囲を拡張" })
map("v", "<S-A-Right>", "an", { remap = true, desc = "選択範囲を拡張" })
map("v", "<S-A-Left>", "in", { remap = true, desc = "選択範囲を縮小" })

map("n", "<C-S-e>", function()
  require("util.activity-bar").select(1)
end, { desc = "エクスプローラーにフォーカス" })
map("n", "<C-S-g>", function()
  require("util.activity-bar").select(3)
end, { desc = "ソース管理" })

-- VSCodeのCtrl+K S(すべてのファイルを保存)相当
map("n", "<C-k>s", "<cmd>wa<cr>", { desc = "すべてのファイルを保存" })

-- LazyVim標準の<C-s>(vim.cmd.write())は名前なしバッファでE32: No file nameで落ちるため、
-- 保存先を尋ねてから保存するutil.saveへ差し替える(util.bufdelete.closeと同じ対策)
map({ "n", "x", "s" }, "<C-s>", function()
  require("util.save").save_current_buffer()
end, { desc = "ファイルを保存" })
map("i", "<C-s>", function()
  vim.cmd.stopinsert()
  require("util.save").save_current_buffer()
end, { desc = "ファイルを保存" })

-- VSCodeのCtrl+Shift+[ / Ctrl+Shift+](折りたたみ・展開)相当。treesitterのfoldを利用する
map("n", "<C-S-[>", "zc", { desc = "折りたたむ" })
map("n", "<C-S-]>", "zo", { desc = "展開する" })

-- VSCodeのF3/Shift+F3(次・前の検索結果)相当。vim標準のn/Nと役割は重複するが、直後にF3でも送れるようにする
-- LazyVim標準のn/N(検索方向を考慮したexprマッピング)へremapする
map("n", "<F3>", "n", { remap = true, desc = "次を検索" })
map("n", "<S-F3>", "N", { remap = true, desc = "前を検索" })
