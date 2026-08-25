import base64
import io
import struct
import zlib

import pypdf
from weasyprint import HTML

from kdp_publisher.interior.validate import (
    _font_is_embedded,
    validate_interior_pdf,
)


def _blank_pdf(width_in, height_in, pages):
    w = pypdf.PdfWriter()
    for _ in range(pages):
        w.add_blank_page(width=width_in * 72, height=height_in * 72)
    buf = io.BytesIO()
    w.write(buf)
    return buf.getvalue()


def _weasy_pdf_6x9(pages_text):
    html = f"""<html><head><style>
      @page {{ size: 6in 9in; margin: 0.5in; }}
      body {{ font-family: serif; }}
      .pb {{ page-break-after: always; }}
    </style></head><body>{pages_text}</body></html>"""
    return HTML(string=html).write_pdf()


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


def _weasy_pdf_6x9_with_tiny_image(pages_text, image_px=12):
    png_b64 = base64.b64encode(_tiny_png_bytes(size=image_px)).decode()
    img_tag = f'<img src="data:image/png;base64,{png_b64}" width="{image_px}" height="{image_px}">'
    html = f"""<html><head><style>
      @page {{ size: 6in 9in; margin: 0.5in; }}
      body {{ font-family: serif; }}
      .pb {{ page-break-after: always; }}
    </style></head><body>{img_tag}{pages_text}</body></html>"""
    return HTML(string=html).write_pdf()


def _strip_font_files(font_obj):
    """Recursively delete /FontFile*/FontFile2/FontFile3 from a font's descriptor(s),
    including descendant fonts of Type0 composite fonts, turning an embedded-font PDF
    into a bare-font one in place."""
    desc = font_obj.get("/FontDescriptor")
    if desc is not None:
        desc_obj = desc.get_object()
        for key in ("/FontFile", "/FontFile2", "/FontFile3"):
            if key in desc_obj:
                del desc_obj[key]
    for descendant in font_obj.get("/DescendantFonts", []) or []:
        _strip_font_files(descendant.get_object())


def _strip_all_embedded_fonts(pdf_bytes):
    """Load a real PDF, strip every font's embedded font-file streams, and re-serialize
    it with PdfWriter so validate_interior_pdf sees bare (non-embedded) fonts."""
    reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
    for page in reader.pages:
        fonts = (page.get("/Resources", {}) or {}).get("/Font", {}) or {}
        for ref in fonts.values():
            _strip_font_files(ref.get_object())
    writer = pypdf.PdfWriter()
    writer.append(reader)
    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()


def test_wrong_trim_fails():
    report = validate_interior_pdf(_blank_pdf(8.5, 11, 30), "6x9")
    assert report.ok is False
    assert any(c.name == "trim" and c.status == "fail" for c in report.checks)


def test_too_few_pages_fails():
    report = validate_interior_pdf(_blank_pdf(6, 9, 10), "6x9")
    assert any(c.name == "min_pages" and c.status == "fail" for c in report.checks)


def test_font_embedding_helper():
    assert _font_is_embedded({"/FontDescriptor": {"/FontFile2": object()}}) is True
    assert _font_is_embedded({"/FontDescriptor": {}}) is False


def test_weasyprint_output_passes_trim_and_pages():
    body = "".join(f"<p class='pb'>page {i}</p>" for i in range(30))
    report = validate_interior_pdf(_weasy_pdf_6x9(body), "6x9")
    assert any(c.name == "trim" and c.status == "pass" for c in report.checks)
    assert any(c.name == "min_pages" and c.status == "pass" for c in report.checks)
    assert any(c.name == "fonts" and c.status == "pass" for c in report.checks)
    assert any(c.name == "gutter" and c.status == "pass" for c in report.checks)
    assert report.ok is True


def test_tiny_raster_image_warns_on_dpi():
    body = "".join(f"<p class='pb'>page {i}</p>" for i in range(30))
    pdf_bytes = _weasy_pdf_6x9_with_tiny_image(body, image_px=12)
    report = validate_interior_pdf(pdf_bytes, "6x9")
    image_dpi_check = next(c for c in report.checks if c.name == "image_dpi")
    assert image_dpi_check.status == "warn"


def test_bare_fonts_fail():
    body = "".join(f"<p class='pb'>page {i}</p>" for i in range(30))
    embedded_pdf = _weasy_pdf_6x9(body)
    stripped_pdf = _strip_all_embedded_fonts(embedded_pdf)
    report = validate_interior_pdf(stripped_pdf, "6x9")
    fonts_check = next(c for c in report.checks if c.name == "fonts")
    assert fonts_check.status == "fail"
    assert report.ok is False


