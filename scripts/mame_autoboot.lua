-- T08.2.5 — updated for MAME 0.287: emu.register_* deprecated, emu.framecount() removed.
-- T10.1.1.2 — per-frame callback added using emu.add_machine_frame_notifier (confirmed in T10.1.1.1).
-- T10.1.4 — input plan JSON is exported by the harness and passed via env for frame-accurate input injection.
local INPUT_PLAN_ENV_VAR = "BLACKBOX_INPUT_PLAN_PATH"
local BUTTON_FIELD_MAP = {
  coin = { tag = ":SYSTEM", name = "Coin 1" },
  start = { tag = ":SYSTEM", name = "1 Player Start" },
  left = { tag = ":P1", name = "P1 Left" },
  right = { tag = ":P1", name = "P1 Right" },
  up = { tag = ":P1", name = "P1 Up" },
  down = { tag = ":P1", name = "P1 Down" },
  button1 = { tag = ":P1", name = "P1 Button 1" },
  button2 = { tag = ":P1", name = "P1 Button 2" },
}

local function skip_whitespace(text, index)
  while index <= #text do
    local byte = string.byte(text, index)
    if byte ~= 32 and byte ~= 9 and byte ~= 10 and byte ~= 13 then
      break
    end
    index = index + 1
  end
  return index
end

local function parse_string(text, index)
  index = index + 1
  local chunks = {}
  while index <= #text do
    local char = string.sub(text, index, index)
    if char == '"' then
      return table.concat(chunks), index + 1
    end
    if char == "\\" then
      local escaped = string.sub(text, index + 1, index + 1)
      local mapping = {
        ['"'] = '"',
        ["\\"] = "\\",
        ["/"] = "/",
        b = "\b",
        f = "\f",
        n = "\n",
        r = "\r",
        t = "\t",
      }
      if escaped == "u" then
        error("unicode escapes are not supported in input plan JSON")
      end
      if mapping[escaped] == nil then
        error("invalid JSON escape sequence")
      end
      table.insert(chunks, mapping[escaped])
      index = index + 2
    else
      table.insert(chunks, char)
      index = index + 1
    end
  end
  error("unterminated JSON string")
end

local function parse_number(text, index)
  local end_index = index
  while end_index <= #text and string.match(string.sub(text, end_index, end_index), "[%d%+%-%eE%.]") do
    end_index = end_index + 1
  end
  local value = tonumber(string.sub(text, index, end_index - 1))
  if value == nil then
    error("invalid JSON number")
  end
  return value, end_index
end

local parse_value

local function parse_array(text, index)
  local result = {}
  index = skip_whitespace(text, index + 1)
  if string.sub(text, index, index) == "]" then
    return result, index + 1
  end
  while true do
    local value
    value, index = parse_value(text, index)
    table.insert(result, value)
    index = skip_whitespace(text, index)
    local delimiter = string.sub(text, index, index)
    if delimiter == "]" then
      return result, index + 1
    end
    if delimiter ~= "," then
      error("expected ',' or ']' in JSON array")
    end
    index = skip_whitespace(text, index + 1)
  end
end

local function parse_object(text, index)
  local result = {}
  index = skip_whitespace(text, index + 1)
  if string.sub(text, index, index) == "}" then
    return result, index + 1
  end
  while true do
    if string.sub(text, index, index) ~= '"' then
      error("expected string key in JSON object")
    end
    local key
    key, index = parse_string(text, index)
    index = skip_whitespace(text, index)
    if string.sub(text, index, index) ~= ":" then
      error("expected ':' in JSON object")
    end
    local value
    value, index = parse_value(text, skip_whitespace(text, index + 1))
    result[key] = value
    index = skip_whitespace(text, index)
    local delimiter = string.sub(text, index, index)
    if delimiter == "}" then
      return result, index + 1
    end
    if delimiter ~= "," then
      error("expected ',' or '}' in JSON object")
    end
    index = skip_whitespace(text, index + 1)
  end
