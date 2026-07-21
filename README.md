# claude-config

Rob Sartin's personal Claude configuration, managed as a single git repo that doubles as a Claude Code **plugin marketplace**. One source of truth, installed everywhere I run Claude.

## What's here

```
claude-config/
├── .claude-plugin/
│   └── marketplace.json          # marketplace catalog (lists the plugins below)
├── plugins/
│   ├── voice/                    # the "voice" plugin
│   │   ├── .claude-plugin/
│   │   │   └── plugin.json        # plugin manifest
│   │   └── skills/
│   │       └── writing-in-robs-voice/
│   │           ├── SKILL.md        # my voice profile (auto-loads when I draft prose)
│   │           └── references/
│   │               └── blog-index.md   # index of my blog posts, loaded on demand
│   ├── adr-toolkit/               # the "adr-toolkit" plugin (Python-backed)
│   │   ├── .claude-plugin/
│   │   │   └── plugin.json        # plugin manifest
│   │   ├── skills/
│   │   │   └── adr-toolkit/
│   │   │       └── SKILL.md        # scaffolds docs/adr/ from composable packs
│   │   ├── packs/                 # ADR packs: universal + language/framework/app-shape/concern
│   │   └── bin/
│   │       └── install.sh          # one-time venv bootstrap (Python-backed, unlike voice)
│   ├── wordpress-block-theme/     # the "wordpress-block-theme" plugin (content + tooling)
│   │   ├── .claude-plugin/
│   │   │   └── plugin.json        # plugin manifest
│   │   ├── skills/
│   │   │   └── wordpress-block-theme/
│   │   │       └── SKILL.md        # workflow for building a WP block (FSE) theme
│   │   ├── assets/
│   │   │   └── starter/            # canonical, self-validating block-theme starter
│   │   └── references/            # block-markup rules, dev/editor/deploy guides
│   ├── kdp-publisher/             # Google Doc → KDP interior/cover/spec/EPUB (Python)
│   ├── plugin-sync/               # the /plugin-sync:sync command + sync-plugins.sh
│   ├── start-work/                # ticket/idea → tracked issue + branch, GitHub or GitLab/Jira (Python-backed)
│   └── worklog/                   # work activity → Obsidian Worklog.md + weekly/perf report drafts (Python-backed)
├── bin/
│   └── bootstrap.sh              # one-shot new-machine setup
└── README.md
```

## New machine setup

Adding the marketplace clones this whole repo into Claude Code's cache, so `bin/bootstrap.sh` is available with no separate `git clone`:

```bash
claude plugin marketplace add robsartin/claude-config
bash ~/.claude/plugins/marketplaces/claude-config/bin/bootstrap.sh --extras
```

`bootstrap.sh` adds the marketplace, installs/updates every claude-config plugin (via `plugins/plugin-sync/sync-plugins.sh`, which reads the catalog — no hard-coded list), and runs the `adr-toolkit` Python engine bootstrap. `--extras` also sets up the external marketplaces I use (superpowers, frontend-design, claude-hud); `--dry-run` previews without changing anything. Restart Claude Code when it finishes.

Not carried over (machine-local): `settings.json`, the claude-hud statusline/HUD config, keybindings, and memory.

## Keeping plugins in sync

Once `plugin-sync` is installed, run `/plugin-sync:sync` in any session to install new + update installed claude-config plugins. `--dry-run` previews; `--prune` uninstalls plugins that have been dropped from the marketplace.

## Installing individual plugins

```bash
/plugin marketplace add robsartin/claude-config       # once per machine
/plugin install <name>@claude-config                  # voice · adr-toolkit · wordpress-block-theme · kdp-publisher · plugin-sync · start-work · worklog
```

## Other surfaces

- **Cowork (desktop)** — the same plugins install; add the marketplace and install from the desktop app's plugin interface. Cowork-specific state (project memory, connected folders) stays local and isn't deployed from this repo.
- **Web projects (claude.ai)** — can't install plugins. This repo stays the source of truth: paste the body of `plugins/voice/skills/writing-in-robs-voice/SKILL.md` (below the frontmatter) into the project's custom instructions when it changes.

## The voice plugin

