---
name: open-tickets
description: Use to summarize a user's currently-open Jira tickets as a table, especially to surface what each one is blocked on and what the next step is. Triggers on "summarize my open tickets", "ticket status", "what am I blocked on", "waiting-on breakdown".
---

# Open Tickets

Summarize the user's open Jira tickets as a table with **ID, Description, Blocker, Next Steps**
columns — one row per ticket. The point is surfacing what's actually stalled waiting on someone
else versus what's moving, since a normal Jira board doesn't distinguish the two.

A helper at `${CLAUDE_PLUGIN_ROOT}/bin/open_tickets.py` (run with `python3`) fetches the raw
data; synthesizing Blocker/Next Steps from it is a judgment call and stays with the agent, not
the script.

## Fetching the data

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/bin/open_tickets.py" fetch
```

Reads `server`/`login` from the `jira` CLI's own config (`~/.config/.jira/.config.yml`) and the
token from `$JIRA_API_TOKEN` — machine-local, so no host or account ever lands in this repo. It
talks to the Jira Cloud REST API directly rather than shelling out to the `jira` CLI, because that
CLI silently scopes `-q`/`--jql` searches to its one configured default project — a cross-project
JQL comes back empty with no error, which would hide most of a user's actual work. Missing config,
missing token, or a network/auth failure all print `[]` and a one-line note on stderr and exit 0.
Use `--user` to pass a different JQL assignee expression (default `currentUser()`).

Output is a JSON array, one object per open (`statusCategory != Done`) ticket assigned to the
user, sorted by most-recently-updated:

```json
{"key": "ABC-123", "summary": "...", "status": "In Progress",
 "description": "...", "comments": [{"author": "...", "body": "..."}, ...]}
```

`comments` holds only the most recent handful (oldest of that tail first) — enough to see the
latest disposition without dragging in a ticket's entire history.

## Building the table

For each ticket, read `description` and `comments` (comments carry the *current* state — later
comments override the original description) and fill in:

- **ID** — the key, e.g. `ABC-123`.
- **Description** — one line: what the ticket is about.
- **Blocker** — what's stopping progress right now, and who/what it's waiting on (a person, a
  team, another ticket, a system access request). If nothing external is blocking it, say `—`
  (actively being worked) rather than inventing a blocker.
- **Next Steps** — the concrete next action, and who owns it (the user, or whoever they're
  waiting on).

Render as a single markdown table, most-recently-updated first (the fetch order). If the fetch
returned nothing (no access, or no open tickets), say so plainly instead of showing an empty
table.

## Quick reference

| Symptom | Cause | Fix |
| --- | --- | --- |
| Empty `[]` with a stderr note | Missing `$JIRA_API_TOKEN` or unconfigured `jira` CLI | Tell the user to set `JIRA_API_TOKEN`, or run whatever configures `~/.config/.jira/.config.yml` on their machine |
| Ticket shows a blocker that's since been resolved | A later comment supersedes an earlier one | Always weight the most recent comment over the description or earlier comments |
| Table has a `—` in Blocker | Ticket isn't stuck on anything external | Correct — don't force a blocker where the ticket is just in normal progress |
