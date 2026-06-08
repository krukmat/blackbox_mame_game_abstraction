-- T08.2.5 — updated for MAME 0.287: emu.register_* deprecated, emu.framecount() removed.
-- T10.1.1.2 — per-frame callback added using emu.add_machine_frame_notifier (confirmed in T10.1.1.1).
-- T10.1.4 — input plan JSON is exported by the harness and passed via env for frame-accurate input injection.
local INPUT_PLAN_ENV_VAR = "BLACKBOX_INPUT_PLAN_PATH"
-- T20.1: per-frame ground-truth input timeline (ADR-023). The effective input state
-- (injected plan OR human keyboard) is logged to a private input_timeline.json.
local INPUT_TIMELINE_ENV_VAR = "BLACKBOX_INPUT_TIMELINE_PATH"
-- T20.5 (ADR-026): optional RAM memory tap. The harness converts a local/private YAML
-- address map to a private JSON and points this env var at it. When present, per-frame
-- numeric entity state is logged to a private state_timeline.json. Addresses and raw
-- values stay private and are never printed (clause 2). Absent config = no tap (clause 5).
local MEMORY_MAP_ENV_VAR = "BLACKBOX_MEMORY_MAP_PATH"
local STATE_TIMELINE_ENV_VAR = "BLACKBOX_STATE_TIMELINE_PATH"
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
-- T20.1: fixed iteration order so the recorded `buttons` array is deterministic
-- (HP-1: scripted timeline must match the injected plan byte-for-byte ordering).
local BUTTON_ORDER = { "coin", "start", "left", "right", "up", "down", "button1", "button2" }

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
        -- T20.1: keep port + mask + defvalue so the effective state can be read back.
        -- field:set_value() overrides are reflected in port:read(); active-low vs
        -- active-high is normalized via `(value ~ defvalue) & mask`. MAME 0.287 has
        -- no ioport_field:read(), so the port read is the authoritative source.
        resolved[button_name] = {
          field = field,
          port = port,
          mask = field.mask,
          defvalue = field.defvalue,
        }
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
  for _, entry in pairs(injected_fields) do
    entry.field:clear_value()
  end
end

local function apply_buttons(buttons)
  if buttons == nil or injected_fields == nil then
    return
  end
  for _, button_name in ipairs(buttons) do
    local entry = injected_fields[button_name]
    if entry ~= nil then
      entry.field:set_value(1)
    elseif warned_buttons[button_name] ~= true then
      warned_buttons[button_name] = true
      print("blackbox_harness:input_button:unmapped:" .. tostring(button_name))
    end
  end
end

-- T20.1: in-memory ground-truth timeline, flushed to JSON on machine stop.
local input_timeline = {}

-- Read the effective per-frame input state (injected plan OR human keyboard) and
-- append it as { frame = N, buttons = {...} }. Buttons follow BUTTON_ORDER so the
-- serialized array is deterministic.
local function record_effective_state(frame_number)
  if injected_fields == nil then
    return
  end
  local port_values = {}
  local pressed = {}
  for _, button_name in ipairs(BUTTON_ORDER) do
    local entry = injected_fields[button_name]
    if entry ~= nil then
      local value = port_values[entry.port]
      if value == nil then
        value = entry.port:read()
        port_values[entry.port] = value
      end
      if (value ~ entry.defvalue) & entry.mask ~= 0 then
        table.insert(pressed, button_name)
      end
    end
  end
  table.insert(input_timeline, { frame = frame_number, buttons = pressed })
end

-- Resolve the private timeline path: explicit env var first, otherwise derived
-- from the input-plan path (same logs/ directory). Returns nil if neither exists.
local function resolve_timeline_path()
  local explicit = os.getenv(INPUT_TIMELINE_ENV_VAR)
  if explicit ~= nil and explicit ~= "" then
    return explicit
  end
  local plan_path = os.getenv(INPUT_PLAN_ENV_VAR)
  if plan_path ~= nil and plan_path ~= "" then
    return (plan_path:gsub("input_plan%.json$", "input_timeline.json"))
  end
  return nil
end

-- Serialize the timeline to JSON. Button names are a fixed ASCII set, so no string
-- escaping is required.
local function encode_timeline(timeline)
  local entries = {}
  for _, entry in ipairs(timeline) do
    local quoted = {}
    for _, button_name in ipairs(entry.buttons) do
      table.insert(quoted, '"' .. button_name .. '"')
    end
    table.insert(
      entries,
      string.format('{"frame":%d,"buttons":[%s]}', entry.frame, table.concat(quoted, ","))
    )
  end
  return "[" .. table.concat(entries, ",") .. "]"
end

