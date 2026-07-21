---
description: Gate, push, and put the current branch's PR/MR up for review
allowed-tools: Bash, Skill
---

Invoke the `start-work` skill's "Finish the work" step (section 8) for the **current branch**.

Refuse if the working tree is dirty or you're on the default branch. Replay the repo's CI gate
and stop without pushing if it fails, always listing any steps you skipped. Then push and create
or un-draft the PR/MR, and report its URL.

Do not merge, do not change the ticket, and do not write a worklog entry — those belong to
`/start-work:merge`.
