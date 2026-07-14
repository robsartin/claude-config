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


def test_format_entry():
    assert wl.format_entry("started", "PROJ-1", "Add limiting", "[branch: b]") == \
        "- **started** PROJ-1 — Add limiting  `[branch: b]`"
    assert wl.format_entry("note", None, "Paired with Dana") == "- **note** Paired with Dana"


def test_append_creates_file_with_heading():
    out = wl.append_entry("", "2026-07-14", "- **note** hi")
    assert out == "## 2026-07-14\n- **note** hi\n"


def test_append_newest_day_on_top():
    existing = "## 2026-07-13\n- **note** old\n"
    out = wl.append_entry(existing, "2026-07-14", "- **note** new")
    assert out.index("2026-07-14") < out.index("2026-07-13")


def test_append_same_day_appends_within_section():
    existing = "## 2026-07-14\n- **note** first\n"
    out = wl.append_entry(existing, "2026-07-14", "- **note** second")
    lines = [l for l in out.splitlines() if l.startswith("- ")]
    assert lines == ["- **note** first", "- **note** second"]


def test_append_idempotent_on_dedup_key():
    existing = "## 2026-07-14\n- **started** PROJ-1 — X\n"
    out = wl.append_entry(existing, "2026-07-14", "- **started** PROJ-1 — X",
                          dedup_key="**started** PROJ-1")
    assert out == existing  # unchanged
