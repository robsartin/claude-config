# Design: `adr-claude-skill` — composable ADR toolkit as a Claude skill

- **Date:** 2026-07-07
- **Status:** Draft (awaiting approval)
- **Repo:** `adr-claude-skill` (`~/code/adr-claude-skill`)

## Problem

Every new project should start with the same baseline architectural decisions
already recorded as ADRs — TDD, PR workflow, CI gates, licensing, and so on — plus
decisions specific to the project's stack (language, framework, app shape) and to
cross-cutting concerns it opts into (i18n, observability, privacy). Re-litigating
settled conventions on each new repo is wasted work, and hand-copying ADRs is
error-prone (numbering, namespace substitution, keeping an index current).

We want a reusable library of **pre-written, already-decided ADRs**, plus a small
**index**, delivered as a **Claude skill** that scaffolds the right set into a new
repo's `docs/adr/`. A later "start a new project" skill will call this one as a step.

## Goals

- A pre-written ADR library (real "Decision" text, not blank stubs) covering a
  universal baseline plus stack- and concern-specific add-ons.
- Organized so decisions **compose** rather than multiply into per-combination variants.
- Delivered as a Claude skill: `SKILL.md` holds process only; ADR content is data.
- Deterministic emit: renumber into the target repo's existing sequence, keep ADRs
  immutable (supersede, never edit), and generate/update an index.
- Authored only for stacks actually in use (YAGNI); everything else is a deferred
  backlog slot, not speculative content.

## Non-goals

- Not a full project-starter (repo init, build scaffold, CI wiring). That's a future
  skill that *calls* this one. This skill only handles ADRs.
- No WordPress support.
- No authored content for deferred stacks (PHP, Python web frameworks, Vue, Svelte,
  Swift/SwiftUI, published-library shape) until pulled off the backlog.

## The composable-packs model

ADRs are organized as **packs** keyed to independent **axes**. The skill runs a short
interview, resolves which packs apply, and unions them. This avoids the combinatorial
explosion of variant lists (e.g. JVM × Spring × {CLI, service, library} × …).

**Axes:**

1. **Universal** — always applied. Every repo gets these.
2. **Language** — Kotlin/JVM, Java, Python, JS/TS, … (one or more).
3. **Framework** — optional; stacks on a language (Spring Boot, …).
4. **App-shape** — CLI, backend service, web frontend, native UI, library.
5. **Cross-cutting concern** — opt-in: i18n, observability, privacy.

**Pack dependency edges.** A pack can depend on another; selecting it auto-pulls the
dependency. Examples: `react → js-ts`, `compose → jvm`, `spring-boot → jvm`,
`swiftui → swift`. The manifest declares these edges.

**Interaction ADRs.** When two packs combine in a way that forces a decision, that
decision lives in a **pairwise interaction ADR**, emitted only when *both* packs are
selected, and authored only for combinations actually in use. This is where
"it depends on the host" content lives, instead of polluting either single pack.
Examples:

- `d3 + react` (React owns the DOM, D3 owns the math — no `d3.select` on
  React-managed nodes) vs. `d3 + plain` (D3 owns the DOM via enter/update/exit).
- `a11y + react`, `a11y + compose`.
- `i18n + {jvm, js-ts, python}`, `observability + {spring-boot, js-ts}`.

**Accessibility is not a toggle.** It is mandatory whenever a UI-bearing app-shape
(`web-frontend`, `native-ui`) is selected, so it is bundled with those app-shape packs
(base ADR auto-included) plus a tech-specific interaction ADR. It is *not* on the
opt-in concerns axis.

**Coverage thresholds are policy, not tooling.** The threshold values
(**line > 80% / branch > 65%**) live in the Universal CI-gate ADR so they are
consistent across every project. Each language pack only supplies the *measurement
tool* (JaCoCo / coverage.py / c8 / …) and any justified exclusions, and may **tighten
but never loosen** the thresholds.

## Skill architecture

The repo **is** the skill package. Content and process are separated so `SKILL.md`
stays lean (progressive disclosure — orchestration up top, ADR detail loaded on demand).

```
adr-claude-skill/                 (repo == skill)
  SKILL.md                        process only: interview → resolve facets →
                                  select packs → renumber → emit → build index
  packs.yaml                      manifest: packs, axes, dependency edges,
                                  interaction rules, concern toggles
  packs/
    universal/*.md                one ADR template per decision
    lang/{kotlin,java,python,js-ts}/*.md
    framework/{spring-boot}/*.md
    app-shape/{cli,service,web-frontend,native-ui}/*.md
    interaction/{d3-react,d3-plain,a11y-react,a11y-compose,...}/*.md
    concern/{i18n,observability,privacy}/*.md
  scripts/                        emit + renumber + index-build (TDD'd)
  docs/adr/                       the toolkit's OWN ADRs (dogfood)
  docs/design/                    this spec
```

**Templates & tokens.** Pack files are templates with substitution tokens filled at
emit time: `{{project}}`, `{{package}}` (→ `com.robsartin.<project>`), `{{date}}`,
and ADR numbers. Numbering is resolved into the *target repo's* existing sequence
(append-only; immutable ADRs are superseded, never renumbered). A scaffold/emit script
performs the renumber + index build deterministically rather than freehand.

**Manifest (`packs.yaml`).** Machine-readable declaration the skill reads to drive the
interview and selection: each pack's axis, its dependency edges, interaction rules
(pack-pair → interaction ADR), and which concerns are opt-in toggles. The conversational
model we designed must exist here as data.

