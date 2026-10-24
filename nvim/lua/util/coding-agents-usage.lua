-- Coding Agentsの月間利用額を非同期取得し、設定された利用枠に対する使用率を表示する。
-- 予算・期間・換算率はsetupの引数で受け取り、公開設定に実際の値を含めない。
local platform = require("platform")
local M = {}

M.ICON = "󰚩"
M.DEFAULT_BUDGET_USD = nil
M.BUDGET_OVERRIDES = {}
M.COST_TTL_SEC = 15 * 60
M.PACE_TTL_SEC = 15 * 60
M.COST_CACHE_VERSION = 3
M.CODEX_USD_PER_CREDIT = nil
M.UTC_OFFSET_HOURS = 0
M.CODEX_CMD = vim.env.CODEX_CMD or "codex"
M.CODEX_USAGE_TIMEOUT_MS = 20 * 1000
M.CODEX_USAGE_GRACE_MS = 10 * 1000
M.TASKS_CMD = platform.is_wsl() and vim.fn.expand("~/.local/bin/tasks") or "tasks"
-- autoモードはログに保存された事前計算額を優先するため、ログ作成時の単価に依存する。
-- トークン数から再計算し、保存済みの費用値に依存しない。
M.CC_USAGE_CMD = {
  "npx",
  "ccusage@latest",
  "monthly",
  "--last",
  "1",
  "--mode",
  "calculate",
  "--by-agent",
  "--json",
}
M.CODEX_USAGE_CMD = { M.CODEX_CMD, "app-server", "--stdio" }

local cost_cache_path = vim.fn.stdpath("cache") .. "/coding-agents-usage-cost.json"
local pace_cache_path = vim.fn.stdpath("cache") .. "/coding-agents-usage-pace.json"

---端末のタイムゾーンに依存せず、設定した時差で期間を判定する。
---@param timestamp integer?
---@return string
function M.current_date(timestamp)
  return os.date("!%Y-%m-%d", (timestamp or os.time()) + M.UTC_OFFSET_HOURS * 60 * 60)
end

---利用量と勤務ペースのキャッシュを同じ年月で管理する。
---@return string
function M.current_period()
  return M.current_date():sub(1, 7)
end

local function is_valid_date(value)
  if type(value) ~= "string" then
    return false
  end
  local year, month, day = value:match("^(%d%d%d%d)%-(%d%d)%-(%d%d)$")
  year, month, day = tonumber(year), tonumber(month), tonumber(day)
  if not year or year < 1 or month < 1 or month > 12 then
    return false
  end
  local days = { 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31 }
  if year % 4 == 0 and (year % 100 ~= 0 or year % 400 == 0) then
    days[2] = 29
  end
  return day >= 1 and day <= days[month]
end

local function is_positive_amount(amount)
  return type(amount) == "number" and amount > 0 and amount < math.huge
end

---@param date string YYYY-MM-DD（設定したタイムゾーン）
---@param overrides table[]?
---@param default_budget_usd number?
---@return number
function M.resolve_budget_usd(date, overrides, default_budget_usd)
  assert(is_valid_date(date), "Coding Agents 使用量: 日付は実在するYYYY-MM-DDで指定してください")
  assert(
    is_positive_amount(default_budget_usd or M.DEFAULT_BUDGET_USD),
    "Coding Agents 使用量: 通常枠は正の有限値で指定してください"
  )
  local budget_usd = default_budget_usd or M.DEFAULT_BUDGET_USD
  for _, override in ipairs(overrides or M.BUDGET_OVERRIDES) do
    assert(
      type(override) == "table"
        and is_valid_date(override.start_date)
        and is_valid_date(override.end_date)
        and override.start_date <= override.end_date
        and override.start_date:sub(1, 7) == override.end_date:sub(1, 7),
      "Coding Agents 使用量: 増額期間は同じ月内の開始日・終了日で指定してください"
    )
    assert(
      is_positive_amount(override.budget_usd),
      "Coding Agents 使用量: 総枠は正の有限値で指定してください"
    )
    if override.start_date <= date and date <= override.end_date then
      budget_usd = math.max(budget_usd, override.budget_usd)
    end
  end
  return budget_usd
