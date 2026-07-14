#!/usr/bin/env python3
"""worklog: capture work activity into a rolling Worklog.md. Stdlib only."""
import copy
import json
import os
import sys

DEFAULTS = {
    "vaultPath": "~/Obsidian",
    "worklogFile": "Worklog.md",
    "reportsDir": "Reports",
    "types": ["started", "shipped", "note"],
}


def load_config(path):
    """The `worklog` section of start-work.json merged over DEFAULTS.
    Missing file -> a fresh copy of DEFAULTS."""
    cfg = copy.deepcopy(DEFAULTS)
    if not os.path.exists(path):
        return cfg
    with open(path) as f:
        section = json.load(f).get("worklog", {})
    cfg.update(section)
    return cfg


def worklog_path(cfg):
    return os.path.expanduser(os.path.join(cfg["vaultPath"], cfg["worklogFile"]))


def _default_config_path():
    base = os.environ.get("CLAUDE_CONFIG_DIR", os.path.expanduser("~/.claude"))
    return os.path.join(base, "start-work.json")


def main(argv):
    if not argv:
        print("usage: worklog.py <log|entries> ...", file=sys.stderr)
        return 2
    print(f"unknown subcommand: {argv[0]}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
