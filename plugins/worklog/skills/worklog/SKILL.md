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
   Do not send or post it. Professional register — do not use the personal `voice` skill, and do not include anything not present in the pulled entries.

## Performance review

Same shape, longer horizon (default the current quarter, or an explicit range). Synthesize
accomplishments, recurring themes, scope/impact, and collaboration into a narrative, shaped by
`worklog.perfTemplate` if present. Draft only, into the vault. Professional register — do not
use the personal `voice` skill, and do not claim work that isn't in the log.
