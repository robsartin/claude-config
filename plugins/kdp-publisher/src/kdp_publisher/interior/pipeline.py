import io
from dataclasses import dataclass

import pypdf

from kdp_publisher.interior.render import render_interior
from kdp_publisher.interior.validate import ValidationReport, validate_interior_pdf
from kdp_publisher.model import BookModel


@dataclass
class InteriorResult:
    pdf: bytes
    page_count: int
    source: str  # "google" | "rendered"
    report: ValidationReport | None


def produce_interior(book: BookModel, google_pdf: bytes | None) -> InteriorResult:
    if google_pdf is not None:
        report = validate_interior_pdf(google_pdf, book.metadata.trim)
        if report.ok:
            pages = len(pypdf.PdfReader(io.BytesIO(google_pdf)).pages)
            return InteriorResult(google_pdf, pages, "google", report)
        pdf, pages = render_interior(book)
        return InteriorResult(pdf, pages, "rendered", report)
    pdf, pages = render_interior(book)
    return InteriorResult(pdf, pages, "rendered", None)
