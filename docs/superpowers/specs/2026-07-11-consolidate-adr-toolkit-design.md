# Consolidate adr-toolkit into claude-config + plugin-source policy

Date: 2026-07-11
Issue: robsartin/claude-config#1

## Problem

`claude-config` is Rob's personal Claude configuration managed as a git repo that
doubles as a plugin marketplace. Today it hosts one vendored plugin (`voice`). Rob
wants this marketplace to be the single control panel for every plugin he uses, and
needs a clear rule for three cases: plugins whose source belongs here, plugins of his
that currently live in their own repos, and third-party plugins written by others.

The immediate driver is `adr-claude-skill` — a separate public, MIT-licensed repo
(`robsartin/adr-claude-skill`) backed by a real Python package with its own CI. Rob
has decided to fold it in here as a second plugin (`adr-toolkit`) and archive the
standalone repo.

## Decisions locked in brainstorming

- **adr-toolkit is vendored** (source physically moved into `claude-config`), not
  cataloged as an external source.
- **The standalone repo is archived** (read-only) with a README pointer; its CI/tests
  come along so the skill stays gated here.
- **Clean copy, no history graft** — current source tree copied as a fresh commit;
  full history remains discoverable in the archived repo.

## Plugin-source policy (the general rule)

Written into `CLAUDE.md`. For any plugin Rob wants available through this marketplace:

| Case | Handling | `marketplace.json` source |
| --- | --- | --- |
| His, source belongs here (`voice`) | **Vendor** under `plugins/<name>/` | `"./plugins/<name>"` |
| His, currently a separate repo (`adr-toolkit`) | **Vendor + archive** the old repo | `"./plugins/<name>"` |
| Someone else's plugin | **Catalog, don't copy** their code | `{"source":{"source":"github","repo":"owner/repo"}}` — or just `/plugin marketplace add owner/repo` directly |

Rationale: vendoring keeps a single source of truth for Rob's own code; cataloging
external plugins avoids copying other people's code (licensing) and avoids a two-way
sync burden. Third-party code is never vendored.

## Target structure

```
claude-config/
├── .claude-plugin/marketplace.json      # + adr-toolkit entry
├── plugins/
│   ├── voice/…                          # unchanged
│   └── adr-toolkit/                      # NEW plugin root
│       ├── .claude-plugin/plugin.json    # new manifest
│       ├── skills/
│       │   └── adr-toolkit/
│       │       └── SKILL.md              # moved from adr repo root, paths rewired
│       ├── src/adr_toolkit/…             # Python package, copied as-is
│       ├── packs/  packs.yaml            # data
│       ├── bin/install.sh                # trimmed (see below)
│       ├── bin/gen-examples.sh
│       ├── scripts/check_coverage.py  scripts/lint_adrs.py
│       ├── tests/…
│       ├── examples/…
│       ├── docs/…                        # adr's own design/adr docs
│       ├── pyproject.toml  README.md  LICENSE  .gitignore
└── .github/workflows/adr-toolkit.yml     # path-scoped CI (first CI gate for claude-config)
```

### What is copied vs skipped

- **Copied**: `src/`, `packs/`, `packs.yaml`, `bin/`, `scripts/`, `tests/`,
  `examples/`, `docs/`, `pyproject.toml`, `README.md`, `LICENSE`, `.gitignore`
  (merged into the plugin dir; claude-config's root `.gitignore` already covers macOS/
  editor noise).
- **Skipped** (build/tool artifacts and cruft): `.venv/`, `.coverage`, `*_cache/`
  (`.pytest_cache`, `.mypy_cache`, `.ruff_cache`), `.superpowers/`, the self-referential
  `adr-claude-skill -> .` symlink, and the old `.github/` beyond the CI workflow.

## Component-by-component design

### 1. `plugins/adr-toolkit/.claude-plugin/plugin.json` (new)

Mirrors `voice`'s manifest shape — `name`, `description`, `author`, `keywords`. No
`version` field, so each push is treated as an update (consistent with `voice` and the
repo convention in CLAUDE.md).

```json
{
  "name": "adr-toolkit",
  "description": "Scaffold a stack-appropriate docs/adr/ from composable ADR packs.",
  "author": { "name": "Rob Sartin" },
  "keywords": ["adr", "architecture", "documentation", "scaffolding"]
}
```

### 2. Skill placement + path rewiring

`SKILL.md` moves from the adr repo root to `plugins/adr-toolkit/skills/adr-toolkit/SKILL.md`
(the default scan path `<plugin-root>/skills/<name>/SKILL.md`, so no `strict:false` /
custom `skills` list is needed). Its `name: adr-toolkit` frontmatter is unchanged so the
invocation name stays stable.

Paths inside SKILL.md are rewired because the file is now two levels below the plugin
root while the package/data sit at the root:

- Runtime commands use the plugin-root env var: `${CLAUDE_PLUGIN_ROOT}/packs.yaml`,
  `${CLAUDE_PLUGIN_ROOT}/packs`, `${CLAUDE_PLUGIN_ROOT}/bin/install.sh`. Claude Code sets
  `CLAUDE_PLUGIN_ROOT` to the plugin's install directory (the dir containing
  `.claude-plugin/`).
- Doc links become relative to the new location: `README.md` → `../../README.md`;
  `docs/design/...` → `../../docs/design/...`.

Every `<toolkit>` / `<tk>` placeholder in the emit/reconcile command blocks is replaced
with `${CLAUDE_PLUGIN_ROOT}`.