## ADR catalog

Scope markers: `[now]` author real content · `[defer]` slot + backlog issue (filed as
GitHub issue with the `notready` label).

### Universal (every project) — `[now]`

- `U1` ADR process (numbered, immutable, supersede-don't-edit) — the repo's `0001`
- `U2` Test-Driven Development (red → green → refactor)
- `U3` PR-based trunk workflow (issue → branch → commits → PR → squash to `main`;
  never commit direct to main; no new dev on an open non-draft PR)
- `U4` Mikado method (refactoring, bug fixes, new work where feasible; green build every step)
- `U5` CI merge gate (format + all tests pass; **coverage line > 80% / branch > 65%**)
- `U6` Docs kept current (developer *and* user docs)
- `U7` Licensing & copyright (explicit license per repo)
- `U8` Security baseline — secrets never in repo, secret management, dependency-update
  automation (**mandatory**)

### Language packs — build, formatter/linter, coverage tool, test framework, conventions

- `L1` Kotlin/JVM `[now]` — Gradle, ktlint/Spotless, JaCoCo, ArchUnit/Konsist,
  Testcontainers, package/group `com.robsartin.<project>`
- `L2` Java `[now]` — Gradle, Spotless, JaCoCo, ArchUnit
- `L3` Python `[now]` — ruff, pytest, coverage.py, mypy (as a CLI/service language)
- `L5` JS/TS `[now]` — eslint/prettier, vitest, c8, tsconfig strictness

### Framework packs (stack on a language)

- `F1` Spring Boot `[now]` — DI conventions, config-properties, profiles,
  `@SpringBootTest` slicing, actuator

### App-shape packs

- `S1` CLI `[now]`
- `S2` Backend service `[now]`
- `S3` Web frontend `[now]` — auto-includes accessibility base
- `S4` Native UI `[now, ordered last]` — auto-includes accessibility base (via Compose)

### UI-tech packs (under web-frontend / native-ui)

- `T1` React `[now]` (→ JS/TS)
- `T2` Vanilla/plain JS `[now]`
- `T6` Compose (JVM) `[now, ordered last]` (→ JVM)

### Library packs

- `B1` D3 base — host-agnostic (why D3, responsive sizing, chart accessibility) `[now]`

### Cross-cutting concern packs (opt-in)

- `C1` i18n — base: ICU MessageFormat, locale negotiation, pluralization, RTL,
  locale-aware formatting `[now]`
- `C2` Observability — logging / metrics / tracing conventions `[now]`
- `C3` Privacy / data handling — PII, retention (flexible) `[now]`

### Interaction ADRs (emit only when both packs selected)

- `X1` d3 + react `[now]` · `X2` d3 + plain `[now]`
- `X3` a11y + react `[now]` · `X-compose` a11y + compose `[now, ordered last]`
- `X5` i18n + {jvm, js-ts, python} `[now]`
- `X6` observability + {spring-boot, js-ts} `[now]`

### Deferred — backlog slots, authored later (GitHub issues with `notready`)

- PHP language + Laravel/Symfony framework
- Python web/UI framework (Django / FastAPI / Flask)
- Vue pack (+ d3-vue, a11y-vue, i18n-vue)
- Svelte pack
- Swift language + SwiftUI (+ a11y-swiftui)
- Library / published-artifact app-shape (SemVer, API-stability, publishing target)

## Build order

Dependency-driven; each phase is its own issue → branch → PR. Universal is front-loaded
so the toolkit can dogfood its own ADRs.

- **Phase 0 — Foundation:** repo scaffold, this spec, toolkit's own `docs/adr/0001`
  (ADR process). `[I1, U1]`
- **Phase 1 — Engine:** `packs.yaml` schema, template/token conventions, emit + renumber
  + index scripts — TDD against a tiny fixture pack. `[I2–I6]`
- **Phase 2 — Universal pack:** `U2–U8`; dogfood into the toolkit. `[U2–U8, I7]`
- **Phase 3 — Languages:** Kotlin, Java, Python, JS/TS. `[L1–L3, L5]`
- **Phase 4 — Framework:** Spring Boot. `[F1]`
- **Phase 5 — App-shapes:** CLI, service, web-frontend. `[S1, S2, S3]`
- **Phase 6 — UI + viz:** React, plain-JS, D3 base + interactions (d3+react, d3+plain,
  a11y+react). `[T1, T2, B1, X1–X3]`
- **Phase 7 — Concerns:** i18n (base + i18n×{jvm, js-ts, python}), observability
  (base + obs×{spring-boot, js-ts}), privacy. `[C1–C3, X5, X6]`
- **Phase 8 — Native UI (last):** native-ui shape, Compose, a11y+compose.
  `[S4, T6, X-compose]`
- **Backlog:** PHP, Python backend, Vue, Svelte, Swift/SwiftUI, Library — filed as
  `notready` issues, not authored.

## Success criteria

- Running the skill against a fresh repo produces a correct, sequentially-numbered
  `docs/adr/` set for the interviewed stack, with tokens substituted and an index built.
- Adding a new pack means adding one file + one manifest entry — no edits to existing
  packs or to `SKILL.md`.
- A new stack combination that forces a decision is expressible as one interaction ADR,
  not a new variant of an existing pack.
- The toolkit dogfoods: `adr-claude-skill`'s own `docs/adr/` is generated from its
  Universal pack.

## Open questions

- None blocking. Deferred stacks are captured as backlog and will be brainstormed when pulled.
