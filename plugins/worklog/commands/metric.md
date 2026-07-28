---
description: Record a numeric KPI reading (upserts per day) to your Metrics.md
argument-hint: "<name=value> [<name=value> ...] [--date YYYY-MM-DD]"
allowed-tools: Bash
---

Invoke the `worklog` skill's "Metrics — Record a reading" step with the user's arguments
($ARGUMENTS). Accepts one reading or several `name=value` tokens in one call (a whole day at once);
if nothing is given, ask. Values must be numeric — if any token is bad the whole batch is rejected
and nothing is written. Re-recording a metric for the same day replaces it.
