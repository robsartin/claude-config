---
name: start-work
description: Use to start a piece of work — turn a ticket or idea into a tracked issue/ticket and a correctly-named branch, make the linkage live, and hand off to brainstorming. Adapts to the repo's host — GitHub via gh, or GitLab/Jira via glab and jira. Triggers on "start work on …", "let's start work", "kick off <issue/ticket>", "start a branch for …".
---

# Start Work

Turn a request into a ready-to-design workspace. This skill orchestrates; it does not do the
design itself — it ends by invoking `superpowers:brainstorming`.

Helpers (deterministic bits) live at `${CLAUDE_PLUGIN_ROOT}/bin/start_work.py`, run with
`python3`. Config (machine-local) is `${CLAUDE_CONFIG_DIR:-$HOME/.claude}/start-work.json` — it
holds `gitlabHosts` and a `jira` section (`defaultProject`, `inProgressStatus`, `doneStatus`) for
work repos; nothing work-specific is baked into this skill.

## 1. Detect the provider

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/bin/start_work.py" provider
```

- `github` → use the **GitHub** steps below (`gh`).
- `gitlab` → use the **GitLab/Jira** steps below (`glab` + `jira`). This requires the repo's host
  listed in config `gitlabHosts` and a `jira` config section.
- `unknown` → ask the user which provider, or to run from inside the target repo.

State the detected provider before acting.

## 2. Resolve or create the work item

### GitHub

If the user gave an identifier — an issue number (`42`), `#42`, or an issue URL — **reference**
it: `gh issue view <n> --json number,title,url`.

Otherwise, from the user's short description, **create** one and mark it ready:

```bash
gh label create ready --color 0E8A16 --description "Ready to be worked" 2>/dev/null || true
gh issue create --title "<title>" --body "<one-line context>" --label ready
```

Confirm the title before creating. The **ref** is the issue number; the **title** is the issue title.

### GitLab/Jira

