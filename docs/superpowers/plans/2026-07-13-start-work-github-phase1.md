# start-work GitHub adapter (Phase 1) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the GitHub/`gh` path of the `start-work` skill — a `claude-config` plugin that turns a request into a tracked GitHub issue + branch, makes the linkage live, and hands off to brainstorming.

**Architecture:** A `start-work` plugin whose `SKILL.md` holds the orchestration (judgment: detect provider → resolve-or-create issue → branch → assign → hand off) and calls small **pure Python helpers** (`bin/start_work.py`, stdlib-only, run via `python3`, no venv) for the deterministic bits — provider detection, branch/slug naming, config loading — which are unit-tested with `pytest`. GitLab/Jira is a later adapter; this phase's helpers return `gitlab` for work hosts but the skill stops with "not yet implemented" on that path.

**Tech Stack:** Claude Code plugin (SKILL.md + command), Python 3 (stdlib only) + pytest, `gh` CLI, GitHub Actions.

## Global Constraints

- Never commit to `main`; work on branch `20-start-work-github-phase1`, squash-PR (issue #20).
- Plugin omits a `version` field (repo convention); only `plugin.json` lives in `.claude-plugin/`.
- Skill `name:` frontmatter is exactly `start-work`.
- Helpers are **stdlib-only Python**, run as `python3 ${CLAUDE_PLUGIN_ROOT}/bin/start_work.py <subcmd>` — no venv, no third-party deps, no packaging.
- Readiness convention: the positive **`ready`** label (create per-repo if missing); never the retired `notready`.
- Machine-local config path: `${CLAUDE_CONFIG_DIR:-$HOME/.claude}/start-work.json`; **no** work host/key/token ever written to a repo file.
- Branch naming: `<ref>-<slug>` where ref is the GitHub issue number (personal) or Jira key (work), slug is the kebab-cased, ≤50-char title.
- Draft PR is NOT opened at kickoff (deferred to first push, per spec).
- The worklog `append` seam is a **graceful no-op** when worklog isn't present.

## File Structure

Created under `plugins/start-work/`:
- `.claude-plugin/plugin.json` — manifest (`commands` array, no version).
- `bin/start_work.py` — pure helpers + a tiny CLI (`provider`, `branch-name`, `config-get`).
- `tests/test_start_work.py` — pytest unit tests for the helpers.
- `skills/start-work/SKILL.md` — the orchestration process.
- `commands/start-work.md` — `/start-work [identifier]` thin command.

Also:
- `.github/workflows/start-work.yml` — path-scoped pytest gate.
- `.claude-plugin/marketplace.json` — add the `start-work` entry.
- `CLAUDE.md`, `README.md` — add the plugin.

---

### Task 1: Plugin scaffold + config loader

**Files:**
- Create: `plugins/start-work/.claude-plugin/plugin.json`
- Create: `plugins/start-work/bin/start_work.py`
- Create: `plugins/start-work/tests/test_start_work.py`

**Interfaces:**
- Produces: `load_config(path: str) -> dict` (merges user JSON over `DEFAULTS`; missing file → a copy of `DEFAULTS`); module-level `DEFAULTS` dict. CLI subcommand `config-get <dotted.key>`.

- [ ] **Step 1: Write the failing test**

Create `plugins/start-work/tests/test_start_work.py`:

```python
import json, os, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "bin"))
import start_work as sw


def test_load_config_missing_returns_defaults(tmp_path):
    cfg = sw.load_config(str(tmp_path / "nope.json"))
    assert cfg == sw.DEFAULTS
    assert cfg is not sw.DEFAULTS  # a copy, not the shared dict


def test_load_config_merges_user_over_defaults(tmp_path):
    p = tmp_path / "start-work.json"
    p.write_text(json.dumps({"gitlabHosts": ["gitlab.corp.com"]}))
    cfg = sw.load_config(str(p))
    assert cfg["gitlabHosts"] == ["gitlab.corp.com"]
    # untouched defaults still present
    assert cfg["worklog"]["worklogFile"] == "Worklog.md"
```

- [ ] **Step 2: Run it, expect failure**

Run: `cd plugins/start-work && python3 -m pytest tests/test_start_work.py -q`
Expected: FAIL (`ModuleNotFoundError: No module named 'start_work'`).

- [ ] **Step 3: Implement the module skeleton + config**

Create `plugins/start-work/bin/start_work.py`:

```python
#!/usr/bin/env python3
"""start-work helpers: deterministic bits the SKILL.md calls. Stdlib only."""
import json
import os
import sys

DEFAULTS = {
    "gitlabHosts": [],
    "worklog": {"vaultPath": "~/Obsidian", "worklogFile": "Worklog.md"},
}


def load_config(path):
    """User JSON shallow-merged over DEFAULTS (worklog sub-dict deep-merged).
    Missing file -> a fresh copy of DEFAULTS."""
    import copy
    cfg = copy.deepcopy(DEFAULTS)
    if not os.path.exists(path):
        return cfg
    with open(path) as f:
        user = json.load(f)
    for k, v in user.items():
        if k == "worklog" and isinstance(v, dict):
            cfg["worklog"].update(v)
        else:
            cfg[k] = v
    return cfg


def _config_get(cfg, dotted):
    cur = cfg
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return ""
        cur = cur[part]
    return cur


def _default_config_path():
    base = os.environ.get("CLAUDE_CONFIG_DIR", os.path.expanduser("~/.claude"))
    return os.path.join(base, "start-work.json")


def main(argv):
    if not argv:
        print("usage: start_work.py <provider|branch-name|config-get> ...", file=sys.stderr)
        return 2
    cmd, rest = argv[0], argv[1:]
    if cmd == "config-get":
        cfg = load_config(_default_config_path())
        val = _config_get(cfg, rest[0]) if rest else ""
        print(val if not isinstance(val, (dict, list)) else json.dumps(val))
        return 0
    print(f"unknown subcommand: {cmd}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
```

- [ ] **Step 4: Run tests, expect pass**

Run: `cd plugins/start-work && python3 -m pytest tests/test_start_work.py -q`
Expected: PASS (2 passed).

- [ ] **Step 5: Write the manifest**

Create `plugins/start-work/.claude-plugin/plugin.json`:

```json
{
  "name": "start-work",
  "description": "Turn a ticket or idea into a tracked issue + branch and hand off to planning.",
  "author": { "name": "Rob Sartin" },
  "keywords": ["workflow", "github", "issues", "branch", "kickoff"],
  "commands": ["./commands/start-work.md"]
}
```

- [ ] **Step 6: Commit**

```bash
git add plugins/start-work/.claude-plugin plugins/start-work/bin plugins/start-work/tests
git commit -m "start-work: plugin scaffold + config loader"
```

---

### Task 2: Provider detection

**Files:**
- Modify: `plugins/start-work/bin/start_work.py`
- Modify: `plugins/start-work/tests/test_start_work.py`

**Interfaces:**
- Consumes: `load_config` (Task 1).
- Produces: `host_of(remote_url) -> str`, `provider_for_remote(remote_url, gitlab_hosts) -> str` (`"github" | "gitlab" | "unknown"`); CLI `provider` (reads `git remote get-url origin` + config).

- [ ] **Step 1: Write the failing test**

Append to `tests/test_start_work.py`:

```python
import pytest


@pytest.mark.parametrize("url,expected", [
    ("https://github.com/robsartin/claude-config.git", "github.com"),
    ("git@github.com:robsartin/claude-config.git", "github.com"),
    ("ssh://git@gitlab.corp.com/team/app.git", "gitlab.corp.com"),
    ("https://gitlab.corp.com/team/app", "gitlab.corp.com"),
])
def test_host_of(url, expected):
    assert sw.host_of(url) == expected


def test_provider_for_remote():
    assert sw.provider_for_remote("git@github.com:o/r.git", []) == "github"
    assert sw.provider_for_remote("https://gitlab.corp.com/o/r.git",
                                  ["gitlab.corp.com"]) == "gitlab"
    assert sw.provider_for_remote("https://example.com/o/r.git", []) == "unknown"
```

- [ ] **Step 2: Run it, expect failure**

Run: `cd plugins/start-work && python3 -m pytest tests/test_start_work.py -q`
Expected: FAIL (`AttributeError: module 'start_work' has no attribute 'host_of'`).

- [ ] **Step 3: Implement**

Add to `start_work.py` (above `main`), and add a `re`/`subprocess` import at the top:

```python
import re
import subprocess


def host_of(remote_url):
    m = re.match(r"(?:https?://|ssh://git@|git@)([^/:]+)", remote_url.strip())
    return m.group(1) if m else ""


def provider_for_remote(remote_url, gitlab_hosts):
    host = host_of(remote_url)
    if host == "github.com":
        return "github"
    if host in gitlab_hosts:
        return "gitlab"
    return "unknown"


def _origin_url():
    try:
        return subprocess.check_output(
            ["git", "remote", "get-url", "origin"], text=True, stderr=subprocess.DEVNULL
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ""
```

Add a `provider` branch inside `main()` before the unknown-subcommand line:

```python
    if cmd == "provider":
        cfg = load_config(_default_config_path())
        print(provider_for_remote(_origin_url(), cfg.get("gitlabHosts", [])))
        return 0
```

- [ ] **Step 4: Run tests, expect pass**

Run: `cd plugins/start-work && python3 -m pytest tests/test_start_work.py -q`
Expected: PASS (all passing). Also smoke the CLI from this repo:
`python3 plugins/start-work/bin/start_work.py provider` → prints `github`.

- [ ] **Step 5: Commit**

```bash
git add plugins/start-work/bin/start_work.py plugins/start-work/tests/test_start_work.py
git commit -m "start-work: provider detection from origin remote"
```

---

### Task 3: Branch/slug naming

**Files:**
- Modify: `plugins/start-work/bin/start_work.py`
- Modify: `plugins/start-work/tests/test_start_work.py`

**Interfaces:**
- Produces: `slugify(title, max_len=50) -> str`, `branch_name(ref, title) -> str`; CLI `branch-name <ref> <title...>`.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_start_work.py`:

```python
def test_slugify():
    assert sw.slugify("Add API rate limiting") == "add-api-rate-limiting"
    assert sw.slugify("Fix login redirect!") == "fix-login-redirect"
    assert sw.slugify("  Multiple   spaces ") == "multiple-spaces"
    assert sw.slugify("A" * 80).count("a") <= 50


def test_branch_name():
    assert sw.branch_name("PROJ-123", "Add API rate limiting") == "PROJ-123-add-api-rate-limiting"
    assert sw.branch_name("42", "Fix login redirect!") == "42-fix-login-redirect"
```

- [ ] **Step 2: Run it, expect failure**

Run: `cd plugins/start-work && python3 -m pytest tests/test_start_work.py -q`
Expected: FAIL (`AttributeError: ... 'slugify'`).

- [ ] **Step 3: Implement**

Add to `start_work.py`:

```python
def slugify(title, max_len=50):
    s = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    if len(s) > max_len:
        s = s[:max_len].rstrip("-")
    return s


def branch_name(ref, title):
    return f"{ref}-{slugify(title)}"
```

Add a `branch-name` branch inside `main()`:

```python
    if cmd == "branch-name":
        if len(rest) < 2:
            print("usage: branch-name <ref> <title...>", file=sys.stderr)
            return 2
        print(branch_name(rest[0], " ".join(rest[1:])))
        return 0
```

- [ ] **Step 4: Run tests, expect pass**

Run: `cd plugins/start-work && python3 -m pytest tests/test_start_work.py -q`
Expected: PASS. Smoke: `python3 plugins/start-work/bin/start_work.py branch-name PROJ-9 "Test this thing"` → `PROJ-9-test-this-thing`.

- [ ] **Step 5: Commit**

```bash
git add plugins/start-work/bin/start_work.py plugins/start-work/tests/test_start_work.py
git commit -m "start-work: branch/slug naming"
```

---

### Task 4: SKILL.md orchestration + command

**Files:**
- Create: `plugins/start-work/skills/start-work/SKILL.md`
- Create: `plugins/start-work/commands/start-work.md`

**Interfaces:**
- Consumes: the `start_work.py` CLI (`provider`, `branch-name`, `config-get`) from Tasks 1–3.
- Produces: the invocable `start-work` skill + `/start-work` command.

- [ ] **Step 1: Write SKILL.md**

Create `plugins/start-work/skills/start-work/SKILL.md` with this content:

````markdown
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
````

- [ ] **Step 2: Write the command**

Create `plugins/start-work/commands/start-work.md`:

```markdown
---
description: Start a piece of work — issue/ticket + branch, then hand off to brainstorming
argument-hint: "[issue number | #n | url | short description]"
allowed-tools: Bash, Skill
---

Invoke the `start-work` skill to begin work. If the user supplied an argument
($ARGUMENTS), treat it as the identifier or description to start from; otherwise
ask what they want to start. Follow the skill's steps exactly.
```

- [ ] **Step 3: Verify structure + references**

```bash
cd ~/code/claude-config
grep -c 'CLAUDE_PLUGIN_ROOT' plugins/start-work/skills/start-work/SKILL.md   # expect >= 3
grep -q 'name: start-work' plugins/start-work/skills/start-work/SKILL.md && echo "frontmatter OK"
claude plugin validate plugins/start-work 2>&1 | tail -3
```
Expected: count ≥ 3, `frontmatter OK`, validation passes (only the no-version warning).

- [ ] **Step 4: Commit**

```bash
git add plugins/start-work/skills plugins/start-work/commands
git commit -m "start-work: SKILL.md orchestration + /start-work command"
```

---

### Task 5: CI gate, marketplace entry, and docs

**Files:**
- Create: `.github/workflows/start-work.yml`
- Modify: `.claude-plugin/marketplace.json`
- Modify: `CLAUDE.md`, `README.md`

**Interfaces:**
- Consumes: the plugin (Tasks 1–4).

- [ ] **Step 1: Write the CI workflow**

Create `.github/workflows/start-work.yml`:

```yaml
name: start-work

on:
  pull_request:
    paths: ['plugins/start-work/**', '.github/workflows/start-work.yml']
  push:
    branches: [main]
    paths: ['plugins/start-work/**', '.github/workflows/start-work.yml']

defaults:
  run:
    working-directory: plugins/start-work

jobs:
  tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      - uses: actions/setup-python@v6
        with:
          python-version: "3.12"
      - name: Install pytest
        run: pip install pytest
      - name: Unit tests
        run: python3 -m pytest tests -q
```

Validate: `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/start-work.yml')); print('YAML OK')"` → `YAML OK`.

- [ ] **Step 2: Add the marketplace entry**

Append to the `plugins` array in `.claude-plugin/marketplace.json` (after `plugin-sync`):

```json
{
  "name": "start-work",
  "source": "./plugins/start-work",
  "description": "Turn a ticket or idea into a tracked issue + branch and hand off to planning."
}
```

Validate: `python3 -c "import json; n=[p['name'] for p in json.load(open('.claude-plugin/marketplace.json'))['plugins']]; print(n); assert n[-1]=='start-work'"`.

- [ ] **Step 3: Docs**

In `CLAUDE.md`: add `start-work` to the Layout block and a one-line note (Python-backed helpers run on `python3`, no venv; GitHub path only for now, GitLab/Jira is a later adapter). Do NOT touch the Plugin-source policy section.
In `README.md`: add `plugins/start-work/` to the tree and `start-work` to the individual-install plugin list.

Verify: `grep -c start-work CLAUDE.md README.md` → non-zero in each.

- [ ] **Step 4: Commit**

```bash
git add .github/workflows/start-work.yml .claude-plugin/marketplace.json CLAUDE.md README.md
git commit -m "start-work: CI gate, marketplace entry, docs"
```

---

### Task 6: Verify end-to-end (dogfood) + PR

**Files:** none (verification + PR).

- [ ] **Step 1: Full unit suite**

```bash
cd ~/code/claude-config/plugins/start-work && python3 -m pytest tests -q
```
Expected: all green.

- [ ] **Step 2: Dogfood the helpers against this repo**

```bash
cd ~/code/claude-config
python3 plugins/start-work/bin/start_work.py provider      # expect: github
python3 plugins/start-work/bin/start_work.py branch-name 99 "Dogfood the start work helper"
# expect: 99-dogfood-the-start-work-helper
```

- [ ] **Step 3: Dogfood the full flow on a throwaway issue**

Create a real throwaway issue in `claude-config`, run the skill's GitHub steps against it
(reference it, compute the branch, assign, check out the branch), confirm each `gh`/git command
succeeds, then clean up (delete the local branch; close the throwaway issue). Report exactly
which commands ran and their output. Do NOT push the throwaway branch.

- [ ] **Step 4: Push and open the PR**

```bash
cd ~/code/claude-config
git push -u origin 20-start-work-github-phase1
gh pr create --repo robsartin/claude-config --base main \
  --title "Build: start-work GitHub adapter (Phase 1)" \
  --body "Closes #20. GitHub path of the start-work skill: plugin + stdlib-Python helpers (provider detection, branch/slug naming, config) with pytest, SKILL.md orchestration, /start-work command, path-scoped CI, marketplace entry, docs. GitLab/Jira adapter and worklog are later phases; the worklog seam no-ops gracefully."
```

- [ ] **Step 5: Confirm CI green**

```bash
gh pr checks --repo robsartin/claude-config --watch
```
Expected: `start-work / tests` passes.

---

## Self-Review

**Spec coverage:**
- Plugin shape (skill + command + manifest) → Tasks 1, 4. ✓
- Provider detection from origin remote → Task 2. ✓
- Machine-local config, no secrets in repo → Task 1 (loader) + SKILL.md (reads local path). ✓
- Resolve-or-create item, `ready` label → Task 4 SKILL.md §2. ✓
- Branch `<ref>-<slug>` → Task 3. ✓
- Linkage = assign + status, draft PR deferred → Task 4 §4. ✓
- Worklog append seam, graceful no-op → Task 4 §5. ✓
- Hand off to brainstorming → Task 4 §6. ✓
- GitLab path stops "not yet" → Task 4 §1. ✓
- CI + marketplace + docs → Task 5. ✓
- Verify + dogfood → Task 6. ✓

**Placeholder scan:** helper code and tests are complete; SKILL.md and command content are given in full. The one `command -v /dev/null` line in SKILL.md §5 is explicitly labelled a placeholder-for-illustration with the concrete behavior described right after — acceptable as skill prose, not code to run.

**Type/name consistency:** `load_config`, `host_of`, `provider_for_remote`, `slugify`, `branch_name`, and CLI subcommands `provider` / `branch-name` / `config-get` are named identically across the plan, the tests, and the SKILL.md invocations. Plugin/skill/command/marketplace name all `start-work`.
