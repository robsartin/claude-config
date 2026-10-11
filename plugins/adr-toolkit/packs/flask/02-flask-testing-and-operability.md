---
status: Accepted
date: "{{date}}"
topic: flask-testing-and-operability
tags: [framework, flask, testing]
supersedes: []
related: [python-toolchain, flask-conventions, service-conventions, observability-in-python]
---
# {{number}}. Flask testing and operability

## Context

The application factory makes Flask easy to test, and the lack of built-in persistence makes
it easy to test against whatever is nearest at hand. The service must also be operable. This
applies the Python toolchain and the service conventions to Flask.

## Decision

- **pytest with an app fixture** that calls `create_app` with a test configuration and uses
  Flask's test client; the toolchain's coverage thresholds apply.
- **Business logic is tested without the app**, as plain functions; route tests cover
  routing, validation, permissions and status codes.
- **Integration tests use real dependencies** (for example PostgreSQL through
  **Testcontainers**) in a separate directory and marker.
- **Architecture tests** fail the build when domain code imports Flask or when blueprints
  import each other's internals, using an import-contract tool.
- **Health and readiness routes** exist, readiness checking the database; logs are
  structured with a request id attached per request.
- **CI runs the app under the production WSGI server** in a smoke test, so server-specific
  configuration problems appear before deploy.

## Alternatives considered

- **Testing everything through the test client** — one style, but every rule test pays
  for request setup and failures point at the HTTP layer instead of the rule.
- **SQLite or an in-memory store for integration tests** — rejected for the reason given in
  the other Python packs: it behaves differently from the production database.
- **Importing the global app object into tests** — not possible under the factory
  convention, which is the point: each test builds the app it needs.
- **Skipping the production-server smoke test** — cheaper, and then the first run under the
  real server is production.

## Consequences

- Rules are fast to test and routes are tested for what is theirs.
- Layering is enforced by the build rather than by habit.
- CI carries a container runtime and a small extra smoke step.
