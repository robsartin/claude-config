import json, os, sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "bin"))
import start_work as sw


def test_load_config_missing_returns_defaults(tmp_path):
    cfg = sw.load_config(str(tmp_path / "nope.json"))
    assert cfg == sw.DEFAULTS
    assert cfg is not sw.DEFAULTS  # a copy, not the shared dict


def test_load_config_merges_user_over_defaults(tmp_path):
    p = tmp_path / "start-work.json"
    p.write_text(json.dumps({"gitlabHosts": ["gitlab.corp.com"]}))
    cfg = sw.load_config(str(p))
    assert cfg["gitlabHosts"] == ["gitlab.corp.com"]
    # untouched defaults still present
    assert cfg["worklog"]["worklogFile"] == "Worklog.md"


def test_load_config_partial_worklog_override_keeps_other_defaults(tmp_path):
    p = tmp_path / "start-work.json"
    p.write_text(json.dumps({"worklog": {"vaultPath": "/custom/vault"}}))
    cfg = sw.load_config(str(p))
    assert cfg["worklog"]["vaultPath"] == "/custom/vault"   # overridden
    assert cfg["worklog"]["worklogFile"] == "Worklog.md"    # default preserved (deep-merge)


@pytest.mark.parametrize("url,expected", [
    ("https://github.com/robsartin/claude-config.git", "github.com"),
    ("git@github.com:robsartin/claude-config.git", "github.com"),
    ("ssh://git@gitlab.corp.com/team/app.git", "gitlab.corp.com"),
    ("https://gitlab.corp.com/team/app", "gitlab.corp.com"),
])
def test_host_of(url, expected):
    assert sw.host_of(url) == expected


def test_provider_for_remote():
    assert sw.provider_for_remote("git@github.com:o/r.git", []) == "github"
    assert sw.provider_for_remote("https://gitlab.corp.com/o/r.git",
                                  ["gitlab.corp.com"]) == "gitlab"
    assert sw.provider_for_remote("https://example.com/o/r.git", []) == "unknown"


def test_slugify():
    assert sw.slugify("Add API rate limiting") == "add-api-rate-limiting"
    assert sw.slugify("Fix login redirect!") == "fix-login-redirect"
    assert sw.slugify("  Multiple   spaces ") == "multiple-spaces"
    capped = sw.slugify("A" * 80)
    assert len(capped) <= 50
    assert not capped.endswith("-")


def test_branch_name():
    assert sw.branch_name("PROJ-123", "Add API rate limiting") == "PROJ-123-add-api-rate-limiting"
    assert sw.branch_name("42", "Fix login redirect!") == "42-fix-login-redirect"


# Synthetic fixture shaped like `jira issue view <KEY> --raw` (Jira REST issue).
JIRA_RAW = {
    "key": "PROJ-42",
    "fields": {
        "summary": "Add API rate limiting",
        "status": {"name": "To Do", "statusCategory": {"key": "new"}},
        "project": {"key": "PROJ", "name": "Example"},
        "assignee": None,
    },
}


def test_parse_jira_issue_unassigned():
    assert sw.parse_jira_issue(JIRA_RAW) == {
        "key": "PROJ-42",
        "summary": "Add API rate limiting",
        "status": "To Do",
        "project": "PROJ",
        "assignee": None,
    }


def test_parse_jira_issue_assigned_prefers_display_name():
    raw = {
        "key": "PROJ-7",
        "fields": {
            "summary": "Fix bug",
            "status": {"name": "In Progress"},
            "project": {"key": "PROJ"},
            "assignee": {"displayName": "Ada L", "emailAddress": "ada@example.com"},
        },
    }
    assert sw.parse_jira_issue(raw)["assignee"] == "Ada L"


def test_parse_jira_issue_accepts_json_string():
    assert sw.parse_jira_issue(json.dumps(JIRA_RAW))["key"] == "PROJ-42"


def test_parse_jira_issue_branch_name_from_summary():
    item = sw.parse_jira_issue(JIRA_RAW)
    assert sw.branch_name(item["key"], item["summary"]) == "PROJ-42-add-api-rate-limiting"
