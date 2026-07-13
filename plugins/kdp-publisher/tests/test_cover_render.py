import io
import struct
import zlib

import pypdf
import pytest

from kdp_publisher.cover.render import _cover_fill_size, render_cover
from kdp_publisher.cover.spec import compute_cover_spec


def _png(w=40, h=60, rgb=(200, 120, 60)) -> bytes:
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


def _page_size_in(pdf: bytes):
    box = pypdf.PdfReader(io.BytesIO(pdf)).pages[0].mediabox
    return float(box.width) / 72, float(box.height) / 72


def test_cover_pdf_has_correct_page_size():
    spec = compute_cover_spec("6x9", 120, "white-bw")
    pdf = render_cover(spec, _png(), "My Book", "Rob", blurb="A short blurb.")
    w_in, h_in = _page_size_in(pdf)
    assert abs(w_in - spec.width_in) < 0.05
    assert abs(h_in - spec.height_in) < 0.05
    assert len(pypdf.PdfReader(io.BytesIO(pdf)).pages) == 1


def test_thin_spine_no_text_still_renders():
    spec = compute_cover_spec("6x9", 40, "white-bw")  # < 79pp, no spine text
    pdf = render_cover(spec, _png(), "Thin Book", "Rob")
    assert _page_size_in(pdf)[0] > 0  # rendered, no crash


def test_bad_image_degrades_to_background():
    spec = compute_cover_spec("6x9", 120, "white-bw")
    pdf = render_cover(spec, b"not-an-image", "Title", "Rob")
    assert len(pypdf.PdfReader(io.BytesIO(pdf)).pages) == 1  # no crash


def test_empty_image_bytes_degrades_to_background():
    spec = compute_cover_spec("6x9", 120, "white-bw")
    pdf = render_cover(spec, b"", "Title", "Rob")
    assert len(pypdf.PdfReader(io.BytesIO(pdf)).pages) == 1  # no crash


# (img_w, img_h, panel_w, panel_h) combinations where `int(img_w * scale)` or
# `int(img_h * scale)` truncates below the panel size, per the crop-to-fill
# scale factor `max(panel_w / img_w, panel_h / img_h)`.
_FLOOR_TRUNCATION_CASES = [
    (1749, 671, 1026, 783),
    (1350, 436, 1291, 1750),
    (666, 767, 943, 419),
    (175, 1081, 1006, 130),
    (1841, 1091, 1929, 687),
    (844, 1582, 898, 1747),
    (623, 1460, 423, 255),
    (1370, 760, 285, 1835),
]


@pytest.mark.parametrize("img_w,img_h,panel_w,panel_h", _FLOOR_TRUNCATION_CASES)
def test_cover_fill_size_always_covers_panel(img_w, img_h, panel_w, panel_h):
    dw, dh = _cover_fill_size(img_w, img_h, panel_w, panel_h)
    assert dw >= panel_w
    assert dh >= panel_h
