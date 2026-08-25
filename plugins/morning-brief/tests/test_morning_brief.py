import datetime
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "bin"))
import morning_brief as mb


def cfg_for(tmp_path):
    return {
        "vaultPath": str(tmp_path),
        "planningDir": "0 - Planning",
        "briefFile": "Morning Brief.md",
        "historyDir": "0 - Planning/History",
        "archivePrefix": "brief",
    }


def note(date, body="# hello\n"):
    return f"---\ndate: {date}\ntype: morning-brief\n---\n{body}"


# --- config ---------------------------------------------------------------


def test_load_config_missing_returns_defaults(tmp_path):
    cfg = mb.load_config(str(tmp_path / "nope.json"))
    assert cfg == mb.DEFAULTS
    assert cfg is not mb.DEFAULTS


def test_load_config_reads_morning_brief_section(tmp_path):
    p = tmp_path / "start-work.json"
    p.write_text(json.dumps({"morningBrief": {"vaultPath": "/v"}, "worklog": {"vaultPath": "/w"}}))
    cfg = mb.load_config(str(p))
    assert cfg["vaultPath"] == "/v"  # from the morningBrief section
    assert cfg["briefFile"] == "Morning Brief.md"  # default preserved


# --- date + naming --------------------------------------------------------


def test_note_date_reads_frontmatter():
    assert mb.note_date(note("2026-08-24")) == datetime.date(2026, 8, 24)


def test_note_date_accepts_compact_form():
    assert mb.note_date(note("20260824")) == datetime.date(2026, 8, 24)


def test_note_date_falls_back_without_frontmatter():
    fb = datetime.date(2026, 1, 1)
    assert mb.note_date("# no frontmatter", fallback=fb) == fb
    assert mb.note_date("", fallback=fb) == fb


def test_note_date_falls_back_on_garbage_date():
    fb = datetime.date(2026, 1, 1)
    assert mb.note_date(note("not-a-date"), fallback=fb) == fb


def test_note_date_ignores_a_date_outside_frontmatter():
    fb = datetime.date(2026, 1, 1)
    assert mb.note_date("# brief\ndate: 2026-08-24\n", fallback=fb) == fb


def test_archive_dir_matches_the_daily_convention(tmp_path):
    when = datetime.date(2026, 8, 24)
    got = mb.archive_dir(cfg_for(tmp_path), when)
    assert got == str(tmp_path / "0 - Planning" / "History" / "2026" / "202608")


def test_archive_name_matches_the_daily_convention(tmp_path):
    assert mb.archive_name(cfg_for(tmp_path), datetime.date(2026, 8, 24)) == "brief - 20260824"


def test_free_path_suffixes_on_collision(tmp_path):
    (tmp_path / "brief - 20260824.md").write_text("x")
    assert mb.free_path(str(tmp_path), "brief - 20260824") == str(
        tmp_path / "brief - 20260824 (2).md"
    )
    (tmp_path / "brief - 20260824 (2).md").write_text("x")
    assert mb.free_path(str(tmp_path), "brief - 20260824") == str(
        tmp_path / "brief - 20260824 (3).md"
    )


# --- rotate ---------------------------------------------------------------


def test_rotate_first_run_just_writes(tmp_path):
    cfg = cfg_for(tmp_path)
    (tmp_path / "0 - Planning").mkdir()
    r = mb.rotate(cfg, note("2026-08-24"), today=datetime.date(2026, 8, 24))
    assert r["archived"] is None
    assert r["skipped_reason"] == "no existing brief to archive"
    assert Path(r["written"]).read_text().startswith("---\ndate: 2026-08-24")


def test_rotate_archives_yesterday_then_writes_today(tmp_path):
    cfg = cfg_for(tmp_path)
    planning = tmp_path / "0 - Planning"
    planning.mkdir()
    (planning / "Morning Brief.md").write_text(note("2026-08-23", "# yesterday\n"))

    r = mb.rotate(cfg, note("2026-08-24", "# today\n"), today=datetime.date(2026, 8, 24))

    archived = Path(r["archived"])
    assert archived == planning / "History" / "2026" / "202608" / "brief - 20260823.md"
    assert "# yesterday" in archived.read_text()
    assert r["archived_from_date"] == "2026-08-23"
    assert "# today" in (planning / "Morning Brief.md").read_text()


def test_rotate_archives_across_a_month_boundary(tmp_path):
    """August's brief belongs in 202608 even when it is archived on Sept 1."""
    cfg = cfg_for(tmp_path)
    planning = tmp_path / "0 - Planning"
    planning.mkdir()
    (planning / "Morning Brief.md").write_text(note("2026-08-31"))

    r = mb.rotate(cfg, note("2026-09-01"), today=datetime.date(2026, 9, 1))
    assert Path(r["archived"]) == planning / "History" / "2026" / "202608" / "brief - 20260831.md"


