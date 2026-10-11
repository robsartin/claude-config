---
status: Accepted
date: "{{date}}"
topic: fastapi-conventions
tags: [framework, fastapi]
supersedes: []
related: [python-project-layout, service-conventions, security-baseline, fastapi-testing-and-operability, observability-in-python]
---
# {{number}}. FastAPI conventions

## Context

FastAPI is an ASGI framework built on Starlette and Pydantic: type annotations drive request
parsing, validation, dependency injection and the generated OpenAPI document. That is its
strength and its trap. Annotations are executable here, so sloppy types become sloppy
contracts, and the async model means one blocking call in a handler stalls every request
sharing the event loop. FastAPI is only the application; a separate ASGI server runs it.
This builds on the service conventions, which already require config from the environment,
versioned APIs and graceful shutdown.

## Decision

- **Pydantic models define every request and response body**, and routes declare
  `response_model` (or a return annotation) so internal fields cannot leak. Domain objects
  stay plain Python; conversion happens at the edge.
- **Dependencies are injected with `Depends` using `Annotated` aliases**, declared once and
  reused. Database sessions, settings and the current user come in this way, never from
  module-level globals, which is also what makes them overridable in tests.
- **Startup and shutdown use a lifespan handler**, which owns pools and clients so graceful
  shutdown actually releases them.
- **Routes are grouped in `APIRouter` modules per bounded concern**, mounted under an
  explicit version prefix; the generated OpenAPI document is the published contract and is
  diffed in CI to catch accidental breaking changes.
- **Do not block the event loop.** Handlers are `async def` only when everything they await
  is genuinely async; otherwise they are plain `def` and run in the threadpool. CPU-heavy
  work goes to a worker, not a handler.
- **Settings are a typed settings object** populated from the environment, validated at
  startup so a bad deployment fails immediately.
- **Run under a production ASGI server** with the process count set by the deployment, not
  by in-app code.

## Alternatives considered

- **Returning ORM objects or dicts directly** — less code, but the response shape becomes
  whatever the object currently holds, so a new column or a password hash can reach clients
  without anyone choosing that.
- **Module-level singletons for the database and settings** — simple, but they cannot be
  swapped per test and hide start-up order; `Depends` makes the wiring visible and
  overridable.
- **`on_event("startup")` hooks** — the older mechanism; split setup and teardown cannot
  share state, which is how leaked connections appear. Lifespan keeps both in one place.
- **Flask or Django REST for a typed JSON API** — viable and covered by their own packs, but
  they validate and document through add-ons; choosing FastAPI is justified when the typed
  contract and async IO are the point, and not otherwise.
- **`async def` everywhere by default** — looks modern, yet a single synchronous driver call
  inside one blocks all concurrent requests, a failure that only shows under load.

## Consequences

- The contract is explicit, validated, and visible in the OpenAPI document.
- Wiring is injectable, so handlers are testable without patching.
- Developers must understand the sync-versus-async rule; the cost of getting it wrong is
  latency, not an error.
