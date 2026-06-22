-- poke_live.lua — T30.2 live poke-confirmation (operator watches the screen).
--
-- Boots GNG to controllable, then every ~2 seconds writes POKE_VALUE to the
-- candidate address (passed via env). The operator watches Arthur: if he snaps to a
-- fixed horizontal position each time the poke fires, the address is player_x.
--
-- Clean-room: the address comes from a private env var, never hard-coded.

local CAND_ENV    = "BLACKBOX_POKE_ADDR"     -- decimal address
local VALUE_ENV   = "BLACKBOX_POKE_VALUE"    -- decimal value (default 200)
local COIN_FRAME  = 950
local START_FRAME = 1025
local CONTROLLABLE = 1520
local POKE_PERIOD = 120   -- frames between pokes (~2s)

local memory_space = nil
local fields = nil
local addr = tonumber(os.getenv(CAND_ENV) or "")
local value = tonumber(os.getenv(VALUE_ENV) or "200") or 200

local function init_memory()
  local cpu = manager.machine.devices[":maincpu"]
  if cpu ~= nil then memory_space = cpu.spaces["program"] end
end

local function init_fields()
  fields = {}
  local sys = manager.machine.ioport.ports[":SYSTEM"]
  if sys ~= nil then
    fields.coin = sys.fields["Coin 1"]
    fields.start = sys.fields["1 Player Start"]
  end
end

local function on_frame()
  local screen = manager.machine.screens[":screen"]
  if screen == nil then return end
  local frame = screen:frame_number()
  if memory_space == nil then init_memory() end
  if fields == nil then init_fields() end
  if fields ~= nil then
    if fields.coin then fields.coin:clear_value() end
    if fields.start then fields.start:clear_value() end
  end

  if frame >= COIN_FRAME and frame < COIN_FRAME + 10 then fields.coin:set_value(1); return end
  if frame >= START_FRAME and frame < START_FRAME + 5 then fields.start:set_value(1); return end
  if frame < CONTROLLABLE then return end

  if addr ~= nil and memory_space ~= nil and (frame % POKE_PERIOD == 0) then
    pcall(function() memory_space:write_u8(math.floor(addr), value) end)
    print("blackbox_harness:poke_live:fired")
  end
end

poke_live_sub = emu.add_machine_frame_notifier(on_frame)
emu.add_machine_reset_notifier(function() init_memory() end)
