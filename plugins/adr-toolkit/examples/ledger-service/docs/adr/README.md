# Architecture Decision Records

## Universal

- [1. Record architecture decisions with ADRs](0001-record-architecture-decisions.md) — _Accepted_
  Architecturally significant decisions — choices that shape structure, dependencies, interfaces, or the way the team works — need a durable record.
  Related: [6. Keep developer and user documentation current](0006-keep-documentation-current.md)
- [2. Develop with Test-Driven Development](0002-use-test-driven-development.md) — _Accepted_
  We want a fast feedback loop, a regression safety net, executable documentation of behavior, and the freedom to refactor without fear.
- [3. Integrate via a PR-based trunk workflow](0003-pr-based-trunk-workflow.md) — _Accepted_
  We want `main` to stay releasable at all times, changes to be reviewable in coherent units, and history to be legible.
  Related: [4. Use the Mikado Method to keep the build green](0004-mikado-method-for-changes.md), [5. Make CI the merge gate](0005-ci-is-the-merge-gate.md), [6. Keep developer and user documentation current](0006-keep-documentation-current.md)
- [4. Use the Mikado Method to keep the build green](0004-mikado-method-for-changes.md) — _Accepted_
  Large refactorings, and changes that ripple across a codebase, tempt us into long stretches where nothing compiles and nothing is committable.
  Related: [3. Integrate via a PR-based trunk workflow](0003-pr-based-trunk-workflow.md)
- [5. Make CI the merge gate](0005-ci-is-the-merge-gate.md) — _Accepted_
  Standards that are not enforced erode.
  Related: [10. Enforce JVM quality gates and layered tests](0010-jvm-quality-and-tests.md)
- [6. Keep developer and user documentation current](0006-keep-documentation-current.md) — _Accepted_
  Documentation that lags the code is worse than none — it misleads.
  Related: [1. Record architecture decisions with ADRs](0001-record-architecture-decisions.md), [3. Integrate via a PR-based trunk workflow](0003-pr-based-trunk-workflow.md)
- [7. Declare an explicit license and copyright](0007-license-and-copyright.md) — _Accepted_
  A repository with no license is "all rights reserved" by default — others (and future us) have no clear terms for use, and intent is ambiguous.
- [8. Maintain a security baseline](0008-security-baseline.md) — _Accepted_
  Secrets committed to a repository are effectively public and permanent — history preserves them even after deletion.
  Related: [16. Privacy and data handling](0016-privacy-and-data-handling.md), [14. Backend service conventions](0014-service-conventions.md)

## Language

- [9. Build JVM projects with Gradle](0009-jvm-build-with-gradle.md) — _Accepted_
  JVM projects need a consistent build tool, dependency management, and package organization so repositories are predictable to build and navigate, and so shared tooling (formatting, coverage, arch tests) can be applied the same way everywhere.
  Related: [10. Enforce JVM quality gates and layered tests](0010-jvm-quality-and-tests.md), [11. Java language conventions](0011-java-conventions.md)
- [10. Enforce JVM quality gates and layered tests](0010-jvm-quality-and-tests.md) — _Accepted_
  The universal CI-gate decision requires enforced formatting, tests, and coverage, and this project's baseline also calls for architecture tests and real-dependency integration tests.
  Related: [9. Build JVM projects with Gradle](0009-jvm-build-with-gradle.md), [11. Java language conventions](0011-java-conventions.md), [5. Make CI the merge gate](0005-ci-is-the-merge-gate.md)
- [11. Java language conventions](0011-java-conventions.md) — _Accepted_
  Java builds on the shared JVM baseline (Gradle, Spotless, JaCoCo, layered tests) and needs its language level and formatting standard pinned so Java repositories are consistent.
  Related: [9. Build JVM projects with Gradle](0009-jvm-build-with-gradle.md), [10. Enforce JVM quality gates and layered tests](0010-jvm-quality-and-tests.md)

## Framework

- [12. Spring Boot application conventions](0012-spring-boot-conventions.md) — _Accepted_
  Spring Boot offers several ways to do most things — wire dependencies, bind configuration, select environment-specific behavior.
  Related: [9. Build JVM projects with Gradle](0009-jvm-build-with-gradle.md), [10. Enforce JVM quality gates and layered tests](0010-jvm-quality-and-tests.md), [13. Spring Boot testing and operability](0013-spring-boot-testing-and-operability.md)
- [13. Spring Boot testing and operability](0013-spring-boot-testing-and-operability.md) — _Accepted_
  A full `@SpringBootTest` for every test is slow and blunt, and a service that ships without health and metrics endpoints is hard to operate.
  Related: [10. Enforce JVM quality gates and layered tests](0010-jvm-quality-and-tests.md), [12. Spring Boot application conventions](0012-spring-boot-conventions.md), [17. Observability in Spring Boot](0017-observability-in-spring-boot.md)

## App shape

- [14. Backend service conventions](0014-service-conventions.md) — _Accepted_
  A long-running backend service has to be configurable across environments, observable, safely deployable, and evolvable without breaking clients.
  Related: [8. Maintain a security baseline](0008-security-baseline.md), [15. Observability baseline](0015-observability-baseline.md)

## Concern

- [15. Observability baseline](0015-observability-baseline.md) — _Accepted_
  When something goes wrong in production, we need to understand it without redeploying to add print statements.
  Related: [17. Observability in Spring Boot](0017-observability-in-spring-boot.md), [16. Privacy and data handling](0016-privacy-and-data-handling.md)
- [16. Privacy and data handling](0016-privacy-and-data-handling.md) — _Accepted_
  Handling personal data carries legal and ethical obligations, and the cheapest way to reduce risk is to hold less data and handle it deliberately.
  Related: [15. Observability baseline](0015-observability-baseline.md), [8. Maintain a security baseline](0008-security-baseline.md)

## Interaction

- [17. Observability in Spring Boot](0017-observability-in-spring-boot.md) — _Accepted_
  The observability baseline (structured logs, metrics, OpenTelemetry tracing, correlation) needs concrete Spring Boot wiring.
  Related: [15. Observability baseline](0015-observability-baseline.md), [13. Spring Boot testing and operability](0013-spring-boot-testing-and-operability.md)
