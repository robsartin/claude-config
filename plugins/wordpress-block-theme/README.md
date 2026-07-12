# wordpress-block-theme

A personal [Claude](https://claude.com/claude-code) skill, **`wordpress-block-theme`**,
that captures the hard-won, reusable knowledge for building WordPress **block
themes** (Full Site Editing) — especially the canonical-block-markup rules that
keep the editor from flagging "invalid content" on sites running the bleeding-edge
Gutenberg plugin.

Distilled from the "Editorial Calm" build. Scope: **build pipeline + gotchas**
(scaffold → author blocks → test in `wp-env` → package → deploy to WordPress.com).

## Install

Install via the claude-config marketplace:

```bash
/plugin marketplace add robsartin/claude-config   # once, per machine
/plugin install wordpress-block-theme@claude-config
```

## Layout

- `skills/wordpress-block-theme/SKILL.md` — the workflow + the gotcha-rules as hard constraints
- `references/` — deep-dive rules and the WordPress.com deployment runbook
- `assets/starter/` — a genericized-but-working block-theme scaffold + validation harness
- `bin/update-starter.sh` — refresh the bundled starter from a source theme
- `MANIFEST.md` — per-starter-file provenance

## Development

This plugin lives in [robsartin/claude-config](https://github.com/robsartin/claude-config).
Changes land via pull request to `main`, following that repo's workflow.
