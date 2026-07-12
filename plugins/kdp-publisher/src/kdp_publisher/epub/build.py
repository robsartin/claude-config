import html as _html
import os
import tempfile

from ebooklib import epub

from kdp_publisher.model import (
    Block,
    BookModel,
    Heading,
    ImageBlock,
    ListBlock,
    Paragraph,
)


def _epub_media_type(data: bytes) -> tuple[str, str]:
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png", "png"
    if data[:2] == b"\xff\xd8":
        return "image/jpeg", "jpg"
    raise ValueError("unsupported image format; EPUB covers/images must be PNG or JPEG")


def _slug(title: str) -> str:
    keep = [c.lower() if c.isalnum() else "-" for c in title]
    s = "".join(keep).strip("-") or "book"
    while "--" in s:
        s = s.replace("--", "-")
    return s


def _blocks_to_xhtml(blocks: list[Block], image_refs: list[str]) -> str:
    out: list[str] = []
    img_i = 0
    for b in blocks:
        if isinstance(b, Heading):
            lvl = min(max(b.level, 1), 6)
            out.append(f"<h{lvl}>{_html.escape(b.text)}</h{lvl}>")
        elif isinstance(b, Paragraph):
            out.append(f"<p>{_html.escape(b.text)}</p>")
        elif isinstance(b, ListBlock):
            tag = "ol" if b.ordered else "ul"
            items = "".join(f"<li>{_html.escape(i)}</li>" for i in b.items)
            out.append(f"<{tag}>{items}</{tag}>")
        elif isinstance(b, ImageBlock):
            if img_i < len(image_refs):
                out.append(f'<p><img src="{image_refs[img_i]}" alt=""/></p>')
                img_i += 1
    return "".join(out)


def build_epub(book: BookModel, cover_image: bytes | None = None) -> bytes:
    meta = book.metadata
    eb = epub.EpubBook()
    eb.set_identifier(f"urn:kdp-publisher:{_slug(meta.title)}")
    eb.set_title(meta.title)
    eb.set_language("en")
    if meta.author:
        eb.add_author(meta.author)

    has_cover = bool(cover_image)
    if cover_image:
        _, ext = _epub_media_type(cover_image)
        eb.set_cover(f"cover.{ext}", cover_image)

    spine: list[object] = ["cover", "nav"] if has_cover else ["nav"]
    toc: list[object] = []
    img_counter = 0

    for ci, chapter in enumerate(book.chapters, start=1):
        # Embed this chapter's images as resources, collect their filenames.
        refs: list[str] = []
        for blk in chapter.blocks:
            if isinstance(blk, ImageBlock):
                img_counter += 1
                media_type, ext = _epub_media_type(blk.data)
                name = f"images/img-{img_counter}.{ext}"
                item = epub.EpubItem(
                    uid=f"img-{img_counter}",
                    file_name=name,
                    media_type=media_type,
                    content=blk.data,
                )
                eb.add_item(item)
                refs.append(name)

        body = _blocks_to_xhtml(chapter.blocks, refs)
        title = chapter.title or f"Chapter {ci}"
        doc = epub.EpubHtml(title=title, file_name=f"chap-{ci}.xhtml", lang="en")
        doc.content = (
            f"<html xmlns='http://www.w3.org/1999/xhtml'><head>"
            f"<title>{_html.escape(title)}</title></head><body>"
            f"<h1>{_html.escape(title)}</h1>{body}</body></html>"
        )
        eb.add_item(doc)
        spine.append(doc)
        toc.append(doc)

    eb.toc = toc
    eb.add_item(epub.EpubNcx())
    eb.add_item(epub.EpubNav())
    eb.spine = spine

    with tempfile.NamedTemporaryFile(suffix=".epub", delete=False) as f:
        path = f.name
    try:
        epub.write_epub(path, eb)
        with open(path, "rb") as fh:
            return fh.read()
    finally:
        os.unlink(path)
