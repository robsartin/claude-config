---
status: Accepted
date: "{{date}}"
topic: php-quality-and-tests
tags: [language, php, testing]
supersedes: []
related: [php-project-layout, ci-is-the-merge-gate, laravel-testing-and-operability, symfony-testing-and-operability]
---
# {{number}}. Enforce PHP quality gates and layered tests

## Context

The universal CI-gate decision requires enforced formatting, tests and coverage, and this
baseline also calls for static analysis, architecture tests and real-dependency integration
tests. PHP needs concrete tools so those requirements are measurable and the same locally
and in CI.

## Decision

Configured in the repository and exposed as Composer scripts; CI runs exactly those scripts:

- **Formatting** with **PHP-CS-Fixer** enforcing the **PER Coding Style** ruleset, run in
  check mode in CI so a violation fails the build. (**Laravel Pint**, which wraps
  PHP-CS-Fixer, is the equivalent where the framework pack selects it.)
- **Static analysis** with **PHPStan** at its highest rule level (`max`), configured in
  `phpstan.neon`. Pre-existing violations in a legacy codebase are captured in a committed
  **baseline** and burned down; new code is never added to the baseline.
- **Tests** with **PHPUnit** (Pest is acceptable only where a framework pack adopts it),
  configured in `phpunit.xml`. Fast **unit tests** need no framework or I/O; **integration
  tests** live in their own suite and exercise real dependencies (database, queue, cache)
  started in containers, e.g. Testcontainers or the CI service containers.
- **Coverage** is collected with **PCOV** (or Xdebug) and enforces the universal
  thresholds, **line > 80%, branch > 65%**, failing the build below them. A project may
  tighten these. Branch coverage needs Xdebug in coverage mode; the project records which
  driver measures which number.
- **Architecture tests** keep layer boundaries mechanical: **Deptrac** (layer rules in a
  YAML config) or **PHPat** (rules as PHPStan-run tests) fails the build on a forbidden
  dependency or cycle. One of the two is chosen per project, not both.
- **Dependency audit**: `composer audit` runs in CI alongside the security baseline.

## Alternatives considered

- **Psalm instead of PHPStan** — a capable analyzer, rejected as the default because PHPStan
  has the wider framework-extension ecosystem (Larastan, Symfony and Doctrine extensions)
  that the framework packs rely on. A project already standardized on Psalm may record a
  superseding ADR.
- **PHP_CodeSniffer instead of PHP-CS-Fixer** — rejected as the primary formatter; a fixer
  rewrites files to compliance rather than only reporting, matching Pint and the other
  languages' formatters.
- **SQLite or in-memory fakes instead of real databases for integration tests** — faster,
  but they diverge from production SQL and locking behavior, undermining trust in the suite.
- **Coverage from line metrics only** — rejected; the universal gate has a branch threshold
  that needs a branch-capable driver.
- **Reviewer-enforced layering (no architecture tests)** — drifts; boundaries erode silently
  without a failing build.

## Consequences

- The universal formatting and coverage gates are concrete for PHP, and type, layering and
  dependency regressions fail mechanically rather than in review.
- The `max` level plus a shrinking baseline raises up-front effort on legacy code but makes
  strictness monotonic.
- CI needs a coverage driver and a container runtime for the integration suite.
- Tool versions are pinned in `composer.lock`, so upgrading an analyzer is a reviewed change.
