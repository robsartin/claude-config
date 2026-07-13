import io
import struct
import zlib

import pypdf

from kdp_publisher.interior.render import converge_gutter, render_interior
from kdp_publisher.interior.validate import validate_interior_pdf
from kdp_publisher.model import (
    BookModel,
    Chapter,
    Heading,
    ImageBlock,
    Metadata,
    Paragraph,
)


def _png_chunk(tag, data):
    return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data))


def _tiny_png_bytes(size=12, rgb=(200, 50, 50)):
    """Hand-built minimal 8-bit RGB PNG (stdlib zlib/struct only, no imaging library)."""
    ihdr = struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0)  # 8-bit depth, RGB truecolor
    raw_row = b"\x00" + bytes(rgb) * size  # filter-type-0 byte + solid-color pixels
    raw = raw_row * size
    idat = zlib.compress(raw)
    return (
        b"\x89PNG\r\n\x1a\n"
        + _png_chunk(b"IHDR", ihdr)
        + _png_chunk(b"IDAT", idat)
        + _png_chunk(b"IEND", b"")
    )


def _big_book(paras=600):
    blocks = [Heading(1, "Chapter One")]
    blocks += [Paragraph(f"Body paragraph number {i} with some words.") for i in range(paras)]
    return BookModel(Metadata("T", "A", "6x9", "cream-bw"), [Chapter("Chapter One", blocks)])


def test_converge_gutter_returns_stable_bracket():
    # A fake render: pages depend on gutter (bigger gutter -> more pages).
    def fake_render(gutter):
        return 140 if gutter <= 0.375 else 160  # crosses the 150 bracket

    gutter, pages = converge_gutter(fake_render)
    from kdp_publisher import kdp_rules as r

    assert r.gutter_in(pages) == gutter  # settled consistently


def test_converge_gutter_requires_multiple_iterations():
    # First render (at the starting gutter 0.375) reports 160 pages, whose
    # implied gutter (0.5) differs from 0.375 -- forcing a second render.
    # The second render (at gutter 0.5) again reports 160 pages, whose
    # implied gutter (0.5) matches -- convergence, after 2+ calls.
    call_count = 0

    def fake_render(gutter):
        nonlocal call_count
        call_count += 1
        return 160

    gutter, pages = converge_gutter(fake_render)

    from kdp_publisher import kdp_rules as r

    assert call_count >= 2
    assert gutter == 0.5
    assert pages == 160
    assert r.gutter_in(pages) == gutter


def test_render_produces_6x9_pdf_that_validates():
    pdf, pages = render_interior(_big_book())
    assert pages >= 24
    report = validate_interior_pdf(pdf, "6x9")
    assert report.ok is True
    reader = pypdf.PdfReader(io.BytesIO(pdf))
    box = reader.pages[0].mediabox
    assert abs(float(box.width) / 72 - 6.0) < 0.03


def test_render_interior_breaks_page_before_each_chapter():
    # Three chapters, each with only a heading and a single short paragraph.
    # Without a page-break-before on chapters 2..N, this tiny amount of
    # content would collapse onto a single page. With the page breaks in
    # place, each chapter starts on its own page, so page_count >= 3.
    chapters = [
        Chapter(f"Chapter {n}", [Heading(1, f"Chapter {n}"), Paragraph("A short paragraph.")])
        for n in (1, 2, 3)
    ]
    book = BookModel(Metadata("T", "A", "6x9", "cream-bw"), chapters)

    pdf, pages = render_interior(book)

    assert pages >= 3


def test_render_embeds_image_as_xobject():
    png_bytes = _tiny_png_bytes()
    chapter = Chapter(
        "Chapter One",
        [
            Heading(1, "Chapter One"),
            ImageBlock(data=png_bytes),
            Paragraph("A short paragraph."),
        ],
    )
    book = BookModel(Metadata("T", "A", "6x9", "cream-bw"), [chapter])

    pdf, _ = render_interior(book)

    reader = pypdf.PdfReader(io.BytesIO(pdf))
    found_image = False
    for page in reader.pages:
        xobjs = (page.get("/Resources", {}) or {}).get("/XObject", {}) or {}
        for ref in xobjs.values():
            if ref.get_object().get("/Subtype") == "/Image":
                found_image = True
    assert found_image
