# Vendor wordpress-block-theme into claude-config

Date: 2026-07-12
Issue: robsartin/claude-config#3

## Problem

`claude-config` is the single marketplace for the plugins Rob uses. `voice` and
`adr-toolkit` now live here. The next skill to fold in is the standalone repo
`robsartin/claude-wp-theme-skill` — a WordPress block-theme skill — following the
plugin-source policy (vendor his own skills; archive the old repo). Rob has already
deleted his local clone; the GitHub repo still exists and is unarchived.

Unlike `adr-toolkit` (a Python package with an existing CI gate), this skill is a
content-and-tooling skill: a canonical starter theme plus reference guides and helper
scripts, with **no CI today**. Rob opted for a **full CI gate** on vendoring.

## Decisions (from brainstorming)

- **Vendor + archive**, clean copy (no git-history graft), per the plugin-source policy
  established with `adr-toolkit`.
- **Full CI gate**: static Python validators + a maintainer smoke test, PLUS a Docker
  job running `@wordpress/env` + the PHP Theme Check plugin against the starter.

## Source repo shape (upstream)

```
SKILL.md                       # skill (name: wordpress-block-theme), at repo root
README.md  MANIFEST.md  .gitignore
references/                    # 4 on-demand guides
  block-markup-rules.md  wordpress-com-deploy.md  editor-guide.md  development.md
assets/starter/                # canonical block-theme starter
  theme.json  style.css  functions.php  phpcs.xml  readme.txt  screenshot.png
  .wp-env.json                 # boots WP 6.5 + Theme Check plugin
  templates/  parts/  patterns/  styles/  assets/fonts/
  bin/                         # per-theme harness (copied into a user's theme)
    check-all.sh check-a11y.sh validate-theme-json.py check-contrast.py
    check-button-contrast.py check-font-fallbacks.py check-templates.py
    check-patterns.py check-markup-consistency.py check-frontpage.py _wcag.py
    theme-check.sh theme-check-run.php package.sh screenshot.sh
bin/                           # repo-level maintainer tooling
  install.sh                   # symlink/clone installer — DROPPED (see §4)
  update-starter.sh test-update-starter.sh _manifest.tsv
docs/superpowers/              # the skill's own spec/plan — DROPPED (dev scratch)
```

## Target structure

```
plugins/wordpress-block-theme/
├── .claude-plugin/plugin.json               # new manifest
├── skills/wordpress-block-theme/SKILL.md    # moved from repo root, paths rewired (§3)
├── assets/starter/…                         # copied verbatim
├── references/…                             # copied verbatim
├── bin/update-starter.sh test-update-starter.sh _manifest.tsv
├── MANIFEST.md  README.md  .gitignore
└── (dropped: bin/install.sh, docs/)
.github/workflows/wordpress-block-theme.yml  # new, path-scoped
```

### Copied vs dropped

- **Copied** (via `git archive` of upstream `HEAD`, tracked files only): everything
  above except the two drops.
- **Dropped**: `bin/install.sh` (§4) and `docs/` (only the skill's own
  `docs/superpowers/` spec/plan live there — dev scratch, same call as adr).
- Artifacts (`node_modules/`, `.venv/`, `*.zip`, `.superpowers/`) are untracked /
  gitignored upstream, so `git archive` skips them automatically.

## Component-by-component design

### 1. `plugins/wordpress-block-theme/.claude-plugin/plugin.json` (new)

Mirrors the `voice` / `adr-toolkit` manifest shape — `name`, `description`, `author`,
`keywords`. No `version` field (repo convention: every push is an update).

```json
{
  "name": "wordpress-block-theme",
  "description": "Build a WordPress block theme (FSE) from a canonical, self-validating starter.",
  "author": { "name": "Rob Sartin" },
  "keywords": ["wordpress", "block-theme", "fse", "gutenberg", "theme"]
}
```

### 2. Skill placement

`SKILL.md` moves from the upstream repo root to
`plugins/wordpress-block-theme/skills/wordpress-block-theme/SKILL.md` (the default scan
path `<plugin-root>/skills/<name>/SKILL.md`). Frontmatter `name: wordpress-block-theme`
is unchanged (stable invocation name).

### 3. Path rewiring in SKILL.md — TWO path classes

