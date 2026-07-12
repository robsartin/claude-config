"""Command-line entry point the skill calls once a selection is resolved."""

import argparse
import datetime
import sys

from adr_toolkit.manifest import load_manifest
from adr_toolkit.numbering import existing_adr_names, next_number
from adr_toolkit.planning import UnknownTopicError, plan_emission
from adr_toolkit.scaffold import scaffold
from adr_toolkit.selection import UnknownPackError, resolve_all


def _build_context(project: str, date: str) -> dict[str, str]:
    return {
        "project": project,
        "package": f"com.robsartin.{project}",
        "date": date,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="adr-toolkit")
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--packs-dir", required=True)
    parser.add_argument("--target", required=True, help="target repo docs/adr directory")
    parser.add_argument("--project", required=True)
    parser.add_argument("--date", default=datetime.date.today().isoformat())
    parser.add_argument("--pack", action="append", dest="packs", required=True, help="repeatable")
    parser.add_argument(
        "--exclude",
        action="append",
        dest="exclude",
        default=[],
        metavar="TOPIC",
        help="ADR topic to skip, e.g. use-test-driven-development (repeatable)",
    )
    parser.add_argument(
        "--plan",
        action="store_true",
        help="print the ADRs that would be emitted, then exit without writing",
    )
    args = parser.parse_args(argv)

    manifest = load_manifest(args.manifest)

    try:
        if args.plan:
            ordered = resolve_all(manifest, args.packs)
            start = next_number(existing_adr_names(args.target))
            planned = plan_emission(args.packs_dir, manifest, ordered, start, args.exclude)
            for adr in planned:
                print(f"{adr.number:04d}  {adr.topic}  (pack: {adr.pack_id})")
            return 0

        context = _build_context(args.project, args.date)
        written, index = scaffold(
            args.packs_dir, manifest, args.packs, context, args.target, args.exclude
        )
    except (UnknownPackError, UnknownTopicError) as error:
        print(f"error: {error}", file=sys.stderr)
        if isinstance(error, UnknownTopicError):
            print("       run again with --plan to list the available topics", file=sys.stderr)
        return 2

    for path in written:
        print(f"wrote {path}")
    print(f"index {index}")
    return 0
