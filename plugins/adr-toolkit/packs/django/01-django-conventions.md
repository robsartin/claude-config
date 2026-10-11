---
status: Accepted
date: "{{date}}"
topic: django-conventions
tags: [framework, django]
supersedes: []
related: [python-project-layout, security-baseline, django-testing-and-operability, accessibility-baseline, observability-in-python]
---
# {{number}}. Django conventions

## Context

Django is a batteries-included framework: ORM, migrations, forms, auth, admin, templates and
CSRF/XSS protection ship together. The risk is not missing features but inconsistent use of
them: business rules scattered through views and templates, settings that differ by hand
between environments, and security switches left at development values. Django also
publishes a support policy with long-term-support series, so the version a project sits on
is a decision with an expiry date. This builds on the Python layout and the security
baseline; the support schedule lives at <https://www.djangoproject.com/download/>, not here.

## Decision

- **Track a supported release.** Pin Django to a series that is currently supported
  upstream (an LTS series for long-lived services) in `pyproject.toml`, and treat leaving
  support as a scheduled upgrade rather than an incident.
- **One app per bounded concern**, each with its own `models`, `urls` and tests. Business
  rules live in plain service functions or model methods; views stay thin (parse request,
  call a service, render or serialize).
- **Settings come from the environment** (per the service conventions), with one settings
  module whose environment-specific values are read from variables. `DEBUG` defaults to
  off, `SECRET_KEY` and `ALLOWED_HOSTS` have no usable default, and CI runs
  `manage.py check --deploy` against the production configuration.
- **Migrations are committed, reviewed and never edited once merged**; CI fails if
  `makemigrations --check` finds model changes without a migration.
- **Keep Django's security machinery on**: CSRF middleware, template auto-escaping,
  parameterized ORM queries, and the password hashers and session settings that
  `check --deploy` expects. Raw SQL and `mark_safe` need a comment saying why.
- **Server-rendered HTML is accessible by default**: templates use semantic elements,
  forms render through Django forms with each field's `<label>` and its errors linked via
  `aria-describedby`, and the WCAG 2.1 AA expectations of the accessibility baseline apply
  to every template, including the admin customizations.
- **WSGI by default.** Serve with a production WSGI server; adopt ASGI only for a concrete
  need (websockets, long-lived streaming) and then for the whole deployment, not per view.

## Alternatives considered

- **Pinning whatever version was current at project creation and never revisiting** —
  zero effort until the security-support window closes, at which point the upgrade spans
  several deprecation cycles at once. A scheduled upgrade is cheaper than a forced one.
- **Fat views and fat templates** — fastest for the first screen, but rules are then only
  testable through the HTTP layer and get duplicated across views; services and model
  methods are testable directly.
- **Per-environment settings files that import each other** (`settings/dev.py`,
  `settings/prod.py`) — familiar, but values drift between files and "works in dev" hides
  production-only configuration. Environment-driven values keep one reviewable file and the
  deploy check exercises the real configuration.
- **ASGI for everything because it is newer** — pays the cost of async discipline (sync
  ORM calls inside async code, thread-hopping) for apps that have no concurrent-IO need.
- **Disabling CSRF or auto-escaping for convenience on internal tools** — rejected;
  internal tools are still reachable by a browser carrying someone's session.

## Consequences

- Upgrades are routine and dated, and the security switches are verified by a gate rather
  than by memory.
- Rules live where they can be unit tested; views stay readable.
- The migration check and `check --deploy` add CI steps and occasionally block a merge on
  a configuration nobody touched on purpose.
- Environment-driven settings need a documented variable list, which must be kept current
  with the code that reads it.
