from pathlib import Path

import pytest

from adr_toolkit.planning import PlannedAdr, UnknownTopicError, plan_emission, topic_of
from conftest import make_manifest, make_pack


def _pack(tmp_path: Path, name: str, *templates: str) -> Path:
    d = tmp_path / "packs" / name
    d.mkdir(parents=True)
    for t in templates:
        (d / t).write_text("# {{number}}. X\n")
    return tmp_path / "packs"


def test_topic_strips_numeric_ordering_prefix() -> None:
    assert topic_of(Path("01-use-tdd.md")) == "use-tdd"
    assert topic_of(Path("use-tdd.md")) == "use-tdd"


def test_plan_numbers_topics_in_order_from_start(tmp_path: Path) -> None:
    packs = _pack(tmp_path, "universal", "01-record.md", "02-use-tdd.md")
    manifest = make_manifest({"universal": make_pack("universal", path="universal")})

    planned = plan_emission(packs, manifest, ["universal"], start_number=3)

    assert planned == [
        PlannedAdr(
            3,
            "record",
            "universal",
            packs / "universal" / "01-record.md",
            "0003-record.md",
        ),
        PlannedAdr(
            4,
            "use-tdd",
            "universal",
            packs / "universal" / "02-use-tdd.md",
            "0004-use-tdd.md",
        ),
    ]


def test_excluded_topics_are_skipped_and_do_not_consume_numbers(tmp_path: Path) -> None:
    packs = _pack(tmp_path, "universal", "01-record.md", "02-use-tdd.md", "03-license.md")
    manifest = make_manifest({"universal": make_pack("universal", path="universal")})

    planned = plan_emission(packs, manifest, ["universal"], start_number=1, exclude=["use-tdd"])

    assert [(p.number, p.topic) for p in planned] == [(1, "record"), (2, "license")]


def test_unmatched_exclude_raises_listing_the_unknown_topics(tmp_path: Path) -> None:
    packs = _pack(tmp_path, "universal", "01-record.md", "02-use-tdd.md")
    manifest = make_manifest({"universal": make_pack("universal", path="universal")})

    with pytest.raises(UnknownTopicError) as excinfo:
        plan_emission(
            packs,
            manifest,
            ["universal"],
            start_number=1,
            exclude=["use-tdd", "zebra", "apple"],
        )

    # Only the genuinely unknown ones, sorted for a stable message.
    assert excinfo.value.unknown == ["apple", "zebra"]
    assert "apple, zebra" in str(excinfo.value)