The critical subtlety of this migration. SKILL.md references two different roots and a
blanket find/replace would break the skill.

**Class R — skill-root-relative resources → `${CLAUDE_PLUGIN_ROOT}/…`**
These are files the skill (Claude) must open or copy *from the plugin*. Claude Code sets
`${CLAUDE_PLUGIN_ROOT}` to the plugin's install dir.

| SKILL.md line | current | becomes |
| --- | --- | --- |
| 14 (scaffold source) | `assets/starter/` | `${CLAUDE_PLUGIN_ROOT}/assets/starter/` |
| 19 | `references/block-markup-rules.md` | `${CLAUDE_PLUGIN_ROOT}/references/block-markup-rules.md` |
| 28 | `references/wordpress-com-deploy.md` | `${CLAUDE_PLUGIN_ROOT}/references/wordpress-com-deploy.md` |
| 41 | `assets/starter/patterns/card-section.php` | `${CLAUDE_PLUGIN_ROOT}/assets/starter/patterns/card-section.php` |
| 49 | `assets/starter/parts/footer.html` | `${CLAUDE_PLUGIN_ROOT}/assets/starter/parts/footer.html` |
| 55 | `references/block-markup-rules.md`, `references/wordpress-com-deploy.md` | prefix both with `${CLAUDE_PLUGIN_ROOT}/` |
| 58 | `references/editor-guide.md` | `${CLAUDE_PLUGIN_ROOT}/references/editor-guide.md` |
| 60 | `references/development.md` | `${CLAUDE_PLUGIN_ROOT}/references/development.md` |
| 64 (maintainer tool) | `bin/update-starter.sh` | `${CLAUDE_PLUGIN_ROOT}/bin/update-starter.sh` |
| 66 | `MANIFEST.md` | `${CLAUDE_PLUGIN_ROOT}/MANIFEST.md` |

Line 42's elliptical `plain-section.php` (same directory as the card ref, human-readable
prose) stays as prose — it is not a resolvable path on its own and reads clearly.

**Class T — theme-relative harness scripts → LEFT AS `bin/…`**
These run *inside the user's scaffolded theme*, because `assets/starter/bin/` is copied
into the new theme during scaffold (step 1). Rewiring them would be a bug.

| SKILL.md line | stays |
| --- | --- |
| 21 | `bin/check-all.sh` |
| 22 | `bin/theme-check.sh` |
| 23 | `bin/screenshot.sh` |
| 26 | `bin/package.sh` |

Lines 16-17, 50 (`functions.php`, `theme.json`, `phpcs.xml`) describe files to edit in
the copied theme — also theme-relative, left as-is.

### 4. Drop `bin/install.sh`

Upstream `bin/install.sh` only symlinks/clones the skill into `~/.claude/skills/` — the
exact registration the marketplace now performs, and this skill has no build step (the
validators run on stock `python3`; the live check uses `npx`). So it is removed outright.
Its only references are in `README.md`:

- L31 "Helper script — `bin/install.sh` does either of the above for you"
- L35-36 the `./bin/install.sh` / `--clone` snippet
- L52 the bullet in the file list

Rewrite the README "Install" section to: install via the `claude-config` marketplace
(`/plugin marketplace add robsartin/claude-config` → `/plugin install
wordpress-block-theme@claude-config`); drop the symlink/clone helper description. Leave
`MANIFEST.md` unchanged (it references `update-starter.sh` / `_manifest.tsv` / the harness
scripts, none of which are removed).

### 5. CI — `.github/workflows/wordpress-block-theme.yml`

Path-scoped: `pull_request` and `push` to `main` filtered on
`['plugins/wordpress-block-theme/**', '.github/workflows/wordpress-block-theme.yml']`.
Two jobs so the cheap gate fails fast:

**Job `static`** (fast, no Docker):
- `actions/checkout@v5`, `actions/setup-python@v6` (Python 3.12).
- `python3 assets/starter/bin/check-all.sh` — validates the shipped starter
  (theme.json, font fallbacks, text + button contrast on `theme.json` and each
  `styles/*.json`, templates, patterns, markup consistency, front page).
- `bash bin/test-update-starter.sh` — smoke-tests the `update-starter.sh` maintainer
  tool (slug rewrite / leak checks).
