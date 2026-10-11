---
status: Accepted
date: "{{date}}"
topic: laravel-conventions
tags: [framework, laravel]
supersedes: []
related: [php-project-layout, php-quality-and-tests, laravel-testing-and-operability, security-baseline, accessibility-baseline, i18n-in-php]
---
# {{number}}. Laravel application conventions

## Context

Laravel makes most things possible several ways: facades, helpers, container resolution,
fat controllers, `env()` calls scattered through the code. Left unconstrained, a codebase
mixes styles that are hard to test and that break under configuration caching. We pin one
set on top of the PHP baseline.

## Decision

- **Track a supported Laravel major.** The version is chosen from the support policy in the
  Laravel release notes (<https://laravel.com/docs/releases>) and declared with a caret
  constraint in `composer.json`. A major that has left security support is not run.
- **Constructor injection** into controllers, jobs and services; facades and global helpers
  appear only at the framework edge (routes, service providers, Blade), not in domain code.
- **Thin controllers.** A controller validates through a **Form Request**, delegates to an
  action or service class, and returns a response or **API Resource**. Business rules live
  outside controllers and Eloquent models' HTTP concerns.
- **Configuration through `config/*.php` only.** `env()` is called only inside config files,
  so `php artisan config:cache` works in production; code reads `config()`.
- **Authorization via Policies and Gates**, applied at the route or controller, never ad hoc
  role checks inline. Mass assignment is guarded explicitly (`$fillable`).
- **Database changes through migrations** committed with the code; production schema is never
  edited by hand. Queries that load relations use eager loading, and lazy-loading is made
  to throw outside production so N+1 queries fail in tests.
- **Formatting** uses **Laravel Pint** with the `per` preset (PER Coding Style), matching the
  PHP baseline; static analysis uses **Larastan** (PHPStan extension) at the baseline level.
- **Templates (Blade)** use escaped echo output by default; the unescaped `{!! !!}` form requires
  a reviewed reason. Where the accessibility baseline is selected, templates meet it.

## Alternatives considered

- **`env()` throughout the application** — convenient, but returns `null` once configuration
  is cached, a failure that only appears in production.
- **Fat controllers / logic in models** — fewer files, but untestable without HTTP and
  entangled with persistence; Form Requests plus action classes keep each concern testable.
- **Inline validation and `if ($user->role === ...)` authorization** — quick, but scatters
  rules; Form Requests and Policies centralize and are discoverable by the framework.
- **Facades everywhere** — terse, but hides dependencies and couples domain code to the
  container; constructor injection keeps classes testable in isolation.
- **Pint's default `laravel` preset** — idiomatic to Laravel but diverges from the PER
  standard the PHP baseline sets for every PHP project.

## Consequences

- Components are unit-testable without booting the framework, and the app survives
  `config:cache` and `route:cache`.
- Authorization and validation are enumerable rather than scattered.
- A team follows one Laravel style, enforced by Pint and Larastan in CI.
- Strictness such as throwing on lazy loading surfaces performance defects early, at the
  cost of fixing them as they appear.
