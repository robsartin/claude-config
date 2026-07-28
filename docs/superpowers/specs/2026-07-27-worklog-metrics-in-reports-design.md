# worklog: work-hours metric + metrics in the weekly/perf reports

Date: 2026-07-27
Issue: robsartin/claude-config#48
Related: `docs/superpowers/specs/2026-07-14-worklog-metrics-design.md` (the metrics feature this extends)

## Problem

Rob wants a `work-hours` KPI that shows up in his weekly status report. `work-hours` is a
*work* metric (unlike sleep/energy), so it belongs in the report — but metric readings live in
`Metrics.md`, which the weekly and perf reports were deliberately built **never to read** (so
health/personal metrics could not leak into a work draft).

The ask reverses that separation, on purpose. Rob's decision: **surface all metrics in the
reports and curate by hand** rather than build a filter — the reports are drafts he reviews and
trims before any use, so a clearly-marked, trim-ready section is enough.

## Decisions (from brainstorming)

- **`work-hours` needs no capture code.** Any metric name already works
  (`/worklog:metric work-hours 8`). "Adding it" = documenting it as a recommended KPI.
- **Both** `/worklog:weekly-report` **and** `/worklog:perf-review` gain a metrics section (Rob
  chose to include perf-review, not just weekly).
- The section is a **clearly-marked "## Metrics (curate before sharing)" block**, easy to trim or
  delete wholesale — not woven into the prose.
- Each metric is summarized as **total + daily average** over the report's range
  (e.g. `work-hours: 42.5 total over 5 days, 8.5/day`).
- **All** metrics are included; Rob curates which belong in a given report. No allowlist, no
  naming convention, no per-metric config (YAGNI).

## The separation reversal (recorded on purpose)

The metrics feature's original guarantee — "the work weekly/perf reports never read `Metrics.md`"
— is **retired** by this change. Both reports now read `Metrics.md`. This is safe because:

- The reports are **drafts written into the vault, never sent** (unchanged).
- Metrics land in a **clearly-delimited section explicitly labelled to curate before sharing**, so
  anything personal is trivially trimmed before the draft is used.
- Rob owns the data and made this call knowingly.

`Metrics.md` remains a **separate file** from `Worklog.md`; only the *report-drafting* steps now
read both. The capture paths (`/worklog:log`, `/worklog:metric`) are unchanged.

## Shape

Small. One tiny code change plus SKILL/command/doc edits — no new commands, no new store.

- `plugins/worklog/bin/worklog.py` — add a `total` field to the existing `summarize()`.
- `plugins/worklog/skills/worklog/SKILL.md` — the "Weekly report" and "Performance review" steps
  each gain a metrics-section step; the "Metrics" section notes `work-hours` as a recommended KPI.
- `plugins/worklog/commands/weekly-report.md`, `perf-review.md` — descriptions mention the metrics
  section (optional polish; no behavior lives in command files).
- `CLAUDE.md`, `README.md` — note that the reports now surface `Metrics.md` (curate before sharing).

No `plugin.json` change (no new command); no config change.

## `bin/worklog.py` change

Add `total` to `summarize()` so the reports can show a sum alongside the average:

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

- `total` is the sum of the range's readings. For additive metrics (`work-hours`) it is the
  headline number; for rating metrics (`energy`) it is inert and the SKILL prose leans on `avg` —
  the field always exists, the prose chooses what to show.
- The existing `_cmd_metrics` JSON already embeds `summarize()`'s output, so `total` flows to both
  the standalone `/worklog:metrics` report and the new report sections with no CLI change.

The existing `test_summarize` / `test_summarize_single_value` assertions are updated to include
`total` (single-value: `total == that value`).

## Report sections (SKILL-driven)

Both report steps, after building their existing Worklog-based content, run:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/bin/worklog.py" metrics --since <D> --until <D>
```

(weekly → the current week; perf-review → the current quarter) and append:

```markdown
## Metrics (curate before sharing)

- work-hours: 42.5 total over 5 days, 8.5/day avg
- focus-hours: 21.0 total over 5 days, 4.2/day avg
- energy: 4.0/day avg (min 3, max 5)
```

- Each metric with readings in range gets one line: total + daily average (count = days with a
  reading). A rating-style metric may show avg (+ min–max) and omit the total — the prose decides.
- The header text tells Rob to trim it. **If there are no readings in range, omit the whole
  section** (don't emit an empty "Metrics" block) — consistent with the existing "no metrics in
  range, never fabricate" rule.
- The section is always the **last** block of the draft, so it is easy to delete in one stroke.

## Error handling / edge cases

- **No metrics in range** → the section is omitted entirely (no empty header).
- **A metric read once in range** → total = that value, "1 day, X/day"; no divide-by-zero
  (`summarize` is only called on non-empty series).
- **Metrics never auto-sent** → unchanged; reports remain vault-only drafts.
- **Capture paths unchanged** → `/worklog:log` and `/worklog:metric` behave exactly as before.

## Testing strategy

- Unit: `summarize()` now returns `total`; update `test_summarize` and `test_summarize_single_value`
  to assert it (single-value → `total` equals the reading). No other pure function changes.
- The report *prose* (both sections) is SKILL-driven, validated by `claude plugin validate` and by
  reading a drafted report against a synthetic `Metrics.md`; the numeric substrate (`summarize`,
  `metric_series`, `count_events`) is already unit-tested.

## Scope

**In:** `total` on `summarize()`; a "Metrics (curate before sharing)" section in the weekly and
perf reports; `work-hours` documented as a recommended KPI; docs updated for the reversal.
**Out:** any per-metric allowlist/filter/config; changes to capture; a new command or store;
`meeting-hours` calendar pull and the Friday scheduled run (still deferred work-laptop follow-ons).

## Workflow

Issue #48 → branch `48-work-hours-metric-surfaced-in-the-weekly-report` → spec, plan, build on the
one branch → PR to `main`.
