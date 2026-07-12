from pathlib import Path

from adr_toolkit.numbering import existing_adr_names, next_number


def test_next_number_follows_highest_existing_adr() -> None:
    existing = ["0001-foo.md", "0003-bar.md", "0002-baz.md"]

    assert next_number(existing) == 4


def test_next_number_in_empty_dir_is_one() -> None:
    assert next_number([]) == 1


def test_non_numbered_files_are_ignored() -> None:
    assert next_number(["README.md", "index.md", "0001-foo.md"]) == 2


def test_existing_adr_names_for_missing_dir_is_empty(tmp_path: Path) -> None:
    assert existing_adr_names(tmp_path / "nope") == []


def test_existing_adr_names_lists_files(tmp_path: Path) -> None:
    (tmp_path / "0001-a.md").write_text("x")
    assert existing_adr_names(tmp_path) == ["0001-a.md"]
