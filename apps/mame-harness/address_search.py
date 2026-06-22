"""T30.2 / ADR-028 — Guided RAM address-search TUI.

Workflow:
  1. Launch MAME with address_search.lua (sets BLACKBOX_ADDR_SNAPSHOT_PATH + BLACKBOX_ADDR_CMD_PATH).
  2. Run this TUI: python address_search.py --snapshot <path> --cmd <path> --out <candidates.json>
  3. Take a snapshot baseline (all 64 KB).
  4. Play the game, change a variable (e.g. move Arthur right).
  5. Apply a filter (!=, <, >, =, changed, unchanged) to narrow candidates.
  6. Repeat until 1 candidate per variable.
  7. Name and accept each candidate → saved to private candidates JSON.
  8. Load a prior session with --resume to skip step 3.

Clean-room contract (ADR-026):
  - Addresses and raw values stay private (never printed to stdout in production mode).
  - Output JSON lives under evidence/private/ only.
  - No addresses or raw values appear in public specs.
"""
from __future__ import annotations

import argparse
import json
import os
import struct
import sys
import time
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Snapshot reader
# ---------------------------------------------------------------------------

def read_snapshot(path: Path) -> tuple[int, bytes] | None:
    """Return (frame, ram_bytes) or None if file is absent/incomplete."""
    try:
        data = path.read_bytes()
    except OSError:
        return None
    if len(data) < 4:
        return None
    frame = struct.unpack_from("<I", data, 0)[0]
    ram = data[4:]
    if len(ram) < 0x10000:
        return None
    return frame, ram


# ---------------------------------------------------------------------------
# Filter engine
# ---------------------------------------------------------------------------

def apply_filter(
    candidates: list[int],
    baseline: bytes,
    current: bytes,
    op: str,
    value: Optional[int],
) -> list[int]:
    result = []
    for addr in candidates:
        b = baseline[addr]
        c = current[addr]
        if op == "!=":
            if c != b:
                result.append(addr)
        elif op == "<":
            if c < b:
                result.append(addr)
        elif op == ">":
            if c > b:
                result.append(addr)
        elif op == "=" and value is not None:
            if c == value:
                result.append(addr)
        elif op == "changed":
            if c != b:
                result.append(addr)
        elif op == "unchanged":
            if c == b:
                result.append(addr)
    return result


# ---------------------------------------------------------------------------
# BCD detection
# ---------------------------------------------------------------------------

def _looks_bcd(value: int) -> bool:
    lo = value & 0x0F
    hi = (value >> 4) & 0x0F
    return lo <= 9 and hi <= 9


def detect_encoding(addr: int, snapshots: list[bytes]) -> str:
    values = [s[addr] for s in snapshots if len(s) > addr]
    if len(values) < 2:
        return "u8"
    if all(_looks_bcd(v) for v in values):
        return "bcd8"
    return "u8"


# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------