If the user gave a Jira key (e.g. `PROJ-123`), **reference** it:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/bin/start_work.py" jira-item <KEY>
# -> {"key","summary","status","project","assignee"}
```

Otherwise, from the user's description, **create** a ticket in the default project (confirm the
summary first):

```bash
proj=$(python3 "${CLAUDE_PLUGIN_ROOT}/bin/start_work.py" config-get jira.defaultProject)
[ -n "$proj" ] || { echo "Set jira.defaultProject in ~/.claude/start-work.json first"; exit 1; }
type=$(python3 "${CLAUDE_PLUGIN_ROOT}/bin/start_work.py" config-get jira.issueType); [ -n "$type" ] || type=Task
jira issue create -p"$proj" -t"$type" -s"<summary>"
```

`jira issue create` prints a browse URL (`…/browse/<KEY>`) — the **ref** is that URL's last path
segment (the key). The **title** is the `summary` (Jira `description` is ADF, not plain text, so
never slug from it). Issue **type** is project-dependent; it defaults to `Task` — set
`jira.issueType` in config if your project uses a different type.

## 3. Branch (both providers)

```bash
name=$(python3 "${CLAUDE_PLUGIN_ROOT}/bin/start_work.py" branch-name "<ref>" "<title>")
base=$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null) && base=${base#origin/} || base=main
git checkout "$base" -q && git pull -q
git checkout -b "$name"
```

`branch-name` yields `<ref>-<slug>` — `42-add-rate-limiting` (GitHub) or `PROJ-123-add-rate-limiting`
(GitLab/Jira). If the branch already exists, check it out and continue (idempotent).

## 4. Make the linkage live

**Do not** open a draft PR/MR now — both hosts need a commit first; it's opened at the first push.

### GitHub

```bash
gh issue edit <number> --add-assignee @me
```
Move it to in-progress if the repo uses a project/status board (skip if none).

### GitLab/Jira

```bash
jira issue assign <KEY> "$(jira me)"
inprog=$(python3 "${CLAUDE_PLUGIN_ROOT}/bin/start_work.py" config-get jira.inProgressStatus)
[ -n "$inprog" ] && jira issue move <KEY> "$inprog"     # skip the transition if not configured
```

If the user asked not to change the ticket's status, skip the `jira issue move` and just assign.

## 5. Log to the worklog (graceful seam)

Record a "started" entry **if** the `worklog` plugin is available; if it isn't, skip silently —
start-work never depends on it. If a `/worklog:log` command exists (or the worklog plugin is
installed), log the start as `started "<title>" --ref <ref> --branch "$name"` (ref = the GitHub
issue number or the Jira key — `--ref` is a structured field the reports join against, so it must
never be folded into the text). Otherwise say "worklog not configured — skipping" and move on.

## 6. Set up the workspace and hand off

Record the item + branch (a one-line note is enough), then invoke `superpowers:brainstorming`
to start the design. If the item is already a crisp, fully-specified task, offer to jump
straight to `superpowers:writing-plans` instead.

## 7. Open the draft PR/MR (later — at the first push)

Kickoff deliberately skips this (both hosts need a commit first). Once there's a first commit,
`/start-work:draft-mr` runs these steps. Push the branch if it has no upstream yet:

```bash
git rev-parse --abbrev-ref --symbolic-full-name '@{u}' >/dev/null 2>&1 || git push -u origin HEAD
```

Then open the draft, by provider:

```bash
# GitHub
gh pr create --draft --fill
# GitLab
glab mr create --draft --fill --yes
```

Report the resulting URL. The branch name already carries the ref (`<KEY>-slug` or `<n>-slug`),
which both hosts use to associate the change with the ticket/issue — add `Closes #<n>` (GitHub)
or the Jira key in the description if you want the linkage spelled out. If your `glab` version
rejects a flag or prompts anyway, drop `--yes` and answer interactively.

## 8. Finish the work — `/start-work:finish` (prep)

Gate, push, and put the PR/MR up for review. Stops there; merging is step 9.

**Preconditions — check first, and stop if either fails:**

```bash
base=$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null) && base=${base#origin/} || base=main
[ "$(git branch --show-current)" != "$base" ] || { echo "On $base — nothing to finish."; exit 1; }
[ -z "$(git status --porcelain)" ] || { echo "Working tree is dirty (including untracked files) — commit or stash first."; exit 1; }
```

Never auto-commit on the user's behalf.

### Replay the repo's CI gate

Read the repo's CI config — prefer `.github/workflows/*.yml`, else `.gitlab-ci.yml` — and run it
locally as faithfully as is honest:

- If a workflow is **path-scoped**, only run it when this branch's diff touches those paths
  (`git diff --name-only "origin/$base"...HEAD`).
- Run the steps that genuinely run here: test suites, linters, formatters, type checks.
- **Skip** anything needing infrastructure this machine lacks — Docker/services, matrix
  expansions, deploys/publishes, steps needing CI secrets.
- **Always list what you skipped.** A skipped step must never be reported as a passed one. Say
  "the part of the gate I could run passed", not "the gate passed", whenever anything was skipped.
  This includes **which workflows applied and which were excluded by path scoping** — if nothing
  ran because no workflow matched the diff, say that explicitly; it must never read as "the gate
  passed".
- If there is **no** CI config, say so and ask before continuing rather than pushing ungated.

**If any step fails, stop — do not push.** Report which step failed and its output.

### Push and put the PR/MR up

```bash
git rev-parse --abbrev-ref --symbolic-full-name '@{u}' >/dev/null 2>&1 || git push -u origin HEAD
git push
```

Then, by provider (`python3 "${CLAUDE_PLUGIN_ROOT}/bin/start_work.py" provider`):

```bash
# GitHub — create if absent (or if a prior PR was closed/merged), else un-draft the open one
if [ -n "$(gh pr view --json number,state --jq 'select(.state=="OPEN") | .number' 2>/dev/null)" ]; then gh pr ready; else gh pr create --fill; fi
# GitLab
if glab mr view >/dev/null 2>&1; then glab mr update --ready; else glab mr create --fill --yes; fi
```

Make sure the body carries the linkage — `Closes #<n>` on GitHub, the Jira key on GitLab. Report
the PR/MR URL.

**Stop here.** Do not change the ticket and do not write a worklog entry — those happen at merge,
so that "shipped" keeps meaning *merged*.

## 9. Merge it — `/start-work:merge`

**Verify before merging — stop if anything is off:**

```bash
# GitHub
gh pr view --json state,mergeable,mergeStateStatus,statusCheckRollup
# GitLab
glab mr view
```

Require: the PR/MR exists, its checks are **green** (not pending), and it is **mergeable** (no
conflicts). If checks are red or still running, or there are conflicts, report and stop —
conflicts are the user's to resolve. If it is **already merged**, say so and skip ahead to the
worklog and ticket steps (so an interrupted run finishes cleanly).

**Capture the ref before merging.** The branch name is the only place it lives, and
`--delete-branch`/`--remove-source-branch` remove it — do this before the merge step, not after:

```bash
# Capture the ref BEFORE merging — the branch name is the only place it lives, and
# --delete-branch removes it. Branch names are <ref>-<slug>.
ref=$(git branch --show-current | sed -E 's/^([A-Za-z]+-[0-9]+|[0-9]+)-.*/\1/')
```

That yields `42` from `42-slug` and `PROJ-123` from `PROJ-123-slug`. If the branch is already gone
or the ref can't be derived (the already-merged path can land here), ask the user for the issue
number / Jira key rather than guessing.

**Merge and clean up:**

```bash
# GitHub
gh pr merge --squash --delete-branch
# GitLab
glab mr merge --squash --remove-source-branch
```

**Log what shipped** (graceful seam — skip silently if `worklog` isn't installed): log
`shipped "<title>" --ref "$ref"`. This is what gives weekly reports a record of shipped work.

**Move the ticket:**

- GitHub — the issue closes automatically via `Closes #<n>`. Verify and report; don't act.
- GitLab/Jira — transition if a done status is configured:

```bash
done_status=$(python3 "${CLAUDE_PLUGIN_ROOT}/bin/start_work.py" config-get jira.doneStatus)
if [ -n "$done_status" ]; then jira issue move "$ref" "$done_status"; fi
```

**Return to the default branch** (runs on both paths — normal merge and already-merged):

```bash
base=$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null) && base=${base#origin/} || base=main
if [ -n "$(git status --porcelain)" ]; then echo "note: working tree dirty — staying put"; else git checkout "$base" -q && git pull -q; fi
```

Report what merged, what was logged, and the ticket's final state.
