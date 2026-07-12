"""Load the ``packs.yaml`` manifest describing packs, deps, and interactions."""

from pathlib import Path
from typing import cast

import yaml

from adr_toolkit.types import Manifest, StrPath


def load_manifest(path: StrPath) -> Manifest:
    """Parse the manifest YAML file at *path* into a Manifest."""
    return cast(Manifest, yaml.safe_load(Path(path).read_text()))
