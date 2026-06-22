-- address_search.lua — T30.2 RAM address search tool (ADR-026 / ADR-028).
--
-- Dumps a full 64KB RAM snapshot to a private exchange file every DUMP_INTERVAL frames.
-- The Python TUI (address_search.py) reads the snapshot, applies incremental filters,
-- and saves accepted candidates to evidence/private/gng_address_candidates.json.
--
-- Clean-room contract: addresses and raw values stay in private exchange files only.
-- Nothing is printed to stdout. The committed script contains no real addresses.

local SNAPSHOT_ENV_VAR  = "BLACKBOX_ADDR_SNAPSHOT_PATH"   -- written by Lua each frame
local CMD_ENV_VAR       = "BLACKBOX_ADDR_CMD_PATH"         -- Python writes commands here
-- Optional savestate anchor (ADR-028): a MAME state slot name. When set, the script
-- loads it once a few frames in (machine:load), starting the search at the controllable
-- state without re-booting. Loading from Lua avoids the -state reset-notifier loop.
local ANCHOR_SLOT_ENV_VAR = "BLACKBOX_ADDR_ANCHOR_SLOT"
local ANCHOR_LOAD_FRAME = 30   -- load the anchor after the machine has settled
local DUMP_INTERVAL     = 4    -- frames between snapshots (reduce I/O)
local RAM_SIZE          = 0x10000  -- 64 KB

local snapshot_path = nil
local cmd_path      = nil
local anchor_slot   = nil
local anchor_loaded = false
local memory_space  = nil
local frame_count   = 0
local paused        = false

local function resolve_paths()
  snapshot_path = os.getenv(SNAPSHOT_ENV_VAR)
  cmd_path      = os.getenv(CMD_ENV_VAR)
  anchor_slot   = os.getenv(ANCHOR_SLOT_ENV_VAR)
end

local function init_memory()
  local cpu = manager.machine.devices[":maincpu"]
  if cpu == nil then
    return false
  end
  memory_space = cpu.spaces["program"]
  return memory_space ~= nil
end

local function dump_ram()
  if snapshot_path == nil or memory_space == nil then
    return
  end
  local buf = {}
  for addr = 0, RAM_SIZE - 1 do
    buf[addr + 1] = memory_space:read_u8(addr)
  end
  local handle = io.open(snapshot_path .. ".tmp", "wb")
  if handle == nil then
    return
  end
  -- Write frame number as 4-byte little-endian header, then raw bytes.
  local fn = frame_count
  handle:write(string.char(
    fn % 256,
    math.floor(fn / 256) % 256,
    math.floor(fn / 65536) % 256,
    math.floor(fn / 16777216) % 256
  ))
  handle:write(string.char(table.unpack(buf)))
  handle:close()
  -- Atomic rename so Python never reads a partial file.
  os.rename(snapshot_path .. ".tmp", snapshot_path)
end

local function read_cmd()
  if cmd_path == nil then
    return nil
  end
  local handle = io.open(cmd_path, "r")
  if handle == nil then
    return nil
  end
  local cmd = handle:read("*l")
  handle:close()
  -- Consume the command so it's not re-read.
  local wh = io.open(cmd_path, "w")
  if wh ~= nil then
    wh:close()
  end
  return cmd
end

local function on_frame()
  frame_count = frame_count + 1
  if memory_space == nil then
    init_memory()
    return
  end
  -- Load the savestate anchor once, after the machine has settled. machine:load
  -- triggers a reset; anchor_loaded guards against reloading in the reset notifier.
  if anchor_slot ~= nil and anchor_slot ~= "" and not anchor_loaded
      and frame_count >= ANCHOR_LOAD_FRAME then
    anchor_loaded = true
    pcall(function() manager.machine:load(anchor_slot) end)
  end
  local cmd = read_cmd()
  if cmd == "pause" then
    paused = true
  elseif cmd == "resume" then
    paused = false
  end
  if paused then
    return
  end
  if frame_count % DUMP_INTERVAL == 0 then
    dump_ram()
  end
end

-- Boot.
-- MAME 0.287+ removed emu.register_*; use add_machine_reset_notifier instead
-- (mirrors scripts/mame_autoboot.lua). The frame-notifier subscription is stored at
-- module scope so Lua GC does not destroy it between frames.
resolve_paths()
addr_search_frame_sub = emu.add_machine_frame_notifier(on_frame)
emu.add_machine_reset_notifier(function()
  -- A reset fired by the anchor load (machine:load) must not rewind our frame
  -- counter, or the load would retrigger forever. Only reset on the true cold boot.
  if not anchor_loaded then
    frame_count = 0
  end
  paused = false
  init_memory()
end)
