---
description: Squash-merge the current PR/MR, log what shipped, and close out the ticket
allowed-tools: Bash, Skill
---

Invoke the `start-work` skill's "Merge it" step (section 9) for the **current branch**.

Verify first — the PR/MR exists, checks are green (not pending), and it is mergeable. Stop and
report if anything is red, pending, or conflicted. If it is already merged, skip ahead to the
worklog and ticket steps.

Then squash-merge with branch deletion, return to the default branch and pull, log a `shipped`
worklog entry if worklog is available, and transition the Jira ticket if `jira.doneStatus` is set.
Report what merged, what was logged, and the ticket's final state.
