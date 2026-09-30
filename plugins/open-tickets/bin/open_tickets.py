#!/usr/bin/env python3
"""open-tickets: fetch your open Jira issues (with description + recent comments),
plus open issues from your personal GitLab tracker and the MRs you are reviewing,
so a blocker/next-step table can be drafted from them. Stdlib only."""
import base64
import json
import os
import re
import sys
import urllib.parse
import urllib.request

JIRA_CLI_CONFIG = "~/.config/.jira/.config.yml"
MAX_COMMENTS = 8


def read_jira_cli_config(path=JIRA_CLI_CONFIG):
    """Pull `server` and `login` out of the jira CLI's own config. Machine-local by
    design — the host and account never live in this repo. Returns {} if unreadable."""
    p = os.path.expanduser(path)
    if not os.path.exists(p):
        return {}
    out = {}
    with open(p) as f:
        for line in f:
            m = re.match(r"^(server|login):\s*(\S+)\s*$", line)
            if m:
                out[m.group(1)] = m.group(2)
    return out


def jira_search(server, login, token, jql, fields, max_results=100):
    """Cross-project JQL search against Jira Cloud. The `jira` CLI can't do this —
    its --jql runs "in a given project context", so it silently returns nothing for
    work outside the configured default project. Returns the raw response dict."""
    qs = urllib.parse.urlencode({"jql": jql, "fields": fields, "maxResults": max_results})
    url = f"{server.rstrip('/')}/rest/api/3/search/jql?{qs}"
    auth = base64.b64encode(f"{login}:{token}".encode()).decode()
    req = urllib.request.Request(url, headers={
        "Authorization": f"Basic {auth}",
        "Accept": "application/json",
    })
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode())


def adf_to_text(node):
    """Flatten an Atlassian Document Format node (dict/list/str/None) to plain text.
    Good enough for reading, not a faithful renderer (tables/links collapse to text)."""
    if node is None:
        return ""
    if isinstance(node, str):
        return node
    if isinstance(node, list):
        return "".join(adf_to_text(n) for n in node)
    if isinstance(node, dict):
        if node.get("type") == "text":
            return node.get("text", "")
        block = node.get("type") in ("paragraph", "heading", "listItem", "tableRow")
        text = "".join(adf_to_text(c) for c in node.get("content", []))
        return text + "\n" if block else text
    return ""


def normalize_issue(issue, max_comments=MAX_COMMENTS):
    """A Jira search-result issue -> {key, summary, status, description, comments,
    updated}. `comments` keeps only the most recent `max_comments`, oldest of that
    tail first, so a heavily-discussed ticket doesn't dump its entire history into
    the prompt. `updated` (raw ISO 8601, may be "") is sort-only plumbing so this
    source can be interleaved with gitlab-issues output by recency; it's not a
    table column."""
    f = issue.get("fields") or {}
    comments = ((f.get("comment") or {}).get("comments") or [])[-max_comments:]
    return {
        "key": issue.get("key", ""),
        "summary": f.get("summary", "") or "",
        "status": (f.get("status") or {}).get("name", ""),
        "description": adf_to_text(f.get("description")).strip(),
        "comments": [
            {
                "author": (c.get("author") or {}).get("displayName", ""),
                "body": adf_to_text(c.get("body")).strip(),
            }
            for c in comments
        ],
        "updated": f.get("updated", "") or "",
    }


def normalize_gitlab_issue(issue):
    """A `glab api /projects/:id/issues` result -> the same
    {key, summary, status, description, comments, updated} shape `normalize_issue`
    produces, so both sources can feed one table-building pass. `key` is the
    project-qualified reference (e.g. "rsartin/rob-tracker#4"); `status` is the
    label set (this tracker uses labels like "next"/"someday" as its board
    columns, which is more informative here than the constant `state=opened` the
    fetch already filters on). `description` is already plain markdown, not ADF.
    `comments` is always empty — a personal tracker's own description is kept
    current by editing it (or by closing the issue), not by discussion threads."""
    refs = issue.get("references") or {}
    return {
        "key": refs.get("full") or (f"#{issue.get('iid')}" if issue.get("iid") else ""),
        "summary": issue.get("title", "") or "",
        "status": ", ".join(issue.get("labels") or []) or "Open",
        "description": (issue.get("description") or "").strip(),
        "comments": [],
        "updated": issue.get("updated_at", "") or "",
    }


JIRA_KEY = re.compile(r"\b[A-Z][A-Z0-9]+-\d+\b")


