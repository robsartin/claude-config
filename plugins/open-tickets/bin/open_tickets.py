#!/usr/bin/env python3
"""open-tickets: fetch your open Jira issues (with description + recent comments)
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
    """A search-result issue -> {key, summary, status, description, comments}.
    `comments` keeps only the most recent `max_comments`, oldest of that tail first,
    so a heavily-discussed ticket doesn't dump its entire history into the prompt."""
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
                            "summary,status,description,comment")
    except Exception as e:  # network/auth/API failure -> degrade, don't crash
        print(json.dumps([]))
        print(f"open-tickets: fetch failed ({type(e).__name__}: {e}).", file=sys.stderr)
        return 0
    issues = data.get("issues", []) if isinstance(data, dict) else data
    print(json.dumps([normalize_issue(i) for i in issues], indent=2))
    return 0


def main(argv):
    if not argv or argv[0] != "fetch":
        print("usage: open_tickets.py fetch [--user <JQL assignee expression>]", file=sys.stderr)
        return 2
    return _cmd_fetch(argv[1:])


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
