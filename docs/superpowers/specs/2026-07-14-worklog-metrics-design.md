# worklog metrics — KPI capture + trend report

Date: 2026-07-14
Issue: robsartin/claude-config#46
Related: `docs/superpowers/specs/2026-07-13-worklog-reports-design.md` (the event-log half)

## Problem

worklog records *events* (`started`/`shipped`/`note`) that flow into weekly/perf reports. Rob
also wants to track **KPIs** — numeric readings over time (focus-hours, sleep, energy, and
derived counts like how much he mentors) — and see their **trend**. That is a different data
shape: a metric name with a numeric value on a date, tracked for direction, not a one-off event.

It must also stay **separate from the work event log**: health metrics should never leak into a
work perf-review draft, and metrics need their own numeric parsing.

## Decisions (from brainstorming)

- **Separate store**, `<vault>/Metrics.md`, never read by the work weekly/perf reports.
- **Dedicated capture command** `/worklog:metric`, with **upsert-per-day** semantics (a metric is
  a reading, not an event).
- **`help` becomes a worklog event type**, so mentoring/assists are both perf-review records and
  the source of a derived KPI.
- **The metrics report is pure** — it reads only `Metrics.md` (series) and `Worklog.md` (derived
  counts), needing no `jira`/`glab`. Calendar-pulled `meeting-hours` and the true cross-project
  `prs-merged` are deferred.
- **Drafts to the vault**, never sent (like the weekly report).

## Shape

All of this extends the existing `worklog` plugin — new helpers in `bin/worklog.py`, a new
command file, and a SKILL section. No new plugin.

- `plugins/worklog/bin/worklog.py` — new pure functions + `metric` / `metrics` CLI subcommands.
- `plugins/worklog/commands/metric.md` → `/worklog:metric`.
- `plugins/worklog/skills/worklog/SKILL.md` → a "Metrics" section (capture + the report).
- `plugins/worklog/.claude-plugin/plugin.json` → register the new command.

## Storage & format

`<vaultPath>/<metricsFile>` — default `~/Obsidian/Metrics.md`. Same date-grouped shape as
`Worklog.md`, newest day on top, one reading per line:

```markdown
## 2026-07-14
- focus-hours: 4.5
- sleep-hours: 7.2
- energy: 4

## 2026-07-13
- focus-hours: 3.0
- sleep-hours: 6.5
- energy: 3
```

- A reading line is `- <name>: <number>`. `name` is a slug (letters, digits, hyphens).
- **Value is numeric.** A trailing unit is accepted on input (`7.2h`, `4.5`) and the leading
  number is stored bare (`7.2`, `4.5`); a value with no parseable number is rejected.
- **Upsert per day**: writing a metric that already has a line under today's heading **replaces**
  its value (you don't want two `sleep-hours` for one day). Different metrics on the same day
  accumulate under that day.

## Capture — `/worklog:metric`

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/bin/worklog.py" metric <name> <value> [--date YYYY-MM-DD]
```

- Rejects a non-numeric value with a clear message (exit non-zero), writing nothing.
- Rejects an invalid `--date` (must be ISO), like `log` does.
- Missing vault dir → the same "configure `worklog.vaultPath`" message `log` gives; never creates
  a vault in a surprising place.
- Reports the stored reading (`metric: focus-hours = 4.5 on 2026-07-14`).

`help` events use the existing `/worklog:log`, once `help` is added to the default `types`:
`/worklog:log help "Unblocked Dana on the Zuora gateway onboarding"`.

## Report — `/worklog:metrics`

`/worklog:metrics [since..until]` (default: the current week). It:

1. Reads `Metrics.md`, building a series per metric over the range.
2. Reads `Worklog.md` for the **derived** KPIs (no external tools):
   - **help-count** — number of `help` entries in range.
   - **prs-merged** — number of `shipped` entries in range (a clean local proxy; the true
     cross-project count via the Jira/GitLab factual pull is a later enhancement).
3. For each numeric metric, computes latest, average, min, max, count, and a unicode sparkline
   (`▁▂▃▄▅▆▇█`, scaled min→max over the series).
4. Drafts the report into `<vaultPath>/<reportsDir>/Metrics-<YYYY>-W<ww>.md` for Rob to read —
   never sent. An empty range says "no metrics in <range>", never invents readings.

The pure core (`metric_series`, `summarize`, `sparkline`, the two count derivations) returns
structured data; SKILL.md turns it into the drafted prose.

## `bin/worklog.py` — new functions

- `format_metric(name, value) -> str` → `- <name>: <value>`.
- `parse_metric_value(raw) -> float | None` → leading number of `raw` (`"7.2h"` → `7.2`),
  `None` if unparseable.
- `upsert_metric(content, date, name, value) -> str` → insert-or-replace `- <name>: <value>`
  under the `## <date>` heading (newest-day-on-top; reuses the `_parse_days`/`_render_days`
  machinery, replacing an existing same-name line rather than appending).
- `parse_metrics(content) -> list[{date, name, value}]`.
- `metric_series(content, since, until) -> dict[name -> list[(date, value)]]` (inclusive range).
- `summarize(series) -> {latest, avg, min, max, count}`.
- `sparkline(values) -> str`.
- `count_events(worklog_content, type_, since, until) -> int` — used for help-count and the
  shipped-based prs-merged.
- CLI: `metric <name> <value> [--date]` and `metrics --since <D> --until <D>` (prints the series
  + derived counts + summaries as JSON for the SKILL to render).

## Config

- `worklog.metricsFile` (default `Metrics.md`) — added to `DEFAULTS`.
- `help` added to the default `types` list (`started`, `shipped`, `note`, `help`).

No other config. Nothing work-specific; the store is machine-local like the rest of the vault.

## Error handling / edge cases

- **Non-numeric value** → reject, write nothing, clear message.
- **Invalid `--date`** → reject (ISO only), matching `log`.
- **Missing vault dir** → the `log`-style "configure vaultPath" message; never create a vault.
- **Upsert idempotency** → same metric + day twice = one line, latest value; verified by test.
- **Empty range in the report** → "no metrics in <range>", never fabricate.
- **A metric logged once** → its sparkline is a single bar; average = that value (no divide-by-zero).
- **Metrics never enter the work weekly/perf reports** — those read only `Worklog.md`; `Metrics.md`
  is a distinct file they don't touch.

## Testing strategy

Everything new is pure and unit-tested with synthetic fixtures:

- `parse_metric_value` (bare number, trailing unit, non-numeric → None).
- `upsert_metric` (creates heading; newest-day-on-top; replaces same-name same-day; accumulates
  different names same-day).
- `parse_metrics` / `metric_series` (range inclusivity, multiple metrics).
- `summarize` (latest/avg/min/max/count; single-value series).
- `sparkline` (flat series, ascending series, single value).
- `count_events` (help-count and shipped-count over a range).
- The CLI `metric` upsert end-to-end against a temp vault (mirrors the existing `log` e2e test).

Report *prose* generation is SKILL-driven and validated by `claude plugin validate` + reading it;
the numeric substrate is fully covered by the unit tests above.

## Scope

**In:** `Metrics.md` store, `/worklog:metric` (upsert), the `help` type, the `/worklog:metrics`
report with numeric series + derived help-count/prs-merged, config keys, and the pure functions.
**Out:** calendar-pulled `meeting-hours`; the Friday-night scheduled run; the true cross-project
`prs-merged` via the Jira/GitLab factual pull. These are work-laptop follow-ons.

## Workflow

Issue #46 → branch `46-worklog-metrics` → spec, plan, build on the one branch → PR to `main`.
