# Design: reconciling the toolkit against repos that already have ADRs

- **Date:** 2026-07-08
- **Status:** Draft (design captured)
- **Issue:** #41 (deferred / `notready`)

## Problem

The toolkit appends safely to a repo that already has ADRs (it numbers past the highest
existing file — no clobber). But the repo probably already records some of the same
decisions in different words, so a naïve append produces **duplicate and sometimes
conflicting** ADRs. The feature is **reconciliation**: emit only what adds value, and never
contradict what's there.

## Spike (evidence base)

Three of Rob's real repos were classified against the 16 standard decisions the skill
would emit for a JVM/Spring service (universal + jvm + language + spring-boot + service +
observability). Each standard decision was labelled **equivalent** (skip) / **partial**
(flag) / **conflict** (stop) / **gap** (emit).

| Repo | Stack | E | P | C | G |
|---|---|:--:|:--:|:--:|:--:|
| keystone | Java 25 / Maven / Spring Boot | 2 | 8 | 1 | 5 |
| majordomo | Java 25 / Maven / Spring Boot | 3 | 9 | 1 | 3 |
| mise | Kotlin / Gradle / Spring Boot | 1 | 5 | 0 | 10 |

Key findings:

1. **Classification is not static.** The same decision landed differently across repos
   (the PR-workflow decision was equivalent, partial, *and* gap). → Classification must be
   **per-repo and dynamic**, not a hardcoded skip list.
2. **Match against the UNION of sources.** Overlap frequently lived across several ADRs, or
   in enforcement config (JaCoCo, ArchUnit), or in CONTRIBUTING/README — not one ADR. →
   The reconciler must read `docs/adr` **plus** build/enforcement config **plus**
   CONTRIBUTING/README, or it wrongly emits duplicates.
3. **A fifth outcome: FORMALIZE.** A practice enforced/documented but never recorded as an
   ADR (coverage gate in config, ADR convention in README). Neither skip, conflict, nor
   plain gap — our value is codifying it into an actual ADR.
4. **Conflict is predictable: build tool + base package.** Both Maven repos conflicted with
   our Gradle/`com.robsartin.*` standard; the Gradle repo did not. → Detect build tool and
   namespace first; a mismatch is a hard stop.
5. **"Equivalent-minus-a-clause" must not silently skip** — e.g. a trunk-workflow ADR that
   lacks our "no dev on an open ready PR" rule, or a coverage gate missing the *branch*
   threshold. Surface the delta.

## Design decisions

### Classification → resolution (five outcomes)

Per-repo, presented as a **plan the user approves before anything is written**:

- **gap → emit** (auto; the clear value-adds)
- **formalize → emit a "codifies existing practice" ADR** (auto, low-risk)
- **partial / equivalent-with-delta → flag with the specific delta** (human decides)
- **equivalent → skip**, noting any missing sub-clause
- **conflict → hard stop, human only**

Invariants: **never edit their files** (only skip ours, or add a *superseding* ADR that
points at theirs); **detect build-tool + base package up front** as the conflict gate.

### Documentation-only vs change-bearing ADRs

An emitted ADR is a *claim about the code*. Candidates split in two:

- **Documentation-only** — records a convention/existing practice (Mikado, PR-workflow,
  license, "we use ADRs", all FORMALIZE cases). Emitting changes no code → safe to land
  immediately, batched.
- **Change-bearing** — asserts something the code must satisfy (coverage `branch>65%`, JVM
  release, Spotless-enforced, constructor-injection-only). Emitting before the code
  satisfies it makes the ADR false.

For each **change-bearing** candidate the reconciler runs a **satisfy check** ("does the
repo already meet this?"), giving three sub-paths:

1. **Already satisfied** → emit now (documents reality).
2. **Not satisfied, adopt-as-is** → lower the ADR to what's true (their version / their
   number), emit that.
3. **Not satisfied, uplift** → do the migration on a branch, **verify it passes, then land
   the config change and the ADR together on that same branch** (the ADR becomes true in
   the same commit that makes it true — also satisfies our own "docs current in same PR").

### Version uplifts — JVM release and library versions

**Prefer the higher version when viable** — for the JVM release (newer over older, including
non-LTS when it is the higher viable target) and, by the same rule, for **library /
dependency versions**. All are *uplifts*: never assert a version the code doesn't yet
build and pass on — migrate + verify first, then the version ADR lands on that branch.

**Some version uplifts must be handled together.** Library versions are frequently coupled —
a framework BOM bump drags its ecosystem, or library A requires library B ≥ X. Coupled
upgrades cannot be split into separate sequential PRs; they are **one coordinated uplift
work item** (one branch, one atomic PR: the coupled version set + verification + the ADR).
"Viable" for the higher-version rule therefore means *the whole coupled set upgrades and the
build stays green together* — a single library that can't move yet can block or re-scope the
bundle.

