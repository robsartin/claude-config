"""Allocate ADR numbers into a target repo's existing sequence."""

from collections.abc import Iterable
from pathlib import Path

from adr_toolkit.types import StrPath


def existing_adr_names(target_dir: StrPath) -> list[str]:
    """Filenames already in *target_dir*; empty if it does not exist yet."""
    directory = Path(target_dir)
    if not directory.is_dir():
        return []
    return [p.name for p in directory.iterdir()]


def next_number(existing_filenames: Iterable[str]) -> int:
    """Return the next ADR number, one past the highest existing NNNN prefix."""
    highest = 0
    for name in existing_filenames:
        prefix = name.split("-", 1)[0]
        if prefix.isdigit():
            highest = max(highest, int(prefix))
    return highest + 1
