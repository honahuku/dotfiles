-- VSCodeのアクティビティバー相当。左端に固定幅のwindowを置き、
-- Explorer/Search/SCMを1キーで切り替える。中身はneo-tree(filesystem/git_status)と
-- grug-far(検索・置換)を同じsidebar windowへ出し分けるだけで、切り替え先の実体は
-- 既存プラグインをそのまま流用する。
--
-- sidebar windowの位置は、bar・sidebarともに自分たちで作った時点のまま固定する
-- (Neotree showは`position=current`で、現在のwindowに描画するだけ)。
-- neo-tree自身に配置を任せる`position=left`は自分でタブページ最左端に新規splitを
-- 作ってしまい、すでに開いているbarを押しのける。バーを列0へ戻す作り直しを都度
-- 挟む設計は、その作り直し中に閉じるイベントとWinClosedガードの再オープンが
-- 競合してbar windowが重複することがあり(2026-08-10)、position=currentに戻して
-- 位置そのものを動かさない設計にした
--
-- `position=current`はもともと「ファイルを開くとツリーがそのまま消える」問題があった
-- (neo-tree.utils.get_appropriate_windowによる「自分自身を上書きしない」保護は
-- state.current_position=="current"だと素通りする)。そのため、ファイルを開く
-- 操作(<CR>・クリック)自体をこのモジュール側でeditor windowへ横取りする
-- (plugins/neo-tree.luaのwindow.mappingsからM.open_in_editorを参照)
local M = {}

--- ファイルを選択したときにeditor windowへ開き直す。ディレクトリなどの
--- 開閉可能な項目は既定の開閉動作(トグル)のままにする
---@param state table neo-treeのstate
local function open_in_editor(state)
  local node = state.tree:get_node()
  if require("neo-tree.utils").is_expandable(node) then
    require("neo-tree.sources.filesystem.commands").open(state)
    return
  end
  local path = node.path or node:get_id()
  vim.api.nvim_set_current_win(M.ensure_editor_win())
  vim.cmd("edit " .. vim.fn.fnameescape(path))
end
M.open_in_editor = open_in_editor

--- パネル定義。1行1パネルで、行番号=配列indexとして扱う
M.PANELS = {
  {
    key = "1",
    icon = "",
    label = "Explorer",
    ---@param opts { dir?: string }?
    open = function(opts)
      local dir_arg = (opts and opts.dir) and (" dir=" .. vim.fn.fnameescape(opts.dir)) or ""
      vim.cmd("Neotree show filesystem position=current" .. dir_arg)
    end,
  },
  {
    key = "2",
    icon = "",
    label = "Search",
    open = function()
      M.open_search({ transient = true })
    end,
  },
  {
    key = "3",
    icon = "",
    label = "SCM",
    open = function()
      vim.cmd("Neotree show git_status position=current")
    end,
  },
}

--- キー入力("1"/"2"/"3")に対応するパネルのインデックスを返す
---@param key string?
---@return integer?
function M.panel_index_for_key(key)
  if not key then
    return nil
  end
  for i, panel in ipairs(M.PANELS) do
    if panel.key == key then
      return i
    end
  end
  return nil
end

--- grug-farをNeo-treeと同じsidebarへ開き、検索結果はコード編集用windowへ開く
---@param options table?
function M.open_search(options)
  if not M.is_open() then
    M.open()
  end
  vim.api.nvim_set_current_win(M.sidebar_win)
  local open_options = vim.tbl_extend("force", { windowCreationCommand = "edit" }, options or {})
  require("grug-far").open(open_options)
end

--- カーソル行(1-based)に対応するパネルのインデックスを返す。各パネルは
--- 複数行のボタンとして表示する
---@param line integer
---@return integer?
function M.panel_index_for_line(line)
  if line < 1 or line > #M.PANELS * M.ROWS_PER_PANEL then
    return nil
  end
  return math.floor((line - 1) / M.ROWS_PER_PANEL) + 1
