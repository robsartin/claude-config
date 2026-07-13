import pytest

from kdp_publisher import kdp_rules as r
from kdp_publisher.cover.spec import CoverSpec, compute_cover_spec  # noqa: F401


def test_cover_spec_dimensions_6x9_white():
    s = compute_cover_spec("6x9", 100, "white-bw")
    spine = r.spine_in(100, "white-bw")
    assert s.spine_in == pytest.approx(spine)
    assert s.width_in == pytest.approx(2 * 0.125 + 2 * 6.0 + spine)
    assert s.height_in == pytest.approx(9.0 + 2 * 0.125)
    assert s.width_px == round(s.width_in * 300)
    assert s.height_px == round(s.height_in * 300)
    assert s.spine_px == round(spine * 300)


def test_spine_text_threshold():
    assert compute_cover_spec("6x9", 78, "white-bw").allow_spine_text is False
    assert compute_cover_spec("6x9", 79, "white-bw").allow_spine_text is True


def test_barcode_constants_present():
    assert r.BARCODE_W_IN == 2.0 and r.BARCODE_H_IN == 1.2
    assert r.COVER_SAFE_MARGIN_IN == 0.375
