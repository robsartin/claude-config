# start-work — provider-aware work-kickoff skill

Date: 2026-07-13
Issue: robsartin/claude-config#16

## Problem

Rob starts pieces of work the same way over and over: turn a request into a tracked item,
cut a correctly-named branch, wire the item to the code, and begin designing. He does this
in **two different worlds**:

- **Personal** — GitHub issues + `gh`, branch `issue#-slug`, PR to `main`, squash-merge.
- **Work** — Jira ticket (source of truth) → GitLab branch/MR keyed to the Jira key.

Today the kickoff is manual (create issue, create branch, …) and world-specific. `start-work`
makes it one intent — "let's start work on X" — that adapts to whichever world the current
repo lives in and drops Rob straight into the `brainstorm → spec → plan` flow.

This spec is **design-only**. Implementation is deferred: the GitHub adapter is buildable now,
but the GitLab/Jira adapter depends on establishing work access (a later phase, §8).

## Decisions (from brainstorming)

- **One skill, pluggable provider adapters** — a single orchestration through a thin
  per-provider seam, not two duplicated skills.
- **Action scope = scaffold + make-linkage-live + kick off planning** (the most hands-off
  option).
- **Provider detection** from the repo's `origin` remote host, with explicit override.
- **Public skill, machine-local private config** — no work URLs/keys/tokens in the public repo.
- **Readiness = a positive `ready` label** on GitHub issues (replaces the old `notready`
  defer-label). Jira readiness is a status/filter.
- **Form:** skill-primary, plus a thin `/start-work` command alias.
- **Access mechanism** (`glab` + a Jira CLI recommended) is a documented dependency set up in
  a later phase — not built here.

## Shape & trigger

A new `claude-config` plugin, `start-work`, shipping:

- `plugins/start-work/skills/start-work/SKILL.md` — the skill (primary). Triggers on kickoff
  intent: "let's start work on PROJ-123", "start work on this issue", "start a branch for …".
- `plugins/start-work/commands/start-work.md` — a thin `/start-work [identifier]` command that
  just invokes the skill with the given identifier.
- `plugins/start-work/.claude-plugin/plugin.json` — manifest (no `version`; `commands` array).

The skill *orchestrates*; it does not do the design work itself — it ends by invoking
`superpowers:brainstorming`.

## Provider detection

Resolve the provider from the current repository's `origin` remote host:

1. host is `github.com` → **GitHub** provider (uses `gh`).
2. host matches an entry in the local config's `gitlabHosts` → **GitLab/Jira** provider
   (uses `glab` + a Jira CLI).
3. no repo, or an unrecognized host → ask the user, honoring an explicit `--provider github|gitlab`
   flag or a per-repo override in config.

Detection is advisory: the user can always override. The skill states which provider it
detected before taking any action.

## Public skill, private config (the hard constraint)

All skill/adapter logic is public in `claude-config`. Everything work-specific lives in a
**machine-local, non-repo** config file, `~/.claude/start-work.json` (or
`${CLAUDE_CONFIG_DIR}/start-work.json`):

```jsonc
{
  "gitlabHosts": ["gitlab.example-corp.com"],   // marks a repo as "work"
  "jira": {
    "baseUrl": "https://example-corp.atlassian.net",
    "defaultProject": "PROJ",
    "readyStatus": "Ready for Dev",             // what "ready to be done" means in Jira
    "inProgressStatus": "In Progress"
  },
  "branchTemplate": "{key}-{slug}",             // work; personal default is "{number}-{slug}"
  "repoProjectMap": { "some-repo": "PROJ" },     // optional per-repo Jira project override
  "defaultReviewers": []
}
```

The GitLab/Jira adapter is generic and reads all of this from the config, so **no work host,
project key, URL, or token ever appears in the public repo**. If a work repo is detected and
no config exists, the skill explains what it needs and offers to write a starter config
(never committing it).

Personal/GitHub needs little config: `gh` handles auth; naming is `issue#-slug`.

## The adapter seam

Both providers implement the same small interface so the orchestration is a single code path.
Conceptually (the SKILL.md expresses these as steps, not literal code):

- `resolve_or_create_item(identifier | description) → Item{ id, key, title, url, isNew }`
  Given a Jira key / GitHub issue number / URL, reference it. Given only a description, create
  the item (GitHub issue with `ready`; Jira ticket in `defaultProject`).
- `branch_name(item) → string` — apply the provider's template (`KEY-slug` / `number-slug`),
  slug derived from the title, kebab-cased and length-capped.
