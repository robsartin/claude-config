# 9. Structure Python projects with pyproject and a src layout

- **Date:** 2026-07-07
- **Status:** Accepted

## Context

Python offers many ways to lay out and package a project, and inconsistent choices make
repositories harder to move between. We want one predictable structure, isolated
dependencies, and imports that exercise the installed package rather than the working
directory.

## Decision

- **`pyproject.toml`** is the single source of project metadata and tool configuration
  (PEP 621), built with **hatchling**.
- **`src/` layout** — the importable package lives under `src/<package>/`, so tests run
  against the installed package and can't accidentally import from the checkout root.
- **Virtual environment** per project (`python -m venv .venv`); the package is installed
  editable for development (`pip install -e '.[dev]'`).
- **Python version** is pinned with `requires-python` to a currently-supported release
  (>= 3.12 unless the project states otherwise).
- Console entry points are declared under `[project.scripts]`.

## Consequences

- Every Python repo is laid out the same way, so setup and navigation are predictable.
- The src layout catches "works on my machine" import bugs before they ship.
- Contributors must install the package (editable) before imports resolve — a one-time
  step documented in the README.
