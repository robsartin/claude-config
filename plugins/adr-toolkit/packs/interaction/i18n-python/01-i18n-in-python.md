---
status: Accepted
date: "{{date}}"
topic: i18n-in-python
tags: [interaction, i18n, python]
supersedes: []
related: [internationalization-baseline, python-project-layout]
---
# {{number}}. Internationalization in Python

## Context

The internationalization baseline needs concrete Python tooling. Python's traditional
`gettext` does not implement ICU MessageFormat, so the baseline's ICU requirement drives the
choice. Selecting both i18n and Python settles it.

## Decision

- **Messages** use **ICU MessageFormat** via **PyICU** (or `Babel` where its subset
  suffices) so plural/select semantics match the baseline, rather than plain `gettext`
  `.po` strings that can't express ICU rules.
- **Formatting** of dates, numbers, and currency uses **Babel** locale-aware formatters
  with an explicit locale.
- **Catalogs** are extracted with Babel's `pybabel extract`/`update`, keyed by message id;
  CI checks for missing keys.
- **Locale resolution** is centralized (framework middleware or an explicit context), never
  read ad hoc from globals.

## Alternatives considered

- **`gettext` `.po`/`.mo` catalogs** — rejected because `gettext` plural forms can't express
  ICU's plural/select/nested-select syntax the baseline requires.
- **`Babel` message formatting alone, without PyICU** — rejected because Babel's format
  subset doesn't cover full ICU MessageFormat (nested selects, richer plural rules), so
  PyICU is used for messages while Babel remains for locale-aware formatting.
- **Read locale from a thread-local/global set once at startup** — rejected because it
  isn't request-scoped, so concurrent requests could format for the wrong locale.

## Consequences

- ICU plural/select semantics are available in Python via PyICU/Babel.
- Formatting is locale-correct through Babel rather than hand-rolled.
- PyICU depends on the system ICU library, a build/deploy consideration to document.
