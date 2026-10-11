---
status: Accepted
date: "{{date}}"
topic: symfony-testing-and-operability
tags: [framework, symfony, testing]
supersedes: []
related: [symfony-conventions, php-quality-and-tests, ci-is-the-merge-gate, security-baseline]
---
# {{number}}. Test and operate Symfony applications

## Context

The PHP baseline sets the tools; Symfony adds a kernel test harness, a `test` environment,
the Messenger component for async work, and a compiled-container deploy step. We record how
they are used so tests are trustworthy and production matches the tested build.

## Decision

- **Test runner**: **PHPUnit** via the framework's test pack, configured in
  `phpunit.dist.xml`. Pure classes get plain unit tests; services needing the container use
  `KernelTestCase`; HTTP behavior uses `WebTestCase` against the `test` environment.
- **Real databases**: integration and functional tests use the production engine in a
  container with a separate test database, and isolate tests by wrapping each in a rolled-back
  transaction (for example with `dama/doctrine-test-bundle`). Fixtures are loaded
  explicitly, not shared implicitly across tests.
- **Smoke test every route** with a data-provider test, and keep URLs in functional tests
  hard-coded so an accidental URL change fails a test.
- **Console lint commands run in CI**: `lint:container`, `lint:yaml`, `lint:twig` and
  `lint:translations` where those components are used, alongside `composer audit`.
- **Architecture tests** use the PHP baseline's choice (Deptrac or PHPat).
- **Coverage** enforces the universal thresholds from the PHP baseline through PHPUnit's
  coverage configuration.
- **Operability**: structured logs to stdout via Monolog; a health endpoint for probes;
  asynchronous work through **Messenger** with a failure transport and retry strategy, and
  handlers that are **idempotent**. Deploys build with `APP_ENV=prod`, install without dev
  dependencies and warm the cache; secrets come from Symfony secrets or the environment.

## Alternatives considered

- **SQLite or mocked repositories for functional tests** — fast, but diverge from the
  production engine and miss mapping and migration errors.
- **Test-per-test schema rebuild instead of transaction rollback** — correct but slow enough
  that developers stop running the suite.
- **Pest as the default runner** — viable, but the PHP baseline standardizes on PHPUnit,
  which Symfony's own test tooling targets.
- **Synchronous handling of long work in the request** — simpler, but loses retries and
  isolation and ties latency to the slowest step.

## Consequences

- Tests exercise the same container wiring and database behavior as production, and broken
  wiring fails in CI through the container lint.
- CI needs a database container and a coverage driver.
- Idempotent Messenger handlers make retries and redelivery safe, at the cost of designing
  each handler for repeat execution.
