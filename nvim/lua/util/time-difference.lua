local M = {}

local function parse_time(value)
  local hours, minutes = value:match("^%s*(%d+):(%d%d)%s*$")
  local seconds = "0"
  if not hours then
    hours, minutes, seconds = value:match("^%s*(%d+):(%d%d):(%d%d)%s*$")
  end
  if not hours then
    return nil
  end

  hours = tonumber(hours)
  minutes = tonumber(minutes)
  seconds = tonumber(seconds)
  if minutes > 59 or seconds > 59 then
    return nil
  end
  return hours * 3600 + minutes * 60 + seconds
end

local function format_duration(total_seconds)
  local sign = total_seconds < 0 and "-" or ""
  local absolute_seconds = math.abs(total_seconds)
  local hours = math.floor(absolute_seconds / 3600)
  local minutes = math.floor(absolute_seconds % 3600 / 60)
  local seconds = absolute_seconds % 60
  if seconds == 0 then
    return string.format("%s%02d:%02d", sign, hours, minutes)
  end
  return string.format("%s%02d:%02d:%02d", sign, hours, minutes, seconds)
end

function M.try_calculate(expression)
  local left, operator, right = expression:match("^%s*(.-)%s*([+-])%s*(.-)%s*$")
  if not left then
    return nil, "引き算または足し算の式を入力してください"
  end

  local left_seconds = parse_time(left)
  local right_seconds = parse_time(right)
  if not left_seconds or not right_seconds then
    return nil, "時刻はH:MMまたはH:MM:SSで入力してください"
  end

  local result = operator == "+" and left_seconds + right_seconds or left_seconds - right_seconds
  return format_duration(result)
end

function M.calculate(expression)
  local result, error_message = M.try_calculate(expression)
  if not result then
    error(error_message)
  end
  return result
end

function M.open()
  vim.ui.input({ prompt = "時刻計算: " }, function(expression)
    if not expression or expression == "" then
      return
    end

    local result, error_message = M.try_calculate(expression)
    if not result then
      vim.notify(error_message, vim.log.levels.ERROR)
      return
    end

    vim.fn.setreg("+", result)
    vim.notify(result .. " をクリップボードへコピーしました")
  end)
end

function M.setup()
  vim.api.nvim_create_user_command("TimeDifference", M.open, {})
end

return M
