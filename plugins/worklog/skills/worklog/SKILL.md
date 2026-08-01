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

## Factual pull (optional — work environments)

When `jira`/`glab` are installed (a work setup), augment the hand-logged notes with an
authoritative "shipped" spine — tickets you resolved and MRs you merged in the range. This
catches work that never got hand-logged. Skip silently if the tools aren't available; the
reports still work from `Worklog.md` alone.

```bash
# Jira tickets you touched in the range (use a plain date, not -14d, which parses as flags).
# Scoped to your Jira config's default project; for cross-project use --jql instead.
jira issue list -a"$(jira me)" --updated-after <SINCE> --raw \
  | python3 "${CLAUDE_PLUGIN_ROOT}/bin/worklog.py" parse-jira
# GitLab MRs you merged in the range, across projects on your work GitLab host.
# glab must be authed to that host (its default). For a self-hosted instance, either make it
# glab's default host or add `--hostname <your-gitlab-host>` to the call.
glab api "/merge_requests?scope=created_by_me&state=merged&updated_after=<SINCE>T00:00:00Z&per_page=100" \
  | python3 "${CLAUDE_PLUGIN_ROOT}/bin/worklog.py" parse-gitlab
```

Cross-project Jira alternative:
`jira issue list --jql "assignee = currentUser() AND updated >= '<SINCE>'" --raw | … parse-jira`.

Both emit normalized `{date, type: "shipped", ref, text}` entries. If a `ref` from the pull
already appears in the hand-logged entries, prefer the hand-logged one (it has your context) and
drop the duplicate. Everything is still factual — the pull never invents activity.

## Weekly report

1. Resolve the range: default is the current week (Mon–today) unless the user gives one.
2. Pull the hand-logged entries:
   `python3 "${CLAUDE_PLUGIN_ROOT}/bin/worklog.py" entries --since <YYYY-MM-DD> --until <YYYY-MM-DD>`
   Then, if `jira`/`glab` are available, run the **Factual pull** above for the same range and
   merge (dedup by `ref`, hand-logged wins).
3. Draft a report from ONLY those entries — group by ticket/theme, lead with shipped work.
   Use the `worklog.weeklyTemplate` from config as the format if present; otherwise a simple
   "Shipped / In progress / Notes" structure. If there's nothing in range, say "nothing logged in
   <range>" — never invent activity.
4. Write the draft to `<vaultPath>/<reportsDir>/Weekly-<YYYY>-W<ww>.md` for the user to edit.
   Do not send or post it. Professional register — do not use the personal `voice` skill, and do not include anything not present in the pulled entries.
5. Append the **Report metrics section** (see Metrics below) as the last block of the draft, for
   the same range. Omit it if there are no readings in range.

## Performance review

Same shape, longer horizon (default the current quarter, or an explicit range) — pull the
hand-logged entries and, if available, the **Factual pull** spine for the range, merged the same
way. Synthesize accomplishments, recurring themes, scope/impact, and collaboration into a
narrative, shaped by `worklog.perfTemplate` if present. Draft only, into the vault. Professional
register — do not use the personal `voice` skill, and do not claim work that isn't in the log.

Finally, append the **Report metrics section** (see Metrics below) as the last block, for the
review's range — omitting it if there are no readings.

## Metrics (KPIs)

Numeric readings tracked for their **trend** live in a separate file, `Metrics.md`
(`worklog.metricsFile`), kept apart from the `Worklog.md` event log. The weekly report and the
perf-review each end with a **Metrics (curate before sharing)** block built from these readings —
a section you trim before using the draft, so anything personal is easy to drop and nothing is
ever auto-sent.

### Record a reading

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/bin/worklog.py" metric <name=value> [<name=value> ...] [--date YYYY-MM-DD]
# one reading, or a whole day at once:
python3 "${CLAUDE_PLUGIN_ROOT}/bin/worklog.py" metric work-hours=8 sleep-hours=7.2 energy=4
```

e.g. `metric work-hours 8`, `metric sleep-hours 7.2`, `metric energy 4`
(`work-hours` is a good work KPI to surface in the reports). The value must be
numeric (a trailing unit like `7.2h` is fine — the number is kept). Re-recording the same metric
on the same day **replaces** it (a reading, not an event). Mentoring/assists are logged as
`help` events instead — `python3 "${CLAUDE_PLUGIN_ROOT}/bin/worklog.py" log help "<what>"` — so
they double as perf-review records. Pass several `name=value` tokens to record a whole day in one
call; if any token is malformed or non-numeric the **whole batch is rejected** and nothing is
written, so a corrected line can be re-entered. The bare `metric <name> <value>` form still works
for a single reading.

### Metrics report

1. Resolve the range (default the current week).
2. Pull the structured data:
   `python3 "${CLAUDE_PLUGIN_ROOT}/bin/worklog.py" metrics --since <D> --until <D>`
   It returns each metric's points, a `summary` (latest / total / avg / min / max / count), and a
   `sparkline`, plus `derived` counts: `help-count` (logged `help` events) and `prs-merged`
   (logged `shipped` events — a local proxy until the Jira/GitLab factual pull is wired in).
3. Draft a report from ONLY that data — a table (one row per metric) plus the derived counts:

   ```markdown
   | Metric | Total | Daily avg | Trend |
   | --- | --- | --- | --- |
   | work-hours | 42.5h | 8.5 | ▁▃▅▇ |
   | sleep-hours | 49.0h | 7.0 | ▅▄▆▇ |
   | energy | — | 4.0 | ▃▄▅ |

   Derived: help-count 3, prs-merged 2
   ```

   **Total column rule:** fill Total only for metrics whose name ends in `-hours` (show
   `summary.total` with an `h` suffix, e.g. `42.5h`); every other metric shows a dash (`—`). Daily
   avg is `summary.avg`; Trend is the metric's `sparkline`. If the range is empty, say
   "no metrics in <range>"; never invent readings.
4. Write the draft to `<vaultPath>/<reportsDir>/Metrics-<YYYY>-W<ww>.md` for the user to read.
   Do not send it. Professional, factual — do not use the personal `voice` skill.

### Report metrics section (weekly & perf)

Both the weekly report and the performance review end with a metrics block, for the **same range
as the report**:

1. Pull the data: `python3 "${CLAUDE_PLUGIN_ROOT}/bin/worklog.py" metrics --since <D> --until <D>`.
2. If no metric has readings in range, **omit the section entirely** — no empty header.
3. Otherwise append it as the **last** block of the draft:

```markdown
## Metrics (curate before sharing)

| Metric | Total | Daily avg |
| --- | --- | --- |
| work-hours | 42.5h | 8.5 |
| sleep-hours | 49.0h | 7.0 |
| energy | — | 4.0 |
```

One row per metric with readings in range. **Total column rule:** fill Total only for metrics
whose name ends in `-hours` (show `summary.total` with an `h` suffix, e.g. `42.5h`); every other
metric shows a dash (`—`). Daily avg is `summary.avg`. The header tells the reader to trim it
before sharing; never fabricate readings.
