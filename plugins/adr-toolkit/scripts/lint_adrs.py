"""CLI gate: run the ADR content linter against packs/ and report violations."""

import argparse
import sys
from pathlib import Path

from adr_toolkit.lint import lint_packs
from adr_toolkit.manifest import load_manifest

REPO = Path(__file__).resolve().parents[1]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="lint_adrs")
    parser.add_argument("--manifest", default=REPO / "packs.yaml", type=Path)
    parser.add_argument("--packs-dir", default=REPO / "packs", type=Path)
    args = parser.parse_args(argv)

    manifest = load_manifest(args.manifest)
    violations = lint_packs(args.packs_dir, manifest)

    for violation in violations:
        print(violation, file=sys.stderr)
    if violations:
        return 1
    print(f"ADR lint passed ({args.packs_dir})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
