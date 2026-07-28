import json, os, sys
import pytest
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


def test_cmd_log_rejects_unknown_type(tmp_path, monkeypatch):
    vault = tmp_path / "v"; vault.mkdir()
    cfgdir = tmp_path / "c"; cfgdir.mkdir()
    (cfgdir / "start-work.json").write_text(json.dumps({"worklog": {"vaultPath": str(vault)}}))
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(cfgdir))
    assert wl.main(["log", "bogus", "x"]) != 0
    assert not (vault / "Worklog.md").exists()   # nothing written on rejection


def test_cmd_log_rejects_bad_date(tmp_path, monkeypatch):
    vault = tmp_path / "v"; vault.mkdir()
    cfgdir = tmp_path / "c"; cfgdir.mkdir()
    (cfgdir / "start-work.json").write_text(json.dumps({"worklog": {"vaultPath": str(vault)}}))
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(cfgdir))
    assert wl.main(["log", "note", "x", "--date", "not-a-date"]) != 0


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


# Synthetic, shaped like `jira issue list --raw` (Jira search response).
JIRA_LIST = {
    "issues": [
        {"key": "PROJ-9", "fields": {"summary": "Ship the thing",
                                     "resolutiondate": "2026-07-14T11:10:50.442-0500",
                                     "status": {"name": "Done"}}},
        {"key": "PROJ-8", "fields": {"summary": "Older", "updated": "2026-07-01T09:00:00.000-0500",
                                     "status": {"name": "In Progress"}}},
    ]
}


def test_parse_jira_list():
    got = wl.parse_jira_list(JIRA_LIST)
    assert got[0] == {"date": "2026-07-14", "type": "shipped", "ref": "PROJ-9",
                      "text": "PROJ-9 — Ship the thing"}
    assert got[1]["date"] == "2026-07-01"  # falls back to `updated`


def test_parse_jira_list_accepts_bare_list_and_json_string():
    bare = JIRA_LIST["issues"]
    assert wl.parse_jira_list(bare)[0]["ref"] == "PROJ-9"
    assert wl.parse_jira_list(json.dumps(JIRA_LIST))[0]["ref"] == "PROJ-9"


# Synthetic, shaped like `glab api /merge_requests?...` (JSON array of MRs).
GITLAB_MRS = [
    {"iid": 123, "title": "Fix the bug", "merged_at": "2026-07-13T22:00:00.000Z",
     "references": {"full": "grp/app!123"}, "web_url": "https://gitlab.com/grp/app/-/merge_requests/123"},
    {"iid": 7, "title": "No refs block", "merged_at": "2026-07-10T08:00:00.000Z"},
]


def test_parse_gitlab_mrs():
    got = wl.parse_gitlab_mrs(GITLAB_MRS)
    assert got[0] == {"date": "2026-07-13", "type": "shipped", "ref": "grp/app!123",
                      "text": "grp/app!123 — Fix the bug"}
    assert got[1]["ref"] == "!7"  # falls back to !iid when references absent


def test_parse_gitlab_mrs_accepts_json_string():
    assert wl.parse_gitlab_mrs(json.dumps(GITLAB_MRS))[0]["ref"] == "grp/app!123"


def test_parse_jira_list_date_falls_back_to_statuscategorychangedate():
    issues = {"issues": [{"key": "PROJ-3", "fields": {
        "summary": "X", "statuscategorychangedate": "2026-07-05T09:00:00.000-0500"}}]}
    assert wl.parse_jira_list(issues)[0]["date"] == "2026-07-05"


def test_parse_jira_list_sparse_issue_does_not_crash():
    # no fields, no key -> empty strings, no exception
    assert wl.parse_jira_list({"issues": [{}]}) == [
        {"date": "", "type": "shipped", "ref": "", "text": ""}
    ]


def test_parse_gitlab_mrs_error_object_yields_empty():
    # glab emits an object like {"message": "404 Not Found"} on failure
    assert wl.parse_gitlab_mrs({"message": "404 Not Found"}) == []
    assert wl.parse_gitlab_mrs('{"message": "401"}') == []


def test_parse_gitlab_mrs_references_without_full_uses_iid():
    mrs = [{"iid": 9, "title": "T", "merged_at": "2026-07-02T00:00:00Z", "references": {}}]
    assert wl.parse_gitlab_mrs(mrs)[0]["ref"] == "!9"


def test_defaults_have_metrics_file_and_help_type():
    assert wl.DEFAULTS["metricsFile"] == "Metrics.md"
    assert "help" in wl.DEFAULTS["types"]


