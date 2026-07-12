"""Compute which ADRs would be emitted, before writing anything."""

import re
from collections.abc import Iterable
from pathlib import Path
from typing import NamedTuple

from adr_toolkit.types import Manifest, StrPath

_ORDER_PREFIX = re.compile(r"^\d+-")


class PlannedAdr(NamedTuple):
    """One ADR the toolkit would emit, before any file is written."""

    number: int
    topic: str
    pack_id: str
    template: Path
    filename: str


class UnknownTopicError(ValueError):
    """An excluded topic matches no ADR in the selected packs.

    Silently ignoring it would emit an ADR the caller meant to skip — exactly the
    duplication reconciliation exists to prevent — so this fails loudly instead.
    """

    def __init__(self, unknown: list[str]) -> None:
        self.unknown = unknown
        super().__init__(f"no such ADR topic in the selected packs: {', '.join(unknown)}")


def topic_of(template: Path) -> str:
    """Stable handle for an ADR: its slug, independent of the emitted number."""
    return _ORDER_PREFIX.sub("", template.stem)


def plan_emission(
    packs_dir: StrPath,
    manifest: Manifest,
    pack_ids: Iterable[str],
    start_number: int,
    exclude: Iterable[str] = (),
) -> list[PlannedAdr]:
    """Number the ADRs each selected pack would emit, skipping excluded topics.

    Excluded topics consume no number, so the emitted sequence stays contiguous.
    Raises UnknownTopicError if any excluded topic matches nothing; the check runs
    before any numbering, so callers never see a partial plan.
    """
    packs_root = Path(packs_dir)
    excluded = set(exclude)

    candidates: list[tuple[str, Path, str]] = []
    for pack_id in pack_ids:
        pack_path = packs_root / manifest["packs"][pack_id]["path"]
        for template in sorted(pack_path.glob("*.md")):
            candidates.append((pack_id, template, topic_of(template)))

    unknown = sorted(excluded - {topic for _, _, topic in candidates})
    if unknown:
        raise UnknownTopicError(unknown)

    number = start_number
    planned: list[PlannedAdr] = []
    for pack_id, template, topic in candidates:
        if topic in excluded:
            continue
        planned.append(
            PlannedAdr(
                number=number,
                topic=topic,
                pack_id=pack_id,
                template=template,
                filename=f"{number:04d}-{topic}.md",
            )
        )
        number += 1
    return planned
