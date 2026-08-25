"""KDP print constants and geometry. Values are KDP's real requirements
(see reference_kdp_pdf_rules memory / Mise kdp package)."""

BLEED_IN = 0.125
MIN_IMAGE_DPI = 300
MIN_PAGES = 24
MIN_PAGES_SPINE_TEXT = 79
SPINE_FOLD_SAFETY_IN = 0.0625
SAFE_MARGIN_FROM_TRIM_IN = 0.25
MIN_INTERIOR_BOTTOM_MARGIN_IN = 0.5
BARCODE_W_IN = 2.0
BARCODE_H_IN = 1.2
COVER_SAFE_MARGIN_IN = 0.375

PAPER_THICKNESS_IN: dict[str, float] = {
    "white-bw": 0.002252,
    "cream-bw": 0.0025,
    "standard-color": 0.002252,
    "premium-color": 0.002347,
}

TRIMS_IN: dict[str, tuple[float, float]] = {
    "6x9": (6.0, 9.0),
    "5.5x8.5": (5.5, 8.5),
    "5x8": (5.0, 8.0),
    "8.5x11": (8.5, 11.0),
}


def gutter_in(page_count: int) -> float:
    if page_count <= 150:
        return 0.375
    if page_count <= 300:
        return 0.5
    if page_count <= 500:
        return 0.625
    if page_count <= 700:
        return 0.75
    return 0.875


def spine_in(page_count: int, paper_type: str) -> float:
    return page_count * PAPER_THICKNESS_IN[paper_type]


def cover_size_in(trim: str, page_count: int, paper_type: str) -> tuple[float, float]:
    trim_w, trim_h = TRIMS_IN[trim]
    spine = spine_in(page_count, paper_type)
    width = BLEED_IN + trim_w + spine + trim_w + BLEED_IN
    height = trim_h + 2 * BLEED_IN
    return width, height
