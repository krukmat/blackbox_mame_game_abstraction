emu.register_start(function()
  print("blackbox_harness:start")
end)

emu.register_frame_done(function()
  local frame = emu.framecount()
  print(string.format("blackbox_harness:frame=%d", frame))
end)

emu.register_stop(function()
  print("blackbox_harness:stop")
end)
