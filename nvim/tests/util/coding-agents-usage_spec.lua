---@diagnostic disable: undefined-global, undefined-field
local usage = require("util.coding-agents-usage")

-- 実際の予算・申請から独立した架空の設定で検証する。
local function options()
  return {
    default_budget_usd = 600,
    codex_usd_per_credit = 0.02,
    budget_overrides = {
      { start_date = "2040-06-10", end_date = "2040-06-20", budget_usd = 1200 },
    },
  }
end

describe("Coding Agents使用量", function()
  local original_date = usage.current_date
  before_each(function()
    usage.configure(options())
    usage.display_stats = nil
  end)
  after_each(function()
    usage.current_date = original_date
    usage.display_stats = nil
  end)

  it("設定から通常枠・換算率・期間を受け取る", function()
    assert.are.same(600, usage.DEFAULT_BUDGET_USD)
    assert.are.same(0.02, usage.CODEX_USD_PER_CREDIT)
    assert.are.same(1200, usage.resolve_budget_usd("2040-06-15"))
  end)

  it("設定を省略して社内の予算や換算率を推測しない", function()
    assert.has_error(function()
      usage.configure({})
    end)
    assert.has_error(function()
      usage.configure({ default_budget_usd = 600 })
    end)
  end)

  it("開始日・終了日を含む期間だけ総枠を置き換える", function()
    for date, expected in pairs({
      ["2040-06-09"] = 600,
      ["2040-06-10"] = 1200,
      ["2040-06-20"] = 1200,
      ["2040-06-21"] = 600,
      ["2040-07-01"] = 600,
    }) do
      assert.are.same(expected, usage.resolve_budget_usd(date))
    end
  end)

  it("通常枠より小さい申請で上限を引き下げない", function()
    assert.are.same(
      600,
      usage.resolve_budget_usd("2040-06-15", {
        { start_date = "2040-06-10", end_date = "2040-06-20", budget_usd = 100 },
      })
    )
  end)

  it("重なった期間では最大の総枠を使う", function()
    local overrides = options().budget_overrides
    overrides[2] = { start_date = "2040-06-15", end_date = "2040-06-16", budget_usd = 1800 }
    assert.are.same(1800, usage.resolve_budget_usd("2040-06-15", overrides))
    assert.are.same(1200, usage.resolve_budget_usd("2040-06-17", overrides))
  end)

  it("存在しない日付・逆転した期間・月をまたぐ期間を拒否する", function()
    for _, dates in ipairs({
      { "2041-02-29", "2041-02-29" },
      { "2040-06-31", "2040-06-31" },
      { "2040-06-20", "2040-06-10" },
      { "2040-06-10", "2040-07-01" },
      { "2040-6-10", "2040-06-20" },
    }) do
      assert.has_error(function()
        usage.resolve_budget_usd("2040-06-15", {
          { start_date = dates[1], end_date = dates[2], budget_usd = 1200 },
        })
      end)
    end
    assert.are.same(
      1200,
      usage.resolve_budget_usd("2040-02-29", {
        { start_date = "2040-02-29", end_date = "2040-02-29", budget_usd = 1200 },
      })
    )
  end)

  it("不正な金額を拒否する", function()
    for _, amount in ipairs({ 0, -1, "1200", math.huge, 0 / 0 }) do
      assert.has_error(function()
        usage.resolve_budget_usd("2040-06-15", {
          { start_date = "2040-06-10", end_date = "2040-06-20", budget_usd = amount },
        })
      end)
    end
  end)

  it("設定したタイムゾーンで日付を判断する", function()
    assert.are.same("1970-01-01", usage.current_date(0))
    local opts = options()
    opts.utc_offset_hours = -5
    usage.configure(opts)
    assert.are.same("1969-12-31", usage.current_date(0))
  end)

  it("起動したまま期間をまたいでも上限・使用率・ペースを切り替える", function()
    usage.display_stats = { period = "2040-06", cost_usd = 300, pace_percent = 50 }
    usage.current_date = function()
      return "2040-06-10"
    end
    assert.are.same(usage.ICON .. " ≈$300.00 / 上限 $1200.00 (25%%, ペース -25pt)", usage.statusline())
    usage.current_date = function()
      return "2040-06-21"
    end
    assert.are.same(usage.ICON .. " ≈$300.00 / 上限 $600.00 (50%%, ペース通り)", usage.statusline())
    usage.current_date = function()
      return "2040-07-01"
    end
    assert.are.same("", usage.statusline())
  end)

  it("ペース未取得でも金額・上限・使用率を表示する", function()
    usage.display_stats = { period = "2040-06", cost_usd = 300 }
    usage.current_date = function()
      return "2040-06-09"
    end
    assert.are.same(usage.ICON .. " ≈$300.00 / 上限 $600.00 (50%%)", usage.statusline())
  end)

  it("未取得時は表示しない", function()
    assert.are.same("", usage.statusline())
  end)

  it("Claudeだけを月別内訳から取り出す", function()
    local json = [[{"monthly":[{"period":"2040-06","totalCost":99,"agents":[
      {"agent":"claude","totalCost":7},{"agent":"codex","totalCost":9}]}]}]]
    assert.are.same(7, usage.parse_claude_cost_usd(json, "2040-06"))
    assert.are.same(0, usage.parse_claude_cost_usd(json, "2040-07"))
    assert.is_nil(usage.parse_claude_cost_usd('{"monthly":[{"period":"2040-06","totalCost":99}]}', "2040-06"))
    assert.is_nil(usage.parse_claude_cost_usd("invalid"))
  end)

  it("アカウントのレート情報から使用クレジットを取り出す", function()
    assert.are.same(
      42,
      usage.parse_codex_credits(
        [[{"id":2,"result":{"rateLimitsByLimitId":{"codex":{"individualLimit":{"used":"42"}}}}}]]
      )
    )
    assert.are.same(
      42,
      usage.parse_codex_credits([[{"id":2,"result":{"rateLimits":{"individualLimit":{"used":"42"}}}}]])
    )
    assert.is_nil(usage.parse_codex_credits('{"id":2,"result":{}}'))
    assert.is_nil(usage.parse_codex_credits("invalid"))
  end)

  it("指定した換算率だけを使う", function()
    assert.are.same(0.84, usage.codex_credits_to_usd(42, 0.02))
    assert.is_nil(usage.codex_credits_to_usd(42, 0))
  end)

  it("勤務時間と年月を読み取る", function()
    local target, cumulative, period =
      usage.parse_work_summary('{"target_hours":100,"cumulative_hours":50,"month":"2040-06"}')
    assert.are.same({ 100, 50, "2040-06" }, { target, cumulative, period })
    assert.are.same(50, usage.compute_pace_percent(cumulative, target))
    assert.is_nil(usage.compute_pace_percent(1, 0))
  end)

  it("使用率は丸め、上限0で除算しない", function()
    assert.are.same(25, usage.compute_ratio_percent(300, 1200))
    assert.is_nil(usage.compute_ratio_percent(1, 0))
  end)

  it("ペース差分とstatuslineの特殊文字を整形する", function()
    assert.are.same("ペース +3pt", usage.format_pace_diff(3))
    assert.are.same("ペース -3pt", usage.format_pace_diff(-3))
    assert.are.same("ペース通り", usage.format_pace_diff(0))
    assert.are.same("25%%", usage.escape_statusline_percent("25%"))
    assert.are.same("$12.00", usage.format_amount(12))
  end)

  it("キャッシュの期限と年月を判定する", function()
    assert.is_true(usage.is_stale(nil, 10, 100))
    assert.is_true(usage.is_stale(80, 10, 100))
    assert.is_false(usage.is_stale(95, 10, 100))
    assert.is_true(usage.is_current_period("2040-06", "2040-06"))
    assert.is_false(usage.is_current_period("2040-05", "2040-06"))
  end)
end)
