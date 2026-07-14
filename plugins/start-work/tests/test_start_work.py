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
