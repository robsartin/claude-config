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

## Performance review

Same shape, longer horizon (default the current quarter, or an explicit range) — pull the
hand-logged entries and, if available, the **Factual pull** spine for the range, merged the same
way. Synthesize accomplishments, recurring themes, scope/impact, and collaboration into a
narrative, shaped by `worklog.perfTemplate` if present. Draft only, into the vault. Professional
register — do not use the personal `voice` skill, and do not claim work that isn't in the log.
