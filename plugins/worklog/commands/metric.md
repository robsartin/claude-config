---
description: Record a numeric KPI reading (upserts per day) to your Metrics.md
argument-hint: "<name> <value> [--date YYYY-MM-DD]"
allowed-tools: Bash
---

Invoke the `worklog` skill's "Metrics — Record a reading" step with the user's arguments
($ARGUMENTS). If no name/value is given, ask. Report the stored reading. The value must be
numeric; re-recording the same metric on the same day replaces it.
