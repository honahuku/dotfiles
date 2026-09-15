-- private側のAI利用量backendを任意で読み込み、publicの表示層へ委譲する。
local M = {}

local backend
local backend_loaded = false
local setup_done = false

local function load_backend()
  if backend_loaded then
    return backend
  end
  backend_loaded = true

  local ok, module = pcall(require, "private.ai-usage")
  if not ok then
    backend = nil
    return nil
  end
  if type(module) ~= "table" then
    backend = nil
    return nil
  end

  backend = module
  return backend
end

function M.setup()
  if setup_done then
    return
  end
  setup_done = true

  local private_backend = load_backend()
  if private_backend and type(private_backend.setup) == "function" then
    pcall(private_backend.setup)
  end
end

function M.statusline()
  local private_backend = load_backend()
  if private_backend and type(private_backend.statusline) == "function" then
    local ok, result = pcall(private_backend.statusline)
    if ok and type(result) == "string" then
      return result
    end
  end
  return ""
end

return M
