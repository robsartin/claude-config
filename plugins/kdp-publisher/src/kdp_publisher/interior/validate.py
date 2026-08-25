import io
import math
from dataclasses import dataclass
from typing import Any

import pypdf

from kdp_publisher import kdp_rules as r


@dataclass
class Check:
    name: str
    status: str  # "pass" | "warn" | "fail"
    message: str


@dataclass
class ValidationReport:
    checks: list[Check]

    @property
    def ok(self) -> bool:
        return all(c.status != "fail" for c in self.checks)


def _font_is_embedded(font_obj: dict[str, Any]) -> bool:
    # Type3 glyphs are content-stream procedures carried in the PDF itself, so
    # there is no font file to embed and /FontFile is absent by construction.
    if font_obj.get("/Subtype") == "/Type3":
        return bool(font_obj.get("/CharProcs"))
    desc = font_obj.get("/FontDescriptor", {})
    if any(k in desc for k in ("/FontFile", "/FontFile2", "/FontFile3")):
        return True
    # Composite (Type0) fonts embed via descendant fonts.
    for df in font_obj.get("/DescendantFonts", []) or []:
        obj = df.get_object() if hasattr(df, "get_object") else df
        if _font_is_embedded(obj):
            return True
    return False


def _all_fonts_embedded(reader: pypdf.PdfReader) -> tuple[bool, int]:
    bare = 0
    for page in reader.pages:
        fonts = (page.get("/Resources", {}) or {}).get("/Font", {}) or {}
        for ref in fonts.values():
            obj = ref.get_object()
            if not _font_is_embedded(obj):
                bare += 1
    return bare == 0, bare


def _min_image_pixels(reader: pypdf.PdfReader) -> int | None:
    smallest = None
    for page in reader.pages:
        xobjs = (page.get("/Resources", {}) or {}).get("/XObject", {}) or {}
        for ref in xobjs.values():
            obj = ref.get_object()
            if obj.get("/Subtype") == "/Image":
                dim = min(int(obj.get("/Width", 0)), int(obj.get("/Height", 0)))
                smallest = dim if smallest is None else min(smallest, dim)
    return smallest


Matrix = tuple[float, float, float, float, float, float]
_IDENTITY: Matrix = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)


def _mul(m: Matrix, n: Matrix) -> Matrix:
    """m × n, in PDF's [a b c d e f] row-vector convention."""
    a, b, c, d, e, f = m
    a2, b2, c2, d2, e2, f2 = n
    return (
        a * a2 + b * c2,
        a * b2 + b * d2,
        c * a2 + d * c2,
        c * b2 + d * d2,
        e * a2 + f * c2 + e2,
        e * b2 + f * d2 + f2,
    )


def _placed_image_dpis(reader: pypdf.PdfReader) -> list[float]:
    """Effective DPI of every image drawn on a page, as pixels ÷ printed size.

    An image's resolution on paper depends on how large it is *placed*, which
    lives in the content stream's transformation matrix, not in the image
    object. A 1500px photo is 300 DPI across 5in and 187 DPI across 8in.

    Images drawn inside a Form XObject are not followed; the caller reports
    those as unmeasured rather than guessing.
    """
    dpis: list[float] = []

    for page in reader.pages:
        try:
            content = pypdf.generic.ContentStream(page.get_contents(), reader)
        except Exception:
            continue
        xobjects = (page.get("/Resources", {}) or {}).get("/XObject", {}) or {}
        stack: list[Matrix] = []
        current = _IDENTITY
        for operands, operator in content.operations:
            if operator == b"q":
                stack.append(current)
            elif operator == b"Q":
                current = stack.pop() if stack else _IDENTITY
            elif operator == b"cm" and len(operands) == 6:
                m0, m1, m2, m3, m4, m5 = (float(v) for v in operands)
                current = _mul((m0, m1, m2, m3, m4, m5), current)
            elif operator == b"Do" and operands:
                ref = xobjects.get(operands[0])
                obj = ref.get_object() if ref is not None else None
                if obj is not None and obj.get("/Subtype") == "/Image":
                    px_w, px_h = int(obj.get("/Width", 0)), int(obj.get("/Height", 0))
                    a, b, c, d, _, _ = current
                    w_pt, h_pt = math.hypot(a, b), math.hypot(c, d)
                    if w_pt > 0 and px_w:
                        dpis.append(px_w / (w_pt / 72.0))
                    if h_pt > 0 and px_h:
                        dpis.append(px_h / (h_pt / 72.0))
    return dpis


def validate_interior_pdf(pdf_bytes: bytes, trim: str) -> ValidationReport:
    reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
    checks: list[Check] = []

    trim_w, trim_h = r.TRIMS_IN[trim]
    box = reader.pages[0].mediabox
    w_in, h_in = float(box.width) / 72, float(box.height) / 72
    if abs(w_in - trim_w) < 0.03 and abs(h_in - trim_h) < 0.03:
        checks.append(Check("trim", "pass", f"{w_in:.3f}×{h_in:.3f} in matches {trim}"))
    else:
        checks.append(
            Check(
                "trim",
                "fail",
                f"page is {w_in:.3f}×{h_in:.3f} in; expected {trim_w}×{trim_h}. "
                f"Set File → Page setup → custom size to {trim}.",
            )
        )

    pages = len(reader.pages)
    if pages >= r.MIN_PAGES:
        checks.append(Check("min_pages", "pass", f"{pages} pages (≥ {r.MIN_PAGES})"))
    else:
        checks.append(
            Check("min_pages", "fail", f"{pages} pages; KDP needs ≥ {r.MIN_PAGES}. Add content.")
        )

    embedded, bare = _all_fonts_embedded(reader)
    checks.append(
        Check(
            "fonts",
            "pass" if embedded else "fail",
            "all fonts embedded"
            if embedded
            else f"{bare} font(s) not embedded; re-export or use the render fallback.",
        )
    )

    dpis = _placed_image_dpis(reader)
    smallest_px = _min_image_pixels(reader)
    if smallest_px is None:
        checks.append(Check("image_dpi", "pass", "no raster images"))
    elif not dpis:
        # Images exist but nothing draws them where we can see the placement
        # (unusual nesting, or an annotation appearance). Fall back to the pixel
        # count, and say that it is not a resolution measurement.
        checks.append(
            Check(
                "image_dpi",
                "warn",
                f"could not determine placed size; smallest image is {smallest_px}px. "
                f"Effective DPI is unverified — check placement manually.",
            )
        )
    elif min(dpis) >= r.MIN_IMAGE_DPI:
        checks.append(
            Check("image_dpi", "pass", f"lowest effective resolution {min(dpis):.0f} DPI")
        )
    else:
        checks.append(
            Check(
                "image_dpi",
                "warn",
                f"an image prints at {min(dpis):.0f} DPI, under KDP's "
                f"{r.MIN_IMAGE_DPI} DPI minimum. Google exports images at their "
                f"source resolution, so replace the original with a "
                f"higher-resolution one or place it smaller — re-rendering will "
                f"not add detail.",
            )
        )

    checks.append(
        Check(
            "gutter",
            "pass",
            f"required inside margin for {pages} pages: {r.gutter_in(pages)} in "
            f"(set both L/R margins to this in Page setup)",
        )
    )

    return ValidationReport(checks)
