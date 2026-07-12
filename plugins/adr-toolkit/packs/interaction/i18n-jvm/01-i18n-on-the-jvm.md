---
status: Accepted
date: "{{date}}"
topic: i18n-on-the-jvm
tags: [interaction, i18n, jvm]
supersedes: []
related: [internationalization-baseline, jvm-build-with-gradle]
---
# {{number}}. Internationalization on the JVM

## Context

The internationalization baseline (ICU MessageFormat, locale-aware formatting, negotiation)
needs concrete JVM tooling. Selecting both i18n and the JVM base settles the mechanics.

## Decision

- **Messages** are stored in resource bundles and rendered with **ICU4J**
  (`com.ibm.icu.text.MessageFormat`) so ICU plural/select syntax works as specified — not
  `java.text.MessageFormat`, which lacks full ICU support.
- **Formatting** uses ICU4J / `java.time` and `NumberFormat` with an explicit `Locale`;
  never format dates or numbers without one.
- **Locale resolution** is centralized (e.g. a request-scoped `LocaleResolver` in a web
  app) rather than reading the locale ad hoc.
- **Catalogs** are keyed by message id; a build check fails on missing keys across locales.

## Alternatives considered

- **`java.text.MessageFormat`** — rejected because it does not implement full ICU
  plural/select/gender syntax, which the i18n baseline requires.
- **Plain `.properties` bundles with manual string concatenation** — rejected because it has
  no plural or select support and pushes formatting logic into ad hoc code.
- **Read `Locale.getDefault()` ad hoc at each call site instead of a centralized
  resolver** — rejected because it invites default-locale bugs in concurrent/request-scoped
  code, which the baseline's explicit-locale rule exists to prevent.

## Consequences

- ICU semantics (plurals, gender, nested selects) work correctly via ICU4J.
- Locale is threaded explicitly, avoiding default-locale bugs.
- ICU4J is an added dependency, accepted for correct i18n behavior.