end

--- 各パネルの表示行を組み立てる。アイコンだけをボタンの中央に表示する
---@return string[]
function M.render_lines()
  local lines = {}
  for _, panel in ipairs(M.PANELS) do
    local icon_width = vim.fn.strdisplaywidth(panel.icon)
    local left_padding = math.floor((M.WIDTH - icon_width) / 2)
    local right_padding = M.WIDTH - left_padding - icon_width
    local empty_line = string.rep(" ", M.WIDTH)
    local icon_line = string.rep(" ", left_padding) .. panel.icon .. string.rep(" ", right_padding)
    table.insert(lines, empty_line)
    table.insert(lines, icon_line)
    table.insert(lines, empty_line)
  end
  return lines
end

--- 左端に固定表示するbar window幅(列数)。アイコンと左右の余白
M.WIDTH = 10
--- 1つのパネルに割り当てる行数。中央の行にアイコンを表示する
M.ROWS_PER_PANEL = 3
--- Explorer/Search/SCMが共有するsidebar windowの幅
M.SIDEBAR_WIDTH = 32

local highlight_ns = vim.api.nvim_create_namespace("dotfiles_activity_bar_selected")

M.win = nil
M.buf = nil
-- Explorer/Search/SCMが共有するsidebar window。barのすぐ右に自分たちで作り、
-- 位置は固定のまま内容だけ切り替える
M.sidebar_win = nil
-- ファイルを開く先。open_in_editorが参照する。bar/sidebar作成前にカレントだった
-- windowをそのまま使う
M.editor_win = nil
M.current_index = nil

-- persistence.nvimのセッション復元スクリプトは`silent only`/`silent tabonly`で
-- windowを1つに畳む。M.winがそのタイミングでcurrent windowだった場合、
-- window自体はそのbufのまま生き残り全画面化するだけなので、bufの一致まで見て
-- 初めて「乗っ取られていない」と判定できる。sidebar windowは内容が都度変わる
-- ため、有効性だけを見る
---@return boolean
function M.is_open()
  return M.win ~= nil
    and vim.api.nvim_win_is_valid(M.win)
    and vim.api.nvim_win_get_buf(M.win) == M.buf
    and M.sidebar_win ~= nil
    and vim.api.nvim_win_is_valid(M.sidebar_win)
end

--- ファイルを開く先のwindowを取得する。参照が無効なら、bar・sidebar以外の
--- floatでないwindowを探し、それもなければsidebarの右に新規に割る
---@return integer
function M.ensure_editor_win()
  if M.editor_win and vim.api.nvim_win_is_valid(M.editor_win) then
    return M.editor_win
  end
  for _, win in ipairs(vim.api.nvim_tabpage_list_wins(0)) do
    if win ~= M.win and win ~= M.sidebar_win and vim.api.nvim_win_get_config(win).relative == "" then
      M.editor_win = win
      return win
    end
  end
  vim.api.nvim_set_current_win(M.sidebar_win)
  vim.cmd("vsplit")
  M.editor_win = vim.api.nvim_get_current_win()
  return M.editor_win
end

--- 選択中の行のハイライトを更新する
---@param idx integer
local function highlight_selected(idx)
  vim.api.nvim_buf_clear_namespace(M.buf, highlight_ns, 0, -1)
  local start_line = (idx - 1) * M.ROWS_PER_PANEL
  vim.api.nvim_buf_add_highlight(M.buf, highlight_ns, "PmenuSel", start_line, 0, start_line + M.ROWS_PER_PANEL)
end

--- パネルを選択する
---@param idx integer
---@param opts { dir?: string }?
function M.select(idx, opts)
  local panel = M.PANELS[idx]
  if not panel then
    return
  end
  if not M.is_open() then
    M.open()
  end
  M.current_index = idx
  vim.api.nvim_set_current_win(M.sidebar_win)
  panel.open(opts)
  -- panel.open()が呼ぶNeotree showはwindow全体の幅を再計算し、winfixwidthを
  -- 設定していても幅がずれることがあるため、確定後にもう一度固定し直す
  if vim.api.nvim_win_is_valid(M.sidebar_win) then
    vim.api.nvim_win_set_width(M.sidebar_win, M.SIDEBAR_WIDTH)
  end
  highlight_selected(idx)
