# worklog plugin (capture + reports) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the `worklog` plugin — capture work activity into an Obsidian `Worklog.md` and draft weekly-report / perf-review from it.

**Architecture:** A `worklog` plugin whose `bin/worklog.py` (stdlib-only, `python3`, no venv) holds pure, unit-tested functions for the `Worklog.md` document model (append an entry newest-day-on-top + idempotent, parse entries, filter by date range, format an entry line), exposed via a small CLI (`log`, `entries`). `SKILL.md` holds the judgment (drafting reports from the entries + config templates). Config is read from the machine-local `start-work.json`'s `worklog` section.

**Tech Stack:** Claude Code plugin (SKILL.md + commands), Python 3 stdlib + pytest, GitHub Actions.

## Global Constraints

- Never commit to `main`; branch `22-worklog-build`, squash-PR (issue #22).
- Plugin omits `version`; only `plugin.json` in `.claude-plugin/`.
- Skill `name:` is exactly `worklog`.
- Helpers are **stdlib-only Python**, run as `python3 ${CLAUDE_PLUGIN_ROOT}/bin/worklog.py <subcmd>` — no venv, no third-party deps.
- Storage: one rolling file, default `~/Obsidian/Worklog.md`; entries grouped under `## YYYY-MM-DD`, **newest day at the top of the file**.
- Entry line: `- **<type>** [<ref> — ]<text>[  \`<meta>\`]`. Types default `started | shipped | note`.
- Idempotency: appending a `started`/`shipped` for a ref that already has one that day is a **no-op**; `note` always appends.
- Config from `${CLAUDE_CONFIG_DIR:-$HOME/.claude}/start-work.json` → its `worklog` section; **never** written to the repo. Defaults used if absent.
- Reports are **drafts written into the vault**, never sent; professional register, NOT the `voice` skill; must not invent activity absent from the log.

## File Structure

Under `plugins/worklog/`:
- `.claude-plugin/plugin.json` — manifest (`commands` array, no version).
- `bin/worklog.py` — pure document-model functions + CLI.
- `tests/test_worklog.py` — pytest units.
- `skills/worklog/SKILL.md` — capture + report process.
- `commands/log.md`, `commands/weekly-report.md`, `commands/perf-review.md`.

Also: `.github/workflows/worklog.yml`, `.claude-plugin/marketplace.json` (entry), `CLAUDE.md`/`README.md`.

---

### Task 1: Plugin scaffold + config loader + paths

**Files:**
- Create: `plugins/worklog/.claude-plugin/plugin.json`
- Create: `plugins/worklog/bin/worklog.py`
- Create: `plugins/worklog/tests/test_worklog.py`

**Interfaces:**
- Produces: `DEFAULTS` dict; `load_config(path) -> dict` (the `worklog` section of start-work.json merged over defaults; missing file → copy of DEFAULTS); `worklog_path(cfg) -> str` (expanded `vaultPath/worklogFile`).

- [ ] **Step 1: Write the failing test**

Create `plugins/worklog/tests/test_worklog.py`:

```python
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
```

- [ ] **Step 2: Run it, expect failure**

Run: `cd plugins/worklog && python3 -m pytest tests -q`
Expected: FAIL (`ModuleNotFoundError: No module named 'worklog'`).

- [ ] **Step 3: Implement**

Create `plugins/worklog/bin/worklog.py`:

```python
#!/usr/bin/env python3
"""worklog: capture work activity into a rolling Worklog.md. Stdlib only."""
import copy
import json
import os
import sys

DEFAULTS = {
    "vaultPath": "~/Obsidian",
    "worklogFile": "Worklog.md",
    "reportsDir": "Reports",
    "types": ["started", "shipped", "note"],
}


def load_config(path):
    """The `worklog` section of start-work.json merged over DEFAULTS.
    Missing file -> a fresh copy of DEFAULTS."""
    cfg = copy.deepcopy(DEFAULTS)
    if not os.path.exists(path):
        return cfg
    with open(path) as f:
        section = json.load(f).get("worklog", {})
    cfg.update(section)
    return cfg


def worklog_path(cfg):
    return os.path.expanduser(os.path.join(cfg["vaultPath"], cfg["worklogFile"]))


def _default_config_path():
    base = os.environ.get("CLAUDE_CONFIG_DIR", os.path.expanduser("~/.claude"))
    return os.path.join(base, "start-work.json")


def main(argv):
    if not argv:
        print("usage: worklog.py <log|entries> ...", file=sys.stderr)
        return 2
    print(f"unknown subcommand: {argv[0]}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
```

- [ ] **Step 4: Run tests, expect pass**

Run: `cd plugins/worklog && python3 -m pytest tests -q`
Expected: PASS (3 passed).

- [ ] **Step 5: Write the manifest**

Create `plugins/worklog/.claude-plugin/plugin.json`:

```json
{
  "name": "worklog",
  "description": "Capture work activity into an Obsidian Worklog.md and draft weekly/perf reports from it.",
  "author": { "name": "Rob Sartin" },
  "keywords": ["worklog", "reports", "obsidian", "notes", "review"],
  "commands": ["./commands/log.md", "./commands/weekly-report.md", "./commands/perf-review.md"]
}
```

- [ ] **Step 6: Commit**

```bash
git add plugins/worklog/.claude-plugin plugins/worklog/bin plugins/worklog/tests
git commit -m "worklog: plugin scaffold + config loader"
```

---

### Task 2: Entry formatting + append (the document model)

**Files:**
- Modify: `plugins/worklog/bin/worklog.py`
- Modify: `plugins/worklog/tests/test_worklog.py`

**Interfaces:**
- Consumes: nothing new.
- Produces: `format_entry(type_, ref, text, meta=None) -> str`; `append_entry(content, date, entry_line, dedup_key=None) -> str`; internal `_parse_days`/`_render_days`. CLI `log <type> <text> [--ref R] [--branch B] [--date D]`.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_worklog.py`:

```python
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
```

- [ ] **Step 2: Run it, expect failure**

Run: `cd plugins/worklog && python3 -m pytest tests -q`
Expected: FAIL (`AttributeError: ... 'format_entry'`).

- [ ] **Step 3: Implement**

Add to `worklog.py` (above `main`):

```python
def format_entry(type_, ref, text, meta=None):
    body = f" {ref} — {text}" if ref else f" {text}"
    tail = f"  `{meta}`" if meta else ""
    return f"- **{type_}**{body}{tail}"


def _parse_days(content):
    days = []
    cur = None
    for line in content.splitlines():
        if line.startswith("## "):
            cur = [line[3:].strip(), []]
            days.append(cur)
        elif cur is not None and line.strip():
            cur[1].append(line)
    return days


def _render_days(days):
    out = []
    for date, entries in days:
        out.append(f"## {date}")
        out.extend(entries)
        out.append("")
    return "\n".join(out).rstrip("\n") + "\n"


def append_entry(content, date, entry_line, dedup_key=None):
    days = _parse_days(content)
    by_date = {d[0]: d for d in days}
    if date in by_date:
        entries = by_date[date][1]
        if dedup_key and any(dedup_key in e for e in entries):
            return content
        entries.append(entry_line)
    else:
        days.insert(0, [date, [entry_line]])
    return _render_days(days)
```

Replace `main()` with a version that handles `log` (add `import datetime`):

```python
def main(argv):
    if not argv:
        print("usage: worklog.py <log|entries> ...", file=sys.stderr)
        return 2
    cmd, rest = argv[0], argv[1:]
    if cmd == "log":
        return _cmd_log(rest)
    print(f"unknown subcommand: {cmd}", file=sys.stderr)
    return 2


def _cmd_log(rest):
    import argparse
    ap = argparse.ArgumentParser(prog="worklog.py log")
    ap.add_argument("type")
    ap.add_argument("text")
    ap.add_argument("--ref", default=None)
    ap.add_argument("--branch", default=None)
    ap.add_argument("--date", default=None)
    a = ap.parse_args(rest)
    date = a.date or datetime.date.today().isoformat()
    meta = f"[branch: {a.branch}]" if a.branch else None
    line = format_entry(a.type, a.ref, a.text, meta)
    dedup = f"**{a.type}** {a.ref}" if (a.ref and a.type != "note") else None

    cfg = load_config(_default_config_path())
    path = worklog_path(cfg)
    if not os.path.isdir(os.path.dirname(path)):
        print(f"worklog: vault dir missing ({os.path.dirname(path)}) — configure worklog.vaultPath.",
              file=sys.stderr)
        return 1
    content = ""
    if os.path.exists(path):
        with open(path) as f:
            content = f.read()
    new = append_entry(content, date, line, dedup)
    with open(path, "w") as f:
        f.write(new)
    print(f"logged: {line}")
    return 0
```

- [ ] **Step 4: Run tests, expect pass**

Run: `cd plugins/worklog && python3 -m pytest tests -q`
Expected: PASS (all). Smoke the CLI against a temp vault:
```bash
mkdir -p /tmp/wlvault
CLAUDE_CONFIG_DIR=/tmp/wlcfg python3 -c "import os;os.makedirs('/tmp/wlcfg',exist_ok=True);open('/tmp/wlcfg/start-work.json','w').write('{\"worklog\":{\"vaultPath\":\"/tmp/wlvault\"}}')"
CLAUDE_CONFIG_DIR=/tmp/wlcfg python3 plugins/worklog/bin/worklog.py log started "Test entry" --ref 42 --branch 42-test
cat /tmp/wlvault/Worklog.md   # shows the entry under today's heading
rm -rf /tmp/wlvault /tmp/wlcfg
```

- [ ] **Step 5: Commit**

```bash
git add plugins/worklog/bin/worklog.py plugins/worklog/tests/test_worklog.py
git commit -m "worklog: entry formatting + append + log CLI"
```

---

### Task 3: Parse + date-range filtering

**Files:**
- Modify: `plugins/worklog/bin/worklog.py`
- Modify: `plugins/worklog/tests/test_worklog.py`

**Interfaces:**
- Produces: `parse(content) -> list[dict]` (`{date, type, text}`); `entries_in_range(content, since, until) -> list[dict]` (inclusive, ISO date string compare); CLI `entries --since D --until D` (prints JSON).

- [ ] **Step 1: Write the failing test**

Append to `tests/test_worklog.py`:

```python
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
```

- [ ] **Step 2: Run it, expect failure**

Run: `cd plugins/worklog && python3 -m pytest tests -q`
Expected: FAIL (`AttributeError: ... 'parse'`).

- [ ] **Step 3: Implement**

Add to `worklog.py` (add `import re` at top):

```python
_ENTRY_RE = re.compile(r"- \*\*(\w+)\*\*\s+(.*)")


def parse(content):
    out = []
    date = None
    for line in content.splitlines():
        if line.startswith("## "):
            date = line[3:].strip()
        elif date:
            m = _ENTRY_RE.match(line.strip())
            if m:
                out.append({"date": date, "type": m.group(1), "text": m.group(2).strip()})
    return out


def entries_in_range(content, since, until):
    return [e for e in parse(content) if since <= e["date"] <= until]
```

Add an `entries` branch inside `main()`:

```python
    if cmd == "entries":
        import argparse
        ap = argparse.ArgumentParser(prog="worklog.py entries")
        ap.add_argument("--since", required=True)
        ap.add_argument("--until", required=True)
        a = ap.parse_args(rest)
        cfg = load_config(_default_config_path())
        path = worklog_path(cfg)
        content = open(path).read() if os.path.exists(path) else ""
        print(json.dumps(entries_in_range(content, a.since, a.until), indent=2))
        return 0
```

- [ ] **Step 4: Run tests, expect pass**

Run: `cd plugins/worklog && python3 -m pytest tests -q`
Expected: PASS (all).

- [ ] **Step 5: Commit**

```bash
git add plugins/worklog/bin/worklog.py plugins/worklog/tests/test_worklog.py
git commit -m "worklog: parse + date-range filtering"
```

---

### Task 4: SKILL.md + commands

**Files:**
- Create: `plugins/worklog/skills/worklog/SKILL.md`
- Create: `plugins/worklog/commands/log.md`, `weekly-report.md`, `perf-review.md`

**Interfaces:**
- Consumes: the `worklog.py` CLI (`log`, `entries`).
- Produces: the invocable skill + three commands.

- [ ] **Step 1: Write SKILL.md**

Create `plugins/worklog/skills/worklog/SKILL.md`:

````markdown
---
name: worklog
description: Use to record work activity and draft reports from it — log what you started/shipped/helped with, and generate a weekly status report or a performance-review narrative from the rolling Worklog.md. Triggers on "log this", "worklog", "weekly report", "what did I do this week", "perf review", "self-review".
---

# Worklog

Capture work activity into a single rolling `Worklog.md` in the Obsidian vault, and draft
reports from it. Helpers live at `${CLAUDE_PLUGIN_ROOT}/bin/worklog.py` (run with `python3`).
Config is the `worklog` section of `${CLAUDE_CONFIG_DIR:-$HOME/.claude}/start-work.json`
(`vaultPath` default `~/Obsidian`, `worklogFile` default `Worklog.md`). Everything stays in the
vault — never write the log or a report into a code repo.

## Logging an entry

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/bin/worklog.py" log <type> "<text>" [--ref <key>] [--branch <name>]
```

`type` is `started`, `shipped`, or `note`. Use `--ref` for a ticket/issue key. `started`/`shipped`
for the same ref on the same day are idempotent; notes always append. If the vault dir is
missing, the helper says so — tell the user to set `worklog.vaultPath`, don't create a vault.

## Weekly report

1. Resolve the range: default is the current week (Mon–today) unless the user gives one.
2. Pull the entries:
   `python3 "${CLAUDE_PLUGIN_ROOT}/bin/worklog.py" entries --since <YYYY-MM-DD> --until <YYYY-MM-DD>`
3. Draft a report from ONLY those entries — group by ticket/theme, lead with shipped work.
   Use the `worklog.weeklyTemplate` from config as the format if present; otherwise a simple
   "Shipped / In progress / Notes" structure. If the range is empty, say "nothing logged in
   <range>" — never invent activity.
4. Write the draft to `<vaultPath>/<reportsDir>/Weekly-<YYYY>-W<ww>.md` for the user to edit.
   Do not send or post it.

## Performance review

Same shape, longer horizon (default the current quarter, or an explicit range). Synthesize
accomplishments, recurring themes, scope/impact, and collaboration into a narrative, shaped by
`worklog.perfTemplate` if present. Draft only, into the vault. Professional register — do not
use the personal `voice` skill, and do not claim work that isn't in the log.
````

- [ ] **Step 2: Write the commands**

Create `plugins/worklog/commands/log.md`:

```markdown
---
description: Log a work-activity entry (started/shipped/note) to your Worklog.md
argument-hint: "<started|shipped|note> <text> [--ref KEY] [--branch NAME]"
allowed-tools: Bash
---

Invoke the `worklog` skill's "Logging an entry" step with the user's arguments
($ARGUMENTS). If no type/text is given, ask what to log. Report the logged line.
```

Create `plugins/worklog/commands/weekly-report.md`:

```markdown
---
description: Draft a weekly status report from your Worklog.md
argument-hint: "[since..until]"
allowed-tools: Bash, Write
---

Invoke the `worklog` skill's "Weekly report" step. If $ARGUMENTS gives a range, use it;
otherwise default to the current week. Produce a draft only.
```

Create `plugins/worklog/commands/perf-review.md`:

```markdown
---
description: Draft a performance-review narrative from your Worklog.md
argument-hint: "[since..until]"
allowed-tools: Bash, Write
---

Invoke the `worklog` skill's "Performance review" step. If $ARGUMENTS gives a range, use it;
otherwise default to the current quarter. Produce a draft only.
```

- [ ] **Step 3: Verify**

```bash
cd ~/code/claude-config
grep -c 'CLAUDE_PLUGIN_ROOT' plugins/worklog/skills/worklog/SKILL.md   # >= 2
grep -q 'name: worklog' plugins/worklog/skills/worklog/SKILL.md && echo "frontmatter OK"
claude plugin validate plugins/worklog 2>&1 | tail -3
```
Expected: count ≥ 2, `frontmatter OK`, validation passes (only no-version warning).

- [ ] **Step 4: Commit**

```bash
git add plugins/worklog/skills plugins/worklog/commands
git commit -m "worklog: SKILL.md + log/weekly-report/perf-review commands"
```

---

### Task 5: CI gate, marketplace entry, docs

**Files:**
- Create: `.github/workflows/worklog.yml`
- Modify: `.claude-plugin/marketplace.json`, `CLAUDE.md`, `README.md`

- [ ] **Step 1: CI workflow**

Create `.github/workflows/worklog.yml`:

```yaml
name: worklog

on:
  pull_request:
    paths: ['plugins/worklog/**', '.github/workflows/worklog.yml']
  push:
    branches: [main]
    paths: ['plugins/worklog/**', '.github/workflows/worklog.yml']

defaults:
  run:
    working-directory: plugins/worklog

jobs:
  tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      - uses: actions/setup-python@v6
        with:
          python-version: "3.12"
      - name: Install pytest
        run: pip install pytest
      - name: Unit tests
        run: python3 -m pytest tests -q
```

Validate: `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/worklog.yml')); print('YAML OK')"`.

- [ ] **Step 2: Marketplace entry**

Append after `start-work` in `.claude-plugin/marketplace.json`:

```json
{
  "name": "worklog",
  "source": "./plugins/worklog",
  "description": "Capture work activity into an Obsidian Worklog.md and draft weekly/perf reports."
}
```

Validate: `python3 -c "import json; n=[p['name'] for p in json.load(open('.claude-plugin/marketplace.json'))['plugins']]; print(n); assert n[-1]=='worklog'"`.

- [ ] **Step 3: Docs**

In `CLAUDE.md`: add `worklog` to the Layout block + a one-line note (captures to an Obsidian `Worklog.md`, drafts weekly/perf reports; Python helpers on `python3`; vault path is machine-local config). Do NOT touch the Plugin-source policy section.
In `README.md`: add `plugins/worklog/` to the tree and `worklog` to the individual-install list.
Verify: `grep -c worklog CLAUDE.md README.md` → non-zero each.

- [ ] **Step 4: Commit**

```bash
git add .github/workflows/worklog.yml .claude-plugin/marketplace.json CLAUDE.md README.md
git commit -m "worklog: CI gate, marketplace entry, docs"
```

---

### Task 6: Verify end-to-end + PR

**Files:** none.

- [ ] **Step 1: Full unit suite**

```bash
cd ~/code/claude-config/plugins/worklog && python3 -m pytest tests -q
```
Expected: all green.

- [ ] **Step 2: End-to-end against a temp vault**

```bash
cd ~/code/claude-config
rm -rf /tmp/wlv /tmp/wlc && mkdir -p /tmp/wlv /tmp/wlc
printf '{"worklog":{"vaultPath":"/tmp/wlv"}}' > /tmp/wlc/start-work.json
export CLAUDE_CONFIG_DIR=/tmp/wlc
python3 plugins/worklog/bin/worklog.py log started "Build the worklog plugin" --ref 22 --branch 22-worklog-build
python3 plugins/worklog/bin/worklog.py log started "Build the worklog plugin" --ref 22   # idempotent — no dup
python3 plugins/worklog/bin/worklog.py log note "Paired on the design"
echo "--- Worklog.md ---"; cat /tmp/wlv/Worklog.md
TODAY=$(python3 -c "import datetime;print(datetime.date.today().isoformat())")
python3 plugins/worklog/bin/worklog.py entries --since "$TODAY" --until "$TODAY"
unset CLAUDE_CONFIG_DIR; rm -rf /tmp/wlv /tmp/wlc
```
Expected: the started entry appears once (idempotent second call adds nothing), the note appears, and `entries` returns the two entries for today as JSON.

- [ ] **Step 3: Push + PR**

```bash
cd ~/code/claude-config
git push -u origin 22-worklog-build
gh pr create --repo robsartin/claude-config --base main \
  --title "Build: worklog plugin (capture + weekly/perf reports)" \
  --body "Closes #22. worklog plugin: stdlib-Python document model for a rolling Obsidian Worklog.md (append newest-day-on-top + idempotent, parse, date-range filter) with pytest, SKILL.md report synthesis, /log + /weekly-report + /perf-review commands, path-scoped CI, marketplace entry, docs. Reports are drafts into the vault; Jira/GitLab factual pull and start-work seam wiring are later phases."
```

- [ ] **Step 4: CI green**

```bash
gh pr checks --repo robsartin/claude-config --watch
```
Expected: `worklog / tests` passes (check name is `tests`).

---

## Self-Review

**Spec coverage:**
- Separate `worklog` plugin → all tasks. ✓
- Rolling `Worklog.md`, newest-day-on-top, entry format → Tasks 2. ✓
- Idempotent started/shipped, notes append → Task 2. ✓
- `/log` capture → Tasks 2, 4. ✓
- Parse + range for reports → Task 3. ✓
- `/weekly-report` + `/perf-review` reading the log, template-driven, draft-only, no invention → Task 4 SKILL.md. ✓
- Machine-local config (worklog section of start-work.json), never in repo → Task 1. ✓
- CI + marketplace + docs → Task 5. ✓
- Verify → Task 6. ✓
- Out of scope (Jira/GitLab pull, start-work seam wiring) → not built, noted in PR body. ✓

**Placeholder scan:** all helper code, tests, SKILL.md, and command content are complete.

**Type/name consistency:** `load_config`, `worklog_path`, `format_entry`, `append_entry`, `parse`, `entries_in_range`, and CLI `log`/`entries` are named identically across the plan, tests, and SKILL.md. Plugin/skill/marketplace name all `worklog`.
