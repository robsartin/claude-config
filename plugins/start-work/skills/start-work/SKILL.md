---
name: start-work
description: Use to start a piece of work — turn a ticket or idea into a tracked GitHub issue and a correctly-named branch, make the linkage live, and hand off to brainstorming. Triggers on "start work on …", "let's start work", "kick off <issue/idea>", "start a branch for …".
---

# Start Work

Turn a request into a ready-to-design workspace. This skill orchestrates; it does not do the
design itself — it ends by invoking `superpowers:brainstorming`.

Helpers (deterministic bits) live at `${CLAUDE_PLUGIN_ROOT}/bin/start_work.py`, run with
`python3`. Config (optional, machine-local) is `${CLAUDE_CONFIG_DIR:-$HOME/.claude}/start-work.json`.

## 1. Detect the provider

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/bin/start_work.py" provider
```

- `github` → continue below.
- `gitlab` → the GitLab/Jira path is not built yet; tell the user and stop.
- `unknown` → ask the user which provider, or to run from inside the target repo.

State the detected provider before acting.

## 2. Resolve or create the work item (GitHub)

If the user gave an identifier — an issue number (`42`), `#42`, or an issue URL — **reference**
it: `gh issue view <n> --json number,title,url`.

Otherwise, from the user's short description, **create** one and mark it ready:

```bash
gh label create ready --color 0E8A16 --description "Ready to be worked" 2>/dev/null || true
gh issue create --title "<title>" --body "<one-line context>" --label ready
```

Confirm the title with the user before creating. Capture the issue number and title.

## 3. Branch

```bash
name=$(python3 "${CLAUDE_PLUGIN_ROOT}/bin/start_work.py" branch-name "<number>" "<title>")
git checkout main -q && git pull -q
git checkout -b "$name"
```

If the branch already exists, check it out and continue (idempotent).

## 4. Make the linkage live

- Assign the issue to the user: `gh issue edit <number> --add-assignee @me`.
- Move it to in-progress if the repo uses a project/status board (skip if none).
- **Do not** open a draft PR now — GitHub needs a commit first; the PR is opened at the first
  push (the normal PR step handles it).

## 5. Log to the worklog (graceful seam)

Record a "started" entry **if** the `worklog` plugin is available; if it is not installed or
configured, skip silently and proceed — start-work never depends on it. Check for the worklog
command (e.g. is `/worklog:log` available, or does `${CLAUDE_CONFIG_DIR:-$HOME/.claude}/plugins/cache/claude-config/worklog/` exist). If present, log the start as
`started <issue-number> "<title>" [branch: $name]`. If absent, say "worklog not configured —
skipping" and move on. (The worklog plugin is a later build; in this phase this step will
normally skip.)

## 6. Set up the workspace and hand off

Record the item + branch (a one-line note is enough), then invoke `superpowers:brainstorming`
to start the design. If the issue is already a crisp, fully-specified task, offer to jump
straight to `superpowers:writing-plans` instead.