end

---@param cache_period string?
---@param current_period string
---@return boolean
function M.is_current_period(cache_period, current_period)
  return cache_period == current_period
end

---Codex desktopと同じアカウント単位のクレジット値を使うため、レート制限APIを利用する。
---Codex app-serverのJSONLレスポンスから今月の使用クレジットを取り出す。
---@param jsonl string
---@return number?
function M.parse_codex_credits(jsonl)
  for line in jsonl:gmatch("[^\n]+") do
    local ok, message = pcall(vim.json.decode, line)
    if ok and type(message) == "table" and message.id == 2 then
      local result = message.result
      if type(result) ~= "table" then
        return nil
      end

      local rate_limits = result.rateLimitsByLimitId
      if type(rate_limits) == "table" then
        rate_limits = rate_limits.codex
      end
      if type(rate_limits) ~= "table" then
        rate_limits = result.rateLimits
      end
      if type(rate_limits) ~= "table" then
        return nil
      end

      local individual_limit = rate_limits.individualLimit
      local credits = individual_limit and tonumber(individual_limit.used)
      if credits and credits >= 0 then
        return credits
      end
      return nil
    end
  end
  return nil
end

---@param credits number
---@param usd_per_credit number
---@return number?
function M.codex_credits_to_usd(credits, usd_per_credit)
  if type(credits) ~= "number" or type(usd_per_credit) ~= "number" or usd_per_credit <= 0 then
    return nil
  end
  return credits * usd_per_credit
end

---@param amount number
---@return string
function M.format_amount(amount)
  return string.format("$%.2f", amount)
end

---利用率を四捨五入した整数%で返す。上限が0以下ならゼロ除算を避けてnil。
---@param cost_usd number
---@param budget_usd number
---@return integer?
function M.compute_ratio_percent(cost_usd, budget_usd)
  if budget_usd <= 0 then
    return nil
  end
  return math.floor((cost_usd / budget_usd) * 100 + 0.5)
end

---tasks work summaryの出力から年月、所定労働時間、累積勤務時間を取り出す。
---@param json_str string
---@return number? target_hours
---@return number? cumulative_hours
---@return string? period
function M.parse_work_summary(json_str)
  local ok, decoded = pcall(vim.json.decode, json_str)
  if not ok or type(decoded) ~= "table" then
    return nil, nil
  end
  return decoded.target_hours, decoded.cumulative_hours, decoded.month
end

---所定労働時間に対する経過時間の割合を四捨五入した整数%で返す。
---所定労働時間が0以下ならゼロ除算を避けてnil。
---@param cumulative_hours number
---@param target_hours number
---@return integer?
function M.compute_pace_percent(cumulative_hours, target_hours)
  if target_hours <= 0 then
    return nil
  end
  return math.floor((cumulative_hours / target_hours) * 100 + 0.5)
end

---利用率と時間ベースの進捗率の差分（ポイント）を返す。正なら利用が進捗より進んでいる。
---@param ratio_percent integer
---@param pace_percent integer
---@return integer
function M.compute_diff_pt(ratio_percent, pace_percent)
  return ratio_percent - pace_percent
end

---上限超過と混同しないよう、勤務ペースとの差をポイントで表示する。
---@param diff_pt integer
---@return string
function M.format_pace_diff(diff_pt)
  if diff_pt ~= 0 then
    return string.format("ペース %+dpt", diff_pt)
  end
  return "ペース通り"
end

---@class CodingAgentsUsageStats
---@field cost_usd number 取得元ごとの利用額を合算したUSD額
---@field budget_usd number
---@field ratio_percent integer
---@field pace_diff_label string? tasks work summaryが未取得なら省略される