class SearchSession:
    def __init__(self, snapshot_path: Path, cmd_path: Path, out_path: Path) -> None:
        self.snapshot_path = snapshot_path
        self.cmd_path = cmd_path
        self.out_path = out_path
        self.baseline: bytes | None = None
        self.candidates: list[int] = list(range(0x10000))
        self.history: list[list[int]] = []   # for undo
        self.snapshots_seen: list[bytes] = []
        self.accepted: list[dict] = []
        self.last_frame: int = -1

    def wait_for_new_snapshot(self, timeout: float = 10.0) -> bytes | None:
        deadline = time.time() + timeout
        while time.time() < deadline:
            result = read_snapshot(self.snapshot_path)
            if result is not None:
                frame, ram = result
                if frame != self.last_frame:
                    self.last_frame = frame
                    return ram
            time.sleep(0.05)
        return None

    def take_baseline(self) -> bool:
        print("  Waiting for RAM snapshot from MAME...", end=" ", flush=True)
        ram = self.wait_for_new_snapshot()
        if ram is None:
            print("TIMEOUT — is MAME running with address_search.lua?")
            return False
        self.baseline = ram
        self.candidates = list(range(0x10000))
        self.history.clear()
        self.snapshots_seen = [ram]
        print(f"OK  ({len(self.candidates):,} candidates, frame {self.last_frame})")
        return True

    def refresh_snapshot(self) -> bytes | None:
        ram = self.wait_for_new_snapshot(timeout=5.0)
        if ram is not None:
            self.snapshots_seen.append(ram)
        return ram

    def do_filter(self, op: str, value: Optional[int] = None) -> int:
        ram = self.refresh_snapshot()
        if ram is None:
            print("  No new snapshot — MAME may be paused or slow.")
            return len(self.candidates)
        self.history.append(list(self.candidates))
        self.candidates = apply_filter(self.candidates, self.baseline, ram, op, value)  # type: ignore[arg-type]
        self.baseline = ram  # rolling baseline: next filter compares against this frame
        return len(self.candidates)

    def undo(self) -> bool:
        if not self.history:
            return False
        self.candidates = self.history.pop()
        return True

    def show_candidates(self, limit: int = 30) -> None:
        ram = read_snapshot(self.snapshot_path)
        current = ram[1] if ram else self.baseline
        shown = self.candidates[:limit]
        for addr in shown:
            val = current[addr] if current else 0
            print(f"    0x{addr:04X}  current={val:3d} (0x{val:02X})")
        if len(self.candidates) > limit:
            print(f"    ... and {len(self.candidates) - limit} more")

    def accept_candidate(self, addr: int, name: str) -> None:
        encoding = detect_encoding(addr, self.snapshots_seen)
        entry = {"name": name, "address": addr, "type": "u8", "encoding": encoding}
        self.accepted.append(entry)
        print(f"  Accepted: {name} @ 0x{addr:04X}  encoding={encoding}")

    def save(self) -> None:
        self.out_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"variables": self.accepted}
        self.out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"  Saved {len(self.accepted)} variable(s) → {self.out_path}")

    def load(self) -> bool:
        if not self.out_path.exists():
            return False
        try:
            data = json.loads(self.out_path.read_text(encoding="utf-8"))
            self.accepted = data.get("variables", [])
            print(f"  Resumed {len(self.accepted)} accepted variable(s) from {self.out_path}")
            return True
        except Exception:
            return False


# ---------------------------------------------------------------------------
# TUI
# ---------------------------------------------------------------------------

HELP = """
Commands:
  baseline       Take a new baseline snapshot (resets all filters).
  filter !=      Keep addresses where value changed (from last baseline).
  filter <       Keep addresses where value decreased.
  filter >       Keep addresses where value increased.
  filter = N     Keep addresses where current value equals N.
  filter changed   Alias for !=.
  filter unchanged Keep addresses where value did NOT change.
  show [N]       Show up to N candidates (default 30).
  undo           Undo the last filter.
  accept ADDR NAME   Accept address (hex or decimal) and give it a name.
  save           Save accepted candidates to output JSON.
  resume         Load prior session from output JSON.
  help           Show this help.
  quit           Exit.
"""


def parse_addr(token: str) -> int:
    if token.startswith("0x") or token.startswith("0X"):
        return int(token, 16)
    return int(token, 10)


