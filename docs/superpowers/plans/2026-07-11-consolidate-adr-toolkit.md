# Consolidate adr-toolkit into claude-config — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Vendor the `adr-claude-skill` project into `claude-config` as the `adr-toolkit` plugin, wire it into the marketplace with its CI, document the plugin-source policy, and (post-merge) archive the standalone repo.

**Architecture:** Clean-copy the tracked source of `~/code/adr-claude-skill` into `plugins/adr-toolkit/` via `git archive` (no artifacts, no history), relocate `SKILL.md` under `skills/adr-toolkit/` and rewire its paths to `${CLAUDE_PLUGIN_ROOT}`, reproduce the Python quality-gate CI as a path-scoped workflow, and add a marketplace entry. The runtime engine (packs + console scripts) is copied byte-for-byte; only file locations and the install/discovery mechanism change.

**Tech Stack:** Claude Code plugin marketplace (`marketplace.json` / `plugin.json`), Python 3.12 package (`adr-toolkit`, hatchling, ruff/mypy/pytest/coverage), GitHub Actions.

## Global Constraints

- Never commit to `main`; all work on branch `1-consolidate-adr-toolkit`, merged via squash PR (issue #1).
- Plugins here omit a `version` field (every push = an update); do NOT add `version` to `plugin.json`.
- Only `plugin.json` lives inside a `.claude-plugin/` dir; component folders (`skills/`, `bin/`, etc.) sit at the plugin root.
- Skill `name:` frontmatter stays exactly `adr-toolkit` (stable invocation name).
- Python floor: `requires-python >=3.12`; CI uses Python `3.12`.
- Coverage gate: line > 80%, branch > 65% (enforced by `scripts/check_coverage.py`).
- `ruff format --check` AND `ruff check` AND `mypy` AND `pytest` must all pass before pushing (replay the full gate set, not a subset).
- Source of the archived repo is authoritative until the PR merges; §7 (archival) runs only after merge + verification.

## File Structure

Created:
- `plugins/adr-toolkit/.claude-plugin/plugin.json` — plugin manifest.
- `plugins/adr-toolkit/skills/adr-toolkit/SKILL.md` — the skill (relocated + rewired).
- `plugins/adr-toolkit/{src,packs,bin,scripts,tests,examples,docs}/…`, `packs.yaml`, `pyproject.toml`, `README.md`, `LICENSE`, `.gitignore` — vendored Python package (copied).
- `.github/workflows/adr-toolkit.yml` — path-scoped quality-gate CI (repo's first workflow).

Modified:
- `.claude-plugin/marketplace.json` — add the `adr-toolkit` entry.
- `CLAUDE.md`, `README.md` — plugin-source policy + adr-toolkit.

Not carried: `.venv/`, `.coverage`, `*_cache/`, `.superpowers/` (untracked, auto-skipped), the tracked self-symlink `adr-claude-skill`, the nested `.github/`, and `docs/superpowers/` (adr's own scratch).

---

### Task 1: Vendor the adr source tree + plugin manifest

**Files:**
- Create: `plugins/adr-toolkit/` (whole tracked tree via `git archive`)
- Create: `plugins/adr-toolkit/.claude-plugin/plugin.json`
- Prune: `plugins/adr-toolkit/.github`, `plugins/adr-toolkit/adr-claude-skill` (self-symlink), `plugins/adr-toolkit/docs/superpowers`

**Interfaces:**
- Produces: a self-contained Python package at `plugins/adr-toolkit/` whose test suite passes when run with `working-directory: plugins/adr-toolkit`. Console scripts `adr-toolkit` / `adr-supersede` (from `pyproject.toml [project.scripts]`). Data at `plugins/adr-toolkit/packs.yaml` + `plugins/adr-toolkit/packs/`.

- [ ] **Step 1: Clean-copy the tracked tree**

```bash
cd ~/code/claude-config
mkdir -p plugins/adr-toolkit
git -C ~/code/adr-claude-skill archive HEAD | tar -x -C plugins/adr-toolkit
# prune what must not come along
rm -rf plugins/adr-toolkit/.github \
       plugins/adr-toolkit/adr-claude-skill \
       plugins/adr-toolkit/docs/superpowers
```

- [ ] **Step 2: Verify the copy is clean and complete**

```bash
cd ~/code/claude-config
ls plugins/adr-toolkit                      # expect: SKILL.md README.md LICENSE pyproject.toml packs.yaml bin scripts src tests examples packs docs .gitignore
test -f plugins/adr-toolkit/src/adr_toolkit/cli.py && echo "package OK"
test ! -e plugins/adr-toolkit/adr-claude-skill && echo "symlink pruned"
test ! -d plugins/adr-toolkit/.github && echo "nested .github pruned"
```
Expected: `package OK`, `symlink pruned`, `nested .github pruned`.

- [ ] **Step 3: Prove the suite runs green in its new home**

```bash
cd ~/code/claude-config/plugins/adr-toolkit
python3.12 -m venv .venv && . .venv/bin/activate
pip install -q -e '.[dev]'
ruff check . && ruff format --check . && mypy && coverage run -m pytest
python scripts/lint_adrs.py
coverage json -o coverage.json && python scripts/check_coverage.py coverage.json
deactivate
```
Expected: all commands exit 0 (ruff/mypy clean, pytest green, coverage gate passes). `.venv/`, `.coverage`, `coverage.json` are gitignored by the copied `.gitignore`.

- [ ] **Step 4: Write the plugin manifest**

Create `plugins/adr-toolkit/.claude-plugin/plugin.json`:

```json
{
  "name": "adr-toolkit",
  "description": "Scaffold a stack-appropriate docs/adr/ from composable ADR packs.",
  "author": { "name": "Rob Sartin" },
  "keywords": ["adr", "architecture", "documentation", "scaffolding"]
}
```

- [ ] **Step 5: Commit**

```bash
cd ~/code/claude-config
git add plugins/adr-toolkit
git commit -m "Vendor adr-claude-skill source as adr-toolkit plugin"
```

---

### Task 2: Relocate SKILL.md and rewire paths; trim install.sh

**Files:**
- Move: `plugins/adr-toolkit/SKILL.md` → `plugins/adr-toolkit/skills/adr-toolkit/SKILL.md`
- Modify: `plugins/adr-toolkit/skills/adr-toolkit/SKILL.md` (paths)
- Modify: `plugins/adr-toolkit/bin/install.sh` (drop skill symlink)

**Interfaces:**
- Consumes: `${CLAUDE_PLUGIN_ROOT}` — Claude Code sets this to the plugin root (the dir containing `.claude-plugin/`), i.e. the vendored `plugins/adr-toolkit/` at install time.
- Produces: a skill discoverable at the default scan path `skills/adr-toolkit/SKILL.md` whose runtime commands resolve packs/engine via `${CLAUDE_PLUGIN_ROOT}`.

- [ ] **Step 1: Move the skill into the conventional location**

```bash
cd ~/code/claude-config/plugins/adr-toolkit
mkdir -p skills/adr-toolkit
git mv SKILL.md skills/adr-toolkit/SKILL.md
```

- [ ] **Step 2: Rewire runtime paths in SKILL.md**

In `plugins/adr-toolkit/skills/adr-toolkit/SKILL.md`, make these replacements (the file currently references the toolkit root as `.`, `<toolkit>`, `<tk>`):

- The install step `./bin/install.sh` → `${CLAUDE_PLUGIN_ROOT}/bin/install.sh`
- Emit/reconcile command args: `--manifest <toolkit>/packs.yaml` → `--manifest ${CLAUDE_PLUGIN_ROOT}/packs.yaml`; `--packs-dir <toolkit>/packs` → `--packs-dir ${CLAUDE_PLUGIN_ROOT}/packs`; every remaining `<toolkit>` / `<tk>` → `${CLAUDE_PLUGIN_ROOT}`.
- Doc links relative to the new depth: `[README.md](README.md)` → `[README.md](../../README.md)`; `docs/design/2026-07-08-adr-reconciliation-design.md` → `../../docs/design/2026-07-08-adr-reconciliation-design.md`.

- [ ] **Step 3: Verify no stale relative references remain**

```bash
cd ~/code/claude-config/plugins/adr-toolkit
grep -nE '<toolkit>|<tk>|\./bin/install\.sh|\]\(README\.md\)|\]\(docs/' skills/adr-toolkit/SKILL.md
```
Expected: no output (all rewired). Also confirm the intended tokens exist:
```bash
grep -c 'CLAUDE_PLUGIN_ROOT' skills/adr-toolkit/SKILL.md   # expect: >= 3
```

- [ ] **Step 4: Trim `bin/install.sh` — keep venv/console-script, drop the skill symlink**

Edit `plugins/adr-toolkit/bin/install.sh`: remove the block that symlinks the skill into `~/.claude/skills/` (and any related echo). Keep venv creation + `pip install -e '.[dev]'` (or the existing editable install). Reword any user-facing echo so it no longer claims to register the skill (the marketplace does that now). Verify:
```bash
grep -c '.claude/skills' plugins/adr-toolkit/bin/install.sh   # expect: 0
bash -n plugins/adr-toolkit/bin/install.sh && echo "syntax OK"
```
Expected: `0`, then `syntax OK`.

- [ ] **Step 5: Commit**

```bash
cd ~/code/claude-config
git add plugins/adr-toolkit/skills plugins/adr-toolkit/bin/install.sh
git commit -m "Relocate adr SKILL.md under skills/ and rewire paths to CLAUDE_PLUGIN_ROOT"
```

---

### Task 3: Path-scoped CI workflow

**Files:**
- Create: `.github/workflows/adr-toolkit.yml`

**Interfaces:**
- Consumes: the vendored package at `plugins/adr-toolkit/` (Task 1).
- Produces: a CI job that runs the full quality gate only when `plugins/adr-toolkit/**` or the workflow file changes.

- [ ] **Step 1: Write the workflow**

Create `.github/workflows/adr-toolkit.yml`:

```yaml
name: adr-toolkit

on:
  pull_request:
    paths: ['plugins/adr-toolkit/**', '.github/workflows/adr-toolkit.yml']
  push:
    branches: [main]
    paths: ['plugins/adr-toolkit/**', '.github/workflows/adr-toolkit.yml']

defaults:
  run:
    working-directory: plugins/adr-toolkit

jobs:
  quality-gate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      - uses: actions/setup-python@v6
        with:
          python-version: "3.12"
      - name: Install
        run: pip install -e '.[dev]'
      - name: Lint (ruff check)
        run: ruff check .
      - name: Format check (ruff format)
        run: ruff format --check .
      - name: Types (mypy --strict)
        run: mypy
      - name: Tests
        run: coverage run -m pytest
      - name: Lint ADR content
        run: python scripts/lint_adrs.py
      - name: Coverage gate (line > 80%, branch > 65%)
        run: |
          coverage json -o coverage.json
          python scripts/check_coverage.py coverage.json
      - name: Examples are up to date
        run: |
          ./bin/gen-examples.sh
          if [ -n "$(git status --porcelain examples/)" ]; then
            echo "examples/ is out of date — run ./bin/gen-examples.sh and commit:"
            git status --porcelain examples/
            exit 1
          fi
```

- [ ] **Step 2: Validate YAML**

```bash
cd ~/code/claude-config
python3 -c "import yaml,sys; yaml.safe_load(open('.github/workflows/adr-toolkit.yml')); print('YAML OK')"
```
Expected: `YAML OK`.

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/adr-toolkit.yml
git commit -m "Add path-scoped CI for adr-toolkit plugin"
```

---

### Task 4: Marketplace entry

**Files:**
- Modify: `.claude-plugin/marketplace.json`

**Interfaces:**
- Consumes: plugin root `plugins/adr-toolkit/` with its `.claude-plugin/plugin.json` (Task 1).
- Produces: a marketplace listing both `voice` and `adr-toolkit`.

- [ ] **Step 1: Add the entry**

In `.claude-plugin/marketplace.json`, append to the `plugins` array (after `voice`):

```json
{
  "name": "adr-toolkit",
  "source": "./plugins/adr-toolkit",
  "description": "Scaffold a stack-appropriate docs/adr/ from composable ADR packs."
}
```

- [ ] **Step 2: Validate JSON and both entries present**

```bash
cd ~/code/claude-config
python3 -c "import json; d=json.load(open('.claude-plugin/marketplace.json')); n=[p['name'] for p in d['plugins']]; print(n); assert n==['voice','adr-toolkit'], n"
```
Expected: `['voice', 'adr-toolkit']`.

- [ ] **Step 3: Commit**

```bash
git add .claude-plugin/marketplace.json
git commit -m "List adr-toolkit in the marketplace"
```

---

### Task 5: Document the plugin-source policy

**Files:**
- Modify: `CLAUDE.md`
- Modify: `README.md`

**Interfaces:**
- Consumes: the final layout from Tasks 1–4.
- Produces: written policy + updated layout/install docs.

- [ ] **Step 1: Update CLAUDE.md**

In `CLAUDE.md`: (a) add `adr-toolkit` to the Layout block; (b) add a "Plugin-source policy" subsection with this table and note that adr-toolkit is Python-backed and needs a one-time `${CLAUDE_PLUGIN_ROOT}/bin/install.sh` venv bootstrap:

```markdown
## Plugin-source policy

| Case | Handling | marketplace source |
| --- | --- | --- |
| Mine, source belongs here (`voice`) | Vendor under `plugins/<name>/` | `"./plugins/<name>"` |
| Mine, was a separate repo (`adr-toolkit`) | Vendor + archive the old repo | `"./plugins/<name>"` |
| Someone else's plugin | Catalog, don't copy their code | `{"source":{"source":"github","repo":"owner/repo"}}` or `/plugin marketplace add owner/repo` |
```

- [ ] **Step 2: Update README.md**

In `README.md`: add `plugins/adr-toolkit/` to the "What's here" tree and an install line `/plugin install adr-toolkit@claude-config` alongside the existing `voice` one.

- [ ] **Step 3: Verify references**

```bash
cd ~/code/claude-config
grep -c 'adr-toolkit' CLAUDE.md README.md
```
Expected: non-zero count in each file.

- [ ] **Step 4: Commit**

```bash
git add CLAUDE.md README.md
git commit -m "Document plugin-source policy and adr-toolkit"
```

---

### Task 6: End-to-end verification + PR

**Files:** none (verification + PR).

**Interfaces:**
- Consumes: the complete branch (Tasks 1–5).

- [ ] **Step 1: Full gate replay (repo's CI locally)**

```bash
cd ~/code/claude-config/plugins/adr-toolkit
. .venv/bin/activate 2>/dev/null || { python3.12 -m venv .venv && . .venv/bin/activate && pip install -q -e '.[dev]'; }
ruff check . && ruff format --check . && mypy && coverage run -m pytest && python scripts/lint_adrs.py
coverage json -o coverage.json && python scripts/check_coverage.py coverage.json
./bin/gen-examples.sh && git -C ~/code/claude-config status --porcelain plugins/adr-toolkit/examples/
deactivate
```
Expected: all green; the `status --porcelain` line prints nothing (examples already fresh).

- [ ] **Step 2: Install the marketplace locally and confirm both plugins load**

```
/plugin marketplace add ~/code/claude-config
/plugin install adr-toolkit@claude-config
```
Confirm both `voice` and `adr-toolkit` appear and load without error. (If a prior marketplace is registered, use `/plugin marketplace update claude-config`.)

- [ ] **Step 3: Drive adr-toolkit end-to-end**

Bootstrap the engine, then emit into a throwaway target and confirm output:
```bash
"${CLAUDE_PLUGIN_ROOT:-$HOME/code/claude-config/plugins/adr-toolkit}/bin/install.sh"
mkdir -p /private/tmp/claude-501/adr-smoke && cd /private/tmp/claude-501/adr-smoke
adr-toolkit --manifest "$HOME/code/claude-config/plugins/adr-toolkit/packs.yaml" \
  --packs-dir "$HOME/code/claude-config/plugins/adr-toolkit/packs" \
  --target ./docs/adr --project adr-smoke --pack universal --pack python
ls docs/adr    # expect NNNN-*.md files + README.md
```
Expected: numbered ADR files and a generated `docs/adr/README.md`.

- [ ] **Step 4: Push and open the PR**

```bash
cd ~/code/claude-config
git push -u origin 1-consolidate-adr-toolkit
gh pr create --repo robsartin/claude-config --base main \
  --title "Consolidate adr-toolkit into claude-config marketplace" \
  --body "Closes #1. Vendors adr-claude-skill as the adr-toolkit plugin (clean copy), relocates SKILL.md under skills/ with \${CLAUDE_PLUGIN_ROOT} paths, adds path-scoped CI, lists it in the marketplace, and documents the plugin-source policy. Standalone repo archival is a follow-up after merge + verification."
```

- [ ] **Step 5: Confirm CI green on the PR**

```bash
gh pr checks --repo robsartin/claude-config --watch
```
Expected: `adr-toolkit / quality-gate` passes.

---

### Task 7: Retire the standalone repo (POST-MERGE ONLY)

**Do not start until the PR is merged and Task 6 verification passed.** Archiving is a public-facing, outward change — confirm with Rob before executing.

**Files:** (in `~/code/adr-claude-skill`) `README.md`.

- [ ] **Step 1: README pointer on the standalone repo**

In `~/code/adr-claude-skill/README.md`, add a top banner: "**Moved.** This project now lives in [robsartin/claude-config](https://github.com/robsartin/claude-config) as the `adr-toolkit` plugin. Install it from that marketplace." Commit + push (its own branch/PR if branch protection requires; otherwise a direct README commit is acceptable for an about-to-be-archived repo — confirm with Rob).

- [ ] **Step 2: Archive**

```bash
gh repo archive robsartin/adr-claude-skill --yes
```
(Reversible via `gh repo unarchive`.)

- [ ] **Step 3: Remove the stale local symlink**

```bash
rm -f ~/.claude/skills/adr-toolkit    # was -> ~/code/adr-claude-skill
```

- [ ] **Step 4: Flag the scheduled task**

Tell Rob the `resume-adr-claude-skill` scheduled task (`~/.claude/scheduled-tasks/`) is now stale; deleting it is his call (out of scope here).

---

## Self-Review

**Spec coverage:**
- Plugin-source policy → Task 5. ✓
- Vendor clean copy, skip artifacts → Task 1 (`git archive` + prune). ✓
- plugin.json → Task 1 Step 4. ✓
- SKILL.md relocate + `${CLAUDE_PLUGIN_ROOT}` rewiring + doc links → Task 2. ✓
- install.sh trimmed (drop `~/.claude/skills` symlink) → Task 2 Step 4. ✓
- CI moved, path-scoped, working-directory, all steps incl. ADR-lint/coverage/examples → Task 3. ✓
- marketplace entry → Task 4. ✓
- CLAUDE.md/README docs → Task 5. ✓
- Archive standalone + README pointer + remove local symlink + flag scheduled task → Task 7 (post-merge). ✓
- Verification: suite green in new home (Task 1 Step 3 + Task 6 Step 1), both plugins load (Task 6 Step 2), adr emits sample (Task 6 Step 3), CI green (Task 6 Step 5). ✓

**Placeholder scan:** No TBD/TODO; every code/edit step shows exact commands or the exact replacements to make.

**Type/name consistency:** Console scripts `adr-toolkit`/`adr-supersede`, package `adr_toolkit`, gate scripts `scripts/lint_adrs.py` + `scripts/check_coverage.py`, plugin name `adr-toolkit`, source path `./plugins/adr-toolkit` — consistent across all tasks and the marketplace/manifest.
