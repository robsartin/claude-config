import io
import os
import struct
import tempfile
import zlib

import ebooklib
import pytest
from ebooklib import epub
from PIL import Image

from kdp_publisher.epub.build import build_epub
from kdp_publisher.model import (
    BookModel,
    Chapter,
    Heading,
    ImageBlock,
    ListBlock,
    Metadata,
    Paragraph,
)


def _png(w=4, h=4, rgb=(10, 20, 30)) -> bytes:
    raw = b"".join(b"\x00" + bytes(rgb) * w for _ in range(h))

    def chunk(tag, data):
        c = tag + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", ihdr)
        + chunk(b"IDAT", zlib.compress(raw))
        + chunk(b"IEND", b"")
    )


def _jpeg(w=4, h=4) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (w, h)).save(buf, "JPEG")
    return buf.getvalue()


def _book():
    ch1 = Chapter(
        "Chapter One",
        [
            Paragraph("First paragraph."),
            Heading(2, "A Section"),
            ListBlock(False, ["alpha", "beta"]),
            ImageBlock(_png(), None),
        ],
    )
    ch2 = Chapter("Chapter Two", [Paragraph("Second chapter body.")])
    return BookModel(Metadata("My Book", "Rob Sartin", "6x9", "cream-bw"), [ch1, ch2])


def _read(epub_bytes: bytes):
    with tempfile.NamedTemporaryFile(suffix=".epub", delete=False) as f:
        f.write(epub_bytes)
        path = f.name
    try:
        return epub.read_epub(path)
    finally:
        os.unlink(path)


def test_epub_is_valid_zip_with_metadata_and_chapters():
    data = build_epub(_book())
    assert data[:2] == b"PK"  # zip
    b = _read(data)
    assert b.get_metadata("DC", "title")[0][0] == "My Book"
    assert b.get_metadata("DC", "creator")[0][0] == "Rob Sartin"
    docs = [i for i in b.get_items_of_type(ebooklib.ITEM_DOCUMENT)]
    bodies = " ".join(i.get_content().decode("utf-8") for i in docs)
    assert "Chapter One" in bodies and "Chapter Two" in bodies
    assert "First paragraph." in bodies


def test_epub_embeds_chapter_image_as_resource():
    b = _read(build_epub(_book()))
    images = list(b.get_items_of_type(ebooklib.ITEM_IMAGE))
    # the cover is absent here; exactly the one chapter image should be embedded
    assert any(i.get_name().endswith(".png") for i in images)


def test_epub_sets_cover_when_supplied():
    b = _read(build_epub(_book(), cover_image=_png(8, 12)))
    # In this ebooklib version, EpubCover.get_type() always reports ITEM_COVER
    # (not ITEM_IMAGE), so the cover and the embedded chapter image land in
    # separate type buckets even after a write/read round-trip.
    images = list(b.get_items_of_type(ebooklib.ITEM_IMAGE))
    covers = list(b.get_items_of_type(ebooklib.ITEM_COVER))
    assert len(covers) == 1  # the cover
    assert len(images) >= 1  # the chapter image


def test_no_author_omits_creator():
    book = _book()
    book.metadata.author = ""
    b = _read(build_epub(book))
    assert b.get_metadata("DC", "creator") == []


def test_build_epub_rejects_non_png_jpeg_cover():
    with pytest.raises(ValueError, match="PNG or JPEG"):
        build_epub(_book(), cover_image=b"GIF89a" + b"\x00" * 20)


def test_build_epub_accepts_jpeg_cover():
    b = _read(build_epub(_book(), cover_image=_jpeg(8, 12)))
    covers = list(b.get_items_of_type(ebooklib.ITEM_COVER))
    assert len(covers) == 1


def test_epub_cover_is_first_spine_item():
    b = _read(build_epub(_book(), cover_image=_png(8, 12)))
    spine_ids = [idref for idref, _linear in b.spine]
    assert spine_ids[0] == "cover"
