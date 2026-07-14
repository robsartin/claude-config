import json, os, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "bin"))
import worklog as wl


def test_load_config_missing_returns_defaults(tmp_path):
    cfg = wl.load_config(str(tmp_path / "nope.json"))
    assert cfg == wl.DEFAULTS
    assert cfg is not wl.DEFAULTS


def test_load_config_reads_worklog_section(tmp_path):
    p = tmp_path / "start-work.json"
    p.write_text(json.dumps({"worklog": {"vaultPath": "/v"}, "gitlabHosts": ["x"]}))
    cfg = wl.load_config(str(p))
    assert cfg["vaultPath"] == "/v"          # from the worklog section
    assert cfg["worklogFile"] == "Worklog.md"  # default preserved


def test_worklog_path(tmp_path):
    cfg = {"vaultPath": str(tmp_path), "worklogFile": "W.md"}
    assert wl.worklog_path(cfg) == str(tmp_path / "W.md")
