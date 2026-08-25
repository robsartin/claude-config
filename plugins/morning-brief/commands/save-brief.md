---
description: Save today's morning brief into 0 - Planning, archiving the previous one
argument-hint: "[--file <path>] [--date YYYY-MM-DD] [--dry-run]"
allowed-tools: Bash
---

Invoke the `morning-brief` skill's "Saving the brief" step with the user's arguments
($ARGUMENTS). With no arguments, render the brief markdown from the `/morning` output
already in this conversation; if there is none, say so rather than inventing one.
Report which note was archived and where the new one landed.
