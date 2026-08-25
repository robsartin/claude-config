---
status: Accepted
date: "{{date}}"
topic: swift-quality-and-tests
tags: [language, swift, testing]
supersedes: []
related: [swift-build-with-spm, swiftui-conventions, ci-is-the-merge-gate]
---
# {{number}}. Enforce Swift quality gates and layered tests

## Context

The universal CI-gate decision requires enforced formatting, tests, and coverage. Swift
needs concrete tools so those requirements are measurable and uniform, and it has two test
frameworks in active use: XCTest, which every Apple-platform project has used for years, and
Swift Testing, the newer framework integrated with Swift Package Manager. They coexist in
the same test target, so the project has to say which one new tests are written in.

## Decision

Run in CI on every pull request:

- **Formatting** via **swift-format**, failing the build on violations. Linting via
  **SwiftLint** for the rules a formatter cannot express (naming, complexity, force
  unwrapping).
- **Unit tests in Swift Testing** (`@Test`, `#expect`, `#require`) — parameterized cases and
  parallel execution come from the framework rather than from hand-rolled loops.
- **XCTest is retained where it is still required**: `XCUITest` UI automation and
  performance measurement. Existing XCTest suites are not rewritten wholesale; they run
  alongside.
- **Integration tests** that touch real dependencies live in a separate target or are tagged,
  so the fast unit loop stays fast.
- **Coverage** from `swift test --enable-code-coverage`, exported with `llvm-cov` and
  enforced against the universal thresholds — **line > 80%, branch > 65%** — failing the
  build below them. A project may tighten these.
- **No force unwrapping or `try!` in shipped code**, enforced by SwiftLint rather than by
  review.

## Alternatives considered

- **XCTest for new unit tests** — universally known and the safe default, but Swift Testing
  gives parameterized tests, better failure output, and concurrency-aware parallelism
  without the `XCTestCase` subclassing ceremony. XCTest stays for what only it can do.
- **Rewriting existing XCTest suites to Swift Testing in one pass** — rejected because the
  two coexist in one target, so migration can be incremental and does not need to block
  anything.
- **SwiftLint's formatting rules instead of a separate formatter** — one tool fewer, but
  autocorrect for whitespace is not its focus, and swift-format is the toolchain's own
  answer.
- **Coverage measured but unenforced** — visible without blocking anyone, but an unenforced
  number drifts down, which is exactly what the universal gate exists to prevent.

## Consequences

- The universal coverage gate is concrete for Swift, and formatting/lint failures surface
  in CI rather than in review comments.
- New tests get parameterization and clearer failures; legacy XCTest suites keep working, so
  the codebase runs two frameworks during the transition.
- Coverage export needs `llvm-cov` from the toolchain, which is present in Swift CI images
  but is an extra step compared with a single built-in flag.
