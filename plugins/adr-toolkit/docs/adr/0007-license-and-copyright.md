# 7. Declare an explicit license and copyright

- **Date:** 2026-07-07
- **Status:** Accepted

## Context

A repository with no license is "all rights reserved" by default — others (and future us)
have no clear terms for use, and intent is ambiguous. The choice of terms is a decision
worth recording, not leaving implicit.

## Decision

Every repository declares its terms explicitly:

- A **`LICENSE` file** at the repository root stating the chosen license.
- **Copyright** attributed to `adr-claude-skill`'s owner.
- The specific license is chosen deliberately per repository based on its intended use
  (permissive for open libraries, proprietary/all-rights-reserved for private work) and
  recorded here when it is anything other than the repository's stated default.

## Consequences

- Use, distribution, and contribution terms are unambiguous from day one.
- Changing the license later is a deliberate, superseding decision — not a silent edit.
- Third-party dependencies must be checked for license compatibility with the chosen terms.
