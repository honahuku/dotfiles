---@diagnostic disable: undefined-global
local time_difference = require("util.time-difference")

describe("time-difference", function()
  describe("calculate", function()
    it("時刻の引き算を計算する", function()
      assert.are.equal("01:53", time_difference.calculate("12:00 - 10:07"))
    end)

    it("時刻の足し算を計算する", function()
      assert.are.equal("13:07", time_difference.calculate("12:00 + 01:07"))
    end)

    it("マイナス結果を返す", function()
      assert.are.equal("-01:53", time_difference.calculate("10:07 - 12:00"))
    end)

    it("秒付きの入力を計算する", function()
      assert.are.equal("01:53:15", time_difference.calculate("12:00:30 - 10:07:15"))
    end)

    it("24時間を超える入力で日付をまたぐ計算をする", function()
      assert.are.equal("00:45", time_difference.calculate("24:30 - 23:45"))
    end)

    it("不正な入力はエラーを返す", function()
      local result, error_message = time_difference.try_calculate("12:99 - 10:00")

      assert.is_nil(result)
      assert.are.equal("時刻はH:MMまたはH:MM:SSで入力してください", error_message)
    end)

    it("演算子がない入力はエラーを返す", function()
      local result, error_message = time_difference.try_calculate("12:00")

      assert.is_nil(result)
      assert.are.equal("引き算または足し算の式を入力してください", error_message)
    end)
  end)
end)
