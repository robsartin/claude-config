# worklog metrics-in-reports — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Surface `Metrics.md` readings (including a new recommended `work-hours` KPI) as a trim-ready "Metrics (curate before sharing)" section in both the weekly report and the perf-review, and add a `total` field to `summarize()`.

**Architecture:** One tiny code change — `total` on the pure `summarize()` — flows through the existing `metrics --since --until` CLI (which already embeds `summarize`). Everything else is SKILL/command/doc wording: both report steps append a metrics section built from that CLI. `work-hours` needs no capture code (any metric name already works).

**Tech Stack:** Python 3 stdlib + pytest, Claude Code plugin (SKILL.md + command files).

## Global Constraints

- Never commit to `main`; branch `48-work-hours-metric-surfaced-in-the-weekly-report`, squash-PR (issue #48).
- Stdlib-only Python, run via `python3`, no new deps. Skill `name:` stays `worklog`. No `plugin.json` change (no new command).
- The reports are **drafts written into the vault, never sent**. The metrics block is the **last** thing in a draft, under a header that literally says to curate before sharing, and is **omitted entirely when no metric has readings in range** (never an empty header, never fabricated readings).
- Each metric line is **total + daily average** over the report's range; a rating-style metric (e.g. `energy`) may show avg (+ min–max) and omit the total.
- Public repo — NO work-specific identifiers (employer, real hosts, real ticket keys, usernames); generic examples only.
- This deliberately retires the old "weekly/perf reports never read Metrics.md" line — both reports now read it. `Metrics.md` stays a separate file; capture paths (`log`, `metric`) are unchanged.

## File Structure

Modified:
- `plugins/worklog/bin/worklog.py` — add `"total"` to `summarize()`.
- `plugins/worklog/tests/test_worklog.py` — update the two `summarize` tests.
- `plugins/worklog/skills/worklog/SKILL.md` — weekly + perf steps append a metrics section; a shared "Report metrics section" subsection; fix the "never touch" line; document `work-hours`; add `total` to the metrics-report summary parenthetical.
- `plugins/worklog/commands/weekly-report.md`, `plugins/worklog/commands/perf-review.md` — mention the metrics section in the description.
- `CLAUDE.md`, `README.md` — note the reports now surface `Metrics.md` (curate before sharing).

---

### Task 1: `total` on `summarize()`

**Files:**
- Modify: `plugins/worklog/bin/worklog.py:246-254` (the `summarize` function)
- Modify: `plugins/worklog/tests/test_worklog.py:262-269` (the two summarize tests)

**Interfaces:**
- Produces: `summarize(points)` returns a dict that now includes `"total"` (sum of the range's values, rounded to 2). All existing keys (`latest`, `avg`, `min`, `max`, `count`) unchanged.

- [ ] **Step 1: Update the two failing tests**

Replace the two existing test functions at `tests/test_worklog.py:262-269`:

```python
def test_summarize():
    s = wl.summarize([("2026-07-12", 3.0), ("2026-07-14", 5.0)])
    assert s == {"latest": 5.0, "total": 8.0, "avg": 4.0, "min": 3.0, "max": 5.0, "count": 2}


def test_summarize_single_value():
    s = wl.summarize([("2026-07-14", 7.0)])
    assert s == {"latest": 7.0, "total": 7.0, "avg": 7.0, "min": 7.0, "max": 7.0, "count": 1}
```

- [ ] **Step 2: Run, expect failure**

Run: `cd plugins/worklog && python3 -m pytest tests/test_worklog.py::test_summarize tests/test_worklog.py::test_summarize_single_value -q`
Expected: FAIL — the returned dict lacks `total` (assertion mismatch).

- [ ] **Step 3: Add `total` to `summarize`**

In `plugins/worklog/bin/worklog.py`, the `summarize` function becomes:

```python
def summarize(points):
    vals = [v for _, v in points]
    return {
        "latest": vals[-1],
        "total": round(sum(vals), 2),
        "avg": round(sum(vals) / len(vals), 2),
        "min": min(vals),
        "max": max(vals),
        "count": len(vals),
    }
```

- [ ] **Step 4: Run the full suite, expect pass**

Run: `cd plugins/worklog && python3 -m pytest tests -q`
Expected: PASS (40 tests — the two updated summarize tests plus everything else; the `_cmd_metrics` JSON test still passes because it only asserts specific keys, not the whole summary dict).

- [ ] **Step 5: Commit**

```bash
git add plugins/worklog/bin/worklog.py plugins/worklog/tests/test_worklog.py
git commit -m "worklog: add total to summarize()"
```

---

### Task 2: SKILL — metrics section in both reports + work-hours

**Files:**
- Modify: `plugins/worklog/skills/worklog/SKILL.md`

**Interfaces:**
- Consumes: the `metrics --since --until` CLI (unchanged) whose `summary` now carries `total` (Task 1).
- Produces: both report steps reference a shared "Report metrics section" procedure.

- [ ] **Step 1: Fix the "never touch" line + document work-hours**

In `plugins/worklog/skills/worklog/SKILL.md`, replace the opening of the "## Metrics (KPIs)" section (currently lines 74-76):

Replace:
```markdown
Numeric readings tracked for their **trend** live in a separate file, `Metrics.md`
(`worklog.metricsFile`), which the weekly/perf reports never touch — so health numbers stay out
of work drafts.
```
with:
```markdown
Numeric readings tracked for their **trend** live in a separate file, `Metrics.md`
(`worklog.metricsFile`), kept apart from the `Worklog.md` event log. The weekly report and the
perf-review each end with a **Metrics (curate before sharing)** block built from these readings —
a section you trim before using the draft, so anything personal is easy to drop and nothing is
ever auto-sent.
```

Then in the "### Record a reading" paragraph, replace the examples sentence:
```markdown
e.g. `metric focus-hours 4.5`, `metric sleep-hours 7.2`, `metric energy 4`. The value must be
```
with:
```markdown
e.g. `metric work-hours 8`, `metric focus-hours 4.5`, `metric sleep-hours 7.2`, `metric energy 4`
(`work-hours` is a good work KPI to surface in the reports). The value must be
```

- [ ] **Step 2: Add `total` to the metrics-report summary parenthetical**

In the "### Metrics report" step 2 (currently line 95), replace:
```markdown
   It returns each metric's points, a `summary` (latest / avg / min / max / count), and a
```
with:
```markdown
   It returns each metric's points, a `summary` (latest / total / avg / min / max / count), and a
```

- [ ] **Step 3: Add the shared "Report metrics section" subsection**

At the END of the SKILL.md file (after the "### Metrics report" section), append:

````markdown
### Report metrics section (weekly & perf)

Both the weekly report and the performance review end with a metrics block, for the **same range
as the report**:

1. Pull the data: `python3 "${CLAUDE_PLUGIN_ROOT}/bin/worklog.py" metrics --since <D> --until <D>`.
2. If no metric has readings in range, **omit the section entirely** — no empty header.
3. Otherwise append it as the **last** block of the draft:

```markdown
## Metrics (curate before sharing)

- work-hours: 42.5 total over 5 days, 8.5/day avg
- focus-hours: 21.0 total over 5 days, 4.2/day avg
- energy: 4.0/day avg (min 3, max 5)
```

One line per metric with readings in range: `total` + daily average, where the day count is the
metric's `summary.count`. For a rating-style metric where a sum is meaningless (e.g. `energy`),
show the daily average (and min–max) and omit the total. The header tells the reader to trim it
before sharing; never fabricate readings.
````

- [ ] **Step 4: Reference the section from the Weekly report step**

In the "## Weekly report" section, after step 4 (ends "...do not include anything not present in the pulled entries."), add step 5:

```markdown
5. Append the **Report metrics section** (see Metrics below) as the last block of the draft, for
   the same range. Omit it if there are no readings in range.
```

- [ ] **Step 5: Reference the section from the Performance review**

In the "## Performance review" section, at the end of its paragraph (after "...do not claim work that isn't in the log."), add:

```markdown

Finally, append the **Report metrics section** (see Metrics below) as the last block, for the
review's range — omitting it if there are no readings.
```

- [ ] **Step 6: Verify SKILL renders and plugin validates**

```bash
cd ~/code/claude-config
grep -c 'Report metrics section' plugins/worklog/skills/worklog/SKILL.md   # expect 3 (definition + 2 references)
grep -n 'never touch' plugins/worklog/skills/worklog/SKILL.md              # expect 0 — the stale line is gone
claude plugin validate plugins/worklog 2>&1 | tail -2                      # passes (only no-version warning)
```
Expected: 3 mentions, 0 "never touch", validation passes.

- [ ] **Step 7: Commit**

```bash
git add plugins/worklog/skills/worklog/SKILL.md
git commit -m "worklog: surface metrics in weekly/perf reports; document work-hours"
```

---

### Task 3: Command descriptions + docs + verify + PR-prep

**Files:**
- Modify: `plugins/worklog/commands/weekly-report.md`, `plugins/worklog/commands/perf-review.md`
- Modify: `CLAUDE.md`, `README.md`

- [ ] **Step 1: Update the two command descriptions**

In `plugins/worklog/commands/weekly-report.md`, change the `description:` frontmatter line to:
```markdown
description: Draft a weekly status report from your Worklog.md (with a curate-before-sharing metrics section)
```

In `plugins/worklog/commands/perf-review.md`, change the `description:` frontmatter line to:
```markdown
description: Draft a performance-review narrative from your Worklog.md (with a curate-before-sharing metrics section)
```

(Keep the bodies unchanged. No colon-space in an unquoted frontmatter value — these descriptions contain no `: `.)

- [ ] **Step 2: End-to-end verification against a synthetic vault**

Prove the CLI feeds the section correctly (the section prose itself is SKILL-driven, so this checks the data path + `total`):

```bash
cd ~/code/claude-config
rm -rf /tmp/rv /tmp/rc && mkdir -p /tmp/rv /tmp/rc
printf '{"worklog":{"vaultPath":"/tmp/rv"}}' > /tmp/rc/start-work.json
export CLAUDE_CONFIG_DIR=/tmp/rc
python3 plugins/worklog/bin/worklog.py metric work-hours 8 --date 2026-07-27
python3 plugins/worklog/bin/worklog.py metric work-hours 7.5 --date 2026-07-26
python3 plugins/worklog/bin/worklog.py metric energy 4 --date 2026-07-27
python3 plugins/worklog/bin/worklog.py metrics --since 2026-07-20 --until 2026-07-27
unset CLAUDE_CONFIG_DIR; rm -rf /tmp/rv /tmp/rc
```
Expected: the JSON shows `work-hours` with `summary.total == 15.5`, `summary.avg == 7.75`, `summary.count == 2`, and `energy` with `total == 4`, `avg == 4.0` — i.e. exactly the numbers the section lines would render.

- [ ] **Step 3: Docs**

In `CLAUDE.md` (`### worklog`) and `README.md` (`## The worklog plugin`): update the sentence about metrics to say the weekly report and perf-review now each end with a **Metrics (curate before sharing)** section drawn from `Metrics.md` (trim it before using the draft; nothing is auto-sent), and that `work-hours` is a recommended KPI. Do not overstate — the section is omitted when there are no readings. Verify: `grep -c 'curate before sharing' CLAUDE.md README.md`.

- [ ] **Step 4: Full suite + commit docs**

```bash
cd ~/code/claude-config/plugins/worklog && python3 -m pytest tests -q && rm -rf .pytest_cache tests/__pycache__ bin/__pycache__
cd ~/code/claude-config
git add plugins/worklog/commands/weekly-report.md plugins/worklog/commands/perf-review.md CLAUDE.md README.md
git commit -m "worklog: document metrics-in-reports + curate-before-sharing"
```

**STOP after Step 4.** Do not push, do not open a PR — the controller runs the final whole-branch review, then handles push/PR/CI.

---

## Self-Review

**Spec coverage:**
- `total` on `summarize()` + tests → Task 1. ✓
- `work-hours` documented as a recommended KPI (no capture code needed) → Task 2 Step 1. ✓
- Metrics section in BOTH weekly and perf reports, as the last block, marked "curate before sharing" → Task 2 Steps 3–5. ✓
- total + daily average per metric; rating metrics may omit total → Task 2 Step 3. ✓
- Section omitted when no readings in range → Task 2 Steps 2/4/5. ✓
- Separation-reversal recorded (stale "never touch" line removed) → Task 2 Step 1 + Step 6 grep. ✓
- Docs updated for the reversal → Task 3 Step 3. ✓
- No plugin.json change, no capture change, no new store → honored (not in any task). ✓

**Placeholder scan:** every edit gives verbatim old→new text or complete blocks; example numbers are illustrative and labelled as such; no TBD/TODO.

**Type/name consistency:** `total` key is spelled identically in the function, both tests, the SKILL parenthetical, and the e2e expectation. "Report metrics section", "Metrics (curate before sharing)", and "curate before sharing" are used consistently across SKILL, commands, and docs.
