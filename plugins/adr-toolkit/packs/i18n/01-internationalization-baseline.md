---
status: Accepted
date: "{{date}}"
topic: internationalization-baseline
tags: [concern, i18n]
supersedes: []
related: [i18n-in-js-ts, i18n-in-python, i18n-on-the-jvm]
---
# {{number}}. Internationalization baseline

## Context

Retrofitting internationalization is expensive: hard-coded strings, concatenated
sentences, and locale-naive formatting are pervasive and tedious to unpick. When a project
will serve more than one language or locale, deciding the approach up front is far cheaper.
This concern is opt-in; the language/framework mechanics live in the relevant interaction
ADR.

## Decision

When a project internationalizes:

- **No user-facing string literals in code** — all copy comes from message catalogs keyed
  by identifier.
- **ICU MessageFormat** is the message syntax, so pluralization, gender, and
  interpolation are handled correctly per locale rather than by string concatenation.
- **Locale-aware formatting** for dates, numbers, and currency via the platform's
  Intl/ICU facilities — never hand-rolled.
- **Locale negotiation** resolves the user's locale from an explicit preference then
  `Accept-Language`, with a defined fallback chain.
- **Right-to-left (RTL)** support is considered from the start (logical CSS properties,
  direction-aware layout) rather than assumed LTR.

## Alternatives considered

- **Flat key/value catalogs with concatenated strings** — simplest to implement, but
  rejected because concatenation breaks pluralization, gender, and word order once more
  than one locale is in play.
- **gettext / PO-based tooling** — a mature, widely-supported format, but rejected in
  favor of ICU MessageFormat's richer native plural and gender rule support across
  today's JS/Java ecosystems.
- **Deferring locale and RTL support until a second language is needed** — cheaper up
  front, but rejected because it recreates the exact retrofitting cost this ADR exists
  to avoid.

## Consequences

- Adding a locale is a matter of providing catalogs, not editing code.
- Plurals and formatting are correct across locales instead of subtly wrong.
- There is up-front discipline (externalising strings, ICU syntax) and a translation
  workflow to maintain.
