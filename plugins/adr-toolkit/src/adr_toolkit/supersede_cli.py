"""Command-line entry point for the ADR supersede workflow."""

import argparse
import datetime
import sys

from adr_toolkit.supersede import SupersedeError, supersede


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="adr-supersede")
    parser.add_argument("--target", required=True, help="target repo docs/adr directory")
    parser.add_argument("--old", required=True, help="old ADR number (NNNN) or topic slug")
    parser.add_argument("--title", required=True, help="title of the new, superseding decision")
    parser.add_argument("--date", default=datetime.date.today().isoformat())
    args = parser.parse_args(argv)

    try:
        new_path, old_path = supersede(args.target, args.old, args.title, args.date)
    except SupersedeError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    print(f"superseded {old_path.name} -> {new_path.name}")
    print(f"wrote {new_path}")
    print(f"index {new_path.parent / 'README.md'}")
    return 0
