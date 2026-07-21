# finish-work — the two-stage bookend to start-work

Date: 2026-07-14
Issue: robsartin/claude-config#42
Related: `docs/superpowers/specs/2026-07-13-start-work-design.md` (the kickoff half),
`docs/superpowers/specs/2026-07-13-worklog-reports-design.md` (the `shipped` entry consumer)

## Problem

`start-work` automates the *beginning* of a piece of work — ticket, branch, linkage, hand-off to
design. Finishing is still entirely manual and repetitive: replay the repo's CI gate, push, open
or un-draft the PR/MR, then later merge, clean up the branch, log what shipped, and move the
ticket. That ritual runs several times a day and is exactly the kind of thing Rob wanted
automated.

It also closes a real gap in `worklog`: today the log only ever receives `started` entries, so
weekly reports have no hand-logged record of what actually shipped.

## Decisions (from brainstorming)

- **Two-stage.** `/start-work:finish` preps; `/start-work:merge` merges. Merge is the one
  genuinely hard-to-undo step, so it stays a deliberate, separate act.
- **The gate is the repo's own CI config.** Read `.github/workflows/*.yml` (or `.gitlab-ci.yml`),
  run the steps that are genuinely runnable locally, and explicitly report the ones skipped.
- **Side effects happen only at merge.** Prep changes no ticket and writes no worklog entry, so
  "shipped" keeps meaning *merged*.
- **Extend the `start-work` plugin** rather than create a new one.
- **No new Python.**

## Shape

`start-work` gains two commands and two SKILL sections, joining `/start-work` and
`/start-work:draft-mr` as one coherent lifecycle:

- `plugins/start-work/commands/finish.md` → `/start-work:finish`
- `plugins/start-work/commands/merge.md` → `/start-work:merge`
- `plugins/start-work/skills/start-work/SKILL.md` → new sections for each stage
- both registered in `plugin.json`'s `commands` array

**Why extend rather than add a plugin:** finishing needs precisely what `start-work` already
owns — provider detection (`start_work.py provider`), the machine-local config (`config-get`),
and the branch/ticket conventions. A separate plugin would have to reach across
`${CLAUDE_PLUGIN_ROOT}` boundaries for those helpers — the same seam awkwardness that made the
worklog integration a deliberate graceful no-op.

**Why no Python:** deciding which CI steps are runnable locally is judgment, not parsing, and the
stdlib-only rule means there is no YAML parser available anyway. Claude reads YAML natively, so
this belongs in SKILL.md.

## Stage 1 — `/start-work:finish` (prep)

1. **Preconditions.** Must be on a feature branch (not the repo's default) with a clean working
   tree. If the tree is dirty, **report and stop** — never auto-commit on the user's behalf.
2. **Replay the gate** (see below). **Stop on the first failure — never push a red gate.**
3. **Push**, setting upstream if the branch has none.
4. **Make the PR/MR ready.** If none exists, create it; if a draft exists, un-draft it.
   - GitHub: `gh pr create --fill` / `gh pr ready`
   - GitLab: `glab mr create --fill` / `glab mr update --ready`
   The body carries the linkage — `Closes #<n>` on GitHub, the Jira key on GitLab.
5. **Report the URL and stop.** No ticket transition, no worklog entry.

## Stage 2 — `/start-work:merge`

1. **Verify before merging.** The PR/MR exists, its checks are green, and it is mergeable
   (no conflicts). If anything is red, pending, or conflicted, **report and stop** — never merge
   a failing or conflicted change.
2. **Squash-merge and delete the branch.**
   - GitHub: `gh pr merge --squash --delete-branch`
   - GitLab: `glab mr merge --squash --remove-source-branch`
   Then check out the default branch and pull.
3. **Worklog.** Log `shipped <ref> "<title>"` through the worklog plugin if it is available; skip
   silently if it isn't (same graceful seam `start-work` already uses). This is what finally gives
   weekly reports a hand-logged record of shipped work.
4. **Ticket.** GitHub issues close automatically via `Closes #<n>` — verify and report rather than
   acting. Jira: transition to `jira.doneStatus` if configured; skip if unset.

## Gate replay

Read the repo's CI configuration and reproduce it locally as faithfully as is honest:

- Prefer `.github/workflows/*.yml`; fall back to `.gitlab-ci.yml`.
- For a **path-scoped** workflow, only run it when the branch's diff actually touches its `paths`.
- Run the steps that are genuinely runnable locally (test suites, linters, formatters, type
  checks). **Skip** steps that need infrastructure this machine doesn't have — Docker/services,
  matrix expansions, deploy or publish steps, anything needing CI secrets.
- **Always list what was skipped.** A skipped step must never read as a passed one; that is the
  difference between "the gate passed" and "the part of the gate I could run passed."
- If no CI config exists, say so and ask before proceeding rather than silently pushing ungated.

## Config

One optional new machine-local key, in the existing `~/.claude/start-work.json`:

```jsonc
{ "jira": { "doneStatus": "<the status meaning done in your workflow>" } }
```

Absent, the merge stage simply skips the Jira transition. No other new config; provider detection
and the rest come from what `start-work` already reads.

## Error handling / edge cases

- **Dirty working tree** (prep) → report and stop; never auto-commit.
- **On the default branch** (prep) → report and stop; there is nothing to finish.
- **Gate failure** → stop before pushing, showing which step failed.
- **No CI config** → say so and ask, rather than pushing ungated.
- **Checks red or still pending** (merge) → report and stop.
- **Not mergeable / conflicted** (merge) → report and stop; conflicts are the user's to resolve.
- **PR/MR already merged** (merge) → report it and skip to the worklog/ticket steps rather than
  erroring, so a half-completed run can be finished idempotently.
- **worklog absent** → skip the entry silently; never a hard dependency.

## Testing strategy

There is no new pure code, so verification is structural plus a real exercise:

- `claude plugin validate plugins/start-work` passes; both new command files' frontmatter parses;
  the existing suite still passes.
- The SKILL's helper invocations name subcommands that actually exist (`provider`, `config-get`).
- **Dogfood**: run `/start-work:finish` against a real branch in this repo (we open PRs
  constantly), confirming the gate replay, push, and PR-ready behaviour end to end. The merge
  stage is exercised on a genuine PR when one is ready to land.

## Scope

**In:** the two commands, their SKILL sections, the gate-replay rules, the `jira.doneStatus` key,
and the worklog `shipped` seam at merge.
**Out:** auto-committing work; resolving conflicts; a `--force` that bypasses the gate; changing
the kickoff or draft-MR behaviour; the GitLab merge path's live validation (that happens on the
work laptop, like the rest of the GitLab/Jira surface).

## Workflow

Issue #42 → branch `42-finish-work` → spec, plan, and build on the one branch → PR to `main`.
