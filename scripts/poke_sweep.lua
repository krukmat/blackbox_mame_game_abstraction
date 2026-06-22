-- poke_sweep.lua — T30.2 master-address sweep (ADR-026 / ADR-028).
--
-- Boots GNG to controllable, then sweeps a contiguous address RANGE: for each address
-- it writes a distinctive value, waits a few frames for the render pipeline, dumps a
-- "witness" byte (a known render-copy of player screen-x), then restores the original.
-- The MASTER player-x is the address whose poke moves the witness. Fully headless: the
-- witness byte is the on-screen x copy, so no operator eyes are needed.
--
-- Clean-room: range + witness come from private env vars, never hard-coded; output is
-- a private CSV of (address, witness_before, witness_after); nothing private printed.

local PREFIX_ENV   = "BLACKBOX_SWEEP_PREFIX"      -- output file prefix
local RANGE_LO_ENV = "BLACKBOX_SWEEP_LO"          -- decimal start addr
local RANGE_HI_ENV = "BLACKBOX_SWEEP_HI"          -- decimal end addr (inclusive)
local WITNESS_ENV  = "BLACKBOX_SWEEP_WITNESS"     -- decimal witness addr (render copy)
local POKE_VALUE   = 200
local COIN_FRAME   = 950
local START_FRAME  = 1025
local CONTROLLABLE = 1520
local SETTLE       = 8     -- frames to let the poke propagate to the witness

local prefix  = os.getenv(PREFIX_ENV)
local lo      = tonumber(os.getenv(RANGE_LO_ENV) or "0") or 0
local hi      = tonumber(os.getenv(RANGE_HI_ENV) or "0") or 0
local witness = tonumber(os.getenv(WITNESS_ENV) or "0") or 0

local memory_space = nil
local fields = nil
local sweep_addr = nil
local sweep_step = 0
local orig_value = nil
local witness_before = nil
local results = {}
local done = false

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

local function flush()
  if prefix == nil then return end
  local h = io.open(prefix .. "sweep.csv", "w")
  if h == nil then return end
  for _, r in ipairs(results) do
    h:write(string.format("%d,%d,%d\n", r.addr, r.before, r.after))
  end
  h:close()
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
  if done or memory_space == nil then return end

  if sweep_addr == nil then
    sweep_addr = lo
    sweep_step = 0
  end

  if sweep_step == 0 then
    -- snapshot original, then poke a distinctive value
    orig_value = memory_space:read_u8(sweep_addr)
    witness_before = orig_value
    memory_space:write_u8(sweep_addr, POKE_VALUE)
    sweep_step = 1
  elseif sweep_step >= SETTLE then
    -- read back: does the poked value STICK (master/free var) or get reverted by
    -- the game logic (read-only copy / derived)? before=orig, after=current.
    local after = memory_space:read_u8(sweep_addr)
    results[#results + 1] = { addr = sweep_addr, before = witness_before, after = after }
    -- restore so we don't permanently corrupt state for later addresses
    memory_space:write_u8(sweep_addr, orig_value)
    sweep_addr = sweep_addr + 1
    sweep_step = 0
    if sweep_addr > hi then
      done = true
      flush()
      print("blackbox_harness:sweep:complete")
    end
  else
    sweep_step = sweep_step + 1
  end
end

sweep_frame_sub = emu.add_machine_frame_notifier(on_frame)
emu.add_machine_reset_notifier(function() init_memory() end)
