# claude-config

Rob Sartin's personal Claude configuration, managed as one git repo that doubles as a Claude Code **plugin marketplace**. This is the single source of truth for his skills, agents, and settings, installed everywhere he runs Claude.

## Layout

```
.claude-plugin/marketplace.json     # marketplace catalog (name: claude-config)
plugins/voice/                      # "voice" — markdown skill
  .claude-plugin/plugin.json
  skills/writing-in-robs-voice/
    SKILL.md                        # Rob's full voice profile (source of truth)
    references/blog-index.md        # index of his blog posts, loaded on demand
plugins/adr-toolkit/                # "adr-toolkit" — Python-backed (venv)
  .claude-plugin/plugin.json
  skills/adr-toolkit/SKILL.md
  packs/                            # composable ADR packs (universal, python, react, ...)
  src/  tests/  pyproject.toml
  bin/install.sh                    # one-time venv + editable install (see conventions)
plugins/wordpress-block-theme/      # "wordpress-block-theme" — content + tooling
  .claude-plugin/plugin.json
  skills/wordpress-block-theme/SKILL.md
  assets/starter/                   # canonical, self-validating block-theme starter
  references/                       # block-markup rules, dev/editor/deploy guides
plugins/kdp-publisher/              # "kdp-publisher" — Python-backed (venv)
  .claude-plugin/plugin.json
  skills/kdp-publisher/SKILL.md
  src/  tests/  pyproject.toml
  bin/install.sh                    # one-time venv + editable install
plugins/plugin-sync/                # "plugin-sync" — command-only (bash)
  .claude-plugin/plugin.json
  commands/sync.md                  # the /plugin-sync:sync command
  sync-plugins.sh                   # install-new / update-installed / report-orphans
plugins/start-work/                 # "start-work" — Python-backed (python3, no venv)
  .claude-plugin/plugin.json
  skills/start-work/SKILL.md
  bin/start_work.py                 # issue/ticket + branch helpers (gh, or glab+jira)
  commands/start-work.md, draft-mr.md
plugins/worklog/                    # "worklog" — Python-backed (python3, no venv)
  .claude-plugin/plugin.json
  skills/worklog/SKILL.md
  bin/worklog.py                    # log + report helpers
  commands/log.md, weekly-report.md, perf-review.md
bin/bootstrap.sh                    # one-shot new-machine setup (see README)
.github/workflows/                  # per-plugin path-scoped CI
```

## The plugins

Sections below are in marketplace order.

### voice

`writing-in-robs-voice` makes Claude draft and edit prose as Rob (blog posts, LinkedIn, email, book text). It auto-loads when a task matches its description. Pure markdown, no runtime. **When editing Rob's voice, edit `plugins/voice/skills/writing-in-robs-voice/SKILL.md` here** — it is the single source of truth. (An older copy once lived in a `myClaudeVoice/voice.md`; that is retired, do not sync to it.)

Before drafting anything as Rob, read that SKILL.md in full. The most load-bearing rules, as a quick reference:

