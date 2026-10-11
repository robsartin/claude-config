---
status: Accepted
date: "{{date}}"
topic: flask-conventions
tags: [framework, flask]
supersedes: []
related: [python-project-layout, security-baseline, flask-testing-and-operability, accessibility-baseline, observability-in-python]
---
# {{number}}. Flask conventions

## Context

Flask is a deliberately small WSGI framework: routing, request handling, templates through
Jinja, and little else. Everything else (persistence, forms, auth, CSRF protection) is a
choice, and Flask will not stop a project making each choice differently, or making it
implicitly through a module-level `app` object that every file imports. The freedom is the
reason to pick it, so the conventions below fix the few things that must not vary.

## Decision

- **Application factory.** A `create_app(config)` function builds the app; there is no
  global application instance. Extensions are created unbound and initialized inside the
  factory.
- **Blueprints per bounded concern**, registered in the factory, each with its own routes
  and tests. Business rules live in plain functions outside the route handlers.
- **Configuration from the environment**, loaded in the factory; the secret key has no
  default, and debug mode is never enabled outside local development.
- **Choose the extras deliberately and record them**: one persistence layer, one form and
  CSRF approach, one auth approach. CSRF protection is on for every state-changing
  browser route.
- **Server-rendered HTML is accessible**: Jinja templates use semantic elements, every
  input has a label, errors are linked with `aria-describedby`, and the accessibility
  baseline (WCAG 2.1 AA) applies. Jinja auto-escaping stays on; `|safe` needs a comment.
- **Never serve with the built-in development server.** Production runs under a WSGI
  server; the number of workers is a deployment setting.

## Alternatives considered

- **A module-level `app = Flask(__name__)`** — fine for a tutorial, but it makes
  configuration a global, forces circular imports as the app grows, and prevents building
  two differently configured apps in one test run.
- **One flat module of routes** — quick, and then every feature edits the same file;
  blueprints give ownership boundaries and per-concern tests.
- **Adopting Django instead, to get the extras bundled** — a legitimate choice with its own
  pack; Flask is chosen when the app is small or the team wants to pick its own components.
- **Leaving CSRF to each developer** — a protection that depends on every author
  remembering it is eventually missing from one form.
- **`flask run` in production** — convenient and documented as development-only; it is not
  built for concurrency or hardening.

## Consequences

- The app is constructed the same way in production, in tests and in tooling.
- Boundaries between features are visible in the file layout.
- Flask's freedom is spent consciously, at the cost of writing down choices the other
  frameworks make for you.
