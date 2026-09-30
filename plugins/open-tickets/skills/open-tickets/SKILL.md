---
name: open-tickets
description: Use to summarize a user's currently-open Jira tickets, personal GitLab tracker issues, and the MRs they are reviewing as a table, especially to surface what each one is blocked on and what the next step is. Triggers on "summarize my open tickets", "ticket status", "what am I blocked on", "waiting-on breakdown".
---

# Open Tickets

Summarize the user's open Jira tickets, open issues from their personal GitLab tracker
(`rob-tracker`), **and** the open MRs they are a reviewer on, as a single table with
**ID, Description, Blocker, Next Steps** columns — one row per ticket/issue/review. The point
is surfacing what's actually stalled waiting on someone else versus what's moving, since a
normal Jira board (or a personal kanban) doesn't distinguish the two.

A helper at `${CLAUDE_PLUGIN_ROOT}/bin/open_tickets.py` (run with `python3`) fetches/normalizes
the raw data; synthesizing Blocker/Next Steps from it is a judgment call and stays with the
agent, not the script.

## Fetching the data

**Jira:**

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

**Personal GitLab tracker (`rob-tracker`):**

```bash
glab api "/projects/rsartin%2Frob-tracker/issues?state=opened&per_page=100" \
  | python3 "${CLAUDE_PLUGIN_ROOT}/bin/open_tickets.py" parse-gitlab-issues
```

`rob-tracker` is a personal to-do/kanban board kept as GitLab issues (labels like `next`/
`someday` stand in for board columns). This never shells out to `glab` itself — same reasoning as
the `worklog` plugin's `parse-gitlab`: `glab` is already authed to its default host, and the
target project stays in the documented command rather than hardcoded in the script. Skip this
source silently if `glab` isn't installed or the call errors (a missing tool shouldn't block the
Jira half of the table).

**MRs you are reviewing (GitLab):**

```bash
glab api "/merge_requests?reviewer_username=<your-gitlab-username>&state=opened&scope=all&per_page=100" \
  | python3 "${CLAUDE_PLUGIN_ROOT}/bin/open_tickets.py" parse-gitlab-reviews
```

Get the username once with `glab api user` (read `.username`) and reuse it, rather than asking the
user. `reviewer_username` is what finds these: `scope=assigned_to_me` covers MRs you're *assigned*,
not ones you're asked to review. Each MR is keyed by the first Jira key in its title (MR titles lead
with their ticket, e.g. `ABC-123: ...`), falling back to the MR reference, so the review lines up
with the ticket it belongs to even though that ticket is usually assigned to someone else. If a key
also appears in the Jira fetch (you're reviewing an MR on your own ticket), keep the Jira row and
skip the review row. Skip this source silently on any error, same as `rob-tracker`.

For a review row, read the MR's unresolved discussions when you need them to fill in Blocker/Next
Steps: `comments` is empty for reviews, and the MR (not the ticket) is where the current state lives.
The usual shape is "waiting on the author to address your comments" or "ready for your approval".

All three commands print a JSON array in the same shape, one object per open item:

```json
{"key": "ABC-123", "summary": "...", "status": "In Progress",
 "description": "...", "comments": [{"author": "...", "body": "..."}, ...],
 "updated": "2026-09-20T12:00:00.000-0500"}
```

`comments` holds only the most recent handful (oldest of that tail first) for Jira — enough to
see the latest disposition without dragging in a ticket's entire history; it's always empty for
`rob-tracker` issues, which don't carry discussion threads (their `description` is kept current
by editing it, or the issue is just closed). `updated` is sort-only plumbing, not a table column —
use it to interleave the three sources by recency into one fetch-order list before building the
table.

## Building the table

For each ticket/issue, read `description` and `comments` (comments carry the *current* state —
later comments override the original description) and fill in:

- **ID** — the key, e.g. `ABC-123`.
- **Description** — one line: what the ticket is about.
- **Blocker** — what's stopping progress right now, and who/what it's waiting on (a person, a
  team, another ticket, a system access request). If nothing external is blocking it, say `—`
  (actively being worked) rather than inventing a blocker.
- **Next Steps** — the concrete next action, and who owns it (the user, or whoever they're
  waiting on).

Render as a single markdown table combining all three sources, most-recently-updated first (sort the
merged list by each item's `updated` field, descending). If every fetch returned nothing (no
access, or no open items), say so plainly instead of showing an empty table.

## Quick reference

| Symptom | Cause | Fix |
| --- | --- | --- |
| Empty `[]` with a stderr note | Missing `$JIRA_API_TOKEN` or unconfigured `jira` CLI | Tell the user to set `JIRA_API_TOKEN`, or run whatever configures `~/.config/.jira/.config.yml` on their machine |
| `parse-gitlab-issues` prints `[]` with a stderr note | `glab` not installed, not authed to the right host, or the project moved | Tell the user; the Jira half of the table still renders |
| Ticket shows a blocker that's since been resolved | A later comment supersedes an earlier one | Always weight the most recent comment over the description or earlier comments |
| Table has a `—` in Blocker | Ticket isn't stuck on anything external | Correct — don't force a blocker where the ticket is just in normal progress |
