import docx
from docx.document import Document as _Doc
from docx.parts.document import DocumentPart
from docx.text.paragraph import Paragraph as _Paragraph

from kdp_publisher.ingest.frontmatter import REQUIRED, parse_frontmatter
from kdp_publisher.model import (
    BookModel,
    Chapter,
    Heading,
    ImageBlock,
    Metadata,
    Paragraph,
)


def _heading_level(para: _Paragraph) -> int | None:
    name = (para.style.name or "") if para.style else ""
    if name.startswith("Heading "):
        try:
            return int(name.split(" ")[1])
        except (ValueError, IndexError):
            return None
    if name == "Title":
        return 1
    return None


def _images(para: _Paragraph, part: DocumentPart) -> list[ImageBlock]:
    blocks: list[ImageBlock] = []
    blips = para._p.findall(".//{http://schemas.openxmlformats.org/drawingml/2006/main}blip")
    for blip in blips:
        rId = blip.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed")
        if not rId:
            continue
        image_part = part.related_parts.get(rId)
        if image_part is None:
            continue
        blocks.append(ImageBlock(data=image_part.blob, intended_width_in=None))
    return blocks


def ingest_docx(path: str, overrides: dict[str, str] | None = None) -> tuple[BookModel, list[str]]:
    doc: _Doc = docx.Document(path)
    part = doc.part

    front_lines: list[str] = []
    chapters: list[Chapter] = []
    current: Chapter | None = None

    for para in doc.paragraphs:
        level = _heading_level(para)
        text = para.text.strip()
        if level == 1:
            current = Chapter(title=text, blocks=[])
            chapters.append(current)
            continue
        if current is None:
            if text:
                front_lines.append(text)
            continue
        for img in _images(para, part):
            current.blocks.append(img)
        if level is not None and level >= 2 and text:
            current.blocks.append(Heading(level=level, text=text))
        elif text:
            current.blocks.append(Paragraph(text=text))

    fields, _ = parse_frontmatter(front_lines)
    if overrides:
        for k, v in overrides.items():
            fields.setdefault(k, v)
    missing = [k for k in REQUIRED if k not in fields]

    meta = Metadata(
        title=fields.get("title", ""),
        author=fields.get("author", ""),
        trim=fields.get("trim", "6x9"),
        paper_type=fields.get("paper_type", "cream-bw"),
        subtitle=fields.get("subtitle"),
        copyright=fields.get("copyright"),
    )
    return BookModel(metadata=meta, chapters=chapters), missing
