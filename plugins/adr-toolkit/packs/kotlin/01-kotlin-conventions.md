---
status: Accepted
date: "{{date}}"
topic: kotlin-conventions
tags: [language, kotlin]
supersedes: []
related: [jvm-build-with-gradle, jvm-quality-and-tests]
---
# {{number}}. Kotlin language conventions

## Context

Kotlin builds on the shared JVM baseline (Gradle, Spotless, JaCoCo, layered tests) but has
its own idioms and a native tooling ecosystem worth pinning so Kotlin repositories are
consistent.

## Decision

On top of the JVM baseline:

- **ktlint** (run through Spotless) provides Kotlin formatting and lint rules.
- **Konsist** is preferred for architecture tests, being Kotlin-native, where the JVM
  baseline's ArchUnit is not already in use.
- Favor Kotlin idioms: immutability by default (`val`), data classes for value types,
  null-safety over platform types at boundaries, and expression-bodied functions where
  they read clearly.
- Libraries intended for external consumption enable **explicit API mode** so the public
  surface is deliberate.

## Alternatives considered

- **detekt instead of ktlint** — offers broader static-analysis rules, but ktlint's narrower
  focus on formatting keeps it aligned with the JVM baseline's single Spotless-driven gate.
- **ArchUnit for architecture tests** — works from the JVM baseline, but Konsist's Kotlin-native
  DSL reads more idiomatically for a Kotlin-only codebase, so it's preferred where available.
- **Mutable defaults (`var`, plain classes)** — familiar from Java, but forgoing `val` and data
  classes would give up the immutability and equality guarantees Kotlin is chosen for.

## Consequences

- Kotlin code reads idiomatically and is formatted consistently via ktlint.
- Architecture rules are expressed in Kotlin (Konsist) rather than a Java-oriented DSL.
- Explicit API mode adds a little ceremony to library code in exchange for a controlled
  public surface.
