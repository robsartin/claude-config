# Work-laptop setup — start-work + worklog GitLab/Jira phase

This runbook is executed **on the work laptop**. It sets up the deferred GitLab/Jira phase of
[`start-work`](../plugins/start-work/skills/start-work/SKILL.md) and
[`worklog`](../plugins/worklog/skills/worklog/SKILL.md): reaching your work Jira + GitLab so
`start-work` can drive the Jira-ticket → GitLab-branch/MR flow, and `worklog` can pull the
factual spine of a report from tickets/MRs.

Design contracts this implements:
- `docs/superpowers/specs/2026-07-13-start-work-design.md` §8 (access dependency) + the adapter interface.
- `docs/superpowers/specs/2026-07-13-worklog-reports-design.md` "Later enhancement — factual pull".

Nothing here contains work hosts, keys, or tokens — those live only in a machine-local config
(step 4), never in this public repo.

## 0. Prerequisites

- Claude Code installed and signed in **on the work laptop** (use the work account; you do not
  need to switch accounts — plugins install per-machine).
- The claude-config plugins installed there:
  ```bash
  claude plugin marketplace add robsartin/claude-config
  bash ~/.claude/plugins/marketplaces/claude-config/bin/bootstrap.sh
  ```
- `python3` available (the `start-work`/`worklog` helpers need it; already required by bootstrap).
- Your Obsidian vault present (default `~/Obsidian`) if you want `worklog` to write there.

## 1. Choose the access mechanism

`start-work`/`worklog` shell out to CLIs the same way they use `gh` today. **Recommended:
`glab` (GitLab CLI) + a Jira CLI**, each authed once. This mirrors the existing `gh` pattern and
keeps secrets in the tools' own credential stores.

| Mechanism | Pros | Cons | When |
| --- | --- | --- | --- |
| **`glab` + Jira CLI** (recommended) | Mirrors `gh`; auth handled by the tools; scriptable | Two tools to install/auth | Default, if IT allows CLI installs + personal access tokens |
| Atlassian/GitLab **MCP** | Rich, structured; no shelling out | Depends on the servers being available + approved in your org; setup varies | If your org already runs approved MCP servers |
| **REST + PAT** | No extra tools | Most plumbing; you handle tokens/secrets carefully | Fallback if CLIs are blocked |

**Decision points gated by your work IT policy** — confirm before proceeding:
- Are third-party CLIs (`glab`, a Jira CLI) allowed to be installed?
- Are **personal access tokens** permitted for GitLab and Jira? (Some orgs restrict PAT scopes or require SSO-linked tokens.)
- Is there an approved MCP option you should prefer instead?

The rest of this runbook assumes the recommended CLI path. If your org pushes you to MCP or REST,
the adapter interface (step 5) is the same; only the adapter's implementation of each operation
changes.

## 2. Install the CLIs

GitLab CLI (`glab`):
```bash
# macOS
brew install glab
# or see https://gitlab.com/gitlab-org/cli for other installers
glab version
```

A Jira CLI — recommended `jira-cli` (`ankitpokhrel/jira-cli`), or Atlassian's `acli`:
```bash
# macOS
brew install jira-cli
jira version
```

## 3. Authenticate

GitLab (self-managed host → use your work host):
```bash
glab auth login --hostname <your-gitlab-host>     # e.g. gitlab.example-corp.com
glab api /version                                 # verify: prints the GitLab version
```

Jira (interactive init; auth with an API token / PAT per your org):
```bash
jira init            # choose Jira type (Cloud/Server), enter base URL + email + API token
jira me              # verify: prints your account
```

Store tokens only where the tools keep them (keychain / their config), never in this repo.

## 4. Write the machine-local config

`start-work`/`worklog` read `${CLAUDE_CONFIG_DIR:-$HOME/.claude}/start-work.json`. Create it on
the work laptop (fill the placeholders with your real values):

```bash
cat > ~/.claude/start-work.json <<'JSON'
{
  "gitlabHosts": ["<your-gitlab-host>"],
  "jira": {
    "baseUrl": "https://<your-org>.atlassian.net",
    "defaultProject": "<PROJ>",
    "readyStatus": "<the status that means ready-for-dev>",
    "inProgressStatus": "In Progress"
  },
  "branchTemplate": "{key}-{slug}",
  "repoProjectMap": {},
  "worklog": {
    "vaultPath": "~/Obsidian",
    "worklogFile": "Worklog.md",
    "reportsDir": "Reports"
  }
}
JSON
```

This file is **machine-local and private** — it is intentionally not tracked in the repo, and it
must never be committed anywhere public. `gitlabHosts` is what flips `start-work`'s provider
detection from GitHub to GitLab when you're in a work repo.

## 5. Build + validate the GitLab/Jira adapter (a build session on the work laptop)

With access working, do this as its own build (issue → branch → PR in `claude-config`, per the
usual flow — and flip issues #16/#18 back to `ready` first). The interface is already fixed by
the start-work spec; implement it for GitLab/Jira behind the same seam the GitHub adapter uses:

- `resolve_or_create_item(identifier | description)` — reference a Jira key (`glab`/`jira` view)
  or create a ticket in `defaultProject`.
- `branch_name(item)` — `{key}-{slug}` (the existing `branch-name` helper already does this shape;
  the Jira key is the ref).
- `start_linkage(item, branch)` — assign the ticket, transition it to `inProgressStatus`; the
  draft MR is opened on first push (same deferral as GitHub).
- `default_base_branch()` — the GitLab project's default branch.

Then extend `worklog`'s report skills with the **factual pull**: for a date range, query Jira
(tickets moved/closed) and GitLab (MRs merged) and merge that authoritative spine with the
hand-logged `Worklog.md` notes.

**Build the adapter against real responses, not assumptions** — capture actual `glab`/`jira`
command output first (field names, transition names, JSON shapes vary by instance), unit-test the
pure bits with fakes, then **live-validate** end to end:
1. `/start-work <JIRA-KEY>` on a throwaway ticket → confirm the GitLab branch `{KEY}-{slug}` is
   created and the ticket moved to In Progress.
2. Confirm a `worklog` "started" entry landed in `Worklog.md`.
3. `/weekly-report` over the range → confirm the Jira/GitLab pull augments the notes.

## 6. Housekeeping

- Re-label #16 and #18 from `blocked` back to `ready` while you're actively on this phase, and
  close them (or spin child build issues) as the adapter lands.
- Keep every work-specific value in `~/.claude/start-work.json` only. If you ever need to share
  the setup, share this runbook — not your filled-in config.
