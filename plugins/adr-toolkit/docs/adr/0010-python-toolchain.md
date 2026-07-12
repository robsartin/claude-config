# 10. Standardize the Python quality toolchain

- **Date:** 2026-07-07
- **Status:** Accepted

## Context

The universal CI-gate decision requires formatting, tests, and coverage thresholds to be
enforced, but leaves the *tools* to each language. Python needs a concrete, consistent
toolchain so the gate is measurable and every repo checks the same things the same way.

## Decision

Python projects use this toolchain, all configured in `pyproject.toml` and run in CI:

- **Ruff** for both linting and formatting (`ruff check`, `ruff format`) — one tool, no
  separate Black/isort/flake8.
- **pytest** as the test runner, with tests under `tests/` and `pythonpath = ["src"]`.
- **coverage.py** measures the universal thresholds — **line > 80%, branch > 65%** — with
  `branch = true` and `fail_under` set. A project may tighten these but never loosen them.
- **mypy** for static type checking; new code is typed.

## Consequences

- The universal coverage gate is concrete and enforced for Python via coverage.py.
- One formatter/linter (Ruff) keeps configuration and CI simple and fast.
- Typing and coverage add up-front effort that buys earlier error detection and safer
  refactoring; legacy code is typed as it is touched rather than all at once.
