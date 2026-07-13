import base64
import html as _html
import io
from collections.abc import Callable
from pathlib import Path

import pypdf
from weasyprint import HTML

from kdp_publisher import kdp_rules as r
from kdp_publisher.model import Block, BookModel, Heading, ImageBlock, ListBlock, Paragraph

_FONT = Path(__file__).parent.parent / "fonts" / "RobotoSlab-Regular.ttf"


def _image_mime(data: bytes) -> str:
    """Sniff an image blob's magic bytes to pick the correct MIME type."""
    if data.startswith(b"\x89PNG"):
        return "image/png"
    if data.startswith(b"\xff\xd8"):
        return "image/jpeg"
    return "image/jpeg"


def converge_gutter(
    render_at: Callable[[float], int], max_iterations: int = 4
) -> tuple[float, int]:
    gutter = r.gutter_in(1)
    pages = render_at(gutter)
    for _ in range(max_iterations):
        needed = r.gutter_in(pages)
        if needed == gutter:
            return gutter, pages
        gutter = needed
        pages = render_at(gutter)
    return gutter, pages


def _blocks_html(blocks: list[Block]) -> str:
    out: list[str] = []
    for b in blocks:
        if isinstance(b, Heading):
            out.append(f"<h{b.level}>{_html.escape(b.text)}</h{b.level}>")
        elif isinstance(b, Paragraph):
            out.append(f"<p>{_html.escape(b.text)}</p>")
        elif isinstance(b, ListBlock):
            tag = "ol" if b.ordered else "ul"
            items = "".join(f"<li>{_html.escape(i)}</li>" for i in b.items)
            out.append(f"<{tag}>{items}</{tag}>")
        elif isinstance(b, ImageBlock):
            enc = base64.b64encode(b.data).decode("ascii")
            mime = _image_mime(b.data)
            out.append(f'<img src="data:{mime};base64,{enc}"/>')
    return "".join(out)


def _book_html(book: BookModel, gutter: float) -> str:
    trim_w, trim_h = r.TRIMS_IN[book.metadata.trim]
    bottom = max(gutter, r.MIN_INTERIOR_BOTTOM_MARGIN_IN)
    chapters = "".join(
        f'<section class="chapter"><h1>{_html.escape(ch.title)}</h1>'
        f"{_blocks_html([b for b in ch.blocks if not (isinstance(b, Heading) and b.level == 1)])}"
        f"</section>"
        for ch in book.chapters
    )
    return f"""<html><head><meta charset="utf-8"><style>
      @font-face {{ font-family: 'Book Serif'; src: url('file://{_FONT}'); }}
      @page {{ size: {trim_w}in {trim_h}in;
               margin: {gutter}in {gutter}in {bottom}in {gutter}in;
               @bottom-center {{ content: counter(page); font-family: 'Book Serif';
                                 font-size: 9pt; vertical-align: top; }} }}
      body {{ font-family: 'Book Serif'; font-size: 11pt; line-height: 1.35; }}
      h1 {{ font-size: 16pt; margin: 0 0 6pt; page-break-before: always; }}
      section.chapter:first-of-type h1 {{ page-break-before: avoid; }}
      ul, ol {{ margin: 6pt 0; padding-left: 16pt; }}
      img {{ max-width: 100%; }}
    </style></head><body>{chapters}</body></html>"""


def render_interior(book: BookModel) -> tuple[bytes, int]:
    last: dict[str, bytes] = {}

    def render_at(gutter: float) -> int:
        pdf = HTML(string=_book_html(book, gutter)).write_pdf()
        last["pdf"] = pdf
        return len(pypdf.PdfReader(io.BytesIO(pdf)).pages)

    _, pages = converge_gutter(render_at)
    return last["pdf"], pages
