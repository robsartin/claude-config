# worklog + report skills

Date: 2026-07-13
Issue: robsartin/claude-config#18
Related: `docs/superpowers/specs/2026-07-13-start-work-design.md` (start-work is a feeder)

## Problem

Rob needs to produce **weekly status reports** and periodic **performance-review** write-ups
about his work. Reconstructing "what did I do" from memory (or scraping tickets after the
fact) is lossy — the context, the off-ticket help, and the wins that never became tickets are
exactly what a good report needs, and they evaporate.

`worklog` captures work activity as it happens into a single Markdown note in his Obsidian
vault, and generates reports from it. `start-work` (its own spec) is the primary automatic
feeder: when Rob picks up a ticket, a "started" entry is logged without him thinking about it.

This spec is **design-only**. Most of it is validated on the **work laptop** (that's where the
Obsidian vault and the Jira/GitLab systems of record live); the capture and report logic is
generic Markdown read/write that can be unit-tested anywhere.

## Decisions (from brainstorming)

- **Separate `worklog` plugin**, not folded into start-work. It owns capture + the report
  skills; `start-work` calls it through a small seam. Each stays focused (kickoff vs record).
- **Storage = one rolling `Worklog.md`** in the vault (path configurable, default `~/Obsidian`),
  newest date on top, structured-but-readable Markdown.
- **Push capture**: start-work "started" entries + a `/log` command for shipped / notes /
  off-ticket work.
- **Consumers**: `/weekly-report` and `/perf-review` read `Worklog.md`. A later enhancement can
  augment with a factual pull from Jira/GitLab (gated on the start-work work-access phase).
- **Private + professional**: `Worklog.md` and generated reports live in the vault, never the
  public repo; report templates are machine-local config. Reports use a professional register,
  **not** the personal `voice` skill.

## Shape

A new `claude-config` plugin, `worklog`:

- `skills/worklog/SKILL.md` — the record-keeping + reporting knowledge (entry format, parsing,
  report synthesis). Provides the **append seam** other skills call.
- `commands/log.md` — `/log <type> <text>` appends an entry.
- `commands/weekly-report.md` — `/weekly-report [range]` drafts a weekly report.
- `commands/perf-review.md` — `/perf-review [range]` drafts a review narrative.
- `.claude-plugin/plugin.json` — manifest (no `version`; `commands` array).

## Storage & entry format

`<vaultPath>/<worklogFile>` — default `~/Obsidian/Worklog.md`. Entries are grouped under a
per-day `## YYYY-MM-DD` heading, **newest day at the top of the file**; within a day, entries
are appended in order. Each entry is one bullet:

```markdown
## 2026-07-13
- **started** PROJ-123 — Add API rate limiting  `[branch: PROJ-123-rate-limiting]`
- **shipped** PROJ-120 — Fix login redirect  `(MR !45 merged)`
- **note** Paired with Dana on the incident postmortem

## 2026-07-12
- **started** PROJ-120 — Fix login redirect  `[branch: PROJ-120-login-redirect]`
```

Format rules (so a skill can parse it and a human can read it in Obsidian):

- Entry = `- **<type>** [<ref> — ]<text>[  <meta>]`.
- `type` ∈ `started | shipped | note` (extensible via config).
- `ref` is the ticket/issue key when there is one (`PROJ-123`, `#42`); optional for `note`.
- Trailing `` `[...]` `` / `` `(...)` `` backticked meta (branch, MR/PR) is optional and ignored
  by report prose but available for links.
- Appending a "started"/"shipped" for a `ref` that already has one that day is idempotent
  (no duplicate line).

## The append seam (start-work integration)

`worklog` exposes one conceptual operation that other skills call:

`append(type, ref, text, meta?)` → ensures today's `## YYYY-MM-DD` heading exists (creating the
file/heading if needed) and inserts the bullet.

