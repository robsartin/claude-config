from dataclasses import dataclass


@dataclass
class Metadata:
    title: str
    author: str
    trim: str
    paper_type: str
    subtitle: str | None = None
    copyright: str | None = None


@dataclass
class Heading:
    level: int
    text: str


@dataclass
class Paragraph:
    text: str


@dataclass
class ListBlock:
    ordered: bool
    items: list[str]


@dataclass
class ImageBlock:
    data: bytes
    intended_width_in: float | None = None


Block = Heading | Paragraph | ListBlock | ImageBlock


@dataclass
class Chapter:
    title: str
    blocks: list[Block]


@dataclass
class BookModel:
    metadata: Metadata
    chapters: list[Chapter]

    def image_blocks(self) -> list[ImageBlock]:
        return [b for ch in self.chapters for b in ch.blocks if isinstance(b, ImageBlock)]