`voice` ships one skill, `writing-in-robs-voice`. Claude loads it automatically when I ask for a blog post, LinkedIn post, email, or anything "in my voice." It carries my voice profile, the hard rules (no em-dashes), the banned / AI-slop word list, and a dated timeline of my history so drafts get the facts right. The profile is refreshed every 4–6 weeks from new posts and transcripts.

## The adr-toolkit plugin

`adr-toolkit` ships one skill, `adr-toolkit`, that scaffolds a stack-appropriate `docs/adr/` for a project from composable ADR packs (a universal baseline plus language, framework, app-shape, and concern add-ons under `plugins/adr-toolkit/packs/`). Unlike `voice`, it's Python-backed: after installing or updating it, run `${CLAUDE_PLUGIN_ROOT}/bin/install.sh` once to bootstrap its venv before the CLI works.

## The wordpress-block-theme plugin

`wordpress-block-theme` ships one skill, `wordpress-block-theme`, for building a WordPress block (Full Site Editing / Gutenberg) theme that passes block validation on the first try. It's a content-and-tooling plugin: a canonical, self-validating starter theme under `plugins/wordpress-block-theme/assets/starter/`, plus reference guides (block-markup rules, dev/editor workflow, WordPress.com deploy) under `plugins/wordpress-block-theme/references/`. Static gates (`bin/check-all.sh`) run on plain `python3`; the live theme-check (`bin/theme-check.sh`) needs `@wordpress/env` running.

## The kdp-publisher plugin

`kdp-publisher` ships one skill, `kdp-publisher`, that turns a Google Doc (or exported `.docx`) manuscript into print-ready Amazon KDP files: a paperback interior PDF, a wraparound cover PDF, a cover-spec sheet, and a Kindle EPUB. Python-backed like `adr-toolkit` — run `${CLAUDE_PLUGIN_ROOT}/bin/install.sh` once to bootstrap its venv before the CLI works.

## The plugin-sync plugin

`plugin-sync` provides the `/plugin-sync:sync` command, which keeps this machine's installed plugins in step with the marketplace: it refreshes the catalog, installs anything new, updates everything installed, and reports plugins that have left the catalog (`--prune` uninstalls them; `--dry-run` previews). Command-only, backed by the bundled `sync-plugins.sh` (bash, no dependencies). See "Keeping plugins in sync" above.

## The start-work plugin

`start-work` ships one skill plus four commands. It turns a ticket or idea into a tracked issue/ticket + a correctly-named branch, makes the linkage live, and hands off to brainstorming. Helpers (`bin/start_work.py`) run directly on `python3` with no venv. It adapts to the repo's host: **GitHub** via `gh` (issue → branch, `ready` label) or **GitLab/Jira** via `glab` + `jira` (ticket → branch, assign + transition), driven by machine-local config. `/start-work:draft-mr` opens the draft PR/MR at your first push. `/start-work:finish` replays the repo's CI gate, pushes, and puts the PR/MR up for review; `/start-work:merge` then verifies checks are green, squash-merges, logs a `shipped` worklog entry, and transitions the ticket.

## The worklog plugin

`worklog` ships one skill plus three commands. `/worklog:log` captures work activity into a rolling Obsidian `Worklog.md`; `/worklog:weekly-report` and `/worklog:perf-review` draft a weekly status report or a performance-review narrative from it. Helpers (`bin/worklog.py`) run directly on `python3`, no venv. The vault path and report templates are machine-local config (never in this repo), and reports are drafts written into the vault, never sent. Where `jira`/`glab` are available, the reports can augment your hand-logged notes with a **factual pull** — tickets resolved and MRs merged in the range.

## Adding more plugins later

1. Create `plugins/<name>/` with a `.claude-plugin/plugin.json`.
2. Put components at the plugin root: `skills/`, `agents/`, `hooks/hooks.json`, `.mcp.json`.
3. Add an entry to the `plugins` array in `.claude-plugin/marketplace.json`.
4. Commit and push. Installed machines pick it up with `/plugin marketplace update claude-config`.

Versioning: plugins here omit a `version` field, so every push is treated as an update (the git commit SHA is the version). Add `"version": "1.0.0"` to a `plugin.json` if you want to gate updates behind manual version bumps instead.
