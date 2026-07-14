#!/usr/bin/env python3
"""worklog: capture work activity into a rolling Worklog.md. Stdlib only."""
import copy
import datetime
import json
import os
import re
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


def format_entry(type_, ref, text, meta=None):
    body = f" {ref} — {text}" if ref else f" {text}"
    tail = f"  `{meta}`" if meta else ""
    return f"- **{type_}**{body}{tail}"


def _parse_days(content):
    preamble = []
    days = []
    cur = None
    for line in content.splitlines():
        if line.startswith("## "):
            cur = [line[3:].strip(), []]
            days.append(cur)
        elif cur is not None:
            if line.strip():
                cur[1].append(line)
        else:
            preamble.append(line)
    return preamble, days


def _render_days(preamble, days):
    out = list(preamble)
    if preamble and preamble[-1].strip():
        out.append("")
    for date, entries in sorted(days, key=lambda d: d[0], reverse=True):
        out.append(f"## {date}")
        out.extend(entries)
        out.append("")
    return "\n".join(out).rstrip("\n") + "\n"


def append_entry(content, date, entry_line, dedup_key=None):
    preamble, days = _parse_days(content)
    by_date = {d[0]: d for d in days}
    if date in by_date:
        entries = by_date[date][1]
        if dedup_key and any(dedup_key in e for e in entries):
            return content
        entries.append(entry_line)
    else:
        days.append([date, [entry_line]])
    return _render_days(preamble, days)


_ENTRY_RE = re.compile(r"- \*\*(\w+)\*\*\s+(.*)")


def parse(content):
    out = []
    date = None
    for line in content.splitlines():
        if line.startswith("## "):
            date = line[3:].strip()
        elif date:
            m = _ENTRY_RE.match(line.strip())
            if m:
                out.append({"date": date, "type": m.group(1), "text": m.group(2).strip()})
    return out


def entries_in_range(content, since, until):
    return [e for e in parse(content) if since <= e["date"] <= until]


def main(argv):
    if not argv:
        print("usage: worklog.py <log|entries> ...", file=sys.stderr)
        return 2
    cmd, rest = argv[0], argv[1:]
    if cmd == "log":
        return _cmd_log(rest)
    if cmd == "entries":
        import argparse
        ap = argparse.ArgumentParser(prog="worklog.py entries")
        ap.add_argument("--since", required=True)
        ap.add_argument("--until", required=True)
        a = ap.parse_args(rest)
        cfg = load_config(_default_config_path())
        path = worklog_path(cfg)
        content = open(path).read() if os.path.exists(path) else ""
        print(json.dumps(entries_in_range(content, a.since, a.until), indent=2))
        return 0
    print(f"unknown subcommand: {cmd}", file=sys.stderr)
    return 2


def _cmd_log(rest):
    import argparse
    ap = argparse.ArgumentParser(prog="worklog.py log")
    ap.add_argument("type")
    ap.add_argument("text")
    ap.add_argument("--ref", default=None)
    ap.add_argument("--branch", default=None)
    ap.add_argument("--date", default=None)
    a = ap.parse_args(rest)
    cfg = load_config(_default_config_path())
    if a.type not in cfg["types"]:
        print(f"worklog: unknown type '{a.type}' (allowed: {', '.join(cfg['types'])})", file=sys.stderr)
        return 2
    if a.date is not None:
        try:
            datetime.date.fromisoformat(a.date)
        except ValueError:
            print(f"worklog: invalid --date '{a.date}' (expected YYYY-MM-DD)", file=sys.stderr)
            return 2
    date = a.date or datetime.date.today().isoformat()
    meta = f"[branch: {a.branch}]" if a.branch else None
    line = format_entry(a.type, a.ref, a.text, meta)
    dedup = f"**{a.type}** {a.ref} —" if (a.ref and a.type != "note") else None

    path = worklog_path(cfg)
    if not os.path.isdir(os.path.dirname(path)):
        print(f"worklog: vault dir missing ({os.path.dirname(path)}) — configure worklog.vaultPath.",
              file=sys.stderr)
        return 1
    content = ""
    if os.path.exists(path):
        with open(path) as f:
            content = f.read()
    new = append_entry(content, date, line, dedup)
    with open(path, "w") as f:
        f.write(new)
    print(f"logged: {line}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
