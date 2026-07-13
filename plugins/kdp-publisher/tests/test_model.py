from kdp_publisher.model import (
    BookModel,
    Chapter,
    Heading,
    ImageBlock,
    Metadata,
    Paragraph,
)


def _book():
    ch = Chapter("Intro", [Heading(1, "Intro"), Paragraph("hello"), ImageBlock(b"\xff\xd8", 4.0)])
    return BookModel(Metadata("T", "A", "6x9", "cream-bw"), [ch])


def test_book_holds_metadata_and_chapters():
    b = _book()
    assert b.metadata.title == "T"
    assert b.chapters[0].title == "Intro"
    assert isinstance(b.chapters[0].blocks[0], Heading)


def test_image_blocks_flattens_all_images():
    b = _book()
    imgs = b.image_blocks()
    assert len(imgs) == 1
    assert imgs[0].data == b"\xff\xd8"
