---
name: start-work
description: Use to start a piece of work — turn a ticket or idea into a tracked issue/ticket and a correctly-named branch, make the linkage live, and hand off to brainstorming. Adapts to the repo's host — GitHub via gh, or GitLab/Jira via glab and jira. Triggers on "start work on …", "let's start work", "kick off <issue/ticket>", "start a branch for …".
---

# Start Work

Turn a request into a ready-to-design workspace. This skill orchestrates; it does not do the
design itself — it ends by invoking `superpowers:brainstorming`.

Helpers (deterministic bits) live at `${CLAUDE_PLUGIN_ROOT}/bin/start_work.py`, run with
`python3`. Config (machine-local) is `${CLAUDE_CONFIG_DIR:-$HOME/.claude}/start-work.json` — it
holds `gitlabHosts` and a `jira` section (`defaultProject`, `inProgressStatus`) for work repos;
nothing work-specific is baked into this skill.

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
jira issue create -p"$proj" -tTask -s"<summary>"      # capture the new key from the output
```

The **ref** is the Jira key; the **title** is the `summary` (Jira `description` is ADF, not plain
text, so never slug from it).

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
installed), log the start as `started <ref> "<title>" [branch: $name]` (ref = the GitHub issue
number or the Jira key). Otherwise say "worklog not configured — skipping" and move on.

## 6. Set up the workspace and hand off

Record the item + branch (a one-line note is enough), then invoke `superpowers:brainstorming`
to start the design. If the item is already a crisp, fully-specified task, offer to jump
straight to `superpowers:writing-plans` instead.
