---
status: Accepted
date: "{{date}}"
topic: laravel-testing-and-operability
tags: [framework, laravel, testing]
supersedes: []
related: [laravel-conventions, php-quality-and-tests, ci-is-the-merge-gate, security-baseline]
---
# {{number}}. Test and operate Laravel applications

## Context

The PHP baseline sets the tools; Laravel adds a test harness, a queue and scheduler, and a
deploy-time optimization step. We record how they are used so tests are trustworthy and
production behaves like the tested build.

## Decision

- **Test runner**: **PHPUnit**, as the PHP baseline sets, run through `php artisan test` or
  `vendor/bin/phpunit` with the same configuration in CI. Most tests are **Feature tests**
  (HTTP through the kernel); `Unit` tests are for pure classes that never boot the app.
- **Real databases**: Feature tests run against the production engine (for example
  PostgreSQL or MySQL in a container), isolated with `RefreshDatabase` or
  `LazilyRefreshDatabase`. **Parallel testing** (`--parallel`) is used for speed; the
  framework provisions a database per process.
- **Fakes at the edges only**: `Queue::fake()`, `Mail::fake()`, `Http::fake()` and
  `Event::fake()` replace external effects, not the database.
- **Architecture tests** use the PHP baseline's choice (Deptrac or PHPat) to keep controllers
  from reaching into persistence and domain code from depending on HTTP.
- **Coverage** through `php artisan test --coverage --min=<n>` or the PHPUnit config
  enforces the universal thresholds from the PHP baseline.
- **Operability**: structured logging to stdout through a configured log channel; a
  `/up` health route (the framework's default) for orchestration probes; queue workers and
  the scheduler run as supervised processes, and jobs are **idempotent** with explicit
  `tries`/`backoff` and a failed-jobs table. Deploys run `config:cache`, `route:cache`
  and `view:cache`.
- **Secrets** come from the environment or a secret manager; `.env` is never committed and
  `.env.example` documents the keys.

## Alternatives considered

- **SQLite in-memory for Feature tests** — fast, but SQL dialect, constraint and locking
  differences hide production bugs, so it is rejected in favor of the real engine.
- **Pest as the default runner** — supported by Laravel and pleasant, but the PHP baseline
  standardizes on PHPUnit across frameworks; adopting Pest is a project-level superseding
  decision, not a default.
- **Mocking the database or Eloquent** — brittle and couples tests to implementation; real
  queries catch mapping and migration errors.
- **Running queues synchronously in production** — simpler to deploy, but removes isolation
  and retry semantics and blocks the request.

## Consequences

- Tests exercise the same code paths and database behavior as production.
- CI needs a database container and a coverage driver.
- Idempotent jobs and cached config make deploys and retries safe, but require discipline
  when writing jobs and when reading configuration.
