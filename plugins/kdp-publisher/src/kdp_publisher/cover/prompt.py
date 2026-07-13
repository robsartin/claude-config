from kdp_publisher import kdp_rules as r
from kdp_publisher.cover.spec import CoverSpec
from kdp_publisher.model import Metadata


def _inch(v: float) -> str:
    return str(round(v * 1000) / 1000)


def build_cover_prompt(meta: Metadata, spec: CoverSpec) -> str:
    trim_w, trim_h = r.TRIMS_IN[spec.trim]
    byline = f" by {meta.author}" if meta.author else ""
    if spec.allow_spine_text:
        spine_text = (
            f"The spine is {_inch(spec.spine_in)} in ({spec.spine_px} px) wide — wide enough for "
            f"text: place the title{' and author' if meta.author else ''} running vertically, "
            f"centered, kept at least {_inch(r.SPINE_FOLD_SAFETY_IN)} in from each spine fold."
        )
    else:
        spine_text = (
            f"The spine is only {_inch(spec.spine_in)} in ({spec.spine_px} px) wide — too thin for "
            f"text (KDP needs {r.MIN_PAGES_SPINE_TEXT}+ pages); leave it as background/color only."
        )
    return (
        f"Design a print-ready KDP paperback WRAPAROUND cover (a single flat image spanning "
        f'back cover + spine + front cover) for the book "{meta.title}"{byline}.\n\n'
        f"Exact dimensions — produce the image at this size, full bleed:\n"
        f"- Total canvas: {_inch(spec.width_in)} x {_inch(spec.height_in)} in = "
        f"{spec.width_px} x {spec.height_px} px at {spec.dpi} DPI.\n"
        f"- Trim (each cover panel): {_inch(trim_w)} x {_inch(trim_h)} in. "
        f"Bleed: {_inch(r.BLEED_IN)} in on every outer edge.\n"
        f"- Left to right: [{_inch(r.BLEED_IN)} in bleed] [BACK {_inch(trim_w)} in] "
        f"[SPINE {_inch(spec.spine_in)} in] [FRONT {_inch(trim_w)} in] "
        f"[{_inch(r.BLEED_IN)} in bleed].\n\n"
        f"Layout rules:\n"
        f'- FRONT (right panel): the title "{meta.title}"{byline}, prominent and legible. '
        f"Main visual.\n"
        f"- SPINE (center strip): {spine_text}\n"
        f"- BACK (left panel): room for a blurb; keep it simple. RESERVE a clear "
        f"{_inch(r.BARCODE_W_IN)} x {_inch(r.BARCODE_H_IN)} in area at the BACK panel's "
        f"bottom-right corner for the barcode (KDP prints it there) — put nothing important "
        f"in it.\n"
        f"- Keep all text and key artwork at least {_inch(r.SAFE_MARGIN_FROM_TRIM_IN)} in "
        f"inside every trim edge; let only background bleed into the outer "
        f"{_inch(r.BLEED_IN)} in."
    )