- **No em-dashes** in generated drafts. Use parentheticals, full stops, colons, or commas instead. (Rob's own writing uses em-dashes freely; the ban applies only to AI-generated drafts, where they read as a machine tell.)
- **Prefer vague quantifiers** ("several", "a shelf of") over invented precise numbers. Use exact figures only for things actually measured.
- **Authorship**: robsartin.com posts from **July 2024 onward** are Rob's voice; **January–June 2024** posts were written by his wife Rachel and brother Hank during his hospitalization and are NOT his voice. Don't imitate them.
- The SKILL.md also carries a dated timeline of Rob's medical/life history — use it so drafts get facts right.

### adr-toolkit

`adr-toolkit` scaffolds a stack-appropriate `docs/adr/` into a repo from composable ADR packs (a universal baseline plus language / framework / app-shape / concern add-ons under `plugins/adr-toolkit/packs/`). Python-backed: after installing or updating it, run `${CLAUDE_PLUGIN_ROOT}/bin/install.sh` once to bootstrap its venv and editable install before the `adr-toolkit` / `adr-supersede` console scripts work.

### wordpress-block-theme

`wordpress-block-theme` is a content-and-tooling skill: a canonical, self-validating starter theme plus reference guides for building WordPress block (Full Site Editing / Gutenberg) themes that pass validation on the first try. Its static gates (`assets/starter/bin/check-all.sh`) run on `python3` with no Docker required; the live theme-check (`assets/starter/bin/theme-check.sh`) needs `@wordpress/env` running.

### kdp-publisher

`kdp-publisher` turns a Google Doc (or exported `.docx`) manuscript into print-ready Amazon KDP files: a paperback interior PDF, a wraparound cover PDF, a cover-spec sheet, and a Kindle EPUB. Python-backed like `adr-toolkit`: run `${CLAUDE_PLUGIN_ROOT}/bin/install.sh` once to bootstrap its venv before the CLI works.

### plugin-sync

`plugin-sync` provides the `/plugin-sync:sync` command, which syncs this machine's installed plugins with the marketplace: refresh the catalog, install anything new, update everything installed, and report (or with `--prune`, uninstall) plugins that have left the catalog. It's command-only — the logic is the bundled `sync-plugins.sh` (bash, no deps). `--dry-run` previews.

### start-work

`start-work` turns a ticket or idea into a tracked issue/ticket + a correctly-named branch, makes the linkage live, and hands off to `superpowers:brainstorming`. Its helpers (`bin/start_work.py`) run directly on `python3`, no venv bootstrap needed. It adapts to the repo's host: **GitHub** via `gh` (issue → branch, `ready` label) or **GitLab/Jira** via `glab` + `jira` (ticket → branch, assign + transition to `jira.inProgressStatus`), driven by machine-local config. `/start-work:draft-mr` opens the draft PR/MR at your first push (the kickoff defers it — both hosts need a commit first). Its worklog integration is a graceful no-op when `worklog` isn't present.

### worklog

`worklog` captures work activity into a rolling Obsidian `Worklog.md` (via `/log`) and drafts weekly status reports (`/weekly-report`) or performance-review narratives (`/perf-review`) from it. Its helpers (`bin/worklog.py`) run directly on `python3`, no venv. The vault path and report templates are machine-local config (the `worklog` section of `~/.claude/start-work.json`), never part of this repo; reports are drafts written into the vault, never sent. Where `jira`/`glab` are available, the reports augment the hand-logged notes with a **factual pull** (tickets resolved + MRs merged in range).

## Plugin conventions

The pattern every plugin here follows — match it when adding one:

- **Structure**: `plugins/<name>/` with `.claude-plugin/plugin.json`. Only `plugin.json` goes inside a `.claude-plugin/` dir; component folders (`skills/`, `commands/`, `bin/`, `agents/`, `hooks/hooks.json`, `.mcp.json`) sit at the plugin root.
- **Skill**: `skills/<name>/SKILL.md` with a frontmatter `name:` (the stable invocation name). Commands go in `commands/*.md` and are listed in `plugin.json`'s `commands` array.
- **No `version`**: plugins here omit a `version` field, so **every push is treated as an update** (the git commit SHA is the version). Add `"version"` to a `plugin.json` only to gate updates behind manual bumps.
- **Plugin-owned paths**: anything the skill opens or runs *from the plugin* is addressed via `${CLAUDE_PLUGIN_ROOT}/…`. Paths that run inside a user's generated output (e.g. a scaffolded theme's own `bin/`) stay relative.
- **Python helpers**: plain scripts run directly on `python3`, stdlib-only, no venv (`start-work`, `worklog`). Only plugins that ship a packaged console script (`adr-toolkit`, `kdp-publisher`) need a one-time `${CLAUDE_PLUGIN_ROOT}/bin/install.sh` venv bootstrap. Python plugins carry their own `.gitignore` for venv/caches.
- **CI**: each gated plugin has `.github/workflows/<name>.yml`, **path-scoped** to `plugins/<name>/**` plus the workflow file, with `working-directory: plugins/<name>`. Shell scripts are linted by `.github/workflows/shell.yml`.
- **Secrets / machine-local config**: anything work- or machine-specific (hosts, keys, vault paths, report templates) lives in a machine-local file under `~/.claude/`, never committed here. This repo is **public**.
- **Add a plugin**: create the structure above, then add an entry to the `plugins` array in `.claude-plugin/marketplace.json`. Installed machines pick it up via `/plugin-sync:sync` (or `/plugin marketplace update claude-config`).

## Plugin-source policy

Where a new plugin's code lives depends on where it came from:

| Case | Handling | marketplace source |
| --- | --- | --- |
| Mine, source belongs here (`voice`) | Vendor under `plugins/<name>/` | `"./plugins/<name>"` |
| Mine, was a separate repo (`adr-toolkit`) | Vendor + archive the old repo | `"./plugins/<name>"` |
| Someone else's plugin | Catalog, don't copy their code | `{"source":{"source":"github","repo":"owner/repo"}}` or `/plugin marketplace add owner/repo` |

## Install / update

```bash
/plugin marketplace add robsartin/claude-config     # once, per machine
/plugin install <name>@claude-config                # or bin/bootstrap.sh for all (see README)

# after pushing changes, on each machine:
/plugin-sync:sync                                   # install new + update installed
```

See `README.md` for the full new-machine bootstrap and sync workflow.
