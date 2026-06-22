-- address_finder_scripted.lua — T30.2 scripted address finder (ADR-026 / ADR-028).
--
-- Non-interactive companion to address_search.lua. Boots GNG from cold (injecting
-- coin + start like mame_autoboot.lua), waits until Arthur is controllable (~frame
-- 1505), then runs a fixed sequence of input phases (still/right/still/left/jump),
-- injecting P1 inputs and dumping one full 64 KB RAM snapshot per phase to private
-- per-phase files. The Python finder (address_finder.py) intersects filters across
-- phases to isolate player_x / player_y deterministically — no human picker, no TUI.
--
-- Boot-from-cold (not savestate:load) is deliberate: machine:load stops the headless
-- frame notifier, so we drive the boot ourselves and start phases once controllable.
--
-- Clean-room: addresses/values stay in private files; nothing private printed; the
-- committed script holds no real addresses (only the 0x10000 RAM bound).

local SNAPSHOT_PREFIX_ENV = "BLACKBOX_FINDER_SNAPSHOT_PREFIX"  -- "<dir>/phase_"
local RAM_SIZE            = 0x10000
local COIN_FRAME          = 950    -- calibrated boot timing (see CLAUDE.md)
local START_FRAME         = 1025
local CONTROLLABLE_FRAME  = 1520   -- a few frames past 1505 for safety

-- Phase script: { name, button, frames }. button nil = no input (still).
-- Snapshot is taken on the last frame of each phase.
local PHASES = {
  { name = "still1",  button = nil,       frames = 40 },
  -- Sub-sampled right walk: a true position address increments smoothly across
  -- these; copies/scroll artifacts jump or plateau. Lets the finder pick by
  -- monotonic velocity consistency.
  { name = "right_a", button = "right",   frames = 16 },
  { name = "right_b", button = "right",   frames = 16 },
  { name = "right",   button = "right",   frames = 16 },
  { name = "still2",  button = nil,       frames = 40 },
  { name = "left",    button = "left",    frames = 48 },
  { name = "still3",  button = nil,       frames = 40 },
  { name = "jump",    button = "button1", frames = 18 },
  { name = "apex",    button = nil,       frames = 6  },
}

local BUTTON_FIELD_MAP = {
  coin    = { tag = ":SYSTEM", name = "Coin 1" },
  start   = { tag = ":SYSTEM", name = "1 Player Start" },
  right   = { tag = ":P1", name = "P1 Right" },
  left    = { tag = ":P1", name = "P1 Left" },
  button1 = { tag = ":P1", name = "P1 Button 1" },
}

local snapshot_prefix = nil
local memory_space    = nil
local injected_fields = nil
local phase_index     = 0
local phase_frame     = 0

local function resolve_env()
  snapshot_prefix = os.getenv(SNAPSHOT_PREFIX_ENV)
end

local function init_memory()
  local cpu = manager.machine.devices[":maincpu"]
  if cpu == nil then return false end
  memory_space = cpu.spaces["program"]
  return memory_space ~= nil
end

local function resolve_injected_fields()
  local resolved = {}
  for button_name, ref in pairs(BUTTON_FIELD_MAP) do
    local port = manager.machine.ioport.ports[ref.tag]
    if port ~= nil then
      local field = port.fields[ref.name]
      if field ~= nil then
        resolved[button_name] = field
      end
    end
  end
  return resolved
end

local function clear_inputs()
  if injected_fields == nil then return end
  for _, field in pairs(injected_fields) do
    field:clear_value()
  end
end

local function press(button)
  if button == nil or injected_fields == nil then return end
  local field = injected_fields[button]
  if field ~= nil then field:set_value(1) end
end

local function dump_ram(name)
  if snapshot_prefix == nil or memory_space == nil then return end
  local buf = {}
  for addr = 0, RAM_SIZE - 1 do
    buf[addr + 1] = memory_space:read_u8(addr)
  end
  local path = snapshot_prefix .. name .. ".bin"
  local handle = io.open(path .. ".tmp", "wb")
  if handle == nil then return end
  handle:write(string.char(table.unpack(buf)))
  handle:close()
  os.rename(path .. ".tmp", path)
end

local function on_frame()
  local screen = manager.machine.screens[":screen"]
  if screen == nil then return end
  local frame = screen:frame_number()

  if memory_space == nil then
    init_memory()
  end
  if injected_fields == nil then
    injected_fields = resolve_injected_fields()
  end

  clear_inputs()

  -- Boot injection (cold boot → controllable). Hold coin/start a few frames each.
  if frame >= COIN_FRAME and frame < COIN_FRAME + 10 then
    press("coin")
    return
  end
  if frame >= START_FRAME and frame < START_FRAME + 5 then
    press("start")
    return
  end
  if frame < CONTROLLABLE_FRAME then
    return  -- still booting / intro
  end

  -- Phase driver begins once controllable.
  if phase_index == 0 then
    phase_index = 1
    phase_frame = 0
  end
  if phase_index > #PHASES then
    return  -- done; idle
  end

  local phase = PHASES[phase_index]
  press(phase.button)
  phase_frame = phase_frame + 1

  if phase_frame >= phase.frames then
    dump_ram(phase.name)
    print("blackbox_harness:finder:phase_done:" .. phase.name)
    phase_index = phase_index + 1
    phase_frame = 0
    if phase_index > #PHASES then
      print("blackbox_harness:finder:complete")
    end
  end
end

resolve_env()
finder_frame_sub = emu.add_machine_frame_notifier(on_frame)
emu.add_machine_reset_notifier(function()
  init_memory()
end)