- **start-work** calls `append("started", item.key, item.title, {branch})` at kickoff.
- If `worklog` is not installed or no vault is configured, the call is a **graceful no-op**
  (start-work logs a one-line "worklog not configured, skipping" and proceeds). start-work never
  hard-depends on worklog.

Because start-work isn't built yet, what this spec fixes is the **contract** (the entry shape
and the append semantics) so the two plugins agree.

## Consumers

Both read `Worklog.md`, never write reports back into the public repo.

### `/weekly-report [range]`
- Default range: the last 7 days (Mon–Sun of the current week if no range given).
- Reads the day headings in range, groups entries by `ref`/theme, and drafts a report into the
  team's format (from `reports.weeklyTemplate` in config; a sensible default is used if absent).
- Output goes to the vault (e.g. `<vaultPath>/Reports/Weekly-YYYY-Www.md`) as a **draft Rob
  edits** — the skill never sends/posts it.

### `/perf-review [range]`
- Default range: the current quarter (or an explicit range / "since <date>").
- Synthesizes accomplishments, recurring themes, scope/impact, and collaboration into a
  narrative shaped by `reports.perfTemplate` (e.g. the company's competency headings), for Rob
  to refine. Draft only.

## Machine-local config (private)

Shared with start-work's `~/.claude/start-work.json` — a `worklog` section, so there's one
work-config file (or a standalone `~/.claude/worklog.json` if Rob prefers):

```jsonc
{
  "worklog": {
    "vaultPath": "~/Obsidian",
    "worklogFile": "Worklog.md",
    "reportsDir": "Reports",
    "types": ["started", "shipped", "note"],
    "weeklyTemplate": "…team format…",   // or a path to a template note in the vault
    "perfTemplate": "…competency headings…"
  }
}
```

Nothing here — vault path, team format, competency rubric — belongs in the public repo. The
skill reads it locally; if a report skill runs with no template, it uses a generic default and
says so.

## Error handling / edge cases

- **No vault / path missing** → capture (`/log`, start-work seam) is a no-op with a clear
  one-line notice; report skills stop with "configure `worklog.vaultPath` first." Never create a
  vault in a surprising location.
- **Worklog.md missing** → `append` creates it (with today's heading). Report skills over an
  empty/absent log say "no entries in range" rather than erroring.
- **Range with no entries** → report is "nothing logged in <range>," not a fabricated summary.
  The skills must not invent activity that isn't in the log (or, later, in the pulled facts).
- **Never write sensitive work data outside the vault** — reports and the log stay under
  `vaultPath`; the skill refuses to place them in a tracked repo file.

## Testing strategy

- **Parsing + report synthesis**: unit-testable against fixture `Worklog.md` files (known
  entries → expected grouping/draft). No vault or network needed.
- **Capture**: `append` tested by writing to a temp directory acting as the vault (idempotency,
  heading creation, newest-on-top ordering).
- **Live validation** (weekly report / perf review against the real vault, and the eventual
  Jira/GitLab pull) happens on the **work machine** in a later phase.

## Later enhancement — factual pull (deferred)

Once the start-work **work-access phase** (§8 of the start-work spec) establishes Jira/GitLab
access, the report skills can augment the pushed notes with an authoritative pull — tickets
moved/closed and MRs merged in the range — to catch anything not hand-logged. The `Worklog.md`
notes remain the source for context/wins that never became tickets. This is out of scope for
the initial build.

## Scope

**In:** the `worklog` plugin structure, the `Worklog.md` format + parsing, the `append` seam
(start-work contract), the `/log` command, and the `/weekly-report` + `/perf-review` skills
reading the log with config-driven templates.
**Out:** sending/posting reports anywhere; the Jira/GitLab factual pull (later); building
start-work itself; any vault content beyond `Worklog.md` and the drafted reports.

## Workflow

Issue #18 → branch `18-worklog-spec` → this spec commit → PR to `main`. Implementation is
deferred (design-first), and most validation happens on the work machine alongside the
start-work work-access phase.
