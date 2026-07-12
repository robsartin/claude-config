import pytest

from kdp_publisher import kdp_rules as r


def test_gutter_brackets():
    assert r.gutter_in(1) == 0.375
    assert r.gutter_in(150) == 0.375
    assert r.gutter_in(151) == 0.5
    assert r.gutter_in(300) == 0.5
    assert r.gutter_in(501) == 0.75
    assert r.gutter_in(1000) == 0.875


def test_spine_scales_with_pages_and_paper():
    assert r.spine_in(100, "white-bw") == pytest.approx(0.2252)
    assert r.spine_in(100, "cream-bw") == pytest.approx(0.25)
    assert r.spine_in(100, "cream-bw") > r.spine_in(100, "white-bw")


def test_cover_size_is_two_panels_plus_spine_plus_bleed():
    w, h = r.cover_size_in("6x9", 100, "white-bw")
    assert w == pytest.approx(2 * 0.125 + 2 * 6.0 + r.spine_in(100, "white-bw"))
    assert h == pytest.approx(9.0 + 2 * 0.125)


def test_unknown_paper_or_trim_raises():
    with pytest.raises(KeyError):
        r.spine_in(100, "nope")
    with pytest.raises(KeyError):
        r.cover_size_in("nope", 100, "white-bw")
