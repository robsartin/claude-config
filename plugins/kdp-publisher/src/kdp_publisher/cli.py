import argparse

from kdp_publisher import kdp_rules
from kdp_publisher.ingest.docx_ingest import ingest_docx
from kdp_publisher.ingest.frontmatter import parse_frontmatter
from kdp_publisher.interior.pipeline import produce_interior
from kdp_publisher.model import BookModel

# Maps front-matter/override field names to the CLI flag that sets them.
_FLAG_FOR_FIELD = {
    "title": "--title",
    "author": "--author",
    "trim": "--trim",
    "paper_type": "--paper",
}


def _normalize_overrides(args: argparse.Namespace) -> dict[str, str] | int:
    """Routes --trim/--paper/--title/--author through parse_frontmatter's own
    normalization/validation (case-folding, paper aliases, trim whitelist)
    instead of duplicating it here.

    Returns the normalized overrides dict, or an int exit code if --trim or
    --paper failed validation.
    """
    override_lines = []
    if args.title:
        override_lines.append(f"Title: {args.title}")
    if args.author:
        override_lines.append(f"Author: {args.author}")
    if args.trim:
        override_lines.append(f"Trim: {args.trim}")
    if args.paper:
        override_lines.append(f"Paper: {args.paper}")
    overrides, _ = parse_frontmatter(override_lines)

    if args.trim and "trim" not in overrides:
        valid = ", ".join(sorted(kdp_rules.TRIMS_IN))
        print(f"error: invalid --trim {args.trim!r}; valid trims: {valid}")
        return 2
    if args.paper and "paper_type" not in overrides:
        print(f"error: invalid --paper {args.paper!r}; valid papers: cream, white, color, premium")
        return 2
    return overrides


def _ingest_or_error(args: argparse.Namespace) -> BookModel | int:
    """Normalizes overrides and ingests the docx, reporting a missing-metadata
    error the same way for every subcommand.

    Returns the ingested book on success, or an int exit code if overrides
    failed validation or required metadata is still missing after overrides.
    """
    overrides = _normalize_overrides(args)
    if isinstance(overrides, int):
        return overrides

    book, missing = ingest_docx(args.docx_path, overrides=overrides or None)
    if missing:
        flags = "/".join(_FLAG_FOR_FIELD[m] for m in missing)
        print(
            f"error: missing required metadata: {', '.join(missing)} "
            f"(add to the front-matter page or pass {flags})"
        )
        return 2

    return book


def _run_interior(args: argparse.Namespace) -> int:
    book = _ingest_or_error(args)
    if isinstance(book, int):
        return book

    google = None
    if args.google_pdf:
        with open(args.google_pdf, "rb") as f:
            google = f.read()
    result = produce_interior(book, google)
    if result.page_count < kdp_rules.MIN_PAGES:
        print(
            f"error: rendered interior has {result.page_count} pages; "
            f"KDP requires a minimum of {kdp_rules.MIN_PAGES} pages. "
            f"add more content to the manuscript and try again."
        )
        return 2
    with open(args.out, "wb") as f:
        f.write(result.pdf)
    print(f"interior: {result.page_count} pages, source={result.source} -> {args.out}")
    if result.report:
        for c in result.report.checks:
            print(f"  [{c.status}] {c.name}: {c.message}")
    return 0


def _run_cover(args: argparse.Namespace) -> int:
    from kdp_publisher.cover.prompt import build_cover_prompt
    from kdp_publisher.cover.render import render_cover
    from kdp_publisher.cover.spec import compute_cover_spec

    book = _ingest_or_error(args)
    if isinstance(book, int):
        return book

    google = None
    if args.google_pdf:
        with open(args.google_pdf, "rb") as f:
            google = f.read()
    result = produce_interior(book, google)
    if result.page_count < kdp_rules.MIN_PAGES:
        print(
            f"error: interior is {result.page_count} pages; KDP needs "
            f"{kdp_rules.MIN_PAGES}+ before a cover can be built. Add more content."
        )
        return 2

    spec = compute_cover_spec(book.metadata.trim, result.page_count, book.metadata.paper_type)
    if args.cover_image:
        with open(args.cover_image, "rb") as f:
            img = f.read()
        pdf = render_cover(spec, img, book.metadata.title, book.metadata.author, args.blurb)
        with open(args.out, "wb") as f:
            f.write(pdf)
        print(
            f"cover: {spec.width_in:.3f}x{spec.height_in:.3f} in, "
            f"{result.page_count} pages, spine {spec.spine_in:.3f} in -> {args.out}"
        )
        print(
            "note: front text comes from your supplied image; the spine "
            "shows the title only at >=79 pages."
        )
    else:
        sheet = (
            f"KDP wraparound cover spec — {book.metadata.title}\n"
            f"Trim {spec.trim}, {result.page_count} pages, paper {spec.paper_type}\n"
            f"Canvas: {spec.width_in:.3f} x {spec.height_in:.3f} in "
            f"= {spec.width_px} x {spec.height_px} px at {spec.dpi} DPI\n"
            f"Spine: {spec.spine_in:.3f} in ({spec.spine_px} px), "
            f"spine text {'allowed' if spec.allow_spine_text else 'NOT allowed (<79pp)'}\n"
            f"Bleed {kdp_rules.BLEED_IN} in; barcode keep-out "
            f"{kdp_rules.BARCODE_W_IN}x{kdp_rules.BARCODE_H_IN} in (back bottom-right)\n\n"
            f"--- AI cover-art prompt ---\n{build_cover_prompt(book.metadata, spec)}\n"
        )
        with open(args.out, "w") as f:
            f.write(sheet)
        print(f"cover-spec + prompt (no --cover-image given) -> {args.out}")
    return 0


def _run_epub(args: argparse.Namespace) -> int:
    from kdp_publisher.epub.build import build_epub

    book_or_code = _ingest_or_error(args)
    if isinstance(book_or_code, int):
        return book_or_code
    book = book_or_code

    cover = None
    if args.cover_image:
        with open(args.cover_image, "rb") as f:
            cover = f.read()
    data = build_epub(book, cover)
    with open(args.out, "wb") as f:
        f.write(data)
    chapters = len(book.chapters)
    print(
        f"epub: '{book.metadata.title}', {chapters} chapters"
        f"{' + cover' if cover else ''} -> {args.out}"
    )
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="kdp_publisher")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("interior")
    p.add_argument("docx_path")
    p.add_argument("--google-pdf", default=None)
    p.add_argument("--trim")
    p.add_argument("--paper")
    p.add_argument("--author")
    p.add_argument("--title")
    p.add_argument("-o", "--out", required=True)

    pc = sub.add_parser("cover")
    pc.add_argument("docx_path")
    pc.add_argument("--google-pdf", default=None)
    pc.add_argument("--cover-image", default=None)
    pc.add_argument("--blurb", default="")
    pc.add_argument("--trim")
    pc.add_argument("--paper")
    pc.add_argument("--author")
    pc.add_argument("--title")
    pc.add_argument("-o", "--out", required=True)

    pe = sub.add_parser("epub")
    pe.add_argument("docx_path")
    pe.add_argument("--cover-image", default=None)
    pe.add_argument("--trim")
    pe.add_argument("--paper")
    pe.add_argument("--author")
    pe.add_argument("--title")
    pe.add_argument("-o", "--out", required=True)

    args = parser.parse_args(argv)

    if args.cmd == "cover":
        return _run_cover(args)
    if args.cmd == "epub":
        return _run_epub(args)
    return _run_interior(args)


def console_main() -> int:
    import sys

    return main(sys.argv[1:])
