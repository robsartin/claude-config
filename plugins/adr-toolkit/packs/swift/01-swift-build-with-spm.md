---
status: Accepted
date: "{{date}}"
topic: swift-build-with-spm
tags: [language, swift, build]
supersedes: []
related: [swift-quality-and-tests, swiftui-conventions, ci-is-the-merge-gate]
---
# {{number}}. Build Swift with Swift Package Manager

## Context

A Swift project can be driven by an Xcode project file, by a third-party dependency manager,
or by Swift Package Manager. The choice decides what is reviewable in a pull request and
what CI can run without Xcode's UI. Xcode's `.pbxproj` is a generated, densely cross-
referenced file that conflicts badly on merge and cannot be meaningfully reviewed, so making
it the source of truth pushes real decisions somewhere nobody reads.

## Decision

- **Swift Package Manager is the source of truth.** `Package.swift` declares targets,
  products, and dependencies; any Xcode project is generated or opened on top of the
  package, never hand-maintained as the authoritative build.
- **Pin the toolchain** with an explicit `swift-tools-version` and pin dependencies to
  version ranges with `Package.resolved` committed, so builds are reproducible.
- **Modular targets** — split by feature or layer, with test targets alongside. Module
  boundaries are expressed as targets, so a cycle fails the build rather than review.
- **Swift 6 language mode** with **strict concurrency checking** enabled, so data-race
  safety is enforced by the compiler rather than by convention.
- **Resources are declared** (`.process`/`.copy`) in the manifest rather than added through
  Xcode's UI, so they survive a clean checkout.

## Alternatives considered

- **An Xcode project as the source of truth** — the default when you start in the IDE, but
  `.pbxproj` is generated, merge-hostile, and unreviewable, and it ties builds to a machine
  with Xcode rather than to a plain `swift build`.
- **CocoaPods** — long the ecosystem standard and still widely documented, but it needs a
  Ruby toolchain, rewrites the workspace, and is no longer where the ecosystem or Apple's
  own tooling is heading.
- **Carthage** — lighter-touch than CocoaPods and avoids modifying the project, but it
  leaves integration manual and has far less ecosystem support than SPM.
- **Deferring Swift 6 strict concurrency** — less friction on day one, but concurrency
  diagnostics get harder to adopt the more code exists, and the class of bug it prevents is
  exactly the one that is hardest to reproduce.

## Consequences

- The build is declared in a reviewable, diffable Swift file, and `swift build` /
  `swift test` work in CI without driving the IDE.
- Dependency resolution is reproducible across machines and CI.
- Strict concurrency surfaces data-race problems at compile time, at the cost of up-front
  annotation work when adopting or migrating code.
- Some Apple-platform capabilities (app targets, entitlements, UI tests) still need an
  Xcode project layered over the package; that project stays generated, not authoritative.
