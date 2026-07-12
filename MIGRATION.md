# Setup: create the repo, install, and keep it updated

This scaffold is a ready git repo (it already has one commit). You just need to publish it to GitHub and install it. Pick whichever path matches your tooling.

## 1. Publish to GitHub

### Option A — with the GitHub CLI (`gh`)

```bash
cd claude-config
gh repo create claude-config --public --source=. --remote=origin --push
```

That creates `github.com/robsartin/claude-config` and pushes `main` in one step.

### Option B — plain git (create the empty repo on github.com first)

Create a new **empty** repo named `claude-config` on GitHub (no README/license), then:

```bash
cd claude-config
git remote add origin https://github.com/robsartin/claude-config.git
git branch -M main
git push -u origin main
```

## 2. Install in Claude Code (CLI)

```bash
/plugin marketplace add robsartin/claude-config
/plugin install voice@claude-config
```

Test it: ask Claude to "write a short blog intro in my voice." The `writing-in-robs-voice` skill should load automatically.

## 3. Install in Cowork (desktop)

Cowork supports the same plugins. Add the marketplace and install `voice` the same way from the desktop app's plugin interface. Cowork-specific state (project memory, connected folders) stays local and is not deployed from this repo.

## 4. Web projects (claude.ai)

Web projects can't install plugins. Keep this repo as the source of truth and paste the contents of
`plugins/voice/skills/writing-in-robs-voice/SKILL.md` (below the frontmatter) into the project's custom instructions when it changes.

## 5. The update loop

After you edit the voice profile or add a plugin:

```bash
cd claude-config
git add -A && git commit -m "update voice profile" && git push
```

Then on any machine where it's installed:

```bash
/plugin marketplace update claude-config
/plugin update voice@claude-config     # only needed if you pinned a version
```

Because the plugin has no pinned `version`, every push is picked up as the newest version automatically.

## 6. Multiple machines / dotfiles (optional)

For the machine-level bits a plugin doesn't cover (`~/.claude/CLAUDE.md`, `~/.claude/settings.json`), add a top-level `dotfiles/` directory to this repo and symlink from `~/.claude`. Then each machine is just `git pull` plus the plugin update above.

## Notes

- Only `plugin.json` lives inside a `.claude-plugin/` directory. Component folders (`skills/`, `agents/`, `hooks/`) sit at the plugin root.
- The skill's invocation name is fixed by the `name:` in its frontmatter (`writing-in-robs-voice`), so it stays stable across updates.
- Renaming the GitHub repo later changes the marketplace path you type in `/plugin marketplace add`. The marketplace's own name (`claude-config`, used in `voice@claude-config`) comes from `marketplace.json`, not the repo name.
