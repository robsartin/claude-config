# 3. Integrate via a PR-based trunk workflow

- **Date:** 2026-07-07
- **Status:** Accepted

## Context

We want `main` to stay releasable at all times, changes to be reviewable in coherent
units, and history to be legible. Committing directly to `main` or piling unrelated work
onto a long-lived branch works against all three.

## Decision

All work flows through short-lived branches and pull requests:

- Start from an **issue** describing the work.
- Create a **branch** off `main` named for the issue (e.g. `123-short-description`).
- Make focused **commits** on the branch.
- Open a **pull request** into `main`; **squash-merge** it so each change lands as one
  coherent commit.
- **Never commit directly to `main`.**
- **No new development on a PR that is already open and marked ready for review.** If more
  work is needed, branch off it or return the PR to draft first — reviewers should not be
  chasing a moving target.

## Consequences

- `main` is always a series of reviewed, squashed, releasable commits.
- Review happens on stable diffs, not shifting ones.
- The one accepted exception is the initial bootstrap commit of an empty repository, which
  has no base to branch from.