-- ADR-003/ADR-006: never print the private path to stdout; only a count.
local function write_timeline()
  local path = resolve_timeline_path()
  if path == nil then
    print("blackbox_harness:input_timeline:no_path")
    return
  end
  local handle = io.open(path, "w")
  if handle == nil then
    print("blackbox_harness:input_timeline:unwritable")
    return
  end
  handle:write(encode_timeline(input_timeline))
  handle:close()
  print("blackbox_harness:input_timeline:written:" .. tostring(#input_timeline))
end

-- ───────────────────────────────────────────────────────────────────────────
-- T20.5 (ADR-026) — optional RAM memory tap.
-- Reads numeric entity state from configured cheat-DB addresses into a private
-- state_timeline.json. Addresses/values never reach stdout (clause 2). No config
-- means the tap is inert and the pipeline falls back to vision (clause 5).
-- ───────────────────────────────────────────────────────────────────────────

local memory_map = nil
local memory_map_loaded = false
local memory_space = nil
local state_timeline = {}

local function load_memory_map_from_env()
  local path = os.getenv(MEMORY_MAP_ENV_VAR)
  if path == nil or path == "" then
    return nil
  end
  local handle = io.open(path, "r")
  if handle == nil then
    print("blackbox_harness:memory_map:unreadable")  -- no path in stdout (ADR-003)
    return nil
  end
  local raw = handle:read("*a")
  handle:close()
  local ok, decoded = pcall(decode_json, raw)
  if not ok or type(decoded) ~= "table" then
    print("blackbox_harness:memory_map:invalid_json")
    return nil
  end
  return decoded
end

local function initialize_memory_map()
  if memory_map_loaded then
    return
  end
  memory_map_loaded = true
  memory_map = load_memory_map_from_env()
  if memory_map == nil then
    return  -- clause 5: graceful absence, no tap
  end
  local cpu = manager.machine.devices[memory_map.cpu_tag or ":maincpu"]
  if cpu ~= nil then
    memory_space = cpu.spaces[memory_map.space or "program"]
  end
  if memory_space == nil then
    print("blackbox_harness:memory_map:space_unavailable")
    memory_map = nil
  else
    print("blackbox_harness:memory_map:loaded")
  end
end

local function read_memory_field(field)
  if field == nil or field.addr == nil then
    return nil
  end
  local ok, value = pcall(function()
    if field.size == "u16" then
      return memory_space:read_u16(field.addr)
    end
    return memory_space:read_u8(field.addr)
  end)
  if ok then
    return value
  end
  return nil
end

local function record_memory_state(frame_number)
  if memory_map == nil or memory_space == nil then
    return
  end
  if type(memory_map.entities) ~= "table" then
    return
  end
  for _, entity in ipairs(memory_map.entities) do
    if type(entity) == "table" and entity.name ~= nil and type(entity.fields) == "table" then
      local record = { frame = frame_number, entity = entity.name }
      record.x = read_memory_field(entity.fields.x)
      record.y = read_memory_field(entity.fields.y)
      record.state_flags = read_memory_field(entity.fields.state_flags)
      table.insert(state_timeline, record)
    end
  end
end

local function resolve_state_timeline_path()
  local explicit = os.getenv(STATE_TIMELINE_ENV_VAR)
  if explicit ~= nil and explicit ~= "" then
    return explicit
  end
  local plan_path = os.getenv(INPUT_PLAN_ENV_VAR)
  if plan_path ~= nil and plan_path ~= "" then
    return (plan_path:gsub("input_plan%.json$", "state_timeline.json"))
  end
  return nil
end

local function encode_state_timeline(timeline)
  local entries = {}
  for _, record in ipairs(timeline) do
    local parts = {
      string.format('"frame":%d', record.frame),
      string.format('"entity":"%s"', record.entity),
    }
    if record.x ~= nil then
      table.insert(parts, string.format('"x":%d', record.x))
    end
    if record.y ~= nil then
      table.insert(parts, string.format('"y":%d', record.y))
    end
    if record.state_flags ~= nil then
      table.insert(parts, string.format('"state_flags":%d', record.state_flags))
    end
    table.insert(entries, "{" .. table.concat(parts, ",") .. "}")
  end
  return "[" .. table.concat(entries, ",") .. "]"
end

local function write_state_timeline()
  if memory_map == nil then
    return  -- tap was never active
  end
  local path = resolve_state_timeline_path()
  if path == nil then
    print("blackbox_harness:state_timeline:no_path")
    return
  end
  local handle = io.open(path, "w")
  if handle == nil then
    print("blackbox_harness:state_timeline:unwritable")
    return
  end
  handle:write(encode_state_timeline(state_timeline))
  handle:close()
  print("blackbox_harness:state_timeline:written:" .. tostring(#state_timeline))
end

emu.add_machine_reset_notifier(function()
  initialize_input_injection()
  print("blackbox_harness:start")
end)

emu.add_machine_stop_notifier(function()
  write_timeline()  -- T20.1: flush ground-truth input timeline before shutdown
  write_state_timeline()  -- T20.5: flush RAM state timeline (no-op if tap inactive)
  print("blackbox_harness:stop")
end)

-- Subscription stored at module scope to prevent Lua GC from destroying it between frames.
frame_sub = emu.add_machine_frame_notifier(function()
  initialize_input_injection()
  local screen = manager.machine.screens[':screen']
  if screen then
    initialize_memory_map()  -- T20.5: lazy load of the optional RAM address map
    local frame_number = screen:frame_number()
    clear_injected_fields()
    apply_buttons(loaded_input_plan[frame_number])
    -- T20.1: record the effective state AFTER applying the plan, so the read picks up
    -- both the injected override and any human keyboard input for this frame.
    record_effective_state(frame_number)
    record_memory_state(frame_number)  -- T20.5: numeric RAM state (no-op if no config)
    print("blackbox_harness:frame:" .. frame_number)
  end
end)
