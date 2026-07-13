from kdp_publisher.interior.pipeline import produce_interior
from kdp_publisher.interior.render import render_interior
from kdp_publisher.model import BookModel, Chapter, Heading, Metadata, Paragraph


def _book(paras=600):
    blocks = [Heading(1, "Ch")] + [Paragraph(f"p{i} words here") for i in range(paras)]
    return BookModel(Metadata("T", "A", "6x9", "cream-bw"), [Chapter("Ch", blocks)])


def test_uses_google_pdf_when_valid():
    book = _book()
    good_pdf, _ = render_interior(book)  # a valid 6x9 pdf stands in for Google's export
    result = produce_interior(book, good_pdf)
    assert result.source == "google"
    assert result.pdf == good_pdf


def test_falls_back_to_render_when_google_pdf_invalid():
    import io

    import pypdf

    w = pypdf.PdfWriter()
    for _ in range(10):  # wrong: letter-ish size, too few pages
        w.add_blank_page(width=8.5 * 72, height=11 * 72)
    buf = io.BytesIO()
    w.write(buf)
    result = produce_interior(_book(), buf.getvalue())
    assert result.source == "rendered"
    assert result.page_count >= 24
    assert result.report is not None and result.report.ok is False


def test_renders_directly_when_no_google_pdf():
    result = produce_interior(_book(), None)
    assert result.source == "rendered"
    assert result.report is None
