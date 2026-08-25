#!/usr/bin/env python3
"""morning-brief: park today's brief in 0 - Planning and roll the old one into
History, the same way Today.md rotates. Stdlib only."""

import argparse
import copy
import datetime
import json
import os
import re
import sys

DEFAULTS = {
    "vaultPath": "~/Library/Mobile Documents/iCloud~md~obsidian/Documents/main",
    "planningDir": "0 - Planning",
    "briefFile": "Morning Brief.md",
    "historyDir": "0 - Planning/History",
    "archivePrefix": "brief",
}


def load_config(path):
    """The `morningBrief` section of start-work.json merged over DEFAULTS.
    Missing file -> a fresh copy of DEFAULTS."""
    cfg = copy.deepcopy(DEFAULTS)
    if not os.path.exists(path):
        return cfg
    with open(path) as f:
        section = json.load(f).get("morningBrief", {})
    cfg.update(section)
    return cfg


def _default_config_path():
    base = os.environ.get("CLAUDE_CONFIG_DIR", os.path.expanduser("~/.claude"))
    return os.path.join(base, "start-work.json")


def vault_path(cfg, *parts):
    return os.path.expanduser(os.path.join(cfg["vaultPath"], *parts))


def brief_path(cfg):
    """The living note: it keeps this name forever, exactly like Today.md."""
    return vault_path(cfg, cfg["planningDir"], cfg["briefFile"])


_DATE_RE = re.compile(r"^date:\s*(\S+)\s*$", re.M)


def note_date(content, fallback=None):
    """The date a brief is *about*, read from its own frontmatter. Falls back to
    `fallback` (default today) when there is no usable `date:` key."""
    fallback = fallback or datetime.date.today()
    block = re.match(r"^---\n([\s\S]*?)\n---", content or "")
    if not block:
        return fallback
    m = _DATE_RE.search(block.group(1))
    if not m:
        return fallback
    raw = m.group(1).strip().strip("'\"")
    for fmt in ("%Y-%m-%d", "%Y%m%d"):
        try:
            return datetime.datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    return fallback


def archive_dir(cfg, when):
    """History/YYYY/YYYYMM — the folder the daily notes already land in."""
    return vault_path(cfg, cfg["historyDir"], when.strftime("%Y"), when.strftime("%Y%m"))


def archive_name(cfg, when):
    return f"{cfg['archivePrefix']} - {when.strftime('%Y%m%d')}"


def free_path(folder, base):
    """First free "<base>.md", "<base> (2).md", ... in `folder`. Mirrors
    freezeAndArchive's freePath so a re-run never clobbers an archive."""
    candidate = os.path.join(folder, f"{base}.md")
    n = 2
    while os.path.exists(candidate):
        candidate = os.path.join(folder, f"{base} ({n}).md")
        n += 1
    return candidate


def _read(path):
    with open(path) as f:
        return f.read()


def rotate(cfg, new_content, today=None, dry_run=False):
    """Archive the brief now sitting in 0 - Planning, then drop `new_content` in
    its place. Returns {archived, archived_from_date, written, skipped_reason}.

    A brief already dated today is replaced, not archived: the scheduled task
    firing twice in one morning should leave one note, not two."""
    today = today or datetime.date.today()
    current = brief_path(cfg)
    result = {
        "archived": None,
        "archived_from_date": None,
        "written": current,
        "skipped_reason": None,
    }

    if os.path.exists(current):
        old = _read(current)
        when = note_date(old, fallback=today)
        # Emptiness first: a blank file has no frontmatter, so note_date would
        # hand back today's date and the same-day branch would swallow it.
        if not old.strip():
            result["skipped_reason"] = "existing brief is empty"
        elif when == today:
            result["skipped_reason"] = f"existing brief is already dated {today.isoformat()}"
        else:
            folder = archive_dir(cfg, when)
            dest = free_path(folder, archive_name(cfg, when))
            if not dry_run:
                os.makedirs(folder, exist_ok=True)
                with open(dest, "w") as f:
                    f.write(old)
            result["archived"] = dest
            result["archived_from_date"] = when.isoformat()
    else:
        result["skipped_reason"] = "no existing brief to archive"

    if not dry_run:
        os.makedirs(os.path.dirname(current), exist_ok=True)
        with open(current, "w") as f:
            f.write(new_content if new_content.endswith("\n") else new_content + "\n")
    return result


def _cmd_save(rest):
    ap = argparse.ArgumentParser(prog="morning_brief.py save")
    ap.add_argument(
        "--file", default=None, help="markdown file to install as today's brief (default: stdin)"
    )
    ap.add_argument("--date", default=None, help="treat this as today (YYYY-MM-DD)")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(rest)

    today = None
    if a.date:
        try:
            today = datetime.date.fromisoformat(a.date)
        except ValueError:
            print(
                f"morning-brief: invalid --date '{a.date}' (expected YYYY-MM-DD)", file=sys.stderr
            )
            return 2

    content = _read(a.file) if a.file else sys.stdin.read()
    if not content.strip():
        print("morning-brief: refusing to write an empty brief", file=sys.stderr)
        return 2

    cfg = load_config(_default_config_path())
    planning = vault_path(cfg, cfg["planningDir"])
    if not os.path.isdir(planning):
        print(
            f"morning-brief: planning dir missing ({planning}) — configure morningBrief.vaultPath.",
            file=sys.stderr,
        )
        return 1

    r = rotate(cfg, content, today=today, dry_run=a.dry_run)
    prefix = "would " if a.dry_run else ""
    if r["archived"]:
        print(f"{prefix}archived {r['archived_from_date']} -> {r['archived']}")
    else:
        print(f"no archive: {r['skipped_reason']}")
    print(f"{prefix}wrote {r['written']}")
    return 0


def _cmd_paths(rest):
    ap = argparse.ArgumentParser(prog="morning_brief.py paths")
    ap.add_argument("--date", default=None)
    a = ap.parse_args(rest)
    when = datetime.date.fromisoformat(a.date) if a.date else datetime.date.today()
    cfg = load_config(_default_config_path())
    print(
        json.dumps(
            {
                "config": _default_config_path(),
                "brief": brief_path(cfg),
                "archiveDir": archive_dir(cfg, when),
                "archiveName": archive_name(cfg, when) + ".md",
            },
            indent=2,
        )
    )
    return 0


def main(argv):
    if not argv:
        print("usage: morning_brief.py <save|paths> ...", file=sys.stderr)
        return 2
    cmd, rest = argv[0], argv[1:]
    if cmd == "save":
        return _cmd_save(rest)
    if cmd == "paths":
        return _cmd_paths(rest)
    print(f"unknown subcommand: {cmd}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
