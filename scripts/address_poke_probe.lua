-- address_poke_probe.lua — T30.2 poke-verification (RetroAchievements final step).
--
-- Boots GNG to controllable, then for each candidate address (passed as a private
-- comma-separated env list) pokes a distinctive value and dumps RAM a few frames
-- later. The Python side compares pre/post dumps: the MASTER position address is the
-- one whose poke (a) sticks for a frame and (b) propagates to its mirror copies /
-- moves the sprite. Read-only mirrors get overwritten back by the master next frame.
--
-- Clean-room: candidate addresses come from a private env var, never hard-coded;
-- dumps go to private files; nothing private is printed.

local PREFIX_ENV     = "BLACKBOX_POKE_SNAPSHOT_PREFIX"
local CANDIDATES_ENV = "BLACKBOX_POKE_CANDIDATES"   -- "161,1323,1287" (decimal)
local POKE_VALUE     = 200
local RAM_SIZE       = 0x10000
local CONTROLLABLE   = 1520
local COIN_FRAME     = 950
local START_FRAME    = 1025
local SETTLE         = 40       -- frames between pokes

local prefix       = nil
local candidates   = {}
local memory_space = nil
local fields       = nil
local poke_index   = 0
local poke_frame   = 0
local phase        = "boot"

local function split_csv(s)
  local out = {}
  if s == nil then return out end
  for tok in string.gmatch(s, "([^,]+)") do
    local n = tonumber(tok)
    if n ~= nil then out[#out + 1] = math.floor(n) end
  end
  return out
end

local function resolve_env()
  prefix = os.getenv(PREFIX_ENV)
  candidates = split_csv(os.getenv(CANDIDATES_ENV))
end

local function init_memory()
  local cpu = manager.machine.devices[":maincpu"]
  if cpu == nil then return end
  memory_space = cpu.spaces["program"]
end

local function init_fields()
  fields = {}
  local sys = manager.machine.ioport.ports[":SYSTEM"]
  if sys ~= nil then
    fields.coin  = sys.fields["Coin 1"]
    fields.start = sys.fields["1 Player Start"]
  end
end

local function clear_inputs()
  if fields == nil then return end
  for _, fld in pairs(fields) do
    if fld ~= nil then fld:clear_value() end
  end
end

local function dump(name)
  if prefix == nil or memory_space == nil then return end
  local buf = {}
  for addr = 0, RAM_SIZE - 1 do
    buf[addr + 1] = memory_space:read_u8(addr)
  end
  local path = prefix .. name .. ".bin"
  local h = io.open(path .. ".tmp", "wb")
  if h == nil then return end
  h:write(string.char(table.unpack(buf)))
  h:close()
  os.rename(path .. ".tmp", path)
end

local function on_frame()
  local screen = manager.machine.screens[":screen"]
  if screen == nil then return end
  local frame = screen:frame_number()
  if memory_space == nil then init_memory() end
  if fields == nil then init_fields() end
  clear_inputs()

  if frame >= COIN_FRAME and frame < COIN_FRAME + 10 then fields.coin:set_value(1); return end
  if frame >= START_FRAME and frame < START_FRAME + 5 then fields.start:set_value(1); return end
  if frame < CONTROLLABLE then return end

  -- Poke each candidate in turn; dump "before" then "after" around each poke.
  if poke_index == 0 then
    poke_index = 1
    poke_frame = 0
    dump("baseline")
    return
  end
  if poke_index > #candidates then return end

  poke_frame = poke_frame + 1
  local addr = candidates[poke_index]
  if poke_frame == 1 then
    -- write the distinctive value
    pcall(function() memory_space:write_u8(addr, POKE_VALUE) end)
    print("blackbox_harness:poke:wrote:index:" .. poke_index)
  elseif poke_frame == 15 then
    dump("poke_" .. poke_index)  -- read 15 frames later: did it stick & propagate to render copies?
  elseif poke_frame >= SETTLE then
    poke_index = poke_index + 1
    poke_frame = 0
  end
end

resolve_env()
poke_frame_sub = emu.add_machine_frame_notifier(on_frame)
emu.add_machine_reset_notifier(function() init_memory() end)
