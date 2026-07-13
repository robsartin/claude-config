---
description: Sync installed plugins with the claude-config marketplace (install new, update installed, report orphans)
argument-hint: "[--dry-run] [--prune]"
allowed-tools: Bash
---

Run the claude-config plugin sync script, passing along any arguments the user
supplied (`--dry-run` to preview, `--prune` to also uninstall orphaned plugins),
then report the result.

Locate and run the bundled script (it lives beside this plugin; the fallback
handles the case where `CLAUDE_PLUGIN_ROOT` is not set in this context):

```bash
script="${CLAUDE_PLUGIN_ROOT:-}/sync-plugins.sh"
if [ ! -f "$script" ]; then
  script=$(ls -d "${CLAUDE_CONFIG_DIR:-$HOME/.claude}"/plugins/cache/claude-config/plugin-sync/*/sync-plugins.sh 2>/dev/null | tail -1)
fi
if [ -z "$script" ] || [ ! -f "$script" ]; then
  echo "Could not locate sync-plugins.sh — is the plugin-sync plugin installed from claude-config?" >&2
  exit 1
fi
bash "$script" $ARGUMENTS
```

Then briefly summarize to the user what the script reported — how many plugins
were installed, updated, or flagged as orphaned — and, if anything changed,
remind them to restart Claude Code to apply it. Do not take any other action;
this command only runs the sync script.