### 3. `bin/install.sh` (trimmed)

Currently install.sh does two things: (a) create a venv and `pip install -e` the package
(putting `adr-toolkit` / `adr-supersede` console scripts on PATH), and (b) symlink the
skill into `~/.claude/skills/`.

- **Keep (a)** — the Python venv + console-script bootstrap. The plugin framework does
  not automate `pip`, so this remains a documented once-per-machine step, invoked as
  `${CLAUDE_PLUGIN_ROOT}/bin/install.sh`.
- **Drop (b)** — skill discovery is now handled by the plugin/marketplace install, so the
  `~/.claude/skills/` symlink is redundant and would double-register the skill.

SKILL.md's "Ensure the engine is available" step is reworded to run install.sh from the
plugin root and to drop any mention of the manual skill symlink.

### 4. CI — `.github/workflows/adr-toolkit.yml`

adr's `ci.yml` is reproduced as a path-scoped workflow. This is claude-config's first CI
gate.

- Triggers: `pull_request` and `push` to `main`, filtered with
  `paths: ['plugins/adr-toolkit/**', '.github/workflows/adr-toolkit.yml']` so unrelated
  changes (e.g. to `voice`) don't run the Python gate.
- All run steps set `working-directory: plugins/adr-toolkit` (or a job-level `defaults.run.working-directory`).
- Steps preserved verbatim (paths relative to the working dir): `pip install -e '.[dev]'`,
  `ruff check .`, `ruff format --check .`, `mypy`, `coverage run -m pytest`,
  `python scripts/lint_adrs.py`, the coverage gate (`coverage json` +
  `python scripts/check_coverage.py coverage.json`), and the `examples/` freshness check
  (`./bin/gen-examples.sh` then fail if `git status --porcelain examples/` is dirty — the
  porcelain path is scoped to the working dir).

### 5. `marketplace.json`

Append a second entry to the `plugins` array:

```json
{
  "name": "adr-toolkit",
  "source": "./plugins/adr-toolkit",
  "description": "Scaffold a stack-appropriate docs/adr/ from composable ADR packs."
}
```

### 6. CLAUDE.md / README.md

- CLAUDE.md: add the **plugin-source policy** table above, and add adr-toolkit to the
  layout section. Note that adr-toolkit is a Python-backed plugin requiring the one-time
  `bin/install.sh` venv bootstrap.
- README.md: add adr-toolkit to the "what's here" tree and install snippet.

### 7. Retire the standalone repo (`robsartin/adr-claude-skill`)

Done last, after the claude-config PR merges and the plugin is verified working:

1. Commit a README pointer on `robsartin/adr-claude-skill`: "Moved into
   robsartin/claude-config (plugin `adr-toolkit`); install from that marketplace."
2. `gh repo archive robsartin/adr-claude-skill` (reversible via unarchive).
3. Remove the local `~/.claude/skills/adr-toolkit` symlink pointing at
   `~/code/adr-claude-skill`. Note the `resume-adr-claude-skill` scheduled task as stale
   (out of scope to delete here; flag for Rob).

## Data flow (unchanged at runtime)

The skill's runtime behavior is identical to today: Claude reads SKILL.md, interviews the
user for packs, and shells out to the `adr-toolkit` console script with
`--manifest ${CLAUDE_PLUGIN_ROOT}/packs.yaml --packs-dir ${CLAUDE_PLUGIN_ROOT}/packs`,
emitting `docs/adr/` into the target repo. Only the *locations* of packs.yaml/packs and
the install entrypoint change; the engine and pack data are copied byte-for-byte.

## Error handling / edge cases

- **Double registration**: if the old `~/.claude/skills/adr-toolkit` symlink is left in
  place alongside the marketplace install, the skill could register twice. §7 removes it.
- **venv bootstrap in a plugin cache dir**: marketplace-installed plugins live under a
  cache path; `bin/install.sh` creates `.venv` there and installs editable. This works but
  must not assume a writable CWD elsewhere — it uses `${CLAUDE_PLUGIN_ROOT}`.
- **CI path filter correctness**: the `paths:` filter must include the workflow file
  itself so edits to the workflow are testable.
- **`examples/` freshness under a subdir**: the porcelain check must be scoped to
  `plugins/adr-toolkit/examples/` (or run with the working-directory set) or it will scan
  the whole repo.

## Verification

1. In `plugins/adr-toolkit/`, run the full gate locally: `pip install -e '.[dev]'`,
   `ruff check .`, `ruff format --check .`, `mypy`, `coverage run -m pytest`,
   `python scripts/lint_adrs.py`, coverage gate, `./bin/gen-examples.sh` clean. All green.
2. `/plugin marketplace add` this repo locally (or `marketplace update`) and confirm
   **both** `voice` and `adr-toolkit` load.
3. Drive adr-toolkit end-to-end: emit a sample `docs/adr/` into a throwaway target and
   confirm files + regenerated `docs/adr/README.md` appear.
4. CI green on the PR.

## Out of scope

- Migrating `voice` or adding any other plugin.
- Deleting the `resume-adr-claude-skill` scheduled task (flag only).
- Preserving adr git history in claude-config (explicitly declined).
- Automating the Python venv bootstrap through the plugin framework.

## Workflow

Issue #1 → branch `1-consolidate-adr-toolkit` → commits → PR to `main` → squash merge.
Standalone-repo archival (§7) happens only after that PR merges and verification passes.
