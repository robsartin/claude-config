---
status: Accepted
date: "{{date}}"
topic: django-testing-and-operability
tags: [framework, django, testing]
supersedes: []
related: [python-toolchain, django-conventions, service-conventions, observability-in-python]
---
# {{number}}. Django testing and operability

## Context

Django's own `TestCase` and test client make it easy to write slow, database-bound tests for
everything, and its default SQLite configuration makes it equally easy to test against a
database the production system does not use. A service also has to be operable: it needs
health signals and logs that can be queried. This applies the Python toolchain and the
universal testing decisions to Django.

## Decision

- **Tests run under pytest with `pytest-django`**, using the toolchain's coverage
  thresholds; settings for tests are selected by environment variable, not a second
  hand-maintained settings file.
- **Test at the narrowest useful level.** Service functions and model methods get plain
  unit tests; views get test-client tests for routing, permissions and status codes;
  the full stack is exercised by a small number of end-to-end checks.
- **Integration tests use the production database engine** (for example PostgreSQL) in a
  **Testcontainers** container, in their own test directory and marker, not SQLite
  standing in for it.
- **Architecture tests** fail the build when layering is violated (for example, models and
  services importing from views or templates), using an import-contract tool such as
  `import-linter` or `pytest-archon`.
- **Health and readiness endpoints** are served by the app (readiness checks the database
  connection), and logs are structured with a request id on every line.

## Alternatives considered

- **Django's `unittest`-based runner (`manage.py test`)** — works with no dependencies, but
  loses pytest fixtures, parametrization and the shared coverage and marker configuration
  the Python toolchain standardizes.
- **SQLite for all tests** — fast and zero setup, but differs from PostgreSQL in locking,
  JSON, constraint and transaction behavior, so passing tests do not vouch for production.
  The Python and JVM baselines reject in-memory substitutes for the same reason.
- **Mocking the ORM in view tests** — isolates the view, but the mock encodes the author's
  belief about query behavior and keeps passing when the query is wrong.
- **No architecture test; rely on review** — layering erodes one convenient import at a
  time, and reviewers see a diff, not the whole import graph.

## Consequences

- The suite is fast at the base and trustworthy at the integration layer, because real
  dependencies are used where behavior matters.
- Layering is enforced mechanically as the app grows.
- Contributors need a container runtime for the integration tests, and CI needs the same.
