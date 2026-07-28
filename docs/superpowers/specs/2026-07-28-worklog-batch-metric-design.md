# worklog: batch metric entry

Date: 2026-07-28
Issue: robsartin/claude-config#50
Related: `docs/superpowers/specs/2026-07-14-worklog-metrics-design.md` (the metric command this extends)

## Problem

Recording a day's KPIs takes one command per metric — `/worklog:metric work-hours 8`, then
`/worklog:metric focus-hours 4.5`, then `/worklog:metric energy 4`. Rob wants to enter a whole
day's readings in one line.

## Decisions (from brainstorming)

- **Syntax: `name=value` tokens.** `/worklog:metric work-hours=8 focus-hours=4.5 energy=4`.
  Order-free and unambiguous.
- **The legacy single form keeps working:** `/worklog:metric work-hours 8` (two positional
  tokens, no `=`) is still accepted, so nothing that works today breaks.
- **Atomic batch.** If any token is malformed or its value is non-numeric, **reject the whole
  batch, write nothing**, and report the offending token — no half-recorded day. This preserves
  the existing "reject writes nothing" contract.
- **One shared `--date`** across the batch; per-metric **upsert-per-day** is unchanged (each pair
  replaces that metric's reading for the day).
- **Scope: metrics only.** The event log (`/worklog:log`) is untouched.

## Shape

Extends the existing `metric` CLI subcommand and its command file. No new command, no new store.

- `plugins/worklog/bin/worklog.py` — a pure `parse_metric_pairs(tokens)` helper + a multi-pair
  `_cmd_metric`.
- `plugins/worklog/skills/worklog/SKILL.md` — the "Record a reading" step shows the batch form.
- `plugins/worklog/commands/metric.md` — the `argument-hint` and body mention batch entry.

No `plugin.json` change (same command), no config change.

## Token grammar & parsing

A new pure function decides how the positional tokens are interpreted and validates them, so the
whole rule set is unit-testable:

```
parse_metric_pairs(tokens) -> list[(name, value_float)]   # raises ValueError on any bad input
```

- **Empty** `tokens` → `ValueError("no metrics given")`.
- **Batch form** — *every* token contains `=`: split each on the **first** `=` into
  `name`, `raw`. `name` must match `^[\w-]+$` (the metric-name slug); `raw` must parse via the
  existing `parse_metric_value` (leading number, trailing unit allowed) to a non-`None` float.
- **Legacy single form** — exactly **two** tokens and **neither** contains `=`: `tokens[0]` is the
  name (same slug rule), `tokens[1]` the value (same `parse_metric_value`).
- **Anything else** (a mix of `=` and non-`=` tokens, a single bare token, three bare tokens) →
  `ValueError` with a message pointing at the `name=value` form, e.g.
  `"use name=value tokens, e.g. work-hours=8 focus-hours=4.5"`.
- On a bad value or bad name inside an otherwise well-formed batch, the `ValueError` **names the
  offending token** (`"'lots' in 'focus-hours=lots' is not numeric"`), so the whole line can be
  corrected and re-entered.
- **Duplicate names in one batch** (`work-hours=8 work-hours=9`) are allowed; upsert applies them
  in order so the last wins — consistent with same-day upsert. (Not worth rejecting.)

The function raises **before** any I/O; `_cmd_metric` catches `ValueError`, prints the message to
stderr, and returns non-zero **without touching the file** — the atomic guarantee.

## `_cmd_metric` behaviour

```
metric <name=value> [<name=value> ...] [--date YYYY-MM-DD]
metric <name> <value> [--date YYYY-MM-DD]     # legacy single, still valid
```

1. Split off `--date` (validated ISO exactly as today); the rest are the positional tokens.
2. `pairs = parse_metric_pairs(tokens)` — on `ValueError`, print it to stderr, return 2, write
   nothing.
3. Resolve the vault path; missing vault dir → the same "configure `worklog.vaultPath`" message
   and `return 1` as today (checked before any write).
4. Read `Metrics.md` once, `upsert_metric` each pair in order into the content (integral values
   stored bare, e.g. `energy: 4`, exactly as today), write once.
5. Print one confirmation line listing every stored reading and the date, e.g.
   `metric: work-hours=8, focus-hours=4.5, energy=4 on 2026-07-28`.

Nothing about a single-metric call changes from a user's point of view; the batch path is a strict
superset.

## Error handling / edge cases

- **Any bad token** → whole batch rejected, file untouched, offending token named. (atomic)
- **Empty / all-`--date` invocation** (no metrics) → the "no metrics given" / usage error, non-zero.
- **Invalid `--date`** → the existing ISO error, non-zero.
- **Missing vault dir** → the existing configure-vaultPath error, `return 1`, before any write.
- **Legacy `metric name value`** → unchanged behaviour.
- **`=` inside a value** (`ratio=3=4`) → split on the **first** `=` only, so name=`ratio`,
  raw=`3=4`; `parse_metric_value("3=4")` reads the leading `3` (documented "leading number"
  semantics) — acceptable, not an error.

## Testing strategy

- `parse_metric_pairs` (pure, the core): batch of several pairs; single legacy pair; trailing unit
  in a batch value (`sleep-hours=7.2h` → `7.2`); a non-numeric value in a batch → `ValueError`
  naming the token; a bad name (`=8`, `foo bar=1`) → `ValueError`; a mixed form
  (`a=1 b 2`) → `ValueError`; empty → `ValueError`; duplicate name → last wins.
- CLI `_cmd_metric` end-to-end against a temp vault: a 3-metric batch writes all three under one
  day with one call; a batch containing one bad token writes **nothing** (file absent/unchanged)
  and returns non-zero; the legacy single form still works; integral values stored bare.
- All existing metric/metrics tests continue to pass unchanged.

## Scope

**In:** batch `name=value` entry on `/worklog:metric` (atomic, shared `--date`), the legacy single
form preserved, `parse_metric_pairs`, and the doc/command updates.
**Out:** batching the event log; a new command; any config; changes to the metrics report or the
report sections.

## Workflow

Issue #50 → branch `50-batch-metric-entry` → spec, plan, build on the one branch → PR to `main`.