def _weasy_pdf_6x9_with_placed_image(pages_text, image_px, placed_in):
    """A 6x9 PDF whose image is *placed* at a chosen width, independent of its pixels."""
    png_b64 = base64.b64encode(_tiny_png_bytes(size=image_px)).decode()
    img_tag = f'<img src="data:image/png;base64,{png_b64}" style="width:{placed_in}in">'
    html = f"""<html><head><style>
      @page {{ size: 6in 9in; margin: 0.375in; }}
      body {{ font-family: serif; }}
      .pb {{ page-break-after: always; }}
    </style></head><body>{img_tag}{pages_text}</body></html>"""
    return HTML(string=html).write_pdf()


def _dpi_check(pdf_bytes):
    report = validate_interior_pdf(pdf_bytes, "6x9")
    return next(c for c in report.checks if c.name == "image_dpi")


def test_many_pixels_placed_large_warns_because_effective_dpi_is_under_300():
    """1500px across 5.25in prints at ~286 DPI — under KDP's minimum, despite the pixel count."""
    body = "".join(f"<p class='pb'>page {i}</p>" for i in range(30))
    check = _dpi_check(_weasy_pdf_6x9_with_placed_image(body, image_px=1500, placed_in=5.25))

    assert check.status == "warn"
    assert "286" in check.message or "285" in check.message


def test_image_passes_when_effective_dpi_clears_300():
    """Same placement, more pixels: 1600px across 5.25in is ~305 DPI."""
    body = "".join(f"<p class='pb'>page {i}</p>" for i in range(30))
    check = _dpi_check(_weasy_pdf_6x9_with_placed_image(body, image_px=1600, placed_in=5.25))

    assert check.status == "pass"


def test_modest_pixel_count_placed_small_passes():
    """900px at 1in is 900 DPI. Pixel count alone would have flagged this."""
    body = "".join(f"<p class='pb'>page {i}</p>" for i in range(30))
    check = _dpi_check(_weasy_pdf_6x9_with_placed_image(body, image_px=900, placed_in=1.0))

    assert check.status == "pass"


def test_dpi_message_reports_the_measured_resolution():
    body = "".join(f"<p class='pb'>page {i}</p>" for i in range(30))
    check = _dpi_check(_weasy_pdf_6x9_with_placed_image(body, image_px=1600, placed_in=5.25))

    assert "DPI" in check.message


def test_dpi_is_measured_on_merged_pages():
    """A merged/stamped page still reports a measured DPI, not "unknown"."""
    body = "".join(f"<p class='pb'>page {i}</p>" for i in range(30))
    inner = pypdf.PdfReader(
        io.BytesIO(_weasy_pdf_6x9_with_placed_image(body, image_px=1500, placed_in=5.25))
    )
    writer = pypdf.PdfWriter()
    for src in inner.pages:
        page = writer.add_blank_page(width=6 * 72, height=9 * 72)
        page.merge_page(src)
    buf = io.BytesIO()
    writer.write(buf)

    check = _dpi_check(buf.getvalue())

    assert check.status == "warn"
    assert "286" in check.message or "285" in check.message
    assert "could not determine" not in check.message


def test_type3_font_is_self_contained_not_unembedded():
    """Type3 glyphs are content-stream procedures inside the PDF itself.

    There is no font file to embed, so /FontFile is absent by construction.
    Google Docs emits Type3 fonts for bullets and drawings; counting them as
    unembedded fails an otherwise-valid export.
    """
    type3 = {
        "/Subtype": "/Type3",
        "/CharProcs": {"/g0": object(), "/g1": object()},
        "/FontMatrix": [0.00048828125, 0, 0, -0.00048828125, 0, 0],
        "/FontDescriptor": {},
    }

    assert _font_is_embedded(type3) is True


def test_type3_without_charprocs_is_still_reported():
    """A Type3 with no glyph procedures has nothing to draw with — not a free pass."""
    assert _font_is_embedded({"/Subtype": "/Type3", "/FontDescriptor": {}}) is False


def test_5_5x8_5_is_a_supported_trim():
    """KDP's 5.5x8.5 is one of its most common trims."""
    report = validate_interior_pdf(_blank_pdf(5.5, 8.5, 30), "5.5x8.5")
    trim_check = next(c for c in report.checks if c.name == "trim")

    assert trim_check.status == "pass"
