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
│   └── adr-toolkit/               # the "adr-toolkit" plugin (Python-backed)
│       ├── .claude-plugin/
│       │   └── plugin.json        # plugin manifest
│       ├── skills/
│       │   └── adr-toolkit/
│       │       └── SKILL.md        # scaffolds docs/adr/ from composable packs
│       ├── packs/                 # ADR packs: universal + language/framework/app-shape/concern
│       └── bin/
│           └── install.sh          # one-time venv bootstrap (Python-backed, unlike voice)
├── MIGRATION.md                  # how to create the repo, install, and update
└── README.md
```

## Install

```bash
# In Claude Code (CLI):
/plugin marketplace add robsartin/claude-config
/plugin install voice@claude-config
/plugin install adr-toolkit@claude-config
```

The same plugin installs in Cowork (desktop) too. See `MIGRATION.md` for the full setup, update workflow, and how web projects fit in.

## The voice plugin

`voice` ships one skill, `writing-in-robs-voice`. Claude loads it automatically when I ask for a blog post, LinkedIn post, email, or anything "in my voice." It carries my voice profile, the hard rules (no em-dashes), the banned / AI-slop word list, and a dated timeline of my history so drafts get the facts right. The profile is refreshed every 4–6 weeks from new posts and transcripts.

## The adr-toolkit plugin

`adr-toolkit` ships one skill, `adr-toolkit`, that scaffolds a stack-appropriate `docs/adr/` for a project from composable ADR packs (a universal baseline plus language, framework, app-shape, and concern add-ons under `plugins/adr-toolkit/packs/`). Unlike `voice`, it's Python-backed: after installing or updating it, run `${CLAUDE_PLUGIN_ROOT}/bin/install.sh` once to bootstrap its venv before the CLI works.

## Adding more plugins later

1. Create `plugins/<name>/` with a `.claude-plugin/plugin.json`.
2. Put components at the plugin root: `skills/`, `agents/`, `hooks/hooks.json`, `.mcp.json`.
3. Add an entry to the `plugins` array in `.claude-plugin/marketplace.json`.
4. Commit and push. Installed machines pick it up with `/plugin marketplace update claude-config`.

Versioning: plugins here omit a `version` field, so every push is treated as an update (the git commit SHA is the version). Add `"version": "1.0.0"` to a `plugin.json` if you want to gate updates behind manual version bumps instead.