---statusline表示用の文字列を組み立てる。API相当額なので近似記号を付ける。
---statsがなければ空文字（未取得中は何も出さない）。
---@param stats CodingAgentsUsageStats?
---@return string
function M.format_statusline(stats)
  if not stats then
    return ""
  end
  if stats.pace_diff_label then
    return string.format(
      "%s ≈%s / 上限 %s (%d%%, %s)",
      M.ICON,
      M.format_amount(stats.cost_usd),
      M.format_amount(stats.budget_usd),
      stats.ratio_percent,
      stats.pace_diff_label
    )
  end
  return string.format(
    "%s ≈%s / 上限 %s (%d%%)",
    M.ICON,
    M.format_amount(stats.cost_usd),
    M.format_amount(stats.budget_usd),
    stats.ratio_percent
  )
end

---lualineのstatuslineは`%`をハイライト/フィールド指定子として解釈するため、
---コンポーネントが返す文字列に生の`%`が混ざるとE542: Unbalanced groupsで
---リフレッシュ処理ごと失敗する。表示直前に`%%`へエスケープしてリテラル化する。
---@param text string
---@return string
function M.escape_statusline_percent(text)
  return (text:gsub("%%", "%%%%"))
end

---キャッシュが古いかどうかを判定する。updated_atがなければ常に古い扱い。
---@param updated_at number?
---@param ttl_sec number
---@param now number
---@return boolean
function M.is_stale(updated_at, ttl_sec, now)
  if not updated_at then
    return true
  end
  return now - updated_at > ttl_sec
end

---@type {period: string, cost_usd: number, pace_percent: integer?}?
M.display_stats = nil

local function refresh_statusline()
  local ok, lualine = pcall(require, "lualine")
  if ok then
    lualine.refresh()
  end
end

local function read_json_file(path)
  local file = io.open(path, "r")
  -- 改名直後も前回の利用額を表示できるよう、旧名キャッシュは読み取りだけ維持する。
  -- 更新先は新名に統一し、既存キャッシュの移動・削除はしない。
  if not file then
    local legacy_path = path:gsub("/coding%-agents%-usage%-", "/ai-usage-")
    file = io.open(legacy_path, "r")
  end
  if not file then
    return nil
  end
  local content = file:read("*a")
  file:close()
  local ok, decoded = pcall(vim.json.decode, content)
  if not ok then
    return nil
  end
  return decoded
end

local function write_json_file(path, tbl)
  local file = io.open(path, "w")
  if not file then
    return
  end
  file:write(vim.json.encode(tbl), "\n")
  file:close()
end

-- 取得元が変わる前のキャッシュを混ぜないよう、versionが一致するものだけ使う。
-- 勤務ペースを取得できなくても合計額は表示できるため、ペースの欠損時も表示を続ける。
local function recompute_display_stats()
  local cost_cache = read_json_file(cost_cache_path)
  local current_period = M.current_period()
  if
    not cost_cache
    or cost_cache.version ~= M.COST_CACHE_VERSION
    or not M.is_current_period(cost_cache.period, current_period)
  then
    M.display_stats = nil
    return
  end
  local cost_usd = cost_cache.cost_usd
  if type(cost_usd) ~= "number" then
    return
  end
  local pace_percent = nil
  local pace_cache = read_json_file(pace_cache_path)
  if
    pace_cache
    and M.is_current_period(pace_cache.period, current_period)
    and pace_cache.target_hours
    and pace_cache.cumulative_hours
  then
    pace_percent = M.compute_pace_percent(pace_cache.cumulative_hours, pace_cache.target_hours)
  end

  M.display_stats = {
    period = current_period,
    cost_usd = cost_usd,
    pace_percent = pace_percent,
  }
  refresh_statusline()
end

-- コマンド未検出時の同期エラーは非同期コールバックでは扱えない。
-- 利用量の取得失敗でprivate設定の初期化まで中断しないよう、呼び出し自体を保護する。
local function safe_system(cmd, opts, on_exit)
  local ok, process_or_error = pcall(vim.system, cmd, opts, on_exit)
  if not ok then
    vim.schedule(function()
      vim.notify(
        "Coding Agents 使用量: " .. cmd[1] .. "の実行に失敗しました: " .. tostring(process_or_error),
        vim.log.levels.WARN
      )
    end)
    return nil
  end
  return process_or_error
