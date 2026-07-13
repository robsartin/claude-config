from kdp_publisher.ingest.frontmatter import parse_frontmatter


def test_parses_labeled_lines_and_aliases():
    lines = [
        "Title: My Book",
        "Author: Rob Sartin",
        "Trim: 6x9",
        "Paper: cream",
        "Copyright: © 2026 Rob",
    ]
    fields, missing = parse_frontmatter(lines)
    assert fields["title"] == "My Book"
    assert fields["author"] == "Rob Sartin"
    assert fields["trim"] == "6x9"
    assert fields["paper_type"] == "cream-bw"
    assert fields["copyright"] == "© 2026 Rob"
    assert missing == []


def test_reports_missing_and_invalid_required_fields():
    fields, missing = parse_frontmatter(["Title: Only Title", "Trim: A7"])
    assert fields["title"] == "Only Title"
    assert "trim" not in fields  # A7 is not a valid trim
    assert set(missing) == {"author", "trim", "paper_type"}
