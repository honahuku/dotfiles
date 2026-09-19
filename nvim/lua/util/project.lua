-- 引数なしで起動したときに開くディレクトリ。VSCodeの「起動時に開くフォルダ」相当
-- :Reloadが再起動前に置く引き継ぎファイル。復元先のcwdとセッションファイルを1行ずつ書く。
-- 新しいプロセスのcwdが元と同じとは限らないため、パスを明示して渡す
local reload_marker = vim.fs.joinpath(vim.fn.stdpath("state"), "reload.marker")
local reload_log = vim.fs.joinpath(vim.fn.stdpath("state"), "reload.log")

local M = {}
M.DEFAULT_PROJECT_DIR = vim.fs.normalize(vim.env.DOTFILES_DEFAULT_PROJECT_DIR or vim.fn.getcwd())
M.reload_marker = reload_marker

function M.log(message)
  local file = io.open(reload_log, "a")
  if file then
    file:write(os.date("%Y-%m-%d %H:%M:%S ") .. message .. "\n")
    file:close()
  end
end

-- 直近開いたディレクトリの一覧。自前のMRUファイルはDirChangedをフックして
-- 読み書きしていたが、複数nvimプロセスを同時に開くと後勝ちの上書きで
-- 他プロセス分の記録が消える競合があった。persistence.nvimはセッションを
-- プロセスごとに自分のcwd分のファイルへ保存するだけなので競合が起きない。
-- そのセッションファイル一覧をmtime降順で読み、ディレクトリ一覧として使う
-- persistence.nvimのデフォルト値と同じ固定パス。require("persistence.config").options.dirは
-- setup()完了後でないとnilで、open_on_startupが呼ばれるVeryLazy時点でその保証が無いため使わない
local session_dir = vim.fs.normalize(vim.fn.stdpath("state") .. "/sessions")

-- persistence.nvimがセッションファイルへ書き込むのはVimLeavePre(終了時)だけなので、
-- mtimeに任せると「開いた順」ではなく「そのnvimを終了した順」になり、起動中の別
-- セッションで開いたディレクトリはいつまでも上に上がってこない。pick_projectで
-- 選んだ時点でも同じファイルのmtimeを更新し、開いた順に一致させる。
-- ディレクトリごとに異なるファイルを触るだけなので、複数プロセスが同時に別々の
-- ディレクトリを開いても上記の後勝ち上書き競合は起きない
local function touch_session(dir)
  local name = vim.fs.normalize(dir):gsub("[\\/:]+", "%%") .. ".vim"
  local path = vim.fs.joinpath(session_dir, name)
  local now = os.time()
  if vim.fn.filereadable(path) == 1 then
    vim.uv.fs_utime(path, now, now)
  else
    vim.fn.mkdir(session_dir, "p")
    vim.fn.writefile({}, path)
  end
end

local function read_mru()
  local handle = vim.uv.fs_scandir(session_dir)
  if not handle then
    return {}
  end
  local entries = {}
  while true do
    local name, typ = vim.uv.fs_scandir_next(handle)
    if not name then
      break
    end
    if typ == "file" and name:match("%.vim$") then
      -- gsubは(結果, 置換回数)の2値を返すため、括弧で囲まないと置換回数が
      -- vim.fs.normalizeの第2引数(opts)に紛れ込みindexエラーになる
      local dir = vim.fs.normalize((name:gsub("%.vim$", ""):gsub("%%", "/")))
      local stat = vim.uv.fs_stat(vim.fs.joinpath(session_dir, name))
      if stat and vim.fn.isdirectory(dir) == 1 then
        table.insert(entries, { dir = dir, mtime = stat.mtime.sec })
      end
    end
  end
  table.sort(entries, function(a, b)
    return a.mtime > b.mtime
  end)
  local dirs = {}
  for _, entry in ipairs(entries) do
    table.insert(dirs, entry.dir)
  end
  return dirs
end

-- グローバルなカレントディレクトリが変わるたびにセッションファイルを記録する。
-- 以前はpick_projectで選んだ時とnvim終了時(persistence.nvimのVimLeavePre)にしか
-- 記録されず、:cdだけで移動したディレクトリはそのnvimを一度も終了しない限り
-- 一覧に出てこなかった。config/autocmds.luaのDirChanged(global)から呼ぶ
function M.record_cwd()
  touch_session(vim.fn.getcwd())
end

-- サイドバーはセッションに含めないため毎回開き直す。
-- 下部ターミナルは自動で開かず、util.terminalのキーマップ(Ctrl+`等)で手動で開く。
-- persistence.load()のセッション復元スクリプトは`silent only`でwindowを1つに
-- 畳むため、直前に開いていたactivity-barのwindowも失われていることがあるが、
-- select()側がis_open()を見て必要ならopen()から作り直す
local function open_workspace(dir)
  require("util.activity-bar").select(1, { dir = dir })
  vim.cmd("wincmd p")
end

-- 引き継ぎファイルを消した上で復元先を返す。
-- :qaは未保存バッファがあると中断するので、古いファイルは再起動失敗の残骸とみなす。
-- 手動でnvimを起動し直すまでの間隔を見込み、猶予は5分とする
---@return { cwd: string, session: string }|nil
local function consume_reload_marker()
  local stat = vim.uv.fs_stat(reload_marker)
  if not stat then
    return nil
  end
  local lines = vim.fn.readfile(reload_marker)
  vim.uv.fs_unlink(reload_marker)
  if os.time() - stat.mtime.sec >= 300 or #lines < 2 then
    M.log("skip restore: stale marker")
    return nil
  end
  return { cwd = lines[1], session = lines[2] }
end

-- VSCode の Project Manager 相当。<leader>fp / Ctrl+R でプロジェクト一覧から開ける
function M.pick_project()
  local items = {}
  for _, dir in ipairs(read_mru()) do
    table.insert(items, { text = dir, file = dir })
  end
  Snacks.picker.pick({
    title = "プロジェクト",
    items = items,
    format = "text",
    confirm = function(picker, item)
      picker:close()
      if not item then
        return
      end
      vim.fn.chdir(item.file)
      touch_session(item.file)

      -- VSCodeのウィンドウ復元相当。フォルダ単位のセッションがあれば復元し、
      -- 無ければ従来どおりファイルピッカーを開く
      local persistence = require("persistence")
      local session = persistence.current()
      if session and vim.fn.filereadable(session) == 1 then
        persistence.load()
      else
        Snacks.picker.files({ cwd = item.file })
      end

      open_workspace(item.file)
    end,
  })
end

-- 引数なし起動時にreloadマーカーがあれば復元し、無ければdefault_project_dirへ移動してプロジェクトを選ばせる
function M.open_on_startup()
  if vim.fn.argc() > 0 then
    return
  end
  local reload = consume_reload_marker()
  if reload then
    M.log(
      "restore: cwd="
        .. reload.cwd
        .. " session="
        .. reload.session
        .. " readable="
        .. vim.fn.filereadable(reload.session)
    )
    if vim.fn.isdirectory(reload.cwd) == 1 then
      vim.fn.chdir(reload.cwd)
    end
    if vim.fn.filereadable(reload.session) == 1 then
      vim.cmd("silent! source " .. vim.fn.fnameescape(reload.session))
    end
    local dir = vim.fn.getcwd()
    vim.schedule(function()
      open_workspace(dir)
    end)
  else
    if vim.fn.isdirectory(M.DEFAULT_PROJECT_DIR) == 1 then
      vim.fn.chdir(M.DEFAULT_PROJECT_DIR)
    end
    M.pick_project()
  end
end

return M
