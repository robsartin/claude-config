---
description: Open a draft PR (GitHub) or draft MR (GitLab) for the current start-work branch
allowed-tools: Bash, Skill
---

Invoke the `start-work` skill's "Open the draft PR/MR" step for the **current branch**.

1. Detect the provider: `python3 "${CLAUDE_PLUGIN_ROOT}/bin/start_work.py" provider`.
2. Push the branch if it has no upstream yet.
3. Open the draft — `gh pr create --draft --fill` (github) or `glab mr create --draft --fill --yes`
   (gitlab). If the provider is `unknown`, ask rather than guessing.

Report the resulting URL. Do not merge, and do not take the PR/MR out of draft.