def normalize_gitlab_review(mr):
    """A `glab api /merge_requests?reviewer_username=...` result -> the same
    {key, summary, status, description, comments, updated} shape, so MRs you are
    reviewing join the table. `key` is the first Jira key in the title (MR titles
    here lead with their ticket, e.g. "ABC-123: ..."), falling back to the MR's
    project-qualified reference, so a review lines up with the ticket it belongs
    to. `summary` names the MR and its author, since the ticket usually isn't
    yours. `status` is "Reviewing" plus draft and GitLab's detailed_merge_status
    (e.g. "not_approved"). `comments` is empty: review threads are for the agent
    to read on the MR itself when the row needs them."""
    ref = (mr.get("references") or {}).get("full") or (f"!{mr.get('iid')}" if mr.get("iid") else "")
    title = mr.get("title", "") or ""
    m = JIRA_KEY.search(title)
    author = (mr.get("author") or {}).get("username", "")
    by = f" (by {author})" if author else ""
    flags = [f for f in ("draft" if mr.get("draft") else "", mr.get("detailed_merge_status") or "") if f]
    return {
        "key": m.group(0) if m else ref,
        "summary": f"Reviewing {ref}{by}: {title}",
        "status": "Reviewing" + (f" ({', '.join(flags)})" if flags else ""),
        "description": (mr.get("description") or "").strip(),
        "comments": [],
        "updated": mr.get("updated_at", "") or "",
    }


def _cmd_fetch(rest):
    import argparse
    ap = argparse.ArgumentParser(prog="open_tickets.py fetch")
    ap.add_argument("--user", default="currentUser()",
                    help="JQL assignee expression (default: currentUser())")
    a = ap.parse_args(rest)

    cfg = read_jira_cli_config()
    token = os.environ.get("JIRA_API_TOKEN", "")
    missing = [n for n, v in (("server", cfg.get("server")), ("login", cfg.get("login")),
                              ("JIRA_API_TOKEN", token)) if not v]
    if missing:
        print(json.dumps([]))
        print(f"open-tickets: fetch skipped — missing {', '.join(missing)} "
              f"(expected in {JIRA_CLI_CONFIG} / the environment).", file=sys.stderr)
        return 0

    jql = f"assignee = {a.user} AND statusCategory != Done ORDER BY updated DESC"
    try:
        data = jira_search(cfg["server"], cfg["login"], token, jql,
                            "summary,status,description,comment,updated")
    except Exception as e:  # network/auth/API failure -> degrade, don't crash
        print(json.dumps([]))
        print(f"open-tickets: fetch failed ({type(e).__name__}: {e}).", file=sys.stderr)
        return 0
    issues = data.get("issues", []) if isinstance(data, dict) else data
    print(json.dumps([normalize_issue(i) for i in issues], indent=2))
    return 0


def _parse_stdin_list(command, normalize):
    """Read `glab api` JSON from stdin (a JSON array, or an error object such as
    {"message": "404 Project Not Found"}) and print it normalized. Never shells out
    to `glab` itself — same reasoning as worklog's parse-gitlab: invocation (and
    the target host/project) stays in the skill's documented command, not
    hardcoded in this script."""
    raw = sys.stdin.read()
    try:
        data = json.loads(raw) if raw.strip() else []
    except json.JSONDecodeError as e:
        print(json.dumps([]))
        print(f"open-tickets: {command} failed to parse stdin as JSON "
              f"({e}).", file=sys.stderr)
        return 0
    if not isinstance(data, list):  # glab emits an object on errors (bad project, auth, etc.)
        print(json.dumps([]))
        print(f"open-tickets: {command} got a non-list response: "
              f"{json.dumps(data)[:200]}", file=sys.stderr)
        return 0
    print(json.dumps([normalize(i) for i in data], indent=2))
    return 0


def _cmd_parse_gitlab_issues(rest):
    return _parse_stdin_list("parse-gitlab-issues", normalize_gitlab_issue)


def _cmd_parse_gitlab_reviews(rest):
    return _parse_stdin_list("parse-gitlab-reviews", normalize_gitlab_review)

def main(argv):
    if not argv:
        print("usage: open_tickets.py fetch [--user <JQL assignee expression>] "
              "| parse-gitlab-issues | parse-gitlab-reviews", file=sys.stderr)
        return 2
    if argv[0] == "fetch":
        return _cmd_fetch(argv[1:])
    if argv[0] == "parse-gitlab-issues":
        return _cmd_parse_gitlab_issues(argv[1:])
    if argv[0] == "parse-gitlab-reviews":
        return _cmd_parse_gitlab_reviews(argv[1:])
    print("usage: open_tickets.py fetch [--user <JQL assignee expression>] "
          "| parse-gitlab-issues | parse-gitlab-reviews", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
