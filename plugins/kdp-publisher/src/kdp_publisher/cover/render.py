import io
import math
from collections.abc import Callable
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from kdp_publisher import kdp_rules as r
from kdp_publisher.cover.spec import CoverSpec

_FONT_PATH = str(Path(__file__).parent.parent / "fonts" / "RobotoSlab-Regular.ttf")
_BG = (0x2B, 0x3A, 0x42)
_FG = (0xF5, 0xF2, 0xEA)


def _font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(_FONT_PATH, size)


def render_cover(
    spec: CoverSpec, front_image: bytes, title: str, author: str, blurb: str = ""
) -> bytes:
    dpi = spec.dpi
    W, H = spec.width_px, spec.height_px

    def px(inch: float) -> int:
        return round(inch * dpi)

    trim_w, _ = r.TRIMS_IN[spec.trim]
    back_right = px(r.BLEED_IN + trim_w)
    spine_right = px(r.BLEED_IN + trim_w + spec.spine_in)

    canvas = Image.new("RGB", (W, H), _BG)

    # Front panel: crop-to-fill the right panel.
    front = _load(front_image)
    if front is not None:
        fw, fh = W - spine_right, H
        dw, dh = _cover_fill_size(front.width, front.height, fw, fh)
        resized = front.resize((dw, dh))
        crop_x = (dw - fw) // 2
        crop_y = (dh - fh) // 2
        panel = resized.crop((crop_x, crop_y, crop_x + fw, crop_y + fh))
        canvas.paste(panel, (spine_right, 0))

    draw = ImageDraw.Draw(canvas)
    _draw_back(draw, back_right, H, blurb, px)
    if spec.allow_spine_text:
        _draw_spine(canvas, title, author, back_right, spine_right, H, dpi)

    out = io.BytesIO()
    canvas.save(out, format="PDF", resolution=float(dpi))
    return out.getvalue()


def _cover_fill_size(img_w: int, img_h: int, panel_w: int, panel_h: int) -> tuple[int, int]:
    """Resize dimensions for a crop-to-fill of `panel_w x panel_h`.

    Scales the image so it fully covers the panel, then rounds up (not
    truncates) so the resized image is never a fraction of a pixel short of
    the panel on either axis — a shortfall would leave a sliver of the crop
    background showing at the panel edge.
    """
    scale = max(panel_w / img_w, panel_h / img_h)
    return math.ceil(img_w * scale), math.ceil(img_h * scale)


def _load(data: bytes) -> Image.Image | None:
    try:
        img = Image.open(io.BytesIO(data))
        img.load()
        return img.convert("RGB")
    except Exception:
        return None


def _draw_back(
    draw: ImageDraw.ImageDraw, back_right: int, H: int, blurb: str, px: Callable[[float], int]
) -> None:
    if not blurb:
        return
    margin = px(r.COVER_SAFE_MARGIN_IN)
    safe_w = back_right - 2 * margin
    if safe_w <= 0:
        return
    keep_out_top = H - px(r.BARCODE_H_IN)
    keep_out_left = back_right - px(r.BARCODE_W_IN)
    font = _font(36)
    lines = _wrap(draw, blurb, font, safe_w)
    y = margin
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        lh = bbox[3] - bbox[1]
        line_bottom = y + lh
        if line_bottom > H - margin:
            break
        line_w = bbox[2] - bbox[0]
        if line_bottom > keep_out_top and margin + line_w > keep_out_left:
            break
        draw.text((margin, y), line, font=font, fill=_FG)
        y += int(lh * 1.4)


def _draw_spine(
    canvas: Image.Image,
    title: str,
    author: str,
    back_right: int,
    spine_right: int,
    H: int,
    dpi: int,
) -> None:
    spine_w = spine_right - back_right
    if spine_w <= 0:
        return
    fold = round(r.SPINE_FOLD_SAFETY_IN * dpi)
    padding = max(int(spine_w * 0.15), fold)
    max_text_h = spine_w - 2 * padding
    if max_text_h < 1:
        return
    text = f"{title}  ·  {author}" if author else title
    size = min(max_text_h, 72)
    strip = Image.new("RGB", (H, spine_w), _BG)
    d = ImageDraw.Draw(strip)
    font = _font(max(size, 8))
    bbox = d.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    d.text(((H - tw) // 2, (spine_w - th) // 2 - bbox[1]), text, font=font, fill=_FG)
    rotated = strip.rotate(90, expand=True)
    canvas.paste(rotated, (back_right, 0))


def _wrap(
    draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_w: int
) -> list[str]:
    words = text.split()
    lines: list[str] = []
    cur = ""
    for w in words:
        cand = f"{cur} {w}".strip()
        if draw.textlength(cand, font=font) <= max_w or not cur:
            cur = cand
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines
