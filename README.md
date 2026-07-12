# claude-config

Rob Sartin's personal Claude configuration, managed as a single git repo that doubles as a Claude Code **plugin marketplace**. One source of truth, installed everywhere I run Claude.

## What's here

```
claude-config/
├── .claude-plugin/
│   └── marketplace.json          # marketplace catalog (lists the plugins below)
├── plugins/
│   └── voice/                    # the "voice" plugin
│       ├── .claude-plugin/
│       │   └── plugin.json        # plugin manifest
│       └── skills/
│           └── writing-in-robs-voice/
│               ├── SKILL.md        # my voice profile (auto-loads when I draft prose)
│               └── references/
│                   └── blog-index.md   # index of my blog posts, loaded on demand
├── MIGRATION.md                  # how to create the repo, install, and update
└── README.md
```

## Install

```bash
# In Claude Code (CLI):
/plugin marketplace add robsartin/claude-config
/plugin install voice@claude-config
```

The same plugin installs in Cowork (desktop) too. See `MIGRATION.md` for the full setup, update workflow, and how web projects fit in.

## The voice plugin

`voice` ships one skill, `writing-in-robs-voice`. Claude loads it automatically when I ask for a blog post, LinkedIn post, email, or anything "in my voice." It carries my voice profile, the hard rules (no em-dashes), the banned / AI-slop word list, and a dated timeline of my history so drafts get the facts right. The profile is refreshed every 4–6 weeks from new posts and transcripts.

## Adding more plugins later

1. Create `plugins/<name>/` with a `.claude-plugin/plugin.json`.
2. Put components at the plugin root: `skills/`, `agents/`, `hooks/hooks.json`, `.mcp.json`.
3. Add an entry to the `plugins` array in `.claude-plugin/marketplace.json`.
4. Commit and push. Installed machines pick it up with `/plugin marketplace update claude-config`.

Versioning: plugins here omit a `version` field, so every push is treated as an update (the git commit SHA is the version). Add `"version": "1.0.0"` to a `plugin.json` if you want to gate updates behind manual version bumps instead.
