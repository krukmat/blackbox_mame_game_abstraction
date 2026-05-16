from __future__ import annotations

import argparse
import json
from pathlib import Path

from cli import build_parser, handle_doctor


def test_doctor_subcommand_parses() -> None:
    parser = build_parser()

    args = parser.parse_args(["doctor"])

    assert args.command == "doctor"
    assert args.config == Path("blackbox.local.yaml")
    assert args.env_file == Path(".env")


def test_doctor_succeeds_with_yaml_config_and_env_override(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    rom_dir = tmp_path / "private_roms"
    rom_dir.mkdir()
    (rom_dir / "gng.zip").write_text("placeholder", encoding="utf-8")
    fake_mame = _write_fake_executable(tmp_path, "fake-mame", "0.287 (mame0287)\n")
    fake_ffmpeg = _write_fake_executable(tmp_path, "fake-ffmpeg", "ffmpeg version n7.0\n")
    config_path = tmp_path / "blackbox.local.yaml"
    config_path.write_text(
        "\n".join(
            [
                "source_profile: gng",
                "mame_driver: gngb",
                f"mame_binary: {fake_mame}",
                "ffmpeg_binary: ffmpeg-from-config",
                f"rom_path: {rom_dir}",
                "evidence_root: evidence/private",
                "trace_output: specs/traces/gng_trace.json",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("BLACKBOX_FFMPEG_BINARY", str(fake_ffmpeg))

    result = handle_doctor(_make_doctor_args(config=config_path))

    assert result["status"] == "ok"
    assert result["config_sources"]["config_file"] == "blackbox.local.yaml"
    assert result["config_sources"]["env_overrides"] == ["BLACKBOX_FFMPEG_BINARY"]
    check_names = {check["name"] for check in result["checks"]}
    assert "mame_binary" in check_names
    assert "ffmpeg_binary" in check_names
    assert "source_profile_preflight" in check_names
    assert result["issues"] == []


def test_doctor_rejects_absolute_public_trace_output(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    config_path = _write_valid_doctor_config(tmp_path)

    result = handle_doctor(
        _make_doctor_args(
            config=config_path,
            trace_output=Path("/tmp/leaky_trace.json"),
        )
    )

    assert result["status"] == "issues_found"
    assert any(issue["code"] == "trace_output_absolute_path" for issue in result["issues"])
    assert "/tmp/leaky_trace.json" not in json.dumps(result)


def test_doctor_rejects_evidence_root_outside_private_boundary(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    config_path = _write_valid_doctor_config(tmp_path)

    result = handle_doctor(
        _make_doctor_args(
            config=config_path,
            evidence_root=Path("captures"),
        )
    )

    assert result["status"] == "issues_found"
    assert any(issue["code"] == "private_evidence_root_invalid" for issue in result["issues"])


def _make_doctor_args(**overrides) -> argparse.Namespace:
    defaults = dict(
        config=Path("blackbox.local.yaml"),
        env_file=Path(".env"),
        source_profile=None,
        mame_driver=None,
        mame_binary=None,
        ffmpeg_binary=None,
        rom_path=None,
        evidence_root=None,
        trace_output=None,
    )
    defaults.update(overrides)
    return argparse.Namespace(**defaults)


def _write_valid_doctor_config(tmp_path: Path) -> Path:
    rom_dir = tmp_path / "private_roms"
    rom_dir.mkdir()
    (rom_dir / "gng.zip").write_text("placeholder", encoding="utf-8")
    fake_mame = _write_fake_executable(tmp_path, "fake-mame", "0.287 (mame0287)\n")
    fake_ffmpeg = _write_fake_executable(tmp_path, "fake-ffmpeg", "ffmpeg version n7.0\n")
    config_path = tmp_path / "blackbox.local.yaml"
    config_path.write_text(
        "\n".join(
            [
                "source_profile: gng",
                "mame_driver: gngb",
                f"mame_binary: {fake_mame}",
                f"ffmpeg_binary: {fake_ffmpeg}",
                f"rom_path: {rom_dir}",
                "evidence_root: evidence/private",
                "trace_output: specs/traces/gng_trace.json",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return config_path


def _write_fake_executable(tmp_path: Path, name: str, stdout: str) -> Path:
    path = tmp_path / name
    path.write_text(f"#!/bin/sh\necho '{stdout.strip()}'\n", encoding="utf-8")
    path.chmod(0o755)
    return path
