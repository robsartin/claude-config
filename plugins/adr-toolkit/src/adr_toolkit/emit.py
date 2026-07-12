"""Emit resolved ADR templates into a target repo's ``docs/adr/`` directory."""

from collections.abc import Iterable, Mapping
from pathlib import Path

from adr_toolkit.numbering import existing_adr_names, next_number
from adr_toolkit.planning import plan_emission
from adr_toolkit.templating import substitute
from adr_toolkit.types import Manifest, StrPath


def emit(
    packs_dir: StrPath,
    manifest: Manifest,
    pack_ids: Iterable[str],
    context: Mapping[str, object],
    target_dir: StrPath,
    exclude: Iterable[str] = (),
) -> list[Path]:
    """Render each selected pack's ADR templates into *target_dir*.

    ADRs are numbered sequentially starting one past the highest number already
    present. Topics in *exclude* are skipped. Returns the written paths, in order.

    The plan is built before the target directory is created, so a bad *exclude*
    fails without leaving anything behind.
    """
    target = Path(target_dir)

    start = next_number(existing_adr_names(target))
    planned = plan_emission(packs_dir, manifest, pack_ids, start, exclude)

    target.mkdir(parents=True, exist_ok=True)

    written: list[Path] = []
    for adr in planned:
        rendered = substitute(adr.template.read_text(), {**context, "number": adr.number})
        out_path = target / adr.filename
        out_path.write_text(rendered)
        written.append(out_path)
    return written