Until an uplift is done: flag-and-leave, or record the versions actually running and
supersede later.

### Coverage (D5 / D10)

If ours is stricter than the repo's (e.g. keystone: line 0.85, **no** branch gate;
majordomo: no gate), run the satisfy check against the *current code*. If it already clears
our bar → raise gate + ADR together. If not → either lower our number to what passes, or
branch to add the tests, prove green, then raise the gate + ADR in that branch. Override
theirs only once we actually meet it. (D13 itself is the test-slice *convention* —
documentation-only.)

### Delivery — no stacked PRs

Each uplift is `(migrate → verify → config + ADR)` as one atomic branch — where a coupled
version set is *one* such branch (bundled, not split). Stacking is rejected: squash-merge
rewrites the base SHA (forcing restacks) and "no new dev on an open ready PR" blocks building
on a PR under review. **Two lanes instead:**

1. **One batched PR** for all documentation-only ADRs (gap + formalize + adopt-as-is).
2. **A sequence of single-change PRs** for the uplifts — each merged one-at-a-time through
   CI, ordered by dependency. A single uplift may *bundle* a coupled set of version changes
   (atomic), but uplift work items are never *stacked* on each other.

Optional hybrid for authoring latency: pre-author uplift branches locally, but still merge
sequentially and rebase the remainder after each merge — no live stack for reviewers.

### Architecture

The engine stays **deterministic**: emit, the doc-only batch, per-ADR **topic ids** (stable
handles independent of number), and an **exclude/plan (dry-run)** mode so it can emit
"all-but-these-topics". The **classification, union-matching, doc-only-vs-change-bearing
tagging, satisfy check, and sequencing** live in the Claude / `SKILL.md` layer, executed in
the subagent-driven, issue→branch→PR-through-merge style.

Reconciliation's output is an **ordered execution plan**: the batched doc-only ADR PR, plus
an ordered list of uplift work items (each carrying its migration, verification command,
config change, and ADR).

## Satisfy check (change-bearing decisions)

Not one check — a **cheapest-first ladder**. Most decisions resolve near the top; only the
ones that need it pay for the expensive level.

| Level | Mechanism | Cost | Deterministic |
|:--:|---|---|---|
| 1 | File / config *presence* | instant | yes |
| 2 | Config *value* parse | cheap | yes |
| 3 | **Run a command**, read result | expensive | yes |
| 4 | Code grep heuristic | cheap | mostly (edge cases → L5) |
| 5 | LLM judgment | — | no (backstop only) |

Per change-bearing decision:

| Decision | Level | Concrete check |
|---|:--:|---|
| License present | 1 | `LICENSE` at repo root exists |
| Dependency-update automation | 1 | `.github/dependabot.yml` or `renovate.json` present |
| No secrets in repo | 3 | `gitleaks` / `trufflehog` scan comes back clean |
| Build tool (conflict gate) | 1 | `build.gradle*` vs `pom.xml` → conflict if ≠ ours |
| JVM release | 2 | parse toolchain / `maven.compiler.release`; prefer-higher → uplift if a newer viable release exists |
| Library / dependency versions | 2→3 | parse declared versions; **prefer-higher** → uplift the coupled set, verified green together (L3) |
| Formatter enforced | 1→3 | Spotless/ruff plugin present → run `…Check` to confirm clean |
| Architecture tests (no cycles) | 2 | an ArchUnit/Konsist rule forbidding package cycles exists |
| Coverage gate *configured* | 2 | JaCoCo/c8 config sets line ≥ 80 **and** branch ≥ 65 |
| Coverage — code *actually passes* our bar | **3** | run the coverage task, read the report, compare — the real uplift gate |
| Constructor-injection-only | 4 | grep `@Autowired` on fields/setters = violations |
| Slices over `@SpringBootTest` | 4 | ratio of `@SpringBootTest` to `@WebMvcTest`/`@DataJpaTest` |
| OTel tracing wired | 2 | `opentelemetry` / `micrometer-tracing` in deps + config |

**Two principles:**

1. **Run the ladder cheapest-first; stop when a level answers confidently.** L5 (LLM) is the
   backstop for fuzzy intent and to adjudicate L4 false positives — never the default. This
   keeps reconciliation cheap and reproducible.
2. **The Level-3 (execution) decisions are exactly the uplift decisions** — "does the code
   *pass* our coverage bar?", "does it *build and test* on the newer JVM or coupled library
   set?". You can't answer those from config; you run it. That is why they become their own
   migrate→verify branch: **the satisfy check *is* the verification command** re-run until
   green, and its output (current → target) defines both the migration work and its
   done-condition. The check and the migration gate are the same thing.
