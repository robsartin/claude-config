# Vendor wordpress-block-theme into claude-config — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Vendor the standalone `robsartin/claude-wp-theme-skill` into `claude-config` as the `wordpress-block-theme` plugin, with a full CI gate (static validators + live wp-env/theme-check), and (post-merge) archive the standalone repo.

**Architecture:** Clean-copy the tracked upstream source via `git archive` into `plugins/wordpress-block-theme/`, relocate `SKILL.md` under `skills/` and rewire its paths using two distinct rules (plugin-root resources → `${CLAUDE_PLUGIN_ROOT}`; scaffolded-theme harness scripts → left relative), drop the obsolete `bin/install.sh`, add a path-scoped two-job CI workflow, and list the plugin in the marketplace. The starter theme and its harness are copied byte-for-byte.

**Tech Stack:** Claude Code plugin marketplace (`marketplace.json`/`plugin.json`), a static WordPress block-theme starter, Python 3 validators (stdlib only), bash harness, `@wordpress/env` + PHP Theme Check, GitHub Actions.

## Global Constraints

- Never commit to `main`; all work on branch `3-vendor-wordpress-block-theme`, merged via squash PR (issue #3).
- Plugins here omit a `version` field (every push = an update); do NOT add `version` to `plugin.json`.
- Only `plugin.json` lives inside a `.claude-plugin/` dir; component folders sit at the plugin root.
- Skill `name:` frontmatter stays exactly `wordpress-block-theme` (stable invocation name).
- Clean copy, no git-history graft; artifacts (`node_modules/`, `.venv/`, `*.zip`, `.superpowers/`) must not be committed (they are untracked/gitignored upstream).
- **Two path-classes in SKILL.md (do NOT blanket-replace):** plugin-root resources (`assets/starter/`, `references/*.md`, `bin/update-starter.sh`, `MANIFEST.md`) → prefix `${CLAUDE_PLUGIN_ROOT}/`; scaffolded-theme harness refs (`bin/check-all.sh`, `bin/theme-check.sh`, `bin/screenshot.sh`, `bin/package.sh`) → leave exactly as `bin/…`.
- Static gate runs on stock `python3` (validators are stdlib-only); no venv.
- CI Python `3.12`; `actions/checkout@v5`, `actions/setup-python@v6`, `actions/setup-node@v4` (Node 20).

## File Structure

Created:
- `plugins/wordpress-block-theme/.claude-plugin/plugin.json` — manifest.
- `plugins/wordpress-block-theme/skills/wordpress-block-theme/SKILL.md` — relocated + rewired.
- `plugins/wordpress-block-theme/{assets/starter,references,bin}/…`, `MANIFEST.md`, `README.md`, `.gitignore` — vendored.
- `.github/workflows/wordpress-block-theme.yml` — path-scoped, two jobs.

Modified:
- `.claude-plugin/marketplace.json` — add the `wordpress-block-theme` entry.
- `CLAUDE.md`, `README.md` — layout + install line.

Not carried: `bin/install.sh` (dropped in Task 3), `docs/` (upstream's own `docs/superpowers/` scratch), and all artifacts.

---

### Task 1: Vendor the wp source + plugin manifest

**Files:**
- Create: `plugins/wordpress-block-theme/` (tracked tree via `git archive`)
- Create: `plugins/wordpress-block-theme/.claude-plugin/plugin.json`
- Prune: `plugins/wordpress-block-theme/docs`

**Interfaces:**
- Produces: a self-contained plugin dir whose static gate (`bash assets/starter/bin/check-all.sh`) and maintainer smoke test (`bash bin/test-update-starter.sh`) both pass. `${CLAUDE_PLUGIN_ROOT}`-resolvable resources at `assets/starter/`, `references/`, `MANIFEST.md`, `bin/update-starter.sh`.
- Note for Task 3: `bin/install.sh` is intentionally KEPT by this task and removed in Task 3 (together with its README references, so no commit has a dangling reference).

- [ ] **Step 1: Clean-copy the tracked upstream tree**

The local clone was deleted, so clone fresh to a temp dir and archive from it:

```bash
cd ~/code/claude-config
TMP=$(mktemp -d)
git clone --depth 1 https://github.com/robsartin/claude-wp-theme-skill.git "$TMP/wp"
mkdir -p plugins/wordpress-block-theme
git -C "$TMP/wp" archive HEAD | tar -x -C plugins/wordpress-block-theme
rm -rf plugins/wordpress-block-theme/docs
rm -rf "$TMP"
```

- [ ] **Step 2: Verify the copy is clean and complete**

```bash
cd ~/code/claude-config
ls plugins/wordpress-block-theme            # expect: SKILL.md README.md MANIFEST.md .gitignore assets references bin
test -d plugins/wordpress-block-theme/assets/starter && echo "starter OK"
test -f plugins/wordpress-block-theme/references/block-markup-rules.md && echo "references OK"
test ! -d plugins/wordpress-block-theme/docs && echo "docs pruned"
git status --porcelain plugins/wordpress-block-theme | grep -E 'node_modules|\.zip$|\.venv|\.superpowers' && echo "ARTIFACT LEAK" || echo "no artifacts staged"
```
Expected: `starter OK`, `references OK`, `docs pruned`, `no artifacts staged`.

- [ ] **Step 3: Prove both gates pass in the new home**

```bash
cd ~/code/claude-config/plugins/wordpress-block-theme
bash assets/starter/bin/check-all.sh
bash bin/test-update-starter.sh
```
Expected: `check-all.sh` ends `All static gates passed.`; smoke ends `PASS: update-starter smoke test`.

- [ ] **Step 4: Write the plugin manifest**

Create `plugins/wordpress-block-theme/.claude-plugin/plugin.json`:

```json
{
  "name": "wordpress-block-theme",
  "description": "Build a WordPress block theme (FSE) from a canonical, self-validating starter.",
  "author": { "name": "Rob Sartin" },
  "keywords": ["wordpress", "block-theme", "fse", "gutenberg", "theme"]
}
```

- [ ] **Step 5: Commit**

```bash
cd ~/code/claude-config
git add plugins/wordpress-block-theme
git commit -m "Vendor claude-wp-theme-skill source as wordpress-block-theme plugin"
```

---

### Task 2: Relocate SKILL.md and rewire paths (two classes)

**Files:**
- Move: `plugins/wordpress-block-theme/SKILL.md` → `plugins/wordpress-block-theme/skills/wordpress-block-theme/SKILL.md`
- Modify: that SKILL.md (paths)

**Interfaces:**
- Consumes: `${CLAUDE_PLUGIN_ROOT}` (plugin install root, the dir containing `.claude-plugin/`).
- Produces: a skill at the default scan path with plugin-root resources addressed via `${CLAUDE_PLUGIN_ROOT}` and scaffolded-theme harness refs left relative.

- [ ] **Step 1: Move the skill into the conventional location**

```bash
cd ~/code/claude-config/plugins/wordpress-block-theme
mkdir -p skills/wordpress-block-theme
git mv SKILL.md skills/wordpress-block-theme/SKILL.md
```

- [ ] **Step 2: Rewire Class-R (plugin-root resource) references**

In `skills/wordpress-block-theme/SKILL.md`, prefix each of these with `${CLAUDE_PLUGIN_ROOT}/` (they are the resources the skill opens or copies FROM the plugin):

- `assets/starter/` (the scaffold-source in step 1) → `${CLAUDE_PLUGIN_ROOT}/assets/starter/`
- `assets/starter/patterns/card-section.php` → `${CLAUDE_PLUGIN_ROOT}/assets/starter/patterns/card-section.php`
- `assets/starter/parts/footer.html` → `${CLAUDE_PLUGIN_ROOT}/assets/starter/parts/footer.html`
- every `references/<name>.md` mention (`block-markup-rules.md`, `wordpress-com-deploy.md`, `editor-guide.md`, `development.md`) → `${CLAUDE_PLUGIN_ROOT}/references/<name>.md`
- `bin/update-starter.sh` (the maintainer tool) → `${CLAUDE_PLUGIN_ROOT}/bin/update-starter.sh`
- `MANIFEST.md` → `${CLAUDE_PLUGIN_ROOT}/MANIFEST.md`

Leave the elliptical prose `plain-section.php` (line ~42) as-is — it is human-readable prose naming a sibling of the card pattern, not a standalone resolvable path.

- [ ] **Step 3: Confirm Class-T (scaffolded-theme) refs are UNCHANGED**

These run inside the user's copied theme and must stay bare. Verify they still read exactly `bin/<script>`:

```bash
cd ~/code/claude-config/plugins/wordpress-block-theme
grep -nE '`bin/(check-all|theme-check|screenshot|package)\.sh`' skills/wordpress-block-theme/SKILL.md
```
Expected: four lines, each still `bin/…` with NO `${CLAUDE_PLUGIN_ROOT}` prefix.

- [ ] **Step 4: Verify no Class-R path was left bare**

```bash
cd ~/code/claude-config/plugins/wordpress-block-theme
# these should now only ever appear with the CLAUDE_PLUGIN_ROOT prefix or inside prose lists — inspect each hit:
grep -nE '(^|[^/{])assets/starter|(^|[^/{])references/|(^|[^/{])bin/update-starter|(^|[^/{])MANIFEST\.md' skills/wordpress-block-theme/SKILL.md
grep -c 'CLAUDE_PLUGIN_ROOT' skills/wordpress-block-theme/SKILL.md   # expect: >= 8
```
Expected: the first grep shows no *bare* Class-R resource path (each occurrence is prefixed or is the `plain-section.php` prose); `CLAUDE_PLUGIN_ROOT` count >= 8. Fix any bare Class-R hit before committing.

- [ ] **Step 5: Re-run the static gate (nothing runtime changed, but confirm no accidental edit to assets)**

```bash
cd ~/code/claude-config/plugins/wordpress-block-theme
bash assets/starter/bin/check-all.sh
```
Expected: `All static gates passed.`

- [ ] **Step 6: Commit**

```bash
cd ~/code/claude-config
git add plugins/wordpress-block-theme/skills
git commit -m "Relocate wp SKILL.md under skills/ and rewire plugin-root paths to CLAUDE_PLUGIN_ROOT"
```

---

### Task 3: Drop bin/install.sh and fix the plugin README

**Files:**
- Delete: `plugins/wordpress-block-theme/bin/install.sh`
- Modify: `plugins/wordpress-block-theme/README.md`

**Interfaces:**
- Consumes: the vendored tree (Task 1).
- Produces: a plugin with no obsolete symlink installer and a README that describes marketplace install only (no dangling `install.sh` references).

- [ ] **Step 1: Read the current README, then remove install.sh**

```bash
cd ~/code/claude-config/plugins/wordpress-block-theme
sed -n '1,60p' README.md      # read the Install section + file list first
git rm bin/install.sh
```

- [ ] **Step 2: Rewrite the README Install section**

In `plugins/wordpress-block-theme/README.md`, replace the install-methods section (the `bin/install.sh` helper description at ~L31, the `./bin/install.sh` / `--clone` snippet at ~L35-36) and the `bin/install.sh` file-list bullet (~L52) with marketplace install:

```markdown
## Install

Install via the claude-config marketplace:

```bash
/plugin marketplace add robsartin/claude-config   # once, per machine
/plugin install wordpress-block-theme@claude-config
```
```

Remove the `bin/install.sh` bullet from the file list. Leave every other README section (and all of `MANIFEST.md`) untouched.

- [ ] **Step 3: Verify no dangling install.sh reference remains**

```bash
cd ~/code/claude-config/plugins/wordpress-block-theme
grep -rn 'install.sh' README.md MANIFEST.md skills/ && echo "STILL REFERENCED" || echo "clean"
test ! -e bin/install.sh && echo "install.sh gone"
```
Expected: `clean`, `install.sh gone`.

- [ ] **Step 4: Commit**

```bash
cd ~/code/claude-config
git add plugins/wordpress-block-theme/bin plugins/wordpress-block-theme/README.md
git commit -m "Drop obsolete bin/install.sh; README installs via marketplace"
```

---

### Task 4: Full CI gate — `.github/workflows/wordpress-block-theme.yml`

**Files:**
- Create: `.github/workflows/wordpress-block-theme.yml`

**Interfaces:**
- Consumes: the vendored plugin (Tasks 1-3).
- Produces: a path-scoped workflow with a fast `static` job and a Docker `theme-check` job.

- [ ] **Step 1: Write the workflow**

Create `.github/workflows/wordpress-block-theme.yml`:

```yaml
name: wordpress-block-theme

on:
  pull_request:
    paths: ['plugins/wordpress-block-theme/**', '.github/workflows/wordpress-block-theme.yml']
  push:
    branches: [main]
    paths: ['plugins/wordpress-block-theme/**', '.github/workflows/wordpress-block-theme.yml']

jobs:
  static:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: plugins/wordpress-block-theme
    steps:
      - uses: actions/checkout@v5
      - uses: actions/setup-python@v6
        with:
          python-version: "3.12"
      - name: Static gates (theme.json, contrast, templates, patterns, markup)
        run: bash assets/starter/bin/check-all.sh
      - name: update-starter smoke test
        run: bash bin/test-update-starter.sh

  theme-check:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: plugins/wordpress-block-theme/assets/starter
    steps:
      - uses: actions/checkout@v5
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
      - name: Theme Check (live, wp-env)
        run: bash bin/theme-check.sh
      - name: Tear down wp-env
        if: always()
        run: npx @wordpress/env stop || true
```

- [ ] **Step 2: Validate YAML**

```bash
cd ~/code/claude-config
python3 -c "import yaml; d=yaml.safe_load(open('.github/workflows/wordpress-block-theme.yml')); print(sorted(d['jobs'])); assert sorted(d['jobs'])==['static','theme-check']"
```
Expected: `['static', 'theme-check']`.

- [ ] **Step 3: Sanity-check the path filter includes the workflow file**

```bash
cd ~/code/claude-config
grep -c "workflows/wordpress-block-theme.yml" .github/workflows/wordpress-block-theme.yml   # expect: >= 2 (both triggers)
```
Expected: `2`.

- [ ] **Step 4: Commit**

```bash
git add .github/workflows/wordpress-block-theme.yml
git commit -m "Add full CI gate for wordpress-block-theme (static + wp-env theme-check)"
```

---

### Task 5: Marketplace entry

**Files:**
- Modify: `.claude-plugin/marketplace.json`

**Interfaces:**
- Consumes: plugin root `plugins/wordpress-block-theme/` with its `.claude-plugin/plugin.json`.
- Produces: a marketplace listing all three plugins in order.

- [ ] **Step 1: Append the entry**

In `.claude-plugin/marketplace.json`, append to the `plugins` array (after `adr-toolkit`):

```json
{
  "name": "wordpress-block-theme",
  "source": "./plugins/wordpress-block-theme",
  "description": "Build a WordPress block theme (FSE) from a canonical, self-validating starter."
}
```

- [ ] **Step 2: Validate JSON and order**

```bash
cd ~/code/claude-config
python3 -c "import json; d=json.load(open('.claude-plugin/marketplace.json')); n=[p['name'] for p in d['plugins']]; print(n); assert n==['voice','adr-toolkit','wordpress-block-theme'], n"
```
Expected: `['voice', 'adr-toolkit', 'wordpress-block-theme']`.

- [ ] **Step 3: Commit**

```bash
git add .claude-plugin/marketplace.json
git commit -m "List wordpress-block-theme in the marketplace"
```

---

### Task 6: Repo docs (CLAUDE.md + README)

**Files:**
- Modify: `CLAUDE.md`
- Modify: `README.md`

**Interfaces:**
- Consumes: the final layout from Tasks 1-5.
- Produces: repo docs reflecting the third plugin. (The plugin-source policy table already exists from the adr work — do NOT re-add it.)

- [ ] **Step 1: Update CLAUDE.md layout**

In `CLAUDE.md`, add `plugins/wordpress-block-theme/` to the Layout block alongside `voice` and `adr-toolkit`, noting it is a content-and-tooling skill (a starter theme + references; static gates run on `python3`, the live check uses `@wordpress/env`). Do NOT touch the existing Plugin-source policy section.

- [ ] **Step 2: Update README.md**

In `README.md`: add `plugins/wordpress-block-theme/` to the "what's here" tree and an install line `/plugin install wordpress-block-theme@claude-config` alongside the existing `voice` / `adr-toolkit` ones.

- [ ] **Step 3: Verify references**

```bash
cd ~/code/claude-config
grep -c 'wordpress-block-theme' CLAUDE.md README.md
```
Expected: non-zero in each.

- [ ] **Step 4: Commit**

```bash
git add CLAUDE.md README.md
git commit -m "Document wordpress-block-theme plugin"
```

---

### Task 7: Verification + PR

**Files:** none (verification + PR).

**Interfaces:**
- Consumes: the complete branch (Tasks 1-6).

- [ ] **Step 1: Local gate replay (what CAN run without Docker)**

```bash
cd ~/code/claude-config/plugins/wordpress-block-theme
bash assets/starter/bin/check-all.sh
bash bin/test-update-starter.sh
```
Expected: `All static gates passed.` and `PASS: update-starter smoke test`. The live `theme-check` job is NOT run locally (needs Docker) — it is proven by CI in Step 4. Report which ran locally vs. via CI plainly.

- [ ] **Step 2: Install the marketplace locally and confirm all three plugins load**

```
/plugin marketplace add ~/code/claude-config
/plugin install wordpress-block-theme@claude-config
```
Confirm `voice`, `adr-toolkit`, and `wordpress-block-theme` all load. (Use `/plugin marketplace update claude-config` if a prior copy is registered.) This interactive step is run by the human, not the agent.

- [ ] **Step 3: Push and open the PR**

```bash
cd ~/code/claude-config
git push -u origin 3-vendor-wordpress-block-theme
gh pr create --repo robsartin/claude-config --base main \
  --title "Vendor wordpress-block-theme into claude-config marketplace" \
  --body "Closes #3. Vendors claude-wp-theme-skill as the wordpress-block-theme plugin (clean copy), relocates SKILL.md under skills/ with two-path-class rewiring, drops the obsolete bin/install.sh, adds a full CI gate (static validators + wp-env/theme-check), lists it in the marketplace, and updates repo docs. Standalone-repo archival is a follow-up after merge + verification."
```

- [ ] **Step 4: Confirm CI green on the PR (both jobs)**

```bash
gh pr checks --repo robsartin/claude-config --watch
```
Expected: both `static` and `theme-check` pass. The `theme-check` job is the live proof of the wp-env gate.

---

### Task 8: Retire the standalone repo (POST-MERGE ONLY)

**Do not start until the PR is merged and Task 7 verification passed.** Archiving is public-facing — confirm with Rob before executing.

**Files:** (in a fresh clone of `robsartin/claude-wp-theme-skill`) `README.md`.

- [ ] **Step 1: README pointer on the standalone repo**

The local clone was deleted, so:

```bash
TMP=$(mktemp -d)
git clone https://github.com/robsartin/claude-wp-theme-skill.git "$TMP/wp"
cd "$TMP/wp"
# Add a top-of-README banner: "**Moved.** This project now lives in
# robsartin/claude-config as the wordpress-block-theme plugin. Install it from
# that marketplace." Then:
git add README.md
git commit -m "Point README at claude-config (moved to wordpress-block-theme plugin)"
git push
```
(If branch protection blocks a direct push, open a one-commit PR; for an about-to-be-archived repo a direct README commit is acceptable — confirm with Rob.)

- [ ] **Step 2: Archive**

```bash
gh repo archive robsartin/claude-wp-theme-skill --yes
```
(Reversible via `gh repo unarchive`.)

---

## Self-Review

**Spec coverage:**
- Vendor clean copy, drop docs/ + artifacts → Task 1. ✓
- plugin.json (no version) → Task 1 Step 4. ✓
- SKILL.md relocate + two-path-class rewiring (Class-R → `${CLAUDE_PLUGIN_ROOT}`, Class-T left bare) → Task 2. ✓
- Drop bin/install.sh + fix plugin README install section → Task 3. ✓
- Full CI: static job (check-all + smoke) + Docker theme-check job, path-scoped incl. workflow file → Task 4. ✓
- Marketplace entry (order voice/adr-toolkit/wordpress-block-theme) → Task 5. ✓
- CLAUDE.md/README layout, policy table already present → Task 6. ✓
- Archive standalone + README pointer via fresh clone → Task 8 (post-merge, gated). ✓
- Verification: static+smoke local, theme-check via CI, three plugins load → Task 7. ✓

**Placeholder scan:** No TBD/TODO; every step gives exact commands or exact replacements. The README banner text (Task 8) and README Install block (Task 3) are given verbatim.

**Type/name consistency:** plugin name / marketplace name / skill frontmatter all `wordpress-block-theme`; source path `./plugins/wordpress-block-theme`; static runner `bash assets/starter/bin/check-all.sh`; smoke `bash bin/test-update-starter.sh`; live `bash bin/theme-check.sh` (from `assets/starter`) — consistent across Tasks 1-7.
