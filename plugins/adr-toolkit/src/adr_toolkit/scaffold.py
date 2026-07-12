"""Top-level orchestration: resolve a selection and emit ADRs + index."""

from collections.abc import Iterable, Mapping
from pathlib import Path

from adr_toolkit.emit import emit
from adr_toolkit.index import build_index
from adr_toolkit.selection import resolve_all
from adr_toolkit.types import Manifest, StrPath


def scaffold(
    packs_dir: StrPath,
    manifest: Manifest,
    selected: Iterable[str],
    context: Mapping[str, object],
    target_dir: StrPath,
    exclude: Iterable[str] = (),
) -> tuple[list[Path], Path]:
    """Resolve *selected* packs (deps + interactions), emit ADRs, build index.

    Topics in *exclude* are not emitted. Returns ``(written_paths, index_path)``.
    """
    ordered = resolve_all(manifest, selected)
    written = emit(packs_dir, manifest, ordered, context, target_dir, exclude)
    index_path = build_index(target_dir)
    return written, index_path