end

---@param buf integer
local function setup_keymaps(buf)
  for _, panel in ipairs(M.PANELS) do
    vim.keymap.set("n", panel.key, function()
      M.select(M.panel_index_for_key(panel.key))
    end, { buffer = buf, desc = panel.label })
  end
  vim.keymap.set("n", "<CR>", function()
    local line = vim.api.nvim_win_get_cursor(0)[1]
    local idx = M.panel_index_for_line(line)
    if idx then
      M.select(idx)
    end
  end, { buffer = buf, desc = "選択中のパネルを開く" })
  local function select_panel_at_mouse()
    local line = vim.fn.getmousepos().line
    local idx = M.panel_index_for_line(line)
    if idx then
      vim.api.nvim_win_set_cursor(M.win, { line, 0 })
      M.select(idx)
    end
  end
  local mouse_modes = { "n", "v", "x" }
  vim.keymap.set(
    mouse_modes,
    "<LeftMouse>",
    select_panel_at_mouse,
    { buffer = buf, desc = "クリックしたパネルを開く" }
  )
  vim.keymap.set(
    mouse_modes,
    "<2-LeftMouse>",
    select_panel_at_mouse,
    { buffer = buf, desc = "ダブルクリックしたパネルを開く" }
  )

  local function cancel_mouse_selection()
    if vim.fn.mode():match("^[vV\22]") then
      vim.api.nvim_feedkeys(vim.keycode("<Esc>"), "nx", false)
    end
  end
  vim.keymap.set(
    mouse_modes,
    "<LeftDrag>",
    cancel_mouse_selection,
    { buffer = buf, desc = "バー上のドラッグ選択を解除する" }
  )
  vim.keymap.set(
    mouse_modes,
    "<LeftRelease>",
    cancel_mouse_selection,
    { buffer = buf, desc = "バー上のマウス選択を解除する" }
  )
end

--- 左端にbar window、その右にsidebar windowを開く。すでに開いていれば何もしない。
--- 壊れた状態(片方だけ生き残っているなど)が残っていれば一度片付けてから作り直す
function M.open()
  if M.is_open() then
    return
  end
  if M.win and vim.api.nvim_win_is_valid(M.win) then
    pcall(vim.api.nvim_win_close, M.win, true)
  end
  if M.sidebar_win and vim.api.nvim_win_is_valid(M.sidebar_win) then
    pcall(vim.api.nvim_win_close, M.sidebar_win, true)
  end

  -- 分割前にカレントだったwindowをeditor windowとして残す
  M.editor_win = vim.api.nvim_get_current_win()

  vim.cmd("topleft vsplit")
  local win = vim.api.nvim_get_current_win()
  local buf = vim.api.nvim_create_buf(false, true)
  vim.api.nvim_win_set_buf(win, buf)
  vim.api.nvim_win_set_width(win, M.WIDTH)

  vim.bo[buf].buftype = "nofile"
  vim.bo[buf].bufhidden = "wipe"
  vim.bo[buf].swapfile = false
  vim.bo[buf].filetype = "activity-bar"
  vim.api.nvim_buf_set_lines(buf, 0, -1, false, M.render_lines())
  vim.bo[buf].modifiable = false

  vim.wo[win].number = false
  vim.wo[win].relativenumber = false
  vim.wo[win].signcolumn = "no"
  vim.wo[win].winfixwidth = true
  vim.wo[win].wrap = false
  vim.wo[win].list = false
  vim.wo[win].cursorline = false

  M.win = win
  M.buf = buf
  setup_keymaps(buf)

  -- splitright=true(LazyVim既定)のため、カレントwindow(bar)の右にできる
  vim.cmd("vsplit")
  local sidebar_win = vim.api.nvim_get_current_win()
  vim.wo[sidebar_win].winfixwidth = true
  vim.api.nvim_win_set_width(sidebar_win, M.SIDEBAR_WIDTH)
  M.sidebar_win = sidebar_win

  vim.api.nvim_set_current_win(win)

  -- toggle・WinClosedガード経由の再オープンでは、選択中のパネルは変わらない。
  -- 新規バッファに前回の選択行のハイライトだけ復元する
  if M.current_index then
    highlight_selected(M.current_index)
  end
