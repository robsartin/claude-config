---
name: adr-toolkit
description: Use when starting a new project or adding an ADR baseline to a repo — scaffolds a stack-appropriate docs/adr/ from composable ADR packs (universal baseline plus language/framework/app-shape/concern add-ons). Triggers on "set up ADRs", "scaffold architecture decisions", "new project ADRs", "adr baseline".
---

# ADR Toolkit

Emit a stack-appropriate `docs/adr/` set into a repository: a universal baseline of
architecture decisions plus add-on packs for the project's language, framework,
app-shape, and opt-in cross-cutting concerns. Content is data (`packs/` + `packs.yaml`);
this file is the process. Engine details and the manifest schema are in
[README.md](../../README.md).

## Process

### 1. Ensure the engine is available

Once per machine:

```bash
${CLAUDE_PLUGIN_ROOT}/bin/install.sh
```

This creates the venv and installs the package editable, putting the `adr-toolkit` console
script on the venv's PATH. The skill itself is registered by the marketplace plugin
installer, not by this script.

### 2. Interview — resolve which packs apply

Ask the user, one axis at a time. Map each answer to a pack id **that exists in
`packs.yaml`**. The **universal** pack is always included. Only offer packs the manifest
actually defines; if the user names a stack whose pack is not yet authored (see the
deferred/backlog issues), say so plainly and proceed with what exists — do not invent a
pack id.

- **Language(s)** — e.g. Kotlin/JVM, Java, Python, JS/TS.
- **Framework** — optional; e.g. Spring Boot. Pulls in its language automatically.
- **App-shape** — CLI, backend service, web frontend, native UI, library.
- **Cross-cutting concerns** — opt-in: i18n, observability, privacy.

Selecting a pack automatically pulls in its `depends_on` packs, and any interaction ADR
whose two endpoint packs are both selected is emitted — the user does not choose those.

### 3. Confirm the resolved selection

List the pack ids you'll pass and the target repo. Get a nod before writing files.

### 4. Emit

```bash
adr-toolkit \
  --manifest ${CLAUDE_PLUGIN_ROOT}/packs.yaml --packs-dir ${CLAUDE_PLUGIN_ROOT}/packs \
  --target <repo>/docs/adr \
  --project <repo-name> \
  --pack universal [--pack <lang> --pack <shape> ...]
```

`--project` derives `{{package}}` as `com.robsartin.<project>`; `--date` defaults to today.

### 5. Report

Show the emitted `NNNN-*.md` files and the regenerated `docs/adr/README.md`. Remind the
user that ADRs are **immutable** — a later change supersedes an ADR, it does not edit it —
and that re-running the toolkit **appends** after the existing sequence.

Each emitted ADR opens with a YAML frontmatter block (`status`, `date`, `topic`, `tags`,
`supersedes`, `related` — see [README.md](../../README.md)). When a later decision supersedes
one of these, use `adr-supersede` (below) rather than hand-editing; the toolkit never
rewrites an ADR it has already emitted.

## Superseding a decision

When a past decision changes, run the separate `adr-supersede` console script — it
respects ADR immutability: the old ADR's Context/Decision/Alternatives/Consequences text
is never touched, only its frontmatter `status` and link fields.

```bash
adr-supersede --target <repo>/docs/adr --old 0005 --title "Use Bazel instead of Gradle"
```

`--old` takes either the old ADR's 4-digit number or its topic slug. This writes a new,
next-numbered ADR as a **stub** (frontmatter complete, all four sections marked
`_TODO: fill in._`), sets the old ADR's `status` to `Superseded by NNNN`, links the two
via `supersedes`/`superseded-by`/`related`, and rebuilds `README.md`. Then **fill in the
new ADR's Context/Decision/Alternatives/Consequences** by hand before treating it as done.

## Reconciling with an existing `docs/adr`

If the target repo already has ADRs, **do not just emit** — it will duplicate and
sometimes contradict decisions they already made. Reconcile first.

