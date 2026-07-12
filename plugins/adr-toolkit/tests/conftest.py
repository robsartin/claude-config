"""Shared typed helpers for the test suite."""

from pathlib import Path

from adr_toolkit.manifest import load_manifest
from adr_toolkit.scaffold import scaffold
from adr_toolkit.types import Interaction, Manifest, PackSpec

REPO = Path(__file__).resolve().parents[1]
CONTEXT = {"project": "demo", "package": "com.robsartin.demo", "date": "2026-07-07"}


def make_pack(axis: str, *, path: str = "unused", depends_on: list[str] | None = None) -> PackSpec:
    """Build a complete PackSpec. `path` defaults for tests that never emit."""
    pack: PackSpec = {"axis": axis, "path": path}
    if depends_on is not None:
        pack["depends_on"] = depends_on
    return pack


def make_manifest(
    packs: dict[str, PackSpec],
    interactions: list[Interaction] | None = None,
) -> Manifest:
    """Build a Manifest from packs and optional interactions."""
    manifest: Manifest = {"packs": packs}
    if interactions is not None:
        manifest["interactions"] = interactions
    return manifest


def emit_real(tmp_path: Path, selected: list[str]) -> list[Path]:
    """Scaffold the repo's real packs for *selected* into a fresh target dir."""
    target = tmp_path / "docs" / "adr"
    target.mkdir(parents=True)
    manifest = load_manifest(REPO / "packs.yaml")
    written, _ = scaffold(REPO / "packs", manifest, selected, CONTEXT, target)
    return written


def slugs(paths: list[Path]) -> list[str]:
    """ADR slugs (filename minus the NNNN- prefix) for the given paths."""
    return [p.stem[5:] for p in paths]


def emit_slugs(tmp_path: Path, selected: list[str]) -> list[str]:
    """emit_real, but return ADR slugs (filename minus the NNNN- prefix)."""
    return slugs(emit_real(tmp_path, selected))
