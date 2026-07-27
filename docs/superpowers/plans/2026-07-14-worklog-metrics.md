# worklog metrics — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add numeric KPI tracking to the `worklog` plugin — a separate `Metrics.md` store, `/worklog:metric` (upsert-per-day capture), a `/worklog:metrics` trend report with derived help-count/prs-merged, and a `help` event type.

**Architecture:** Pure stdlib functions in `bin/worklog.py` (parse/upsert/series/summarize/sparkline/count) reusing the existing `_parse_days`/`_render_days` document-model machinery, exposed via `metric` and `metrics` CLI subcommands; a `/worklog:metric` command and a SKILL "Metrics" section drive them. Metrics live in a file the work reports never read.

**Tech Stack:** Python 3 stdlib + pytest, Claude Code plugin (SKILL.md + command).

## Global Constraints

- Never commit to `main`; branch `46-worklog-metrics`, squash-PR (issue #46).
- Plugin omits a `version` field; only `plugin.json` in `.claude-plugin/`. Skill `name:` stays `worklog`. **No colon-space (`: `) in an unquoted frontmatter value.**
- **Stdlib-only Python**, run via `python3`, no venv, no new deps.
- Metric store is `<vaultPath>/<metricsFile>`, default `Metrics.md`; **date-grouped, newest day on top**, entries `- <name>: <value>`.
- Metric value is **numeric**; a trailing unit is accepted and the leading number stored bare; unparseable → reject, write nothing.
- **Upsert per day**: same metric + same day replaces the value (not append/dup).
- Metrics **never** enter the work weekly/perf reports (those read only `Worklog.md`).
- `help` added to default `types`; `worklog.metricsFile` added to `DEFAULTS`.
- Report drafts to the vault, never sent; empty range says "no metrics in range", never fabricates.

## File Structure

Modified:
- `plugins/worklog/bin/worklog.py` — new pure functions + `metric`/`metrics` CLI; `DEFAULTS` gains `metricsFile`; `types` gains `help`.
- `plugins/worklog/tests/test_worklog.py` — new tests.
- `plugins/worklog/skills/worklog/SKILL.md` — a "Metrics" section.
- `plugins/worklog/.claude-plugin/plugin.json` — register `commands/metric.md`.

Created:
- `plugins/worklog/commands/metric.md` — `/worklog:metric`.

---

### Task 1: Config + value parsing + entry format

**Files:**
- Modify: `plugins/worklog/bin/worklog.py`
- Modify: `plugins/worklog/tests/test_worklog.py`

**Interfaces:**
- Produces: `DEFAULTS` gains `"metricsFile": "Metrics.md"` and `"help"` in `types`; `metrics_path(cfg) -> str`; `format_metric(name, value) -> str`; `parse_metric_value(raw) -> float | None`.

- [ ] **Step 1: Write the failing tests**

Append to `plugins/worklog/tests/test_worklog.py`:

```python
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
```

- [ ] **Step 2: Run, expect failure**

Run: `cd plugins/worklog && python3 -m pytest tests -q`
Expected: FAIL (`KeyError: 'metricsFile'` / `AttributeError: ... 'metrics_path'`).

- [ ] **Step 3: Implement**

In `plugins/worklog/bin/worklog.py`, update `DEFAULTS` (add the two keys) and add the functions after `worklog_path`:

```python
DEFAULTS = {
    "vaultPath": "~/Obsidian",
    "worklogFile": "Worklog.md",
    "metricsFile": "Metrics.md",
    "reportsDir": "Reports",
    "types": ["started", "shipped", "note", "help"],
}
```

```python
def metrics_path(cfg):
    return os.path.expanduser(os.path.join(cfg["vaultPath"], cfg["metricsFile"]))


def format_metric(name, value):
    return f"- {name}: {value}"


def parse_metric_value(raw):
    """Leading number of `raw` as a float ('7.2h' -> 7.2); None if unparseable."""
    m = re.match(r"\s*(-?\d+(?:\.\d+)?)", str(raw))
    return float(m.group(1)) if m else None
```

(`re` is already imported at the top of the module.)

- [ ] **Step 4: Run, expect pass**

Run: `cd plugins/worklog && python3 -m pytest tests -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add plugins/worklog/bin/worklog.py plugins/worklog/tests/test_worklog.py
git commit -m "worklog: metrics config + value parsing + entry format"
```

---

### Task 2: Upsert + parse + series

**Files:**
- Modify: `plugins/worklog/bin/worklog.py`
- Modify: `plugins/worklog/tests/test_worklog.py`

**Interfaces:**
- Consumes: `_parse_days`/`_render_days` (existing), `format_metric` (Task 1).
- Produces: `upsert_metric(content, date, name, value) -> str`; `parse_metrics(content) -> list[dict]`; `metric_series(content, since, until) -> dict`.

- [ ] **Step 1: Write the failing tests**

Append:

```python
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
```

- [ ] **Step 2: Run, expect failure**

Run: `cd plugins/worklog && python3 -m pytest tests -q`
Expected: FAIL (`AttributeError: ... 'upsert_metric'`).

- [ ] **Step 3: Implement**

Add to `worklog.py`:

```python
_METRIC_RE = re.compile(r"- ([\w-]+):\s*(-?\d+(?:\.\d+)?)\s*$")


def upsert_metric(content, date, name, value):
    """Insert-or-replace `- <name>: <value>` under the `## <date>` heading,
    newest day on top. Same name + same day replaces the value."""
    line = format_metric(name, value)
    preamble, days = _parse_days(content)
    by_date = {d[0]: d for d in days}
    if date in by_date:
        entries = by_date[date][1]
        for i, e in enumerate(entries):
            m = _METRIC_RE.match(e)
            if m and m.group(1) == name:
                entries[i] = line
                break
        else:
            entries.append(line)
    else:
        days.append([date, [line]])
    return _render_days(preamble, days)


def parse_metrics(content):
    out = []
    date = None
    for l in content.splitlines():
        if l.startswith("## "):
            date = l[3:].strip()
        elif date:
            m = _METRIC_RE.match(l.strip())
            if m:
                out.append({"date": date, "name": m.group(1), "value": float(m.group(2))})
    return out


def metric_series(content, since, until):
    series = {}
    for e in parse_metrics(content):
        if since <= e["date"] <= until:
            series.setdefault(e["name"], []).append((e["date"], e["value"]))
    for name in series:
        series[name].sort()
    return series
```

- [ ] **Step 4: Run, expect pass**

Run: `cd plugins/worklog && python3 -m pytest tests -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add plugins/worklog/bin/worklog.py plugins/worklog/tests/test_worklog.py
git commit -m "worklog: metric upsert + parse + series"
```

---

### Task 3: Summaries, sparkline, event counts

**Files:**
- Modify: `plugins/worklog/bin/worklog.py`
- Modify: `plugins/worklog/tests/test_worklog.py`

**Interfaces:**
- Consumes: `metric_series` (Task 2), `parse` (existing event parser).
- Produces: `summarize(points) -> dict`; `sparkline(values) -> str`; `count_events(content, type_, since, until) -> int`.

- [ ] **Step 1: Write the failing tests**

Append:

```python
def test_summarize():
    s = wl.summarize([("2026-07-12", 3.0), ("2026-07-14", 5.0)])
    assert s == {"latest": 5.0, "avg": 4.0, "min": 3.0, "max": 5.0, "count": 2}


def test_summarize_single_value():
    s = wl.summarize([("2026-07-14", 7.0)])
    assert s == {"latest": 7.0, "avg": 7.0, "min": 7.0, "max": 7.0, "count": 1}


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
```

- [ ] **Step 2: Run, expect failure**

Run: `cd plugins/worklog && python3 -m pytest tests -q`
Expected: FAIL (`AttributeError: ... 'summarize'`).

- [ ] **Step 3: Implement**

Add to `worklog.py`:

```python
_SPARK = "▁▂▃▄▅▆▇█"


def summarize(points):
    vals = [v for _, v in points]
    return {
        "latest": vals[-1],
        "avg": round(sum(vals) / len(vals), 2),
        "min": min(vals),
        "max": max(vals),
        "count": len(vals),
    }


def sparkline(values):
    if not values:
        return ""
    lo, hi = min(values), max(values)
    span = hi - lo
    mid = len(_SPARK) // 2
    return "".join(
        _SPARK[mid] if span == 0 else _SPARK[round((v - lo) / span * (len(_SPARK) - 1))]
        for v in values
    )


def count_events(content, type_, since, until):
    return sum(
        1 for e in parse(content)
        if e["type"] == type_ and since <= e["date"] <= until
    )
```

- [ ] **Step 4: Run, expect pass**

Run: `cd plugins/worklog && python3 -m pytest tests -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add plugins/worklog/bin/worklog.py plugins/worklog/tests/test_worklog.py
git commit -m "worklog: metric summaries + sparkline + event counts"
```

---

### Task 4: CLI subcommands `metric` and `metrics`

**Files:**
- Modify: `plugins/worklog/bin/worklog.py`
- Modify: `plugins/worklog/tests/test_worklog.py`

**Interfaces:**
- Consumes: everything from Tasks 1–3, plus existing `load_config`/`_default_config_path`/`worklog_path`.
- Produces: `main(["metric", name, value, ...])` and `main(["metrics", "--since", d, "--until", d])`.

- [ ] **Step 1: Write the failing tests**

Append (mirrors the existing `test_cmd_log_end_to_end...` pattern):

```python
def test_cmd_metric_end_to_end_upsert(tmp_path, monkeypatch):
    vault = tmp_path / "v"; vault.mkdir()
    cfgdir = tmp_path / "c"; cfgdir.mkdir()
    (cfgdir / "start-work.json").write_text(json.dumps({"worklog": {"vaultPath": str(vault)}}))
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(cfgdir))

    assert wl.main(["metric", "focus-hours", "4.5", "--date", "2026-07-14"]) == 0
    assert wl.main(["metric", "focus-hours", "6.0", "--date", "2026-07-14"]) == 0   # upsert
    text = (vault / "Metrics.md").read_text()
    assert text.count("focus-hours") == 1
    assert "- focus-hours: 6.0" in text


def test_cmd_metric_rejects_non_numeric(tmp_path, monkeypatch):
    vault = tmp_path / "v"; vault.mkdir()
    cfgdir = tmp_path / "c"; cfgdir.mkdir()
    (cfgdir / "start-work.json").write_text(json.dumps({"worklog": {"vaultPath": str(vault)}}))
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(cfgdir))
    assert wl.main(["metric", "focus-hours", "lots"]) != 0
    assert not (vault / "Metrics.md").exists()


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
```

- [ ] **Step 2: Run, expect failure**

Run: `cd plugins/worklog && python3 -m pytest tests -q`
Expected: FAIL (metric/metrics subcommands unknown → non-zero exit / KeyError).

- [ ] **Step 3: Implement**

Add two branches inside `main()` (before the final "unknown subcommand" line), and two helper functions:

```python
    if cmd == "metric":
        return _cmd_metric(rest)
    if cmd == "metrics":
        return _cmd_metrics(rest)
```

```python
def _cmd_metric(rest):
    import argparse
    ap = argparse.ArgumentParser(prog="worklog.py metric")
    ap.add_argument("name")
    ap.add_argument("value")
    ap.add_argument("--date", default=None)
    a = ap.parse_args(rest)
    num = parse_metric_value(a.value)
    if num is None:
        print(f"worklog: metric value '{a.value}' is not numeric", file=sys.stderr)
        return 2
    if a.date is not None:
        try:
            datetime.date.fromisoformat(a.date)
        except ValueError:
            print(f"worklog: invalid --date '{a.date}' (expected YYYY-MM-DD)", file=sys.stderr)
            return 2
    date = a.date or datetime.date.today().isoformat()
    cfg = load_config(_default_config_path())
    path = metrics_path(cfg)
    if not os.path.isdir(os.path.dirname(path)):
        print(f"worklog: vault dir missing ({os.path.dirname(path)}) — configure worklog.vaultPath.",
              file=sys.stderr)
        return 1
    content = open(path).read() if os.path.exists(path) else ""
    # store as int when the value is integral (energy: 4, not 4.0)
    stored = int(num) if num == int(num) else num
    with open(path, "w") as f:
        f.write(upsert_metric(content, date, a.name, stored))
    print(f"metric: {a.name} = {stored} on {date}")
    return 0


def _cmd_metrics(rest):
    import argparse
    ap = argparse.ArgumentParser(prog="worklog.py metrics")
    ap.add_argument("--since", required=True)
    ap.add_argument("--until", required=True)
    a = ap.parse_args(rest)
    cfg = load_config(_default_config_path())
    mpath = metrics_path(cfg)
    wpath = worklog_path(cfg)
    mcontent = open(mpath).read() if os.path.exists(mpath) else ""
    wcontent = open(wpath).read() if os.path.exists(wpath) else ""
    series = metric_series(mcontent, a.since, a.until)
    metrics = {
        name: {"points": pts, "summary": summarize(pts), "sparkline": sparkline([v for _, v in pts])}
        for name, pts in series.items()
    }
    derived = {
        "help-count": count_events(wcontent, "help", a.since, a.until),
        "prs-merged": count_events(wcontent, "shipped", a.since, a.until),
    }
    print(json.dumps({"metrics": metrics, "derived": derived}, indent=2))
    return 0
```

- [ ] **Step 4: Run, expect pass**

Run: `cd plugins/worklog && python3 -m pytest tests -q`
Expected: PASS (all tests, existing + new).

- [ ] **Step 5: Commit**

```bash
git add plugins/worklog/bin/worklog.py plugins/worklog/tests/test_worklog.py
git commit -m "worklog: metric + metrics CLI subcommands"
```

---

### Task 5: SKILL section + command + registration

**Files:**
- Modify: `plugins/worklog/skills/worklog/SKILL.md`
- Create: `plugins/worklog/commands/metric.md`
- Modify: `plugins/worklog/.claude-plugin/plugin.json`

**Interfaces:**
- Consumes: the `metric`/`metrics` CLI (Task 4).
- Produces: the `/worklog:metric` command and the documented report procedure.

- [ ] **Step 1: Append the SKILL "Metrics" section**

Append to `plugins/worklog/skills/worklog/SKILL.md`:

````markdown
## Metrics (KPIs)

Numeric readings tracked for their **trend** live in a separate file, `Metrics.md`
(`worklog.metricsFile`), which the weekly/perf reports never touch — so health numbers stay out
of work drafts.

### Record a reading

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/bin/worklog.py" metric <name> <value> [--date YYYY-MM-DD]
```

e.g. `metric focus-hours 4.5`, `metric sleep-hours 7.2`, `metric energy 4`. The value must be
numeric (a trailing unit like `7.2h` is fine — the number is kept). Re-recording the same metric
on the same day **replaces** it (a reading, not an event). Mentoring/assists are logged as
`help` events instead — `python3 "${CLAUDE_PLUGIN_ROOT}/bin/worklog.py" log help "<what>"` — so
they double as perf-review records.

### Metrics report

1. Resolve the range (default the current week).
2. Pull the structured data:
   `python3 "${CLAUDE_PLUGIN_ROOT}/bin/worklog.py" metrics --since <D> --until <D>`
   It returns each metric's points, a `summary` (latest / avg / min / max / count), and a
   `sparkline`, plus `derived` counts: `help-count` (logged `help` events) and `prs-merged`
   (logged `shipped` events — a local proxy until the Jira/GitLab factual pull is wired in).
3. Draft a short report from ONLY that data — one line per metric with its sparkline and latest
   vs average, then the derived counts. If the range is empty, say "no metrics in <range>";
   never invent readings.
4. Write the draft to `<vaultPath>/<reportsDir>/Metrics-<YYYY>-W<ww>.md` for the user to read.
   Do not send it. Professional, factual — do not use the personal `voice` skill.
````

- [ ] **Step 2: Write the command**

Create `plugins/worklog/commands/metric.md`:

```markdown
---
description: Record a numeric KPI reading (upserts per day) to your Metrics.md
argument-hint: "<name> <value> [--date YYYY-MM-DD]"
allowed-tools: Bash
---

Invoke the `worklog` skill's "Metrics — Record a reading" step with the user's arguments
($ARGUMENTS). If no name/value is given, ask. Report the stored reading. The value must be
numeric; re-recording the same metric on the same day replaces it.
```

- [ ] **Step 3: Register the command**

In `plugins/worklog/.claude-plugin/plugin.json`, add `"./commands/metric.md"` to the `commands`
array (after the existing three).

- [ ] **Step 4: Verify**

```bash
cd ~/code/claude-config
python3 -c "import json; d=json.load(open('plugins/worklog/.claude-plugin/plugin.json')); print(d['commands']); assert './commands/metric.md' in d['commands']"
grep -c 'CLAUDE_PLUGIN_ROOT' plugins/worklog/skills/worklog/SKILL.md   # expect increase
python3 -c "import re,yaml; s=open('plugins/worklog/commands/metric.md').read(); print(yaml.safe_load(re.match(r'^---\n(.*?)\n---',s,re.S).group(1))['description'])"
claude plugin validate plugins/worklog 2>&1 | tail -2
```
Expected: 4 commands incl. metric.md, description prints, validation passes (only no-version warning).

- [ ] **Step 5: Commit**

```bash
git add plugins/worklog/skills plugins/worklog/commands plugins/worklog/.claude-plugin/plugin.json
git commit -m "worklog: /worklog:metric command + Metrics SKILL section"
```

---

### Task 6: Verify end-to-end + docs + PR

**Files:**
- Modify: `CLAUDE.md`, `README.md` (mention metrics in the worklog description)

- [ ] **Step 1: Full suite + e2e against a temp vault**

```bash
cd ~/code/claude-config/plugins/worklog && python3 -m pytest tests -q && rm -rf .pytest_cache tests/__pycache__
cd ~/code/claude-config
rm -rf /tmp/mv /tmp/mc && mkdir -p /tmp/mv /tmp/mc
printf '{"worklog":{"vaultPath":"/tmp/mv"}}' > /tmp/mc/start-work.json
export CLAUDE_CONFIG_DIR=/tmp/mc
python3 plugins/worklog/bin/worklog.py metric focus-hours 4.5 --date 2026-07-14
python3 plugins/worklog/bin/worklog.py metric focus-hours 6.0 --date 2026-07-14   # upsert
python3 plugins/worklog/bin/worklog.py metric energy 4 --date 2026-07-14
python3 plugins/worklog/bin/worklog.py log help "Unblocked a teammate"
echo "--- Metrics.md ---"; cat /tmp/mv/Metrics.md
python3 plugins/worklog/bin/worklog.py metrics --since 2026-07-14 --until 2026-07-14
unset CLAUDE_CONFIG_DIR; rm -rf /tmp/mv /tmp/mc
```
Expected: `focus-hours` appears once at `6.0` (upsert), `energy: 4` (integer, not `4.0`), and `metrics` returns the series + `help-count: 1`.

- [ ] **Step 2: Docs**

In `CLAUDE.md` (`### worklog`) and `README.md` (`## The worklog plugin`): append a sentence that `/worklog:metric` records numeric KPIs to a separate `Metrics.md` (kept out of work reports), and `/worklog:metrics` drafts a trend report; note the `help` event type feeds the help-count KPI. Update the README "ships one skill plus three commands" count to four. Verify: `grep -c 'Metrics.md\|/worklog:metric' CLAUDE.md README.md`.

- [ ] **Step 3: Commit docs**

```bash
git add CLAUDE.md README.md
git commit -m "worklog: document metrics + /worklog:metric"
```

- [ ] **Step 4: Push + PR**

```bash
cd ~/code/claude-config
git push -u origin 46-worklog-metrics
gh pr create --repo robsartin/claude-config --base main \
  --title "worklog: metrics (KPI capture + trend report) + help event type" \
  --body "Closes #46. Numeric KPI tracking in worklog: separate Metrics.md store, /worklog:metric (upsert-per-day), /worklog:metrics trend report (series + sparkline + derived help-count/prs-merged), and a help event type. Pure stdlib + pytest; metrics never enter the work weekly/perf reports. Calendar meeting-hours pull, the Friday scheduled run, and true factual-pull prs-merged are deferred work-laptop follow-ons."
```

- [ ] **Step 5: CI green**

```bash
gh pr checks --repo robsartin/claude-config --watch
```
Expected: `tests` passes.

---

## Self-Review

**Spec coverage:**
- Separate `Metrics.md` store, date-grouped, `- name: value` → Tasks 1–2. ✓
- `/worklog:metric` upsert, numeric-only, ISO date, missing-vault → Task 4. ✓
- `help` type + `metricsFile` in DEFAULTS → Task 1. ✓
- `parse_metrics`/`metric_series`/`summarize`/`sparkline`/`count_events` → Tasks 2–3. ✓
- `/worklog:metrics` report (series + sparkline + derived help-count/prs-merged), drafts to vault, empty-range honesty → Tasks 4 (data) + 5 (SKILL prose). ✓
- Metrics never in work reports (separate file) → design honored; work report code untouched. ✓
- Docs + verify + PR → Task 6. ✓
- Out of scope (calendar meeting-hours, Friday schedule, factual-pull prs-merged) → not built. ✓

**Placeholder scan:** every helper, test, SKILL section, and command file is given verbatim; no TBD/TODO.

**Type/name consistency:** `metrics_path`, `format_metric`, `parse_metric_value`, `upsert_metric`, `parse_metrics`, `metric_series`, `summarize`, `sparkline`, `count_events`, and CLI `metric`/`metrics` are named identically across tasks, tests, SKILL, and the report JSON keys (`metrics`, `derived`, `summary`, `sparkline`, `help-count`, `prs-merged`).
