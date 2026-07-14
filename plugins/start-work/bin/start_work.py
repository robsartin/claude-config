#!/usr/bin/env python3
"""start-work helpers: deterministic bits the SKILL.md calls. Stdlib only."""
import json
import os
import re
import subprocess
import sys

DEFAULTS = {
    "gitlabHosts": [],
    "worklog": {"vaultPath": "~/Obsidian", "worklogFile": "Worklog.md"},
}


def load_config(path):
    """User JSON shallow-merged over DEFAULTS (worklog sub-dict deep-merged).
    Missing file -> a fresh copy of DEFAULTS."""
    import copy
    cfg = copy.deepcopy(DEFAULTS)
    if not os.path.exists(path):
        return cfg
    with open(path) as f:
        user = json.load(f)
    for k, v in user.items():
        if k == "worklog" and isinstance(v, dict):
            cfg["worklog"].update(v)
        else:
            cfg[k] = v
    return cfg


def _config_get(cfg, dotted):
    cur = cfg
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return ""
        cur = cur[part]
    return cur


def _default_config_path():
    base = os.environ.get("CLAUDE_CONFIG_DIR", os.path.expanduser("~/.claude"))
    return os.path.join(base, "start-work.json")


def host_of(remote_url):
    m = re.match(r"(?:https?://|ssh://git@|git@)([^/:]+)", remote_url.strip())
    return m.group(1) if m else ""


def provider_for_remote(remote_url, gitlab_hosts):
    host = host_of(remote_url)
    if host == "github.com":
        return "github"
    if host in gitlab_hosts:
        return "gitlab"
    return "unknown"


def slugify(title, max_len=50):
    """Convert a title to a lowercase slug. Non-alphanumeric chars become hyphens."""
    s = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    if len(s) > max_len:
        s = s[:max_len].rstrip("-")
    return s


def branch_name(ref, title):
    """Combine a reference (e.g., issue number) with a slugified title."""
    return f"{ref}-{slugify(title)}"


def _origin_url():
    try:
        return subprocess.check_output(
            ["git", "remote", "get-url", "origin"], text=True, stderr=subprocess.DEVNULL
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ""


def main(argv):
    if not argv:
        print("usage: start_work.py <provider|branch-name|config-get> ...", file=sys.stderr)
        return 2
    cmd, rest = argv[0], argv[1:]
    if cmd == "config-get":
        cfg = load_config(_default_config_path())
        val = _config_get(cfg, rest[0]) if rest else ""
        print(val if not isinstance(val, (dict, list)) else json.dumps(val))
        return 0
    if cmd == "provider":
        cfg = load_config(_default_config_path())
        print(provider_for_remote(_origin_url(), cfg.get("gitlabHosts", [])))
        return 0
    if cmd == "branch-name":
        if len(rest) < 2:
            print("usage: branch-name <ref> <title...>", file=sys.stderr)
            return 2
        print(branch_name(rest[0], " ".join(rest[1:])))
        return 0
    print(f"unknown subcommand: {cmd}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