1. **Conflict gate first.** Detect the repo's build tool and base package. If they
   differ from what a selected pack asserts (e.g. Maven vs the JVM pack's Gradle),
   that ADR is a **hard stop** — never emit a contradicting ADR. Escalate to the user.
2. **Read the union of sources**, not just `docs/adr/`: build and enforcement config
   (`pom.xml` / `build.gradle*`, JaCoCo, ArchUnit/Konsist), plus `CONTRIBUTING`/`README`.
   Overlap frequently lives outside the ADR directory, and a single decision of ours may
   be covered by several of theirs.
3. **Get the candidate list** without writing anything:

   ```bash
   adr-toolkit --manifest ${CLAUDE_PLUGIN_ROOT}/packs.yaml --packs-dir ${CLAUDE_PLUGIN_ROOT}/packs \
     --target <repo>/docs/adr --project <name> --pack ... --plan
   ```

4. **Classify each planned topic** against that union:
   - **equivalent** — they decided the same thing → **skip ours** (note any missing sub-clause).
   - **formalize** — the practice is enforced/documented but never recorded as an ADR →
     **emit**, saying it codifies existing practice.
   - **partial** — they touch it; ours adds something material → **flag with the delta**.
   - **conflict** — incompatible → **stop**, human only.
   - **gap** — uncovered → **emit**.
5. **Split what remains by kind:**
   - **documentation-only** (a convention or existing practice) → safe to emit now.
   - **change-bearing** (asserts something the code must satisfy: coverage thresholds,
     JVM/library versions, formatter enforced) → run the **satisfy check** first.
6. **Satisfy check — cheapest first, stop when a level answers:** file/config presence →
   config value parse → **run a command** → code grep → LLM judgment (backstop only).
   If not satisfied, either *adopt-as-is* (lower the ADR to what is true) or *uplift*
   (migrate, verify, then land the config change **and** the ADR on the same branch).
   Prefer the higher JVM/library version when viable; coupled upgrades move together.
7. **Present the plan and get approval before writing anything.**
8. **Emit the approved set**, passing `--exclude <topic>` for every topic that is skipped,
   stopped, or deferred to an uplift. Copy topic names from the `--plan` output — an
   unmatched topic is a hard error (exit 2), never a silent no-op.
9. **Deliver:** one batched PR for the documentation-only ADRs, then **one sequential PR per
   uplift** (migrate → verify → config + ADR), merged one at a time. Never stack PRs; a
   coupled version set is one bundled PR.

**Invariants:** never edit their ADRs (skip ours, or add a *superseding* ADR that points at
theirs); never silently drop anything — every skip appears in the report.

Full rationale: [docs/design/2026-07-08-adr-reconciliation-design.md](../../docs/design/2026-07-08-adr-reconciliation-design.md).

## Writing a repo's own ADRs

Packs give a repo its baseline. The decisions that make it *this* repo — engine
choice, data model, core domain invariants — are hand-authored, and they take the
`project` axis:

```yaml
tags: [project, <theme>, ...]
```

`build_index` renders those under a **Project** heading first, above `Universal`,
so a repo's own decisions lead its index. Anything with no frontmatter or an
unrecognized axis still lands in `Uncategorized`. Regenerate the index after
adding one; the pack linter never sees these files, so their frontmatter is on you
— match the template shape (`status`, `date`, `topic`, `tags`, `supersedes`,
`related`) so `related:` cross-links resolve.

## Current pack coverage

`packs.yaml` is the source of truth — always check it rather than trusting this list.
Currently authored:

- **universal** (always applied)
- **languages** — jvm (base), kotlin, java, python, js-ts
- **framework** — spring-boot
- **app-shapes** — cli, service, web-frontend, native-ui, accessibility (auto-pulled by UI shapes)
- **ui-tech** — react, plain-js, compose
- **library** — d3
- **concerns** (opt-in) — i18n, observability, privacy
- **interactions** — d3×{react, plain-js}, a11y×{react, compose}, i18n×{jvm, js-ts, python},
  observability×{spring-boot, js-ts}

**Deferred** (see the `notready` backlog issues): PHP + Laravel/Symfony, Python web
framework, Vue, Svelte, Swift/SwiftUI, and the library/published-artifact app-shape. If a
user names one of these, say it's not yet authored and proceed with what exists.

See [`examples/`](../../examples/) for generated ADR sets across representative stacks.
