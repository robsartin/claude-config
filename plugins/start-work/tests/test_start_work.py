import json, os, sys
from pathlib import Path

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


import pytest


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
