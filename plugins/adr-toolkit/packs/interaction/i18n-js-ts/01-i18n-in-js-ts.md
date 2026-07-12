---
status: Accepted
date: "{{date}}"
topic: i18n-in-js-ts
tags: [interaction, i18n, js-ts]
supersedes: []
related: [internationalization-baseline, js-ts-project]
---
# {{number}}. Internationalization in JS/TS

## Context

The internationalization baseline needs concrete JS/TS tooling that speaks ICU
MessageFormat and integrates with the frontend. Selecting both i18n and js-ts settles it.

## Decision

- **Messages** use **ICU MessageFormat** via **FormatJS** (`intl-messageformat` /
  `react-intl` where React is used), so plural/select syntax matches the baseline.
- **Formatting** uses the built-in **`Intl`** APIs (`Intl.DateTimeFormat`,
  `Intl.NumberFormat`, `Intl.PluralRules`) with an explicit locale.
- **Message extraction** is automated from source (FormatJS CLI) so catalogs stay in sync
  with code; missing translations fail the build or fall back explicitly.
- **Bundling** loads only the active locale's catalog (code-split) to keep bundles small.

## Alternatives considered

- **i18next** — rejected because its interpolation/plural syntax is its own convention, not
  ICU MessageFormat, breaking consistency with the ICU baseline shared across stacks.
- **Hand-rolled template strings with native `Intl` only, no message-format library** —
  rejected because `Intl` formats values but has no plural/select message syntax of its own.
- **Ship all locale catalogs in the main bundle instead of code-splitting per locale** —
  rejected because it bloats the initial bundle with translations the user will never see.

## Consequences

- ICU semantics work in the browser via FormatJS, consistent with other stacks.
- Native `Intl` keeps formatting correct without heavy dependencies.
- An extraction/translation step is added to the build pipeline.
