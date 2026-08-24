# adr-toolkit

[![CI](https://github.com/robsartin/claude-config/actions/workflows/adr-toolkit.yml/badge.svg)](https://github.com/robsartin/claude-config/actions/workflows/adr-toolkit.yml)

A composable ADR toolkit, delivered as a Claude skill. It emits a
stack-appropriate `docs/adr/` set into a repository: a **universal** baseline of
architecture decisions plus **add-on packs** for the project's language,
framework, app-shape, and opt-in cross-cutting concerns — composed, not copied.

See the design spec: [docs/design/2026-07-07-adr-claude-skill-design.md](docs/design/2026-07-07-adr-claude-skill-design.md).

## Status

- **Phase 0** — ADR-0001 (ADR process) authored. ✅
- **Phase 1** — the engine (this): selection, numbering, templating, emit,
  index, CLI. ✅
- **Phases 2–8** — author the ADR pack content (universal, languages, framework,
  app-shapes, UI/viz, concerns, native UI). In progress via GitHub issues.

## How it works

The engine separates **process** from **content**. Claude (via `SKILL.md`, added
with the pack content) runs the interview and resolves which packs apply; the
Python engine renders the resolved selection into a target repo:

```
resolve_selection  → expand selected packs by their depends_on edges (transitive)
resolve_interactions → add a pairwise interaction ADR only when both packs are selected
order_packs        → order by axis (universal → language → framework → app-shape → …)
emit               → render {{token}} templates, number sequentially, write docs/adr/NNNN-*.md
build_index        → (re)generate docs/adr/README.md, grouped by axis (project first) with status/summary/related
```

`scaffold()` composes these; `cli.main()` / the `adr-toolkit` console script is
the entry point.

### CLI

```bash
adr-toolkit \
  --manifest packs.yaml --packs-dir packs \
  --target /path/to/repo/docs/adr \
  --project mise \
  --pack universal --pack kotlin --pack cli
```

`--project` derives `{{package}}` as `com.robsartin.<project>`; `--date` defaults
to today. ADRs are appended after any existing ones (numbers are immutable).

Two flags support reconciling against a repo that already has ADRs:

- `--plan` — print the ADRs that *would* be emitted (number, topic, pack) and exit
  without writing anything. Nothing is created, not even the target directory.
- `--exclude TOPIC` — skip an ADR by its stable **topic** (the filename slug, e.g.
  `use-test-driven-development`). Repeatable. Excluded topics consume no number, so the
  emitted sequence stays contiguous. A topic that matches nothing is an **error** (exit 2,
  message on stderr, nothing written) — a typo must never silently emit an ADR you meant
  to skip.

```bash
adr-toolkit --manifest packs.yaml --packs-dir packs \
  --target /path/to/repo/docs/adr --project mise \
  --pack universal --pack kotlin --exclude use-test-driven-development --plan
```

### `adr-supersede`

A separate console script for the supersede workflow: when a past decision changes,
it writes a new ADR and flips the old one's status pointer, without touching the old
ADR's Context/Decision/Alternatives/Consequences text (ADRs are immutable history —
only the frontmatter status/link fields change).

```bash
adr-supersede --target /path/to/repo/docs/adr \
  --old 0005 --title "Use Bazel instead of Gradle"
```

`--old` accepts either the old ADR's 4-digit number (`0005`) or its stable topic
slug (`use-gradle`). `--date` defaults to today. On success it writes a new,
next-numbered ADR as a stub (frontmatter filled in, all four sections
`_TODO: fill in._`) with `supersedes`/`related` pointing at the old ADR, sets the old
ADR's `status` to `Superseded by NNNN`, adds `superseded-by`, appends the new topic
to the old ADR's `related`, and rebuilds `README.md`. An `--old` that matches zero or
more than one ADR is an error (exit 2, nothing written).

## Manifest schema (`packs.yaml`)

```yaml
packs:
  <pack-id>:
    axis: universal | language | framework | app-shape | ui-tech | library | concern | interaction
    path: <dir under packs/ holding this pack's ADR templates>   # one *.md per ADR
    depends_on: [<pack-id>, ...]   # optional; selecting this pack pulls these in

interactions:
  - when: [<pack-id>, <pack-id>]   # both must be selected
    adr: <pack-id with axis: interaction>
```

Each pack directory contains one Markdown template per ADR. Templates use
`{{project}}`, `{{package}}`, `{{date}}`, and `{{number}}` (the assigned ADR
number, e.g. `# {{number}}. Title`). An unresolved token is a hard error, so no
placeholder can reach an emitted ADR.

### Template frontmatter

Every template starts with a machine-readable YAML frontmatter block, before the
`# {{number}}. Title` heading:

```yaml
---
status: Accepted
date: "{{date}}"
topic: <slug>
tags: [<axis>, <theme>, ...]
supersedes: []
related: []
---
```

- `status` is always `Accepted` — templates only ever emit accepted decisions.
- `date` is the literal `{{date}}` token, substituted at emit time like any other
  template placeholder.
- `topic` is the stable slug used by `--exclude` (the filename minus its `NN-`
  ordering prefix and `.md`).
- `tags` starts with the pack's axis (`universal`, `language`, `framework`,
  `app-shape`, `ui-tech`, `library`, `concern`, or `interaction`) followed by
  1–2 theme tags.
- `supersedes` and `related` are empty lists in the template; a project may fill
  them in by hand once an ADR is superseded by or related to another.

### Hand-authored ADRs: the `project` axis

Packs emit a *baseline*. The decisions that make a repo what it is — its data
model, its engine choice, its core domain invariants — are written by hand, and
they have no pack axis to claim. Tag them `project`:

```yaml
tags: [project, <theme>, ...]
```

`build_index` renders those under a **Project** heading placed **first**, above
`Universal`, so a repo's own decisions lead its index instead of trailing the
baseline. `Uncategorized` stays the genuine fallback for ADRs with no
frontmatter or an unrecognized axis.

`project` is an index-only axis: no pack declares it, and the pack linter only
walks `packs/`, so hand-authored ADRs are never linted against the pack rules.

## Examples

See [`examples/`](examples/) for generated ADR sets across representative stacks
(Kotlin/Spring service, React web app, Python CLI) — regenerated by
[`bin/gen-examples.sh`](bin/gen-examples.sh) and drift-checked in CI.

## Install

```bash
./bin/install.sh
```

Idempotent — creates the repo venv and does the editable install, putting the
`adr-toolkit` and `adr-supersede` console scripts on the venv's PATH. Re-run any
time; it reuses an existing venv. Skill discovery/registration is handled by
installing this plugin from the claude-config marketplace, not by this script.

## Development

```bash
python3.12 -m venv .venv          # (or just run ./bin/install.sh)
./.venv/bin/pip install -e '.[dev]'
./.venv/bin/pytest              # tests
./.venv/bin/ruff check .        # lint
./.venv/bin/ruff format --check .
./.venv/bin/mypy                # strict type check (src + scripts + tests)
./.venv/bin/coverage run -m pytest && ./.venv/bin/coverage report
```

Coverage gate (U5): line > 80%, branch > 65%. This repo dogfoods its own
standards — pure TDD, Nygard-style ADRs in `docs/adr/`.
