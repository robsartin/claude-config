# claude-config

Rob Sartin's personal Claude configuration, managed as one git repo that doubles as a Claude Code **plugin marketplace**. This is the single source of truth for his skills, agents, and settings, installed everywhere he runs Claude.

## Layout

```
.claude-plugin/marketplace.json     # marketplace catalog (name: claude-config)
plugins/voice/                      # the "voice" plugin
  .claude-plugin/plugin.json
  skills/writing-in-robs-voice/
    SKILL.md                        # Rob's full voice profile (source of truth)
    references/blog-index.md        # index of his blog posts, loaded on demand
plugins/adr-toolkit/                # the "adr-toolkit" plugin (Python-backed)
  .claude-plugin/plugin.json
  skills/adr-toolkit/SKILL.md
  packs/                            # composable ADR packs (universal, python, react, ...)
  bin/install.sh                    # one-time venv bootstrap (see below)
plugins/wordpress-block-theme/      # the "wordpress-block-theme" plugin (content + tooling)
  .claude-plugin/plugin.json
  skills/wordpress-block-theme/SKILL.md
  assets/starter/                   # canonical, self-validating block-theme starter
  references/                       # block-markup rules, dev/editor/deploy guides
plugins/start-work/                 # the "start-work" plugin (Python-backed)
  .claude-plugin/plugin.json
  skills/start-work/SKILL.md
  bin/start_work.py                 # issue + branch helpers, run on python3, no venv
  commands/start-work.md
```

## The wordpress-block-theme skill

`wordpress-block-theme` is a content-and-tooling skill: a canonical, self-validating starter theme plus reference guides for building WordPress block (Full Site Editing / Gutenberg) themes. Its static gates (`assets/starter/bin/check-all.sh`) run on `python3` with no Docker required; the live theme-check (`assets/starter/bin/theme-check.sh`) needs `@wordpress/env` running.

## The voice skill

`writing-in-robs-voice` is what makes Claude draft and edit prose as Rob (blog posts, LinkedIn, email, book text). It auto-loads when a task matches its description. **When editing Rob's voice, edit `plugins/voice/skills/writing-in-robs-voice/SKILL.md` here** — it is the single source of truth. (An older copy once lived in a `myClaudeVoice/voice.md`; that is retired, do not sync to it.)

Before drafting anything as Rob, read that SKILL.md in full. The most load-bearing rules, as a quick reference:

- **No em-dashes** in generated drafts. Use parentheticals, full stops, colons, or commas instead. (Rob's own writing uses em-dashes freely; the ban applies only to AI-generated drafts, where they read as a machine tell.)
- **Prefer vague quantifiers** ("several", "a shelf of") over invented precise numbers. Use exact figures only for things actually measured.
- **Authorship**: robsartin.com posts from **July 2024 onward** are Rob's voice; **January–June 2024** posts were written by his wife Rachel and brother Hank during his hospitalization and are NOT his voice. Don't imitate them.
- The SKILL.md also carries a dated timeline of Rob's medical/life history — use it so drafts get facts right.

## The start-work skill

`start-work` turns a ticket or idea into a tracked issue + branch and hands off to planning. Its helpers (`bin/start_work.py`) run directly on `python3`, no venv bootstrap needed; it only supports the GitHub path today, with GitLab/Jira as a later adapter.

## Maintaining this repo

- **Add a plugin**: create `plugins/<name>/.claude-plugin/plugin.json`, put components at the plugin root (`skills/`, `agents/`, `hooks/hooks.json`, `.mcp.json`), then add an entry to the `plugins` array in `.claude-plugin/marketplace.json`.
- Only `plugin.json` goes inside a `.claude-plugin/` directory; component folders sit at the plugin root.
- Skills need a frontmatter `name:` so their invocation name stays stable across updates.
- Plugins here omit a `version` field, so **every push is treated as an update** (the git commit SHA is the version). Add `"version"` to a `plugin.json` only if you want to gate updates behind manual bumps.

## Plugin-source policy

Where a new plugin's code lives depends on where it came from:

| Case | Handling | marketplace source |
| --- | --- | --- |
| Mine, source belongs here (`voice`) | Vendor under `plugins/<name>/` | `"./plugins/<name>"` |
| Mine, was a separate repo (`adr-toolkit`) | Vendor + archive the old repo | `"./plugins/<name>"` |
| Someone else's plugin | Catalog, don't copy their code | `{"source":{"source":"github","repo":"owner/repo"}}` or `/plugin marketplace add owner/repo` |

`adr-toolkit` is Python-backed, unlike `voice` (pure markdown skill): after installing or updating the plugin, run `${CLAUDE_PLUGIN_ROOT}/bin/install.sh` once to bootstrap its venv and editable package install before the CLI works.

## Install / update

```bash
/plugin marketplace add robsartin/claude-config     # once, per machine
/plugin install voice@claude-config

# after pushing changes:
/plugin marketplace update claude-config
```
