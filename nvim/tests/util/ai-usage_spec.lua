-- public側はprivateのAI利用量実装を直接持たず、任意のbackendへ委譲する。
-- describe/it/assertはplenary.bustedが実行時にグローバルへ注入するため、
-- 静的解析では未定義に見える。assertもluassert拡張を使うため診断をやめる。
---@diagnostic disable: undefined-global, undefined-field

describe("public ai-usage facade", function()
  local function reset_modules()
    package.loaded["private.ai-usage"] = nil
    package.loaded["util.ai-usage"] = nil
  end

  after_each(function()
    package.preload["private.ai-usage"] = nil
    reset_modules()
  end)

  it("private backendがない場合は空のstatuslineを返す", function()
    reset_modules()
    local ai_usage = require("util.ai-usage")
    assert.are.same("", ai_usage.statusline())
  end)

  it("private backendのstatuslineへ委譲する", function()
    package.preload["private.ai-usage"] = function()
      return {
        statusline = function()
          return "private"
        end,
      }
    end
    reset_modules()

    local ai_usage = require("util.ai-usage")
    assert.are.same("private", ai_usage.statusline())
  end)

  it("private backendのsetupへ一度だけ委譲する", function()
    local setup_count = 0
    package.preload["private.ai-usage"] = function()
      return {
        setup = function()
          setup_count = setup_count + 1
        end,
      }
    end
    reset_modules()

    local ai_usage = require("util.ai-usage")
    ai_usage.setup()
    ai_usage.setup()
    assert.are.same(1, setup_count)
  end)

  it("private backendの読み込み失敗をpublicの起動失敗にしない", function()
    package.preload["private.ai-usage"] = function()
      error("private backend error")
    end
    reset_modules()

    local ai_usage = require("util.ai-usage")
    local ok = pcall(ai_usage.setup)
    assert.is_true(ok)
    assert.are.same("", ai_usage.statusline())
  end)
end)
