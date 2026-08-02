# worklog: metrics tables with a Total column

Date: 2026-07-28
Issue: robsartin/claude-config#52
Related: `docs/superpowers/specs/2026-07-14-worklog-metrics-design.md` (standalone report),
`docs/superpowers/specs/2026-07-27-worklog-metrics-in-reports-design.md` (the report sections)

## Problem

The metric summaries render as a bullet list with total + daily average mixed into prose. Rob
wants a clearer **table with a Total column**, where Total is meaningful only for hours-style
metrics — and wants `focus-hours` dropped from the recommended set (not helpful).

## Decisions (from brainstorming)

- **Table format** (markdown), applied to **both** metric surfaces: the standalone
  `/worklog:metrics` report *and* the weekly/perf "Metrics (curate before sharing)" section.
- **Total column filled only for `-hours` metrics** — a name-based rule: a metric's Total cell is
  filled iff its name ends in `-hours` (`work-hours`, `sleep-hours`, `meeting-hours`, …). Every
  other metric (e.g. `energy`) shows a dash (`—`). Daily-average column is shown for all.
- **Drop `focus-hours`** from the recommended-KPI examples.

## Doc-only

No Python change. `summarize()` already returns `total` (PR #49), and `_cmd_metrics` already emits
per-metric `summary` (with `total`), `sparkline`, and `derived` counts as JSON (PR #47). All the
data the tables need already flows through the CLI; this change only reshapes the SKILL's
rendering instructions and the examples in the docs. No new command, no config, no code, no new
tests.

## The `-hours` rule

For each metric in the table:
- **Total cell** — if the metric **name ends in `-hours`**, show `summary.total` with an `h`
  suffix (e.g. `42.5h`); otherwise show `—`. (Bare numbers are stored; the `h` is display-only.)
- **Daily avg cell** — always `summary.avg` (the metric's per-day mean over the range).

The rule is name-based and predictable: name a metric `<x>-hours` to have it summed. It lives as a
one-line instruction in the shared table spec, applied identically in both surfaces.

## Table shapes

### Report metrics section (weekly & perf)

```markdown
## Metrics (curate before sharing)

| Metric | Total | Daily avg |
| --- | --- | --- |
| work-hours | 42.5h | 8.5 |
| sleep-hours | 49.0h | 7.0 |
| energy | — | 4.0 |
```

- One row per metric with readings in range. Omit the whole section when there are no readings
  (unchanged). The header still tells the reader to curate before sharing; it is still the **last**
  block of the draft.

### Standalone `/worklog:metrics` report

Same table plus a **Trend** column (the existing sparkline), with the derived counts below it:

```markdown
| Metric | Total | Daily avg | Trend |
| --- | --- | --- | --- |
| work-hours | 42.5h | 8.5 | ▁▃▅▇ |
| sleep-hours | 49.0h | 7.0 | ▅▄▆▇ |
| energy | — | 4.0 | ▃▄▅ |

Derived: help-count 3, prs-merged 2
```

- Empty range → "no metrics in <range>" (unchanged). Never fabricate readings.

## Dropping `focus-hours`

`focus-hours` is only ever **example text** — there is no enforced metric registry — so "dropping"
it means removing it from the recommended examples:

- In "### Record a reading", the example line and the one-shot batch example no longer mention
  `focus-hours` (use `work-hours`, `sleep-hours`, `energy`).
- In `CLAUDE.md` / `README.md`, the KPI examples no longer list focus hours.
- **Existing `focus-hours` readings in a user's `Metrics.md` are their data and are untouched** —
  the reports still render whatever metrics are present; Rob simply stops logging it.
- **Test fixtures that use `focus-hours` as a synthetic metric name are left as-is** — they are
  arbitrary placeholder names exercising the parser/report, not user-facing recommendations, and
  renaming them would be churn with no functional value.

## Files

- `plugins/worklog/skills/worklog/SKILL.md` — reshape the "### Metrics report" step 3 and the
  "### Report metrics section" example into the tables above (with the `-hours` rule); drop
  `focus-hours` from "### Record a reading".
- `plugins/worklog/commands/metric.md`, `metrics.md` — only if they name `focus-hours` (they do
  not currently); otherwise untouched.
- `CLAUDE.md`, `README.md` — drop `focus-hours` from the KPI examples; a metrics summary now reads
  as a table with a Total column for `-hours` metrics.

## Testing strategy

No code changes, so no new unit tests. Verification is `claude plugin validate plugins/worklog`
(passes with only the no-version warning) plus reading a rendered table against a synthetic
`Metrics.md` via `worklog.py metrics --since --until` — confirming the JSON carries `total` (for a
`-hours` metric) and `avg`/`sparkline` for the table cells, and that a non-`-hours` metric's Total
would be a dash under the rule. The existing metric/metrics tests continue to pass unchanged.

## Scope

**In:** table rendering (both surfaces) with a Total column governed by the `-hours` name rule;
dropping `focus-hours` from recommended examples; doc updates.
**Out:** any Python/CLI/config change; a new metric registry or per-metric aggregation config;
touching users' existing data or the test fixtures' placeholder names.

## Workflow

Issue #52 → branch `52-metrics-tables-total-column` → spec, plan, build on the one branch → PR to
`main`.
