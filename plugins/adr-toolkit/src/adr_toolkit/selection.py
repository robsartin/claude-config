"""Resolve a user's pack selection into the full set of packs to emit."""

from collections.abc import Iterable

from adr_toolkit.types import Manifest

AXIS_ORDER = [
    "universal",
    "language",
    "framework",
    "app-shape",
    "ui-tech",
    "library",
    "concern",
    "interaction",
]


class UnknownPackError(ValueError):
    """A selected pack id is not defined in the manifest.

    Fails loudly with the unknown ids rather than crashing on a raw KeyError.
    """

    def __init__(self, unknown: list[str]) -> None:
        self.unknown = unknown
        super().__init__(f"no such pack in the manifest: {', '.join(unknown)}")


def order_packs(manifest: Manifest, pack_ids: Iterable[str]) -> list[str]:
    """Order pack ids deterministically by axis, then dependencies-before-dependents.

    The key is ``(axis index, dependency depth, id)``: axis groups the sequence,
    depth guarantees a pack's ``depends_on`` targets sort ahead of it within an
    axis, and id breaks remaining ties so emission is reproducible.
    """
    packs = manifest["packs"]
    depth_cache: dict[str, int] = {}

    def depth(pack_id: str) -> int:
        if pack_id not in depth_cache:
            deps = packs[pack_id].get("depends_on", [])
            depth_cache[pack_id] = 1 + max((depth(d) for d in deps), default=-1)
        return depth_cache[pack_id]

    return sorted(
        pack_ids,
        key=lambda pid: (AXIS_ORDER.index(packs[pid]["axis"]), depth(pid), pid),
    )


def resolve_selection(manifest: Manifest, selected: Iterable[str]) -> list[str]:
    """Expand selected pack ids to include their declared dependencies.

    Raises UnknownPackError if a selected id is not in the manifest, so a typo
    fails with a clear message instead of a raw KeyError.
    """
    packs = manifest["packs"]
    selected = list(selected)
    unknown = sorted({pid for pid in selected if pid not in packs})
    if unknown:
        raise UnknownPackError(unknown)
    result: set[str] = set()
    worklist = list(selected)
    while worklist:
        pack_id = worklist.pop()
        if pack_id in result:
            continue
        result.add(pack_id)
        worklist.extend(packs[pack_id].get("depends_on", []))
    return list(result)


def resolve_interactions(manifest: Manifest, selected: Iterable[str]) -> list[str]:
    """Return interaction ADR ids whose endpoint packs are all selected."""
    selected_set = set(selected)
    return [
        interaction["adr"]
        for interaction in manifest.get("interactions", [])
        if set(interaction["when"]) <= selected_set
    ]


def resolve_all(manifest: Manifest, selected: Iterable[str]) -> list[str]:
    """Expand *selected* by dependencies, add triggered interactions, and order."""
    packs = resolve_selection(manifest, selected)
    interactions = resolve_interactions(manifest, packs)
    return order_packs(manifest, packs + interactions)
