---
status: Accepted
date: "{{date}}"
topic: symfony-conventions
tags: [framework, symfony]
supersedes: []
related: [php-project-layout, php-quality-and-tests, symfony-testing-and-operability, security-baseline, accessibility-baseline, i18n-in-php]
---
# {{number}}. Symfony application conventions

## Context

Symfony supports several configuration formats and wiring styles, and it is easy to reach
into the container or put business logic in controllers. Left unconstrained, a codebase
mixes styles that are hard to test and upgrade. We pin one set on top of the PHP baseline,
following the framework's own published best practices.

## Decision

- **Track a supported Symfony version.** Prefer an LTS line for long-lived applications; the
  choice comes from the release schedule (<https://symfony.com/releases>) and is a caret
  constraint on the `symfony/*` packages, kept to one version across components. A line that
  has left security support is not run.
- **Autowiring and autoconfiguration** with **private services** and constructor injection;
  `$container->get()` is not used. Configuration that belongs next to code uses attributes
  (`#[Autowire]`, routing and security attributes); the remainder is YAML or PHP, one chosen
  per project.
- **Thin controllers** extending `AbstractController`: they map the request, call an
  application service or message bus, and return a response. Business rules live in plain
  classes under `src/`, not in controllers or Doctrine entities' framework glue.
- **Configuration**: environment variables for infrastructure values, **Symfony secrets**
  (or an external secret manager) for sensitive ones, and parameters for application
  behavior; nothing secret in committed `.env` files.
- **Doctrine** entities are mapped with PHP attributes; schema changes ship as migrations.
  Validation constraints sit on the underlying object, not on form fields.
- **Security** uses voters for non-trivial authorization, the `auto` password hasher, and as
  few firewalls as the authentication needs.
- **Formatting** uses PHP-CS-Fixer with the PER ruleset per the PHP baseline; static analysis
  uses PHPStan with its Symfony and Doctrine extensions.
- **Templates (Twig)** keep auto-escaping on; `|raw` requires a reviewed reason. Where the
  accessibility baseline is selected, templates meet it.

## Alternatives considered

- **Pulling services from the container (service locator)** — shorter at call sites, but
  hides dependencies and defeats compile-time container checks.
- **Reusable bundles for internal application code** — over-structure for code that is not
  shared; namespaces under `App\` suffice, and a private bundle is for genuinely shared code.
- **Business logic in controllers or entities** — fewer classes, but untestable without HTTP
  and a database; plain service classes keep rules unit-testable.
- **XML or annotation-based configuration and mapping** — XML is verbose and annotations are
  superseded by native attributes, which keep metadata beside the code.
- **Committing a populated `.env` with real secrets** — rejected by the security baseline.

## Consequences

- Components are unit-testable without the kernel, and the container is compiled and
  validated at build time.
- Upgrades are smaller because the application follows the framework's own recommended
  style and one version line.
- A controller or service with many collaborators grows a visibly long constructor,
  surfacing the too-many-responsibilities signal.
