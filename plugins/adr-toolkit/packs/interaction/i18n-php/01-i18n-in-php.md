---
status: Accepted
date: "{{date}}"
topic: i18n-in-php
tags: [interaction, i18n, php]
supersedes: []
related: [internationalization-baseline, php-project-layout]
---
# {{number}}. Internationalization in PHP

## Context

The internationalization baseline needs concrete PHP tooling. PHP ships the `intl` extension,
whose `MessageFormatter` and `NumberFormatter` implement ICU, while the common framework
translators differ in how much of ICU they expose. Selecting both i18n and PHP settles the
approach.

## Decision

- **Messages** use **ICU MessageFormat** through the `intl` extension's `MessageFormatter`,
  so plural and select semantics match the baseline. Frameworks that support ICU natively
  use it (see the framework pack); otherwise a thin, injected message-formatting service
  wraps `MessageFormatter` rather than relying on pipe-delimited plural strings.
- **Formatting** of dates, numbers and currency uses `IntlDateFormatter` and
  `NumberFormatter` with an explicit locale, never `date()` or `number_format()` for
  user-visible output.
- **Extension requirement**: `ext-intl` is declared in `composer.json` and present in CI and
  production images; polyfills are not used for non-English locales.
- **Locale resolution** is request-scoped and centralized (framework middleware or event
  listener), never read from a global set once at startup. Text handling uses `mb_*`
  functions and UTF-8 throughout.
- **Catalogs** are keyed by message id; CI fails on missing keys for any supported locale.

## Alternatives considered

- **Pipe-delimited plural strings** (`one|many`) — rejected as the sole mechanism because
  they cannot express ICU's select, nested plural and per-locale category rules.
- **`gettext` (`.po`/`.mo`)** — rejected for the same reason as in other languages: its plural
  forms do not cover ICU select syntax, and it adds a system dependency of its own.
- **Polyfills instead of `ext-intl`** — rejected because the common polyfills cover only a
  minimal (English) locale, so other languages would silently format wrongly.
- **Locale in a process-wide global** — rejected; long-running workers and concurrent
  requests would format for the wrong locale.

## Consequences

- ICU plural and select semantics are available in PHP, consistent with the baseline.
- Formatting is locale-correct through `intl` rather than hand-rolled.
- The `intl` extension (and the system ICU library it links) becomes a build and deploy
  requirement to document and keep current.
