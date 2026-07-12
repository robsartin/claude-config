# 5. Make CI the merge gate

- **Date:** 2026-07-07
- **Status:** Accepted

## Context

Standards that are not enforced erode. If formatting, tests, and coverage are advisory,
they drift, and `main` slowly stops being trustworthy. We want the quality bar checked
mechanically on every change, not left to reviewer memory.

## Decision

A GitHub Actions workflow runs on every pull request and **must pass to merge**. It enforces:

- **Formatting/linting** — the project's formatter and linter report no violations.
- **Tests** — the full test suite passes.
- **Coverage thresholds** — **line coverage > 80%** and **branch coverage > 65%**. A drop
  below either fails the build.

These thresholds are policy and are consistent across projects. The language-specific ADR
names the tool that measures coverage and any justified exclusions; a project may *tighten*
the thresholds but never loosen them.

## Consequences

- `main` stays formatted, tested, and adequately covered by construction.
- The gate can block a merge on a coverage regression, which occasionally requires adding
  tests before shipping — the intended behavior.
- CI must stay fast enough not to become a bottleneck; slow suites get attention.