end

-- 合計だけでは取得元ごとの値を調べられないため、表示しない内訳も保存する。
local function update_cost_cache(period, usage_cost_usd, codex_cost_usd)
  local cost_usd = usage_cost_usd + codex_cost_usd
  write_json_file(cost_cache_path, {
    version = M.COST_CACHE_VERSION,
    period = period,
    usage_cost_usd = usage_cost_usd,
    codex_cost_usd = codex_cost_usd,
    cost_usd = cost_usd,
    updated_at = os.time(),
  })
  recompute_display_stats()
end

---ccusageを非同期実行し、設定された抽出処理で指定月のUSDコストを取り出す。
local function refresh_usage_cost_cache(period, on_cost)
  safe_system(
    M.CC_USAGE_CMD,
    { text = true },
    vim.schedule_wrap(function(result)
      if result.code ~= 0 then
        return
      end
      local cost_usd = M.parse_usage_cost_usd(result.stdout, period)
      if not cost_usd then
        return
      end
      on_cost(cost_usd)
    end)
  )
end

---Codex app-serverを非同期実行し、今月のUSDコストを返す。
local function refresh_codex_cost_cache(on_cost)
  local process = safe_system(
    M.CODEX_USAGE_CMD,
    { text = true, stdin = true, timeout = M.CODEX_USAGE_TIMEOUT_MS },
    vim.schedule_wrap(function(result)
      if result.code ~= 0 then
        return
      end
      local credits = M.parse_codex_credits(result.stdout)
      local cost_usd = credits and M.codex_credits_to_usd(credits, M.CODEX_USD_PER_CREDIT)
      if cost_usd then
        on_cost(cost_usd)
      end
    end)
  )
  if not process then
    return
  end

  local requests = {
    vim.json.encode({
      id = 1,
      method = "initialize",
      params = {
        clientInfo = { name = "nvim-coding-agents-usage", version = "1.0.0" },
        capabilities = { experimentalApi = true },
      },
    }),
    vim.json.encode({ method = "initialized", params = {} }),
    vim.json.encode({
      id = 2,
      method = "account/rateLimits/read",
      params = { excludeResetCreditDetails = true },
    }),
  }
  vim.defer_fn(function()
    pcall(process.write, process, requests)
  end, 0)
  vim.defer_fn(function()
    pcall(process.write, process, nil)
  end, M.CODEX_USAGE_GRACE_MS)
end

-- 片方の取得失敗を0として合算すると過少表示になるため、両方がそろうまで更新しない。
-- 失敗時は前回の合計を保持する。初回取得がそろわなければ表示しない。
local function refresh_cost_cache()
  local period = M.current_period()
  local usage_cost_usd
  local codex_cost_usd

  local function finish_if_ready()
    if usage_cost_usd ~= nil and codex_cost_usd ~= nil then
      if M.is_current_period(period, M.current_period()) then
        update_cost_cache(period, usage_cost_usd, codex_cost_usd)
      else
        refresh_cost_cache()
      end
    end
  end

  refresh_usage_cost_cache(period, function(cost_usd)
    usage_cost_usd = cost_usd
    finish_if_ready()
  end)
  refresh_codex_cost_cache(function(cost_usd)
    codex_cost_usd = cost_usd
    finish_if_ready()
  end)
end

---tasksコマンドの月間勤務ペースを非同期取得し、キャッシュファイルへ書く。
local function refresh_pace_cache()
  if vim.fn.executable(M.TASKS_CMD) ~= 1 then
    return
  end
  safe_system(
    { M.TASKS_CMD, "work", "summary" },
    { text = true },
    vim.schedule_wrap(function(result)
      if result.code ~= 0 then
        return
      end
      local target_hours, cumulative_hours, period = M.parse_work_summary(result.stdout)
      if not target_hours or not cumulative_hours or not M.is_current_period(period, M.current_period()) then
        return
      end
      write_json_file(pace_cache_path, {
        period = period,
        target_hours = target_hours,
        cumulative_hours = cumulative_hours,
        updated_at = os.time(),
      })
      recompute_display_stats()
    end)
  )
