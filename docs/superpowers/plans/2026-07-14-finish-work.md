# finish-work (two-stage bookend) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `/start-work:finish` (gate replay → push → PR/MR ready) and `/start-work:merge` (verify → squash-merge → worklog `shipped` → Jira done) to the existing `start-work` plugin.

**Architecture:** Two new command files plus two new SKILL.md sections on the `start-work` plugin, reusing its existing provider detection (`start_work.py provider`) and machine-local config (`config-get`). No new Python: judging which CI steps are locally runnable is judgment, and the stdlib-only rule precludes a YAML parser.

**Tech Stack:** Claude Code plugin (SKILL.md + commands), `gh`, `glab`, `jira`, git.

## Global Constraints

- Never commit to `main`; work on branch `42-finish-work`, squash-PR (issue #42).
- Plugin omits a `version` field; only `plugin.json` lives in `.claude-plugin/`.
- Skill frontmatter `name:` stays exactly `start-work`. **No colon-space (`: `) inside an unquoted frontmatter value** — it breaks YAML parsing (this bit us before).
- **No new Python** and no new dependencies.
- Prep **must never** auto-commit, and **must never** push when the gate fails.
- Merge **must never** proceed when checks are red/pending or the PR/MR is not mergeable.
- Gate replay **must always list skipped steps** — a skipped step must never read as passed.
- All work-specific values (Jira statuses, hosts) stay in machine-local config; nothing work-specific in the repo.
- `jira.doneStatus` is optional; when unset, the merge stage skips the Jira transition.

## File Structure

Created:
- `plugins/start-work/commands/finish.md` — the `/start-work:finish` command.
- `plugins/start-work/commands/merge.md` — the `/start-work:merge` command.

Modified:
- `plugins/start-work/skills/start-work/SKILL.md` — new sections 8 (finish) and 9 (merge).
- `plugins/start-work/.claude-plugin/plugin.json` — register both commands.
- `CLAUDE.md`, `README.md` — mention the new commands in the start-work descriptions.

---

### Task 1: SKILL.md — the finish and merge sections

**Files:**
- Modify: `plugins/start-work/skills/start-work/SKILL.md` (append two sections after the existing section 7)

**Interfaces:**
- Consumes: the existing `start_work.py` CLI — `provider` (no args) and `config-get <dotted.key>`.
- Produces: the documented procedures that `commands/finish.md` and `commands/merge.md` (Task 2) invoke by name.

- [ ] **Step 1: Append the two sections**

Append verbatim to `plugins/start-work/skills/start-work/SKILL.md`:

````markdown
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
  (`git diff --name-only "$base"...HEAD`).
- Run the steps that genuinely run here: test suites, linters, formatters, type checks.
- **Skip** anything needing infrastructure this machine lacks — Docker/services, matrix
  expansions, deploys/publishes, steps needing CI secrets.
- **Always list what you skipped.** A skipped step must never be reported as a passed one. Say
  "the part of the gate I could run passed", not "the gate passed", whenever anything was skipped.
- If there is **no** CI config, say so and ask before continuing rather than pushing ungated.

**If any step fails, stop — do not push.** Report which step failed and its output.

### Push and put the PR/MR up

```bash
git rev-parse --abbrev-ref --symbolic-full-name '@{u}' >/dev/null 2>&1 || git push -u origin HEAD
git push
```

Then, by provider (`python3 "${CLAUDE_PLUGIN_ROOT}/bin/start_work.py" provider`):

```bash
# GitHub — create if absent, else un-draft an existing one
if gh pr view --json number >/dev/null 2>&1; then gh pr ready; else gh pr create --fill; fi
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

**Merge and clean up:**

```bash
# GitHub
gh pr merge --squash --delete-branch
# GitLab
glab mr merge --squash --remove-source-branch
```

Then return to the default branch:

```bash
base=$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null) && base=${base#origin/} || base=main
git checkout "$base" -q && git pull -q
```

**Log what shipped** (graceful seam — skip silently if `worklog` isn't installed): log
`shipped <ref> "<title>"`, where ref is the GitHub issue number or the Jira key. This is what gives
weekly reports a record of shipped work.

**Move the ticket:**

- GitHub — the issue closes automatically via `Closes #<n>`. Verify and report; don't act.
- GitLab/Jira — transition if a done status is configured:

```bash
done=$(python3 "${CLAUDE_PLUGIN_ROOT}/bin/start_work.py" config-get jira.doneStatus)
[ -n "$done" ] && jira issue move <KEY> "$done"   # skip silently when unset
```

Report what merged, what was logged, and the ticket's final state.
````

- [ ] **Step 2: Verify structure and frontmatter**

```bash
cd ~/code/claude-config
grep -c 'CLAUDE_PLUGIN_ROOT' plugins/start-work/skills/start-work/SKILL.md   # expect >= 8
grep -q '^## 8. Finish the work' plugins/start-work/skills/start-work/SKILL.md && echo "section 8 OK"
grep -q '^## 9. Merge it' plugins/start-work/skills/start-work/SKILL.md && echo "section 9 OK"
python3 -c "import re,yaml; s=open('plugins/start-work/skills/start-work/SKILL.md').read(); d=yaml.safe_load(re.match(r'^---\n(.*?)\n---',s,re.S).group(1)); assert d['name']=='start-work'; print('frontmatter OK')"
```
Expected: count ≥ 8, both section lines, `frontmatter OK`.

- [ ] **Step 3: Commit**

```bash
git add plugins/start-work/skills/start-work/SKILL.md
git commit -m "start-work: SKILL sections for finish (prep) and merge"
```

---

### Task 2: The two command files + registration

**Files:**
- Create: `plugins/start-work/commands/finish.md`
- Create: `plugins/start-work/commands/merge.md`
- Modify: `plugins/start-work/.claude-plugin/plugin.json`

**Interfaces:**
- Consumes: SKILL.md sections 8 and 9 from Task 1 (referenced by name).
- Produces: the invocable `/start-work:finish` and `/start-work:merge` commands.

- [ ] **Step 1: Write `commands/finish.md`**

```markdown
---
description: Gate, push, and put the current branch's PR/MR up for review
allowed-tools: Bash
---

Invoke the `start-work` skill's "Finish the work" step (section 8) for the **current branch**.

Refuse if the working tree is dirty or you're on the default branch. Replay the repo's CI gate
and stop without pushing if it fails, always listing any steps you skipped. Then push and create
or un-draft the PR/MR, and report its URL.

Do not merge, do not change the ticket, and do not write a worklog entry — those belong to
`/start-work:merge`.
```

- [ ] **Step 2: Write `commands/merge.md`**

```markdown
---
description: Squash-merge the current PR/MR, log what shipped, and close out the ticket
allowed-tools: Bash
---

Invoke the `start-work` skill's "Merge it" step (section 9) for the **current branch**.

Verify first — the PR/MR exists, checks are green (not pending), and it is mergeable. Stop and
report if anything is red, pending, or conflicted. If it is already merged, skip ahead to the
worklog and ticket steps.

Then squash-merge with branch deletion, return to the default branch and pull, log a `shipped`
worklog entry if worklog is available, and transition the Jira ticket if `jira.doneStatus` is set.
Report what merged, what was logged, and the ticket's final state.
```

- [ ] **Step 3: Register both in `plugin.json`**

Change the `commands` array to:

```json
  "commands": [
    "./commands/start-work.md",
    "./commands/draft-mr.md",
    "./commands/finish.md",
    "./commands/merge.md"
  ]
```

- [ ] **Step 4: Verify**

```bash
cd ~/code/claude-config
python3 -c "import json; d=json.load(open('plugins/start-work/.claude-plugin/plugin.json')); print(d['commands']); assert len(d['commands'])==4"
for f in finish merge; do python3 -c "import re,yaml; s=open('plugins/start-work/commands/$f.md').read(); print('$f:', yaml.safe_load(re.match(r'^---\n(.*?)\n---',s,re.S).group(1))['description'])"; done
claude plugin validate plugins/start-work 2>&1 | tail -2
```
Expected: 4 commands, both descriptions print, validation passes (only the no-version warning).

- [ ] **Step 5: Commit**

```bash
git add plugins/start-work/commands plugins/start-work/.claude-plugin/plugin.json
git commit -m "start-work: /finish and /merge commands"
```

---

### Task 3: Docs

**Files:**
- Modify: `CLAUDE.md` (the `### start-work` section and the layout tree's commands line)
- Modify: `README.md` (the `## The start-work plugin` section)

**Interfaces:**
- Consumes: the commands from Task 2.

- [ ] **Step 1: Update CLAUDE.md**

In the layout tree, change the start-work commands line to:

```
  commands/start-work.md, draft-mr.md, finish.md, merge.md
```

In the `### start-work` section, append this sentence after the `/start-work:draft-mr` sentence:

> `/start-work:finish` replays the repo's CI gate, pushes, and puts the PR/MR up for review; `/start-work:merge` then verifies checks are green, squash-merges, logs a `shipped` worklog entry, and transitions the ticket.

- [ ] **Step 2: Update README.md**

In `## The start-work plugin`, change "ships one skill plus two commands" to "ships one skill plus four commands", and append the same sentence describing `/start-work:finish` and `/start-work:merge`.

- [ ] **Step 3: Verify the docs match reality**

```bash
cd ~/code/claude-config
for f in start-work draft-mr finish merge; do
  test -f "plugins/start-work/commands/$f.md" && echo "  ✓ $f" || echo "  ✗ $f MISSING"
done
grep -c 'start-work:finish' CLAUDE.md README.md
grep -c 'start-work:merge' CLAUDE.md README.md
```
Expected: all four command files exist; non-zero counts in both docs.

- [ ] **Step 4: Commit**

```bash
git add CLAUDE.md README.md
git commit -m "start-work: document /finish and /merge"
```

---

### Task 4: Verify end-to-end (dogfood) + PR

**Files:** none.

- [ ] **Step 1: Structural checks**

```bash
cd ~/code/claude-config
claude plugin validate plugins/start-work 2>&1 | tail -2
(cd plugins/start-work && python3 -m pytest tests -q && rm -rf .pytest_cache tests/__pycache__)
```
Expected: validation passes; the existing suite still passes (this change adds no Python).

- [ ] **Step 2: Dry-run the gate-replay logic on this branch**

Confirm the precondition and path-scoping commands behave here:

```bash
cd ~/code/claude-config
base=$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null) && base=${base#origin/} || base=main
echo "base=$base current=$(git branch --show-current)"
git diff --name-only "$base"...HEAD
ls .github/workflows/
```
Expected: `base=main`, current is `42-finish-work`, the changed-file list matches this branch's work, and the workflow list is shown (so you can see which path-scoped gates apply — for a docs/SKILL-only change to `plugins/start-work/**`, `start-work.yml` applies).

- [ ] **Step 3: Dogfood `/start-work:finish` on this branch**

Run the section-8 procedure by hand against this very branch: check preconditions, replay the applicable gate (`start-work.yml` → `python3 -m pytest tests -q` in `plugins/start-work`), push, and create the PR. Report exactly which gate steps ran and which were skipped.

- [ ] **Step 4: Open the PR**

```bash
cd ~/code/claude-config
gh pr create --repo robsartin/claude-config --base main \
  --title "start-work: /finish and /merge — the two-stage finish-work bookend" \
  --body "Closes #42. Adds /start-work:finish (precondition checks, CI-gate replay, push, PR/MR ready) and /start-work:merge (verify green+mergeable, squash-merge + delete branch, worklog shipped entry, Jira doneStatus transition). Extends the start-work plugin; no new Python. Prep never auto-commits and never pushes a red gate; merge never proceeds on red/pending/conflicted; skipped gate steps are always reported."
```

- [ ] **Step 5: Confirm CI green**

```bash
gh pr checks --repo robsartin/claude-config --watch
```
Expected: `tests` passes.

---

## Self-Review

**Spec coverage:**
- Two-stage split → Tasks 1 (sections 8/9) + 2 (two commands). ✓
- Prep: preconditions, gate replay, push, PR/MR ready, stop → Task 1 section 8. ✓
- Never auto-commit / never push a red gate → Task 1 section 8 + Global Constraints. ✓
- Gate = read CI config, path-scoping, skip infra steps, **always list skipped** → Task 1 section 8. ✓
- Merge: verify green+mergeable, squash+delete, return to default branch → Task 1 section 9. ✓
- Already-merged idempotency → Task 1 section 9. ✓
- Worklog `shipped` at merge, graceful → Task 1 section 9. ✓
- Jira `doneStatus` optional; GitHub auto-closes → Task 1 section 9. ✓
- Extends start-work plugin, no new Python → File Structure + Global Constraints. ✓
- Docs → Task 3. ✓
- Testing (structural + dogfood) → Task 4. ✓
- Out of scope (auto-commit, conflict resolution, `--force`) → not built anywhere. ✓

**Placeholder scan:** every step carries its actual content — the SKILL sections, both command files, and the exact JSON are given verbatim.

**Type/name consistency:** the helper subcommands used (`provider`, `config-get`) exist in `start_work.py`; the config key is `jira.doneStatus` everywhere; command files are `finish.md`/`merge.md` and invoked as `/start-work:finish` / `/start-work:merge` consistently across the plan, SKILL, and docs.
