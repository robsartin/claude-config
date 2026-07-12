import io
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

    smallest = _min_image_pixels(reader)
    if smallest is None:
        checks.append(Check("image_dpi", "pass", "no raster images"))
    elif smallest >= 1500:
        checks.append(Check("image_dpi", "pass", f"smallest image {smallest}px"))
    else:
        checks.append(
            Check(
                "image_dpi",
                "warn",
                f"smallest image is {smallest}px — may print under 300 DPI if placed "
                f"large. Google may have downsampled; consider the render fallback.",
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
