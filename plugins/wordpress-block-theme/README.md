# claude-wp-theme-skill

A personal [Claude](https://claude.com/claude-code) skill, **`wordpress-block-theme`**,
that captures the hard-won, reusable knowledge for building WordPress **block
themes** (Full Site Editing) — especially the canonical-block-markup rules that
keep the editor from flagging "invalid content" on sites running the bleeding-edge
Gutenberg plugin.

Distilled from the "Editorial Calm" build. Scope: **build pipeline + gotchas**
(scaffold → author blocks → test in `wp-env` → package → deploy to WordPress.com).

## Install

Pick one:

**Symlink** (recommended if you have the repo cloned / are developing it) —
edits and `git pull` are live immediately. Run from the repo root:

```sh
ln -s "$(pwd)" ~/.claude/skills/wordpress-block-theme
```

**Clone** (clean install on another machine, no local checkout needed):

```sh
git clone https://github.com/robsartin/claude-wp-theme-skill.git ~/.claude/skills/wordpress-block-theme
```

Update it later with `git -C ~/.claude/skills/wordpress-block-theme pull`.

**Helper script** — `bin/install.sh` does either of the above for you
(symlink by default, `--clone` to clone instead), and is idempotent:

```sh
./bin/install.sh          # symlink
./bin/install.sh --clone  # clone
```

**Scope:** `~/.claude/skills/` makes the skill available in every project.
For a project-scoped install (only active in that project), target
`<project>/.claude/skills/wordpress-block-theme/` instead.

**After installing:** restart Claude Code. The skill triggers automatically
on WordPress/block-theme requests, or invoke it directly as
`/wordpress-block-theme`.

## Layout

- `SKILL.md` — the workflow + the gotcha-rules as hard constraints
- `references/` — deep-dive rules and the WordPress.com deployment runbook
- `assets/starter/` — a genericized-but-working block-theme scaffold + validation harness
- `bin/install.sh` — idempotent install helper (symlink or `--clone`)
- `bin/update-starter.sh` — refresh the bundled starter from a source theme
- `MANIFEST.md` — per-starter-file provenance
- `docs/` — design spec and implementation plan

## Development

All code lands via pull request; `main` is protected by convention (only the
owner merges).