- `default_base_branch() → string` — e.g. `main` (GitHub) / the GitLab default branch.
- `start_linkage(item, branch)` — assign the item to the user and move it to the in-progress
  state; **draft MR/PR is deferred** (§ "Linkage timing").

Adapters:
- **GitHubAdapter** (`gh`) — buildable and testable now against Rob's real repos.
- **GitLabJiraAdapter** (`glab` + Jira CLI) — implemented in the access phase (§8). The
  orchestration and a **fake adapter** are testable without it.

## Common orchestration (identical for both providers)

1. **Detect provider** (above); state it.
2. **Resolve the work item** — reference an existing item by identifier, or create one from a
   short description. On GitHub a newly-created, being-worked item gets the `ready` label; on
   Jira it lands in `defaultProject`.
3. **Ensure readiness signal exists** — GitHub: create the `ready` label in the repo if absent
   (`gh label create ready … || true`). Jira: readiness is a status, no label to create.
4. **Create the branch** — `branch_name(item)` off `default_base_branch()`, isolated via a
   git worktree (per the `superpowers:using-git-worktrees` skill) if desired.
5. **Make linkage live** — assign to the user, move the item to *In Progress*.
6. **Set up the workspace** — a scratch/ledger note recording item + branch (mirrors the SDD
   `.superpowers/` scratch pattern).
7. **Hand off** — invoke `superpowers:brainstorming` by default. If the item is already a
   crisp, fully-specified task, offer to jump straight to `superpowers:writing-plans` instead.

## Linkage timing (the one nuance)

A **draft MR/PR requires at least one commit** (a branch with no diff against base can't open a
meaningful PR on GitHub, and an empty MR is awkward on GitLab). So at kickoff, "make linkage
live" does only **assign + status → In Progress**. The draft MR/PR is opened on the **first
push** — either the skill offers to open it then, or it is left to the existing PR step in
Rob's issue→branch→PR→squash workflow. The spec does not force an empty PR at time zero.

## Readiness convention (`ready` label)

Replaces the retired `notready` defer-label. An issue is actionable only when labeled `ready`;
unlabeled issues are parked backlog ideas. `start-work`:

- creates the `ready` label per-repo if missing (idempotent),
- applies `ready` to issues it creates for immediate work,
- when the user asks to pick up existing work, prefers `ready`-labeled issues
  (`gh issue list --label ready`).

Jira has no label for this; readiness maps to `jira.readyStatus` in config. Legacy repos still
carrying `notready` are not auto-migrated by this skill.

## Error handling / edge cases

- **Required CLI missing** (`gh`, or `glab`/Jira CLI for work) → stop with a clear message
  naming the tool and how to install/auth it; take no partial action.
- **Work repo, no config** → explain and offer to scaffold `~/.claude/start-work.json`; do not
  proceed with guessed values.
- **Ambiguous/no remote** → ask for the provider rather than guessing.
- **Item already In Progress / branch already exists** → detect and continue idempotently
  (reuse the branch, note the state) rather than erroring.
- **Never write secrets to the repo** — the skill refuses to place any work host/key/token in a
  tracked file.

## Testing strategy

- **GitHubAdapter**: exercised now against Rob's real GitHub repos (create/reference issue,
  branch, assign, `ready` label) on this machine.
- **Orchestration**: unit-testable against a **fake adapter** implementing the seam, with no
  network — verifies detection, branch naming, the ready-label logic, and the brainstorming
  hand-off.
- **GitLabJiraAdapter**: tested in the access phase (§8) on the work laptop.

## §8 — Access dependency (documented, NOT built here)

Building the GitLab/Jira adapter requires Claude to reach Jira + GitLab on the work machine.
Recommended (mirrors how `gh` is used today): **`glab`** (official GitLab CLI) + a **Jira CLI**
(`ankitpokhrel/jira-cli` or Atlassian `acli`), each authed once per machine. Alternatives, to be
weighed against work IT policy: an Atlassian/GitLab **MCP** server, or **REST APIs + PATs**
(most plumbing, careful secret handling). Choosing and setting this up is a **separate later
phase** — this spec only fixes the adapter interface it must satisfy.

## Scope

**In:** the skill/plugin structure, provider detection, the config schema, the adapter
interface, the common orchestration, and the GitHub adapter design.
**Out:** wiring work access (§8, later phase); the brainstorming/design itself (handed off);
migrating legacy `notready` labels; non-git providers.

## Workflow

Issue #16 → branch `16-start-work-spec` → this spec commit → PR to `main`. Implementation
(GitHub adapter first, then the work adapter after §8) is deferred to later plan/build cycles.