end

---起動時にキャッシュを読み込み、TTLを超えていれば非同期更新をかける。
---以降はコストとペースを15分ごとにタイマーで更新する。
function M.configure(opts)
  assert(type(opts) == "table", "Coding Agents 使用量: 設定を指定してください")
  assert(
    type(opts.parse_usage_cost_usd) == "function",
    "Coding Agents 使用量: 利用額の抽出処理を指定してください"
  )
  assert(
    is_positive_amount(opts.codex_usd_per_credit),
    "Coding Agents 使用量: 換算率は正の有限値で指定してください"
  )
  local utc_offset_hours = opts.utc_offset_hours or 0
  assert(
    type(utc_offset_hours) == "number" and utc_offset_hours >= -12 and utc_offset_hours <= 14,
    "Coding Agents 使用量: 時差はUTCからの時間数で指定してください"
  )
  local overrides = opts.budget_overrides or {}
  assert(vim.islist(overrides), "Coding Agents 使用量: 増額設定はリストで指定してください")
  assert(is_positive_amount(opts.default_budget_usd), "Coding Agents 使用量: 通常枠を指定してください")
  M.resolve_budget_usd(M.current_date(), overrides, opts.default_budget_usd)
  M.DEFAULT_BUDGET_USD = opts.default_budget_usd
  M.BUDGET_OVERRIDES = overrides
  M.CODEX_USD_PER_CREDIT = opts.codex_usd_per_credit
  M.UTC_OFFSET_HOURS = utc_offset_hours
  M.parse_usage_cost_usd = opts.parse_usage_cost_usd
end

function M.setup(opts)
  M.configure(opts)
  recompute_display_stats()

  local cost_cache = read_json_file(cost_cache_path)
  local current_period = M.current_period()
  if
    not cost_cache
    or cost_cache.version ~= M.COST_CACHE_VERSION
    or not M.is_current_period(cost_cache.period, current_period)
    or M.is_stale(cost_cache.updated_at, M.COST_TTL_SEC, os.time())
  then
    refresh_cost_cache()
  end
  local pace_cache = read_json_file(pace_cache_path)
  if
    M.is_stale(pace_cache and pace_cache.updated_at, M.PACE_TTL_SEC, os.time())
    or not M.is_current_period(pace_cache and pace_cache.period, current_period)
  then
    refresh_pace_cache()
  end

  local cost_timer = vim.uv.new_timer()
  cost_timer:start(M.COST_TTL_SEC * 1000, M.COST_TTL_SEC * 1000, vim.schedule_wrap(refresh_cost_cache))

  local pace_timer = vim.uv.new_timer()
  pace_timer:start(M.PACE_TTL_SEC * 1000, M.PACE_TTL_SEC * 1000, vim.schedule_wrap(refresh_pace_cache))
end

function M.statusline()
  local cached = M.display_stats
  local date = M.current_date()
  if not cached or not M.is_current_period(cached.period, date:sub(1, 7)) then
    return ""
  end
  -- 上限をキャッシュすると、起動したまま期間をまたいだ場合に増額・失効が遅れる。
  -- 描画時は保存済み金額と当日の設定だけで計算し、ファイルや外部APIは読まない。
  local budget_usd = M.resolve_budget_usd(date)
  local ratio_percent = M.compute_ratio_percent(cached.cost_usd, budget_usd)
  local pace_diff_label = cached.pace_percent
    and M.format_pace_diff(M.compute_diff_pt(ratio_percent, cached.pace_percent))
  return M.escape_statusline_percent(M.format_statusline({
    cost_usd = cached.cost_usd,
    budget_usd = budget_usd,
    ratio_percent = ratio_percent,
    pace_diff_label = pace_diff_label,
  }))
end

return M