def run_tui(session: SearchSession) -> None:
    print("\n=== GNG RAM Address Search (T30.2 / ADR-028) ===")
    print(f"Snapshot: {session.snapshot_path}")
    print(f"Output:   {session.out_path}")
    print("Type 'help' for commands.\n")

    while True:
        try:
            raw = input(f"[{len(session.candidates):,} candidates]> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            break

        if not raw:
            continue
        parts = raw.split()
        cmd = parts[0].lower()

        if cmd == "help":
            print(HELP)

        elif cmd == "baseline":
            session.take_baseline()

        elif cmd == "filter":
            if len(parts) < 2:
                print("  Usage: filter <op>  (!=, <, >, = N, changed, unchanged)")
                continue
            op = parts[1]
            value = None
            if op == "=" and len(parts) >= 3:
                try:
                    value = int(parts[2])
                except ValueError:
                    print("  filter = N requires an integer N")
                    continue
            if op not in ("!=", "<", ">", "=", "changed", "unchanged"):
                print(f"  Unknown op '{op}'. Use: !=  <  >  = N  changed  unchanged")
                continue
            n = session.do_filter(op, value)
            print(f"  {n:,} candidates remaining.")

        elif cmd == "show":
            limit = 30
            if len(parts) >= 2:
                try:
                    limit = int(parts[1])
                except ValueError:
                    pass
            session.show_candidates(limit)

        elif cmd == "undo":
            if session.undo():
                print(f"  Undone. {len(session.candidates):,} candidates.")
            else:
                print("  Nothing to undo.")

        elif cmd == "accept":
            if len(parts) < 3:
                print("  Usage: accept <addr_hex> <variable_name>")
                continue
            try:
                addr = parse_addr(parts[1])
            except ValueError:
                print(f"  Invalid address: {parts[1]}")
                continue
            name = parts[2]
            if addr not in session.candidates and addr not in range(0x10000):
                print(f"  Address 0x{addr:04X} not in candidate list (use 'show' to see candidates).")
                continue
            session.accept_candidate(addr, name)

        elif cmd == "save":
            session.save()

        elif cmd == "resume":
            session.load()

        elif cmd in ("quit", "exit", "q"):
            break

        else:
            print(f"  Unknown command '{cmd}'. Type 'help'.")

    print("Done.")


# ---------------------------------------------------------------------------
# Launch helper
# ---------------------------------------------------------------------------

def print_launch_instructions(snapshot_path: Path, cmd_path: Path) -> None:
    print("\n--- Launch MAME with address_search.lua ---")
    print("Set these env vars before launching MAME:\n")
    print(f"  export BLACKBOX_ADDR_SNAPSHOT_PATH={snapshot_path}")
    print(f"  export BLACKBOX_ADDR_CMD_PATH={cmd_path}")
    print()
    print("Then launch MAME with:")
    print("  mame gngb -rompath <rom_dir> -autoboot_script scripts/address_search.lua")
    print()
    print("Or use the convenience wrapper:")
    print("  ./scripts/launch_address_search.sh")
    print()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="T30.2 — Guided RAM address-search TUI (ADR-028 / ADR-026)."
    )
    parser.add_argument(
        "--snapshot",
        type=Path,
        default=Path("evidence/private/addr_snapshot.bin"),
        help="Path to the RAM snapshot exchange file (written by Lua, read by this tool).",
    )
    parser.add_argument(
        "--cmd",
        type=Path,
        default=Path("evidence/private/addr_cmd.txt"),
        help="Path to the command exchange file (written by this tool, read by Lua).",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("evidence/private/gng_address_candidates.json"),
        help="Output path for accepted address candidates (private, never committed).",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Load prior accepted candidates from --out before starting.",
    )
    parser.add_argument(
        "--instructions",
        action="store_true",
        help="Print MAME launch instructions and exit.",
    )
    args = parser.parse_args()

    if args.instructions:
        print_launch_instructions(args.snapshot, args.cmd)
        return

    session = SearchSession(args.snapshot, args.cmd, args.out)

    if args.resume:
        session.load()

    # Check if MAME is already producing snapshots.
    result = read_snapshot(args.snapshot)
    if result is None:
        print("\nNo RAM snapshot found yet.")
        print_launch_instructions(args.snapshot, args.cmd)
        print("Once MAME is running, type 'baseline' to take the first snapshot.\n")
    else:
        frame, _ = result
        print(f"\nMAME snapshot detected (frame {frame}). Type 'baseline' to start.\n")

    run_tui(session)


if __name__ == "__main__":
    main()
