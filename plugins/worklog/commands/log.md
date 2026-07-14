---
description: Log a work-activity entry (started/shipped/note) to your Worklog.md
argument-hint: "<started|shipped|note> <text> [--ref KEY] [--branch NAME]"
allowed-tools: Bash
---

Invoke the `worklog` skill's "Logging an entry" step with the user's arguments
($ARGUMENTS). If no type/text is given, ask what to log. Report the logged line.