def test_metrics_path(tmp_path):
    cfg = {"vaultPath": str(tmp_path), "metricsFile": "M.md"}
    assert wl.metrics_path(cfg) == str(tmp_path / "M.md")


def test_format_metric():
    assert wl.format_metric("focus-hours", 4.5) == "- focus-hours: 4.5"


def test_parse_metric_value():
    assert wl.parse_metric_value("4.5") == 4.5
    assert wl.parse_metric_value("7.2h") == 7.2      # trailing unit accepted
    assert wl.parse_metric_value("12") == 12.0
    assert wl.parse_metric_value("nope") is None      # unparseable
    assert wl.parse_metric_value("") is None


def test_upsert_metric_creates_and_accumulates():
    out = wl.upsert_metric("", "2026-07-14", "focus-hours", 4.5)
    assert out == "## 2026-07-14\n- focus-hours: 4.5\n"
    out = wl.upsert_metric(out, "2026-07-14", "sleep-hours", 7.2)
    lines = [l for l in out.splitlines() if l.startswith("- ")]
    assert lines == ["- focus-hours: 4.5", "- sleep-hours: 7.2"]


def test_upsert_metric_replaces_same_name_same_day():
    existing = "## 2026-07-14\n- focus-hours: 4.5\n"
    out = wl.upsert_metric(existing, "2026-07-14", "focus-hours", 6.0)
    assert out.count("focus-hours") == 1
    assert "- focus-hours: 6.0" in out and "4.5" not in out


def test_upsert_metric_newest_day_on_top():
    existing = "## 2026-07-13\n- focus-hours: 3.0\n"
    out = wl.upsert_metric(existing, "2026-07-14", "focus-hours", 4.0)
    assert out.index("2026-07-14") < out.index("2026-07-13")


METRICS_SAMPLE = (
    "## 2026-07-14\n- focus-hours: 4.5\n- energy: 4\n"
    "## 2026-07-12\n- focus-hours: 3.0\n"
)


def test_parse_metrics():
    got = wl.parse_metrics(METRICS_SAMPLE)
    assert {"date": "2026-07-14", "name": "focus-hours", "value": 4.5} in got
    assert {"date": "2026-07-14", "name": "energy", "value": 4.0} in got
    assert len(got) == 3


def test_metric_series_range_inclusive():
    s = wl.metric_series(METRICS_SAMPLE, "2026-07-13", "2026-07-14")
    assert s == {"focus-hours": [("2026-07-14", 4.5)], "energy": [("2026-07-14", 4.0)]}


def test_summarize():
    s = wl.summarize([("2026-07-12", 3.0), ("2026-07-14", 5.0)])
    assert s == {"latest": 5.0, "total": 8.0, "avg": 4.0, "min": 3.0, "max": 5.0, "count": 2}


def test_summarize_single_value():
    s = wl.summarize([("2026-07-14", 7.0)])
    assert s == {"latest": 7.0, "total": 7.0, "avg": 7.0, "min": 7.0, "max": 7.0, "count": 1}


def test_sparkline():
    assert wl.sparkline([1, 2, 3, 4, 5, 6, 7, 8]) == "▁▂▃▄▅▆▇█"
    assert wl.sparkline([5, 5, 5]) == "▄▄▄"      # flat series -> mid bar, no divide-by-zero
    assert wl.sparkline([3]) == "▄"               # single value


def test_count_events():
    content = (
        "## 2026-07-14\n- **help** Unblocked Dana\n- **shipped** PROJ-1 done\n"
        "## 2026-07-10\n- **help** Reviewed a design\n"
    )
    assert wl.count_events(content, "help", "2026-07-13", "2026-07-14") == 1
    assert wl.count_events(content, "help", "2026-07-01", "2026-07-14") == 2
    assert wl.count_events(content, "shipped", "2026-07-13", "2026-07-14") == 1


def test_cmd_metric_end_to_end_upsert(tmp_path, monkeypatch):
    vault = tmp_path / "v"; vault.mkdir()
    cfgdir = tmp_path / "c"; cfgdir.mkdir()
    (cfgdir / "start-work.json").write_text(json.dumps({"worklog": {"vaultPath": str(vault)}}))
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(cfgdir))

    assert wl.main(["metric", "focus-hours", "4.5", "--date", "2026-07-14"]) == 0
    assert wl.main(["metric", "focus-hours", "6.0", "--date", "2026-07-14"]) == 0   # upsert
    assert wl.main(["metric", "energy", "4", "--date", "2026-07-14"]) == 0
    text = (vault / "Metrics.md").read_text()
    assert text.count("focus-hours") == 1
    assert "- focus-hours: 6" in text and "4.5" not in text   # upsert replaced old value
    assert "- energy: 4\n" in text                             # integral value stored bare, not 4.0


