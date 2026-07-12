from kdp_publisher.cover.prompt import build_cover_prompt
from kdp_publisher.cover.spec import compute_cover_spec
from kdp_publisher.model import Metadata


def _meta(title="My Book", author="Rob"):
    return Metadata(title=title, author=author, trim="6x9", paper_type="white-bw")


def test_prompt_includes_dimensions_and_title():
    spec = compute_cover_spec("6x9", 100, "white-bw")
    p = build_cover_prompt(_meta(), spec)
    assert "My Book" in p
    assert f"{spec.width_px} x {spec.height_px} px" in p
    assert "300 DPI" in p
    assert "barcode" in p.lower()


def test_prompt_spine_text_depends_on_page_count():
    thin = build_cover_prompt(_meta(), compute_cover_spec("6x9", 50, "white-bw"))
    thick = build_cover_prompt(_meta(), compute_cover_spec("6x9", 120, "white-bw"))
    assert "too thin for text" in thin
    assert "running vertically" in thick
