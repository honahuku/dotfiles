local M = {}

function M.should_show(buftype, wrap)
  return buftype == "" and not wrap
end

return M
