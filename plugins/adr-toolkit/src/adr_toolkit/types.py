"""Typed shapes for the manifest that the engine reads."""

import os
from typing import NotRequired, TypedDict

# Paths are accepted as either strings (from the CLI) or Path objects (from callers).
StrPath = str | os.PathLike[str]


class PackSpec(TypedDict):
    """One pack's manifest entry."""

    axis: str
    path: str
    depends_on: NotRequired[list[str]]


class Interaction(TypedDict):
    """A pairwise interaction: emit ``adr`` when all ``when`` packs are selected."""

    when: list[str]
    adr: str


class Manifest(TypedDict):
    """The parsed ``packs.yaml``."""

    packs: dict[str, PackSpec]
    interactions: NotRequired[list[Interaction]]
