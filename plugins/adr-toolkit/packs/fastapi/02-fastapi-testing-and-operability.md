---
status: Accepted
date: "{{date}}"
topic: fastapi-testing-and-operability
tags: [framework, fastapi, testing]
supersedes: []
related: [python-toolchain, fastapi-conventions, service-conventions, observability-in-python]
---
# {{number}}. FastAPI testing and operability

## Context

FastAPI's dependency injection makes the application easy to test in-process, and tempts
teams to override every dependency with a fake, leaving real database and broker behavior
untested. The service must also be operable under an orchestrator. This applies the Python
toolchain and service conventions to FastAPI.

## Decision

- **pytest with the framework's `TestClient`** (or an async HTTP client for async tests)
  drives the app in process; the toolchain's coverage thresholds apply.
- **Override dependencies at the seam, not inside handlers**, with `dependency_overrides`
  scoped to a fixture and cleared afterwards.
- **Integration tests use real dependencies** such as PostgreSQL through **Testcontainers**,
  in a separate test directory and marker, and exercise the real session dependency rather
  than a fake.
- **Architecture tests** fail the build when routers import persistence directly or domain
  code imports FastAPI or Pydantic request models, via an import-contract tool.
- **Liveness and readiness endpoints** are separate routes; readiness checks the
  dependencies the lifespan handler opened. Logs are structured with a request id.
- **CI diffs the OpenAPI document** against the committed one and fails on an unreviewed
  change.

## Alternatives considered

- **Fakes for every dependency in all tests** — fast and easy, but a fake repository agrees
  with the code that wrote it, so SQL and constraint bugs never surface. Fakes are kept for
  unit tests; integration tests use the real thing.
- **SQLite standing in for the production database** — rejected on the same grounds as in
  the other Python and JVM packs: different behavior, false confidence.
- **Testing only through a running server with live HTTP** — truest, but slow and hard to
  fault-inject; reserved for a thin smoke layer.
- **A single health route** — conflates "alive" with "ready", the failure the service
  conventions already reject.

## Consequences

- Most tests are fast and in process, while the behavior that matters is checked against
  real dependencies.
- The API contract cannot change silently.
- Integration tests need a container runtime locally and in CI.
