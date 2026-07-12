# 8. Maintain a security baseline

- **Date:** 2026-07-07
- **Status:** Accepted

## Context

Secrets committed to a repository are effectively public and permanent — history preserves
them even after deletion. Dependencies accumulate known vulnerabilities over time. These
risks are cheap to prevent and expensive to remediate, so we hold a non-negotiable baseline.

## Decision

Every repository upholds these practices; they are mandatory, not opt-in:

- **No secrets in the repository, ever.** Credentials, tokens, and keys are supplied via
  environment or a secret manager and never committed. Configuration templates use
  placeholders. Secret-scanning is enabled where available.
- **A documented way to supply secrets** for local development and CI, so "no secrets in
  the repo" never blocks getting the software running.
- **Automated dependency updates** (e.g. Dependabot or Renovate) raise PRs for vulnerable
  and outdated dependencies, which flow through the normal CI gate.

## Consequences

- A leaked-secret incident is prevented rather than cleaned up after the fact.
- Dependency risk is surfaced continuously instead of discovered during an audit.
- Contributors must route secrets through the sanctioned mechanism, and dependency-update
  PRs are a routine, ongoing part of maintenance.
