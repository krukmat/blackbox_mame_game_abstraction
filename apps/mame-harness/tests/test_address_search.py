"""T30.2 / ADR-028 — Regression tests for the guided RAM address-search TUI.

Covers the pure logic (filter engine, snapshot reader, BCD detection) and the
clean-room contract: the saved candidates JSON must carry no private machine paths
(ensure_no_private_paths), and the committed scripts must contain no real addresses.
"""
from __future__ import annotations

import json
import struct
from pathlib import Path

import pytest

import address_search as a
from guardrails import ensure_no_private_paths


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ram(overrides: dict[int, int]) -> bytes:
    buf = bytearray(0x10000)
    for addr, val in overrides.items():
        buf[addr] = val
    return bytes(buf)


def _write_snapshot(path: Path, frame: int, ram: bytes) -> None:
    path.write_bytes(struct.pack("<I", frame) + ram)


# ---------------------------------------------------------------------------
# Filter engine
# ---------------------------------------------------------------------------

class TestApplyFilter:
    def setup_method(self) -> None:
        self.cands = list(range(0x10000))
        self.base = _ram({0x100: 50, 0x200: 80, 0x300: 42})
        self.curr = _ram({0x100: 60, 0x200: 70, 0x300: 42})  # up, down, same

    def test_increased(self) -> None:
        assert a.apply_filter(self.cands, self.base, self.curr, ">", None) == [0x100]

    def test_decreased(self) -> None:
        assert a.apply_filter(self.cands, self.base, self.curr, "<", None) == [0x200]

    def test_changed(self) -> None:
        assert set(a.apply_filter(self.cands, self.base, self.curr, "!=", None)) == {0x100, 0x200}

    def test_changed_alias(self) -> None:
        ne = a.apply_filter(self.cands, self.base, self.curr, "!=", None)
        changed = a.apply_filter(self.cands, self.base, self.curr, "changed", None)
        assert ne == changed

    def test_unchanged_keeps_equal_addresses(self) -> None:
        result = a.apply_filter(self.cands, self.base, self.curr, "unchanged", None)
        assert 0x300 in result
        assert 0x100 not in result and 0x200 not in result

    def test_equals_matches_current_value(self) -> None:
        assert a.apply_filter(self.cands, self.base, self.curr, "=", 60) == [0x100]
        assert a.apply_filter(self.cands, self.base, self.curr, "=", 70) == [0x200]

    def test_equals_without_value_keeps_nothing(self) -> None:
        # op '=' with value None falls through to no-match (handled by caller, but
        # apply_filter must not raise).
        assert a.apply_filter([0x100], self.base, self.curr, "=", None) == []

    def test_filter_narrows_only_within_candidate_set(self) -> None:
        # An address not in the candidate set is never reintroduced by a filter.
        result = a.apply_filter([0x200], self.base, self.curr, "!=", None)
        assert result == [0x200]
        assert 0x100 not in result


# ---------------------------------------------------------------------------
# Snapshot reader
# ---------------------------------------------------------------------------

class TestReadSnapshot:
    def test_roundtrip(self, tmp_path: Path) -> None:
        ram = _ram({0x1A: 0x7F, 0xFFFF: 0x01})
        p = tmp_path / "snap.bin"
        _write_snapshot(p, 4321, ram)
        result = a.read_snapshot(p)
        assert result is not None
        frame, got = result
        assert frame == 4321
        assert got[0x1A] == 0x7F
        assert got[0xFFFF] == 0x01

    def test_missing_file_returns_none(self, tmp_path: Path) -> None:
        assert a.read_snapshot(tmp_path / "absent.bin") is None

    def test_too_short_header_returns_none(self, tmp_path: Path) -> None:
        p = tmp_path / "short.bin"
        p.write_bytes(b"\x00\x00")  # < 4 bytes
        assert a.read_snapshot(p) is None

    def test_truncated_ram_returns_none(self, tmp_path: Path) -> None:
        p = tmp_path / "trunc.bin"
        p.write_bytes(struct.pack("<I", 1) + b"\x00" * 0x100)  # ram < 0x10000
        assert a.read_snapshot(p) is None


# ---------------------------------------------------------------------------
# BCD detection
# ---------------------------------------------------------------------------

