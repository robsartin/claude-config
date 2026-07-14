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
                          dedup_key="**started** PROJ-1 —")
    assert out == existing  # unchanged


def test_append_dedup_prefix_not_confused():
    existing = "## 2026-07-14\n- **started** PROJ-10 — other\n"
    out = wl.append_entry(existing, "2026-07-14", "- **started** PROJ-1 — new",
                          dedup_key="**started** PROJ-1 —")
    assert "PROJ-1 — new" in out          # distinct ref NOT swallowed
    assert "PROJ-10 — other" in out


def test_append_preserves_preamble():
    existing = "# My Worklog\n\nintro line\n\n## 2026-07-13\n- **note** old\n"
    out = wl.append_entry(existing, "2026-07-14", "- **note** new")
    assert "# My Worklog" in out and "intro line" in out
    assert out.index("2026-07-14") < out.index("2026-07-13")


def test_append_backdated_date_sorts_newest_first():
    existing = "## 2026-07-14\n- **note** a\n## 2026-07-12\n- **note** b\n"
    out = wl.append_entry(existing, "2026-07-13", "- **note** c")
    order = [l[3:] for l in out.splitlines() if l.startswith("## ")]
    assert order == ["2026-07-14", "2026-07-13", "2026-07-12"]


def test_cmd_log_end_to_end_no_ref_prefix_collision(tmp_path, monkeypatch):
    vault = tmp_path / "vault"; vault.mkdir()
    cfgdir = tmp_path / "cfg"; cfgdir.mkdir()
    (cfgdir / "start-work.json").write_text(json.dumps({"worklog": {"vaultPath": str(vault)}}))
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(cfgdir))

    assert wl.main(["log", "started", "First thing", "--ref", "PROJ-10", "--date", "2026-07-14"]) == 0
    assert wl.main(["log", "started", "Second thing", "--ref", "PROJ-1", "--date", "2026-07-14"]) == 0
    # same ref, same day -> idempotent
    assert wl.main(["log", "started", "First thing", "--ref", "PROJ-10", "--date", "2026-07-14"]) == 0

    text = (vault / "Worklog.md").read_text()
    assert "PROJ-10 — First thing" in text                 # kept
    assert "PROJ-1 — Second thing" in text                  # distinct ref NOT swallowed
    assert text.count("PROJ-10 — First thing") == 1         # idempotent, no dup


SAMPLE = (
    "## 2026-07-14\n- **started** PROJ-1 — A\n- **note** off-ticket\n"
    "## 2026-07-10\n- **shipped** PROJ-0 — B\n"
)


def test_parse():
    got = wl.parse(SAMPLE)
    assert got[0] == {"date": "2026-07-14", "type": "started", "text": "PROJ-1 — A"}
    assert {"date": "2026-07-14", "type": "note", "text": "off-ticket"} in got
    assert len(got) == 3


def test_entries_in_range_inclusive():
    got = wl.entries_in_range(SAMPLE, "2026-07-12", "2026-07-14")
    dates = {e["date"] for e in got}
    assert dates == {"2026-07-14"}  # 07-10 excluded
