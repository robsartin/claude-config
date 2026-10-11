---
status: Accepted
date: "{{date}}"
topic: php-project-layout
tags: [language, php, structure]
supersedes: []
related: [php-quality-and-tests, i18n-in-php, security-baseline]
---
# {{number}}. Structure PHP projects with Composer, PSR-4 and strict types

## Context

PHP projects can be assembled from loose includes, global state and ad hoc autoloading, and
the language lets a type error pass silently through coercion. We want one predictable
structure, reproducible dependency installs, and a runtime that fails loudly on type
mistakes, so a repository is easy to move between and its dependencies are auditable.

## Decision

- **Composer** is the only dependency and autoload mechanism. `composer.json` is the source
  of truth for dependencies, autoload maps and scripts; `composer.lock` is **committed** for
  applications so every environment installs the same versions (libraries may omit it).
- **PSR-4 autoloading**: namespaces map to directories under `src/` (and `tests/` for
  `autoload-dev`). No `require`/`include` of class files, and the authoritative classmap is
  never hand-edited.
- **PHP version** is a currently supported release, chosen from the project's support policy
  at <https://www.php.net/supported-versions.php> and declared as a `require.php` constraint
  (and `config.platform.php` so Composer resolves for the real runtime). The project does not
  run on a branch that has left security support. Raising the floor is a deliberate,
  recorded change.
- **Strict typing**: every PHP file opens with `declare(strict_types=1);`, and signatures
  carry parameter, return and property types. `mixed` is used only at genuine boundaries.
- **Extensions the code relies on** (`ext-intl`, `ext-mbstring`, a database driver, ...) are
  declared under `require`, so a missing extension fails at install, not in production.
- **Scripts**: the project's quality commands are exposed as Composer scripts (see the
  quality ADR) so local runs and CI invoke the same entry points.

## Alternatives considered

- **Hand-written `require` chains or a custom autoloader** — rejected because they bypass
  Composer's resolution and classmap optimization and cannot be audited by dependency
  tooling.
- **Non-strict (coercing) mode** — the default, rejected because it silently converts
  `"1abc"`-style values and hides type bugs that static analysis alone cannot catch at
  runtime boundaries.
- **PSR-0 or classmap-only autoloading** — rejected; PSR-0 is deprecated and a classmap needs
  regeneration on every added class during development.
- **Not committing `composer.lock` for applications** — rejected because installs would
  float, making a deploy differ from the tested build.

## Consequences

- Every PHP repo has the same entry points, namespace layout and install story.
- Type errors surface at the call site at runtime, and static analysis has complete type
  information to work with.
- Contributors need a matching PHP and the declared extensions locally; a container or
  version manager is the usual way to provide them.
- Dependencies are reproducible and can be scanned for known vulnerabilities (`composer
  audit`) as part of the security baseline.