class TestDetectEncoding:
    def test_all_bcd_values_detected_as_bcd8(self) -> None:
        snaps = [bytes([0x12]), bytes([0x34]), bytes([0x09])]
        assert a.detect_encoding(0, snaps) == "bcd8"

    def test_any_non_bcd_value_is_u8(self) -> None:
        snaps = [bytes([0x12]), bytes([0xAB])]  # 0xAB has nibbles > 9
        assert a.detect_encoding(0, snaps) == "u8"

    def test_single_sample_defaults_to_u8(self) -> None:
        assert a.detect_encoding(0, [bytes([0x12])]) == "u8"


# ---------------------------------------------------------------------------
# Session: baseline / filter / undo over fake snapshot files
# ---------------------------------------------------------------------------

class TestSearchSession:
    def _session(self, tmp_path: Path) -> a.SearchSession:
        return a.SearchSession(
            snapshot_path=tmp_path / "snap.bin",
            cmd_path=tmp_path / "cmd.txt",
            out_path=tmp_path / "out.json",
        )

    def test_baseline_then_filter_narrows(self, tmp_path: Path) -> None:
        sess = self._session(tmp_path)
        _write_snapshot(sess.snapshot_path, 1, _ram({0x100: 10, 0x200: 20}))
        assert sess.take_baseline() is True
        assert len(sess.candidates) == 0x10000
        # New snapshot: only 0x100 changes.
        _write_snapshot(sess.snapshot_path, 2, _ram({0x100: 11, 0x200: 20}))
        remaining = sess.do_filter("!=", None)
        assert remaining == 1
        assert sess.candidates == [0x100]

    def test_undo_restores_previous_candidates(self, tmp_path: Path) -> None:
        sess = self._session(tmp_path)
        _write_snapshot(sess.snapshot_path, 1, _ram({0x100: 10}))
        sess.take_baseline()
        _write_snapshot(sess.snapshot_path, 2, _ram({0x100: 11}))
        sess.do_filter("!=", None)
        assert sess.candidates == [0x100]
        assert sess.undo() is True
        assert len(sess.candidates) == 0x10000

    def test_undo_with_no_history_returns_false(self, tmp_path: Path) -> None:
        sess = self._session(tmp_path)
        assert sess.undo() is False


# ---------------------------------------------------------------------------
# Clean-room contract (ADR-026 / ADR-003 / ADR-028)
# ---------------------------------------------------------------------------

class TestCleanRoomContract:
    def test_saved_candidates_carry_no_private_paths(self, tmp_path: Path) -> None:
        """The saved candidates JSON must hold only abstract fields (name/address/
        type/encoding) — never a machine path. ensure_no_private_paths must pass."""
        sess = a.SearchSession(
            snapshot_path=tmp_path / "snap.bin",
            cmd_path=tmp_path / "cmd.txt",
            out_path=tmp_path / "candidates.json",
        )
        _write_snapshot(sess.snapshot_path, 1, _ram({0x40: 0x12}))
        sess.take_baseline()
        sess.accept_candidate(0x40, "player_x")
        sess.save()

        payload = json.loads(sess.out_path.read_text(encoding="utf-8"))
        # The guardrail walks all string values; must not raise.
        ensure_no_private_paths(payload)
        assert payload["variables"][0]["name"] == "player_x"
        assert "snapshot" not in json.dumps(payload)
        assert str(tmp_path) not in json.dumps(payload)

    def test_committed_lua_contains_no_real_addresses(self) -> None:
        """address_search.lua must not embed real RAM addresses — only the size
        constant 0x10000 and the dump interval are allowed numeric literals."""
        lua = Path("scripts/address_search.lua").read_text(encoding="utf-8")
        # The only hex literal permitted is the RAM size bound.
        import re

        hex_literals = set(re.findall(r"0x[0-9A-Fa-f]+", lua))
        assert hex_literals <= {"0x10000"}, f"unexpected addresses in Lua: {hex_literals}"

    def test_committed_python_contains_no_real_addresses(self) -> None:
        """address_search.py must not embed real discovered addresses. Only the
        RAM bound 0x10000 / 0xFFFF-style bookkeeping is allowed; discovered
        addresses live in the private JSON, never in source."""
        py = Path("apps/mame-harness/address_search.py").read_text(encoding="utf-8")
        import re

        hex_literals = set(re.findall(r"0x[0-9A-Fa-f]+", py))
        # 0x10000 = RAM size, 0x0F/0x04/0x02 etc. are BCD nibble masks / format specifiers.
        allowed = {"0x10000", "0x0F", "0x04X", "0x02X", "0X"}
        leftover = {h for h in hex_literals if h not in allowed}
        assert not leftover, f"unexpected addresses in Python: {leftover}"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
