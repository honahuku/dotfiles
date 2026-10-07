---@diagnostic disable: undefined-global
local final_blank_line = require("util.final-blank-line")

describe("final-blank-line", function()
  local buf
  local path

  before_each(function()
    vim.cmd("enew!")
    buf = vim.api.nvim_get_current_buf()
    path = vim.fn.tempname()
    vim.api.nvim_buf_set_name(buf, path)
    vim.bo[buf].swapfile = false
    final_blank_line.setup()
    vim.wait(20, function()
      return false
    end)
  end)

  after_each(function()
    vim.cmd("enew!")
  end)

  it("saves a real blank third line after two text lines", function()
    vim.api.nvim_buf_set_lines(buf, 0, -1, false, { "first", "second" })
    vim.cmd("write")
    assert.are.same({ "first", "second", "" }, vim.fn.readfile(path))
    assert.are.same({ "first", "second", "", "" }, vim.fn.readfile(path, "b"))
    assert.are.same({ "first", "second", "" }, vim.api.nvim_buf_get_lines(buf, 0, -1, false))
  end)

  it("does not grow on repeated saves and appends again after typing on the last line", function()
    vim.api.nvim_buf_set_lines(buf, 0, -1, false, { "first" })
    vim.cmd("write")
    vim.cmd("write")
    assert.are.same({ "first", "" }, vim.fn.readfile(path))
    vim.api.nvim_buf_set_lines(buf, -2, -1, false, { "second" })
    vim.cmd("write")
    assert.are.same({ "first", "second", "" }, vim.fn.readfile(path))
  end)

  it("preserves existing blank lines", function()
    vim.api.nvim_buf_set_lines(buf, 0, -1, false, { "first", "", "" })
    vim.cmd("write")
    assert.are.same({ "first", "", "" }, vim.fn.readfile(path))
  end)

  it("leaves an empty file empty", function()
    vim.cmd("write")
    assert.are.equal(0, vim.fn.getfsize(path))
  end)

  it("leaves binary buffers unchanged", function()
    vim.bo[buf].binary = true
    vim.api.nvim_buf_set_lines(buf, 0, -1, false, { "first" })
    vim.cmd("write")
    assert.are.same({ "first" }, vim.fn.readfile(path))
  end)

  it("adds the blank line after a save formatter removes it", function()
    final_blank_line.setup()
    local group = vim.api.nvim_create_augroup("test_final_blank_formatter", { clear = true })
    vim.api.nvim_create_autocmd("BufWritePre", {
      group = group,
      callback = function()
        vim.api.nvim_buf_set_lines(buf, 0, -1, false, { "formatted" })
      end,
    })
    vim.wait(20, function()
      return false
    end)
    vim.cmd("write")
    local saved = vim.fn.readfile(path)
    vim.api.nvim_del_augroup_by_id(group)
    assert.are.same({ "formatted", "" }, saved)
  end)
end)