def test_rotate_same_day_replaces_without_archiving(tmp_path):
    """The scheduled task firing twice in one morning leaves one note."""
    cfg = cfg_for(tmp_path)
    planning = tmp_path / "0 - Planning"
    planning.mkdir()
    (planning / "Morning Brief.md").write_text(note("2026-08-24", "# first pass\n"))

    r = mb.rotate(cfg, note("2026-08-24", "# second pass\n"), today=datetime.date(2026, 8, 24))

    assert r["archived"] is None
    assert "already dated 2026-08-24" in r["skipped_reason"]
    assert not (planning / "History").exists()
    assert "# second pass" in (planning / "Morning Brief.md").read_text()


def test_rotate_does_not_archive_an_empty_brief(tmp_path):
    cfg = cfg_for(tmp_path)
    planning = tmp_path / "0 - Planning"
    planning.mkdir()
    (planning / "Morning Brief.md").write_text("   \n")

    r = mb.rotate(cfg, note("2026-08-24"), today=datetime.date(2026, 8, 24))
    assert r["archived"] is None
    assert r["skipped_reason"] == "existing brief is empty"


def test_rotate_never_overwrites_an_existing_archive(tmp_path):
    cfg = cfg_for(tmp_path)
    planning = tmp_path / "0 - Planning"
    planning.mkdir()
    hist = planning / "History" / "2026" / "202608"
    hist.mkdir(parents=True)
    (hist / "brief - 20260823.md").write_text("# already archived\n")
    (planning / "Morning Brief.md").write_text(note("2026-08-23", "# the live one\n"))

    r = mb.rotate(cfg, note("2026-08-24"), today=datetime.date(2026, 8, 24))

    assert Path(r["archived"]).name == "brief - 20260823 (2).md"
    assert (hist / "brief - 20260823.md").read_text() == "# already archived\n"


def test_rotate_dry_run_touches_nothing(tmp_path):
    cfg = cfg_for(tmp_path)
    planning = tmp_path / "0 - Planning"
    planning.mkdir()
    (planning / "Morning Brief.md").write_text(note("2026-08-23", "# yesterday\n"))

    r = mb.rotate(
        cfg, note("2026-08-24", "# today\n"), today=datetime.date(2026, 8, 24), dry_run=True
    )

    assert r["archived"].endswith("brief - 20260823.md")
    assert not Path(r["archived"]).exists()
    assert "# yesterday" in (planning / "Morning Brief.md").read_text()


def test_rotate_appends_trailing_newline(tmp_path):
    cfg = cfg_for(tmp_path)
    (tmp_path / "0 - Planning").mkdir()
    r = mb.rotate(cfg, "# no trailing newline", today=datetime.date(2026, 8, 24))
    assert Path(r["written"]).read_text().endswith("\n")


# --- cli ------------------------------------------------------------------


def test_save_refuses_empty_stdin(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr("sys.stdin", type("S", (), {"read": staticmethod(lambda: "  \n")})())
    assert mb.main(["save"]) == 2
    assert "empty brief" in capsys.readouterr().err


def test_save_reports_a_missing_planning_dir(tmp_path, monkeypatch, capsys):
    cfgfile = tmp_path / "start-work.json"
    cfgfile.write_text(json.dumps({"morningBrief": {"vaultPath": str(tmp_path / "nope")}}))
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path))
    src = tmp_path / "brief.md"
    src.write_text(note("2026-08-24"))
    assert mb.main(["save", "--file", str(src)]) == 1
    assert "planning dir missing" in capsys.readouterr().err


def test_save_end_to_end(tmp_path, monkeypatch, capsys):
    vault = tmp_path / "vault"
    (vault / "0 - Planning").mkdir(parents=True)
    (vault / "0 - Planning" / "Morning Brief.md").write_text(note("2026-08-23", "# yesterday\n"))
    (tmp_path / "start-work.json").write_text(
        json.dumps({"morningBrief": {"vaultPath": str(vault)}})
    )
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path))

    src = tmp_path / "brief.md"
    src.write_text(note("2026-08-24", "# today\n"))
    assert mb.main(["save", "--file", str(src), "--date", "2026-08-24"]) == 0

    out = capsys.readouterr().out
    assert "archived 2026-08-23" in out
    assert (vault / "0 - Planning" / "History" / "2026" / "202608" / "brief - 20260823.md").exists()
    assert "# today" in (vault / "0 - Planning" / "Morning Brief.md").read_text()


def test_save_rejects_a_bad_date(capsys):
    assert mb.main(["save", "--date", "24-08-2026"]) == 2
    assert "invalid --date" in capsys.readouterr().err


def test_unknown_subcommand(capsys):
    assert mb.main(["nope"]) == 2
    assert "unknown subcommand" in capsys.readouterr().err


def test_paths_emits_resolved_locations(tmp_path, monkeypatch, capsys):
    (tmp_path / "start-work.json").write_text(
        json.dumps({"morningBrief": {"vaultPath": str(tmp_path / "v")}})
    )
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path))
    assert mb.main(["paths", "--date", "2026-08-24"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["brief"].endswith("0 - Planning/Morning Brief.md")
    assert data["archiveDir"].endswith("0 - Planning/History/2026/202608")
    assert data["archiveName"] == "brief - 20260824.md"
