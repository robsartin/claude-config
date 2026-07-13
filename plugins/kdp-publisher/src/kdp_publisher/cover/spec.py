from dataclasses import dataclass

from kdp_publisher import kdp_rules as r


@dataclass
class CoverSpec:
    trim: str
    page_count: int
    paper_type: str
    width_in: float
    height_in: float
    spine_in: float
    width_px: int
    height_px: int
    spine_px: int
    allow_spine_text: bool
    dpi: int = 300


def compute_cover_spec(trim: str, page_count: int, paper_type: str, dpi: int = 300) -> CoverSpec:
    width_in, height_in = r.cover_size_in(trim, page_count, paper_type)
    spine = r.spine_in(page_count, paper_type)

    def px(inch: float) -> int:
        return round(inch * dpi)

    return CoverSpec(
        trim=trim,
        page_count=page_count,
        paper_type=paper_type,
        width_in=width_in,
        height_in=height_in,
        spine_in=spine,
        width_px=px(width_in),
        height_px=px(height_in),
        spine_px=px(spine),
        allow_spine_text=page_count >= r.MIN_PAGES_SPINE_TEXT,
        dpi=dpi,
    )
