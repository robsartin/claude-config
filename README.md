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
│   └── start-work/                # ticket/idea → tracked issue + branch (Python-backed, GitHub only for now)
├── bin/
│   └── bootstrap.sh              # one-shot new-machine setup
├── MIGRATION.md                  # how to create the repo, install, and update
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
/plugin install <name>@claude-config                  # voice · adr-toolkit · wordpress-block-theme · kdp-publisher · plugin-sync · start-work
```

The same plugins install in Cowork (desktop) too. See `MIGRATION.md` for the full setup, update workflow, and how web projects fit in.

## The voice plugin

`voice` ships one skill, `writing-in-robs-voice`. Claude loads it automatically when I ask for a blog post, LinkedIn post, email, or anything "in my voice." It carries my voice profile, the hard rules (no em-dashes), the banned / AI-slop word list, and a dated timeline of my history so drafts get the facts right. The profile is refreshed every 4–6 weeks from new posts and transcripts.

## The adr-toolkit plugin

`adr-toolkit` ships one skill, `adr-toolkit`, that scaffolds a stack-appropriate `docs/adr/` for a project from composable ADR packs (a universal baseline plus language, framework, app-shape, and concern add-ons under `plugins/adr-toolkit/packs/`). Unlike `voice`, it's Python-backed: after installing or updating it, run `${CLAUDE_PLUGIN_ROOT}/bin/install.sh` once to bootstrap its venv before the CLI works.

## The wordpress-block-theme plugin

`wordpress-block-theme` ships one skill, `wordpress-block-theme`, for building a WordPress block (Full Site Editing / Gutenberg) theme that passes block validation on the first try. It's a content-and-tooling plugin: a canonical, self-validating starter theme under `plugins/wordpress-block-theme/assets/starter/`, plus reference guides (block-markup rules, dev/editor workflow, WordPress.com deploy) under `plugins/wordpress-block-theme/references/`. Static gates (`bin/check-all.sh`) run on plain `python3`; the live theme-check (`bin/theme-check.sh`) needs `@wordpress/env` running.

## Adding more plugins later

1. Create `plugins/<name>/` with a `.claude-plugin/plugin.json`.
2. Put components at the plugin root: `skills/`, `agents/`, `hooks/hooks.json`, `.mcp.json`.
3. Add an entry to the `plugins` array in `.claude-plugin/marketplace.json`.
4. Commit and push. Installed machines pick it up with `/plugin marketplace update claude-config`.

Versioning: plugins here omit a `version` field, so every push is treated as an update (the git commit SHA is the version). Add `"version": "1.0.0"` to a `plugin.json` if you want to gate updates behind manual version bumps instead.