end

--- 起動時に常時表示させる。バー自体は引数の有無にかかわらず開くが、パネルの
--- 自動選択は引数あり起動(argc>0、ファイルを直接開く)のときだけ行う。
-- 引数なし起動(argc==0)でここで選択してしまうと、chdir前のディレクトリで
-- Neotree showが走り、直後にutil.project.open_on_startupが出すプロジェクト
-- 選択floatと競合してピッカーが表示されない事故になる(2026-08-10)。
-- 引数なし起動時のExplorer表示は、プロジェクト選択後にutil.project.open_workspace
-- 経由でselect(1)が呼ばれることで行われる
function M.open_on_startup()
  M.open()
  if vim.fn.argc() > 0 then
    M.select(1)
  end
end

-- WinClosedはこのモジュール内のvim.cmd呼び出しでも発生しうるため、復帰処理は
-- これを見て意図した閉じ方と誤操作を区別する
local closing_on_purpose = false

-- persistence.load()の`silent only`はbar・sidebarの両方を1回の操作で同時に
-- 閉じるため、WinClosedが2回連続で走る。復帰予約は同時に1つまでとし、
-- 2回分の復帰がそれぞれM.open()を呼んで対を二重に作ってしまう事故を防ぐ
-- (2026-08-10)
local recovery_scheduled = false

--- VSCodeのCtrl+B(サイドバー全体の表示切り替え)相当。activity-bar windowだけを
--- 開閉し、sidebar window(neo-tree/grug-far)には触れない
function M.toggle()
  if not M.is_open() then
    M.open()
    return
  end
  closing_on_purpose = true
  vim.api.nvim_win_close(M.win, false)
  M.win = nil
  vim.schedule(function()
    closing_on_purpose = false
  end)
end

--- bar windowとsidebar windowを、誤って閉じたら開き直すガードを登録する。
--- どちらが閉じてもレイアウト全体を作り直す(片方だけ残る半端な状態にしない)
function M.enable_guard()
  vim.api.nvim_create_autocmd("WinClosed", {
    callback = function(ev)
      local win = tonumber(ev.match)
      if not win or closing_on_purpose then
        return
      end
      if win ~= M.win and win ~= M.sidebar_win then
        return
      end
      if recovery_scheduled then
        return
      end
      recovery_scheduled = true
      vim.schedule(function()
        recovery_scheduled = false
        -- nvim終了中は開き直さない
        if vim.v.exiting ~= vim.NIL then
          return
        end
        -- bar・sidebarの両方が同時に閉じた場合、先に走ったWinClosedの
        -- 復帰予約がここで両方作り直す。後から走った分はis_open()が
        -- 真になっているので何もしない
        if M.is_open() then
          return
        end
        -- M.win・M.sidebar_winをここでnilにしない。片方だけが閉じて
        -- 生き残っている場合、M.open()自身の後始末処理がこの参照を見て
        -- 生き残った方を先に閉じてから作り直す。先にnilにすると生き残った
        -- windowがeditor windowと誤認識され、古いneo-tree状態が残ったまま
        -- 新しいpair(sidebar)にも描画されてwindowが増え続けた(2026-08-10)
        M.open()
        if M.current_index then
          M.select(M.current_index)
        end
      end)
    end,
  })
end

return M
