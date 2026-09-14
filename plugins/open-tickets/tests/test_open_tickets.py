import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "bin"))
import open_tickets as ot


def test_read_jira_cli_config_missing_file(tmp_path):
    assert ot.read_jira_cli_config(str(tmp_path / "nope.yml")) == {}


def test_read_jira_cli_config_reads_server_and_login(tmp_path):
    p = tmp_path / "config.yml"
    p.write_text("login: rob@example.com\nserver: https://example.atlassian.net\nother: ignored\n")
    assert ot.read_jira_cli_config(str(p)) == {
        "login": "rob@example.com",
        "server": "https://example.atlassian.net",
    }


def test_adf_to_text_none_is_empty():
    assert ot.adf_to_text(None) == ""


def test_adf_to_text_flattens_paragraphs_and_marks():
    doc = {
        "type": "doc",
        "content": [
            {"type": "paragraph", "content": [{"type": "text", "text": "Blocked on "},
                                               {"type": "text", "text": "SPEM-1077", "marks": [{"type": "strong"}]}]},
            {"type": "paragraph", "content": [{"type": "text", "text": "Next: wait for it to land."}]},
        ],
    }
    text = ot.adf_to_text(doc)
    assert "Blocked on SPEM-1077" in text
    assert "Next: wait for it to land." in text


def test_normalize_issue_shapes_fields_and_trims_comments():
    issue = {
        "key": "ABC-1",
        "fields": {
            "summary": "Do the thing",
            "status": {"name": "In Progress"},
            "description": {"type": "doc", "content": [
                {"type": "paragraph", "content": [{"type": "text", "text": "Problem statement."}]}
            ]},
            "comment": {"comments": [
                {"author": {"displayName": f"Person {i}"},
                 "body": {"type": "doc", "content": [
                     {"type": "paragraph", "content": [{"type": "text", "text": f"comment {i}"}]}
                 ]}}
                for i in range(12)
            ]},
        },
    }
    out = ot.normalize_issue(issue, max_comments=3)
    assert out["key"] == "ABC-1"
    assert out["summary"] == "Do the thing"
    assert out["status"] == "In Progress"
    assert "Problem statement." in out["description"]
    assert len(out["comments"]) == 3
    # keeps the most recent tail, in original (oldest-of-tail-first) order
    assert [c["body"] for c in out["comments"]] == ["comment 9", "comment 10", "comment 11"]


def test_normalize_issue_missing_optional_fields():
    out = ot.normalize_issue({"key": "ABC-2", "fields": {}})
    assert out == {
        "key": "ABC-2",
        "summary": "",
        "status": "",
        "description": "",
        "comments": [],
    }
