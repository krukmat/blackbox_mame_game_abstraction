from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class SourceProfile:
    profile_id: str
    display_name: str
    mame_driver: str
    expected_rom_zip: str
    rom_path_kind: str
    rom_path_example: Path
    base_input_plan: Path
    default_frames_to_run: int
    autoboot_script: Path
    private_usage_only: bool
    public_output_boundary: str
    notes: tuple[str, ...]


GNG_SOURCE_PROFILE = SourceProfile(
    profile_id="gng",
    display_name="Ghosts'n Goblins local observation source",
    mame_driver="gngb",
    expected_rom_zip="gng.zip",
    rom_path_kind="directory_containing_rom_zip",
    rom_path_example=Path("local/roms"),
    base_input_plan=Path("plans/basic_controls.yaml"),
    default_frames_to_run=300,
    autoboot_script=Path("scripts/mame_autoboot.lua"),
    private_usage_only=True,
    public_output_boundary=(
        "Use this profile only to drive private observation and redacted metadata generation. "
        "It does not define or promise faithful gameplay reproduction."
    ),
    notes=(
        "The local gng.zip matches MAME driver gngb, not the parent gng driver.",
        "Pass a private rom directory that contains gng.zip; do not publish ROM paths in public outputs.",
        "Base capture settings are for bounded clean-room observation, not clone fidelity.",
    ),
)


SOURCE_PROFILES: dict[str, SourceProfile] = {
    GNG_SOURCE_PROFILE.profile_id: GNG_SOURCE_PROFILE,
}


def get_source_profile(profile_id: str) -> SourceProfile:
    try:
        return SOURCE_PROFILES[profile_id]
    except KeyError as exc:
        available = ", ".join(sorted(SOURCE_PROFILES))
        raise ValueError(f"Unknown source profile '{profile_id}'. Available profiles: {available}") from exc