def test_cmd_metric_rejects_non_numeric(tmp_path, monkeypatch):
    vault = tmp_path / "v"; vault.mkdir()
    cfgdir = tmp_path / "c"; cfgdir.mkdir()
    (cfgdir / "start-work.json").write_text(json.dumps({"worklog": {"vaultPath": str(vault)}}))
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(cfgdir))
    assert wl.main(["metric", "focus-hours", "lots"]) != 0
    assert not (vault / "Metrics.md").exists()


def test_cmd_metric_batch_writes_all_in_one_call(tmp_path, monkeypatch):
    vault = tmp_path / "v"; vault.mkdir()
    cfgdir = tmp_path / "c"; cfgdir.mkdir()
    (cfgdir / "start-work.json").write_text(json.dumps({"worklog": {"vaultPath": str(vault)}}))
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(cfgdir))

    rc = wl.main(["metric", "work-hours=8", "focus-hours=4.5", "energy=4", "--date", "2026-07-28"])
    assert rc == 0
    text = (vault / "Metrics.md").read_text()
    assert "## 2026-07-28" in text
    assert "- work-hours: 8\n" in text        # integral stored bare
    assert "- focus-hours: 4.5\n" in text
    assert "- energy: 4\n" in text


def test_cmd_metric_batch_atomic_on_bad_token(tmp_path, monkeypatch):
    vault = tmp_path / "v"; vault.mkdir()
    cfgdir = tmp_path / "c"; cfgdir.mkdir()
    (cfgdir / "start-work.json").write_text(json.dumps({"worklog": {"vaultPath": str(vault)}}))
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(cfgdir))

    rc = wl.main(["metric", "work-hours=8", "focus-hours=lots", "--date", "2026-07-28"])
    assert rc != 0
    assert not (vault / "Metrics.md").exists()   # nothing written — atomic


def test_cmd_metrics_report_json(tmp_path, monkeypatch, capsys):
    vault = tmp_path / "v"; vault.mkdir()
    cfgdir = tmp_path / "c"; cfgdir.mkdir()
    (cfgdir / "start-work.json").write_text(json.dumps({"worklog": {"vaultPath": str(vault)}}))
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(cfgdir))
    (vault / "Metrics.md").write_text("## 2026-07-14\n- focus-hours: 4.5\n")
    (vault / "Worklog.md").write_text("## 2026-07-14\n- **help** X\n- **shipped** Y\n")

    assert wl.main(["metrics", "--since", "2026-07-13", "--until", "2026-07-14"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["metrics"]["focus-hours"]["summary"]["latest"] == 4.5
    assert out["metrics"]["focus-hours"]["sparkline"] == "▄"
    assert out["derived"]["help-count"] == 1
    assert out["derived"]["prs-merged"] == 1


def test_parse_metric_pairs_batch():
    assert wl.parse_metric_pairs(["work-hours=8", "focus-hours=4.5", "energy=4"]) == [
        ("work-hours", 8.0), ("focus-hours", 4.5), ("energy", 4.0)]


def test_parse_metric_pairs_legacy_single():
    assert wl.parse_metric_pairs(["work-hours", "8"]) == [("work-hours", 8.0)]


def test_parse_metric_pairs_trailing_unit_in_batch():
    assert wl.parse_metric_pairs(["sleep-hours=7.2h"]) == [("sleep-hours", 7.2)]


def test_parse_metric_pairs_bad_value_names_token():
    with pytest.raises(ValueError) as e:
        wl.parse_metric_pairs(["focus-hours=lots"])
    assert "focus-hours=lots" in str(e.value)


def test_parse_metric_pairs_bad_name_rejected():
    with pytest.raises(ValueError):
        wl.parse_metric_pairs(["=8"])


def test_parse_metric_pairs_mixed_form_rejected():
    with pytest.raises(ValueError):
        wl.parse_metric_pairs(["a=1", "b", "2"])


def test_parse_metric_pairs_empty_rejected():
    with pytest.raises(ValueError):
        wl.parse_metric_pairs([])


def test_parse_metric_pairs_duplicates_preserved_in_order():
    assert wl.parse_metric_pairs(["work-hours=8", "work-hours=9"]) == [
        ("work-hours", 8.0), ("work-hours", 9.0)]