end

parse_value = function(text, index)
  index = skip_whitespace(text, index)
  local char = string.sub(text, index, index)
  if char == "{" then
    return parse_object(text, index)
  end
  if char == "[" then
    return parse_array(text, index)
  end
  if char == '"' then
    return parse_string(text, index)
  end
  if char == "-" or string.match(char, "%d") then
    return parse_number(text, index)
  end
  if string.sub(text, index, index + 3) == "true" then
    return true, index + 4
  end
  if string.sub(text, index, index + 4) == "false" then
    return false, index + 5
  end
  if string.sub(text, index, index + 3) == "null" then
    return nil, index + 4
  end
  error("unexpected JSON token")
end

local function decode_json(text)
  local value, next_index = parse_value(text, 1)
  next_index = skip_whitespace(text, next_index)
  if next_index <= #text then
    error("unexpected trailing JSON content")
  end
  return value
end

local function load_input_plan_from_env()
  local path = os.getenv(INPUT_PLAN_ENV_VAR)
  if path == nil or path == "" then
    print("blackbox_harness:input_plan:missing")
    return {}
  end

  local handle = io.open(path, "r")
  if handle == nil then
    print("blackbox_harness:input_plan:unreadable:" .. path)
    return {}
  end

  local raw = handle:read("*a")
  handle:close()

  local ok, decoded = pcall(decode_json, raw)
  if not ok then
    print("blackbox_harness:input_plan:invalid_json")
    return {}
  end

  local frames = {}
  for _, entry in ipairs(decoded) do
    if type(entry) == "table" and type(entry.frame) == "number" and type(entry.buttons) == "table" then
      frames[entry.frame] = entry.buttons
    end
  end
  print("blackbox_harness:input_plan:loaded:" .. tostring(#decoded))
  return frames
end

local function resolve_injected_fields()
  local resolved = {}
  for button_name, field_ref in pairs(BUTTON_FIELD_MAP) do
    local port = manager.machine.ioport.ports[field_ref.tag]
    if port ~= nil then
      local field = port.fields[field_ref.name]
      if field ~= nil then
        resolved[button_name] = field
      else
        print("blackbox_harness:input_field:missing:" .. button_name)
      end
    else
      print("blackbox_harness:input_port:missing:" .. field_ref.tag)
    end
  end
  return resolved
end

local loaded_input_plan = nil
local injected_fields = nil
local warned_buttons = {}

local function initialize_input_injection()
  if loaded_input_plan == nil then
    loaded_input_plan = load_input_plan_from_env()
  end
  if injected_fields == nil then
    injected_fields = resolve_injected_fields()
  end
end

local function clear_injected_fields()
  if injected_fields == nil then
    return
  end
  for _, field in pairs(injected_fields) do
    field:clear_value()
  end
end

local function apply_buttons(buttons)
  if buttons == nil or injected_fields == nil then
    return
  end
  for _, button_name in ipairs(buttons) do
    local field = injected_fields[button_name]
    if field ~= nil then
      field:set_value(1)
    elseif warned_buttons[button_name] ~= true then
      warned_buttons[button_name] = true
      print("blackbox_harness:input_button:unmapped:" .. tostring(button_name))
    end
  end
end

emu.add_machine_reset_notifier(function()
  initialize_input_injection()
  print("blackbox_harness:start")
end)

emu.add_machine_stop_notifier(function()
  print("blackbox_harness:stop")
end)

-- Subscription stored at module scope to prevent Lua GC from destroying it between frames.
frame_sub = emu.add_machine_frame_notifier(function()
  initialize_input_injection()
  local screen = manager.machine.screens[':screen']
  if screen then
    local frame_number = screen:frame_number()
    clear_injected_fields()
    apply_buttons(loaded_input_plan[frame_number])
    print("blackbox_harness:frame:" .. frame_number)
  end
end)