- Runs with `working-directory: plugins/wordpress-block-theme`.

**Job `theme-check`** (Docker; GitHub ubuntu runners ship Docker + Node):
- `actions/checkout@v5`, `actions/setup-node@v4` (Node 20).
- `working-directory: plugins/wordpress-block-theme/assets/starter`.
- `bash bin/theme-check.sh` — `npx @wordpress/env start` boots WP 6.5 + the Theme Check
  plugin, then `wp eval-file bin/theme-check-run.php` runs the suite headlessly.
  `theme-check-run.php` exits nonzero on unexpected REQUIRED findings (the known
  "Shell script file found" dev-tree finding is already excluded upstream).
- Best-effort teardown: `npx @wordpress/env stop` in an `if: always()` step.

The two jobs are independent (no `needs`) so they run in parallel; the PR is green only
when both pass.

### 6. Marketplace + docs

- `marketplace.json`: append a third entry
  `{"name":"wordpress-block-theme","source":"./plugins/wordpress-block-theme","description":"Build a WordPress block theme (FSE) from a canonical, self-validating starter."}`.
- `CLAUDE.md`: add `wordpress-block-theme` to the layout block. The plugin-source policy
  table already exists (added with adr) — no change needed.
- `README.md`: add `plugins/wordpress-block-theme/` to the "what's here" tree and an
  install line `/plugin install wordpress-block-theme@claude-config`.

### 7. Retire the standalone repo (POST-MERGE, gated)

Runs only after the PR merges and verification passes, and only on Rob's explicit
go-ahead (public-facing):
1. Because the local clone was deleted, shallow-clone `robsartin/claude-wp-theme-skill`
   to a temp dir, add a README banner ("Moved into robsartin/claude-config as the
   `wordpress-block-theme` plugin; install from that marketplace."), commit, push.
2. `gh repo archive robsartin/claude-wp-theme-skill` (reversible via unarchive).

## Data flow (unchanged at runtime)

The skill's behavior is identical: Claude reads SKILL.md, copies
`${CLAUDE_PLUGIN_ROOT}/assets/starter/` into the user's new theme dir, the user edits
tokens/slugs, then runs the theme's own `bin/check-all.sh` / `bin/theme-check.sh` /
`bin/package.sh` from inside that theme. Only the location of the plugin's own resources
changes (now under `${CLAUDE_PLUGIN_ROOT}`); the starter and its harness are copied
byte-for-byte.

## Error handling / edge cases

- **Path-class mistake**: the single biggest risk (§3). The plan enumerates each
  occurrence; verification greps for any surviving bare `assets/starter`/`references/`
  in SKILL.md (should be none) and confirms the four Class-T `bin/*.sh` refs remain
  bare.
- **Double registration**: no old `~/.claude/skills/wordpress-block-theme` symlink
  remains (Rob already deleted it), so no conflict with the marketplace install.
- **wp-env flakiness in CI**: the `theme-check` job pulls Docker images and boots WP;
  it is slower and can be flaky. Acceptable per the full-gate decision. `if: always()`
  teardown avoids leaked containers between steps.
- **CI path filter**: must include the workflow file itself so edits to it are testable.

## Verification

1. Locally (provable in this environment): `python3 assets/starter/bin/check-all.sh`
   and `bash bin/test-update-starter.sh` both green from
   `plugins/wordpress-block-theme/`.
2. Live theme-check: proven by the CI `theme-check` job on the PR (needs Docker, which
   is not assumed available locally — the report will state plainly which checks ran
   locally vs. which CI proves).
3. `/plugin marketplace add ~/code/claude-config` (or `marketplace update`) loads all
   three plugins — `voice`, `adr-toolkit`, `wordpress-block-theme` (Rob runs this
   interactive step).

## Out of scope

- Any change to `voice` or `adr-toolkit`.
- Deleting the `resume-adr-claude-skill` scheduled task (adr follow-up, tracked
  separately).
- Preserving upstream git history in claude-config (explicitly declined).
- Automating wp-env locally for the agent's own verification.

## Workflow

Issue #3 → branch `3-vendor-wordpress-block-theme` → commits → PR to `main` → squash
merge. Standalone-repo archival (§7) happens only after that PR merges and verification
passes.
