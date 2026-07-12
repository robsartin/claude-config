# 6. Keep developer and user documentation current

- **Date:** 2026-07-07
- **Status:** Accepted

## Context

Documentation that lags the code is worse than none — it misleads. When docs are treated
as a separate, later task, they rot. We want them to move with the change that affects them.

## Decision

Documentation is part of the definition of done. A change that affects behavior, setup,
interfaces, or usage updates the relevant docs **in the same pull request**:

- **Developer documentation** — how to build, test, run, and reason about the system
  (README, architecture notes, ADRs).
- **User documentation** — how someone uses the software, kept accurate to what ships.

A PR that changes behavior without touching the docs it affects is incomplete.

## Consequences

- Docs stay trustworthy because they change alongside the code, under the same review.
- Each PR carries a little more work; the payoff is documentation people can rely on.
- Reviewers watch for the docs half of a change, not just the code half.
