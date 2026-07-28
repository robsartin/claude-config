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
    "metricsFile": "Metrics.md",
    "reportsDir": "Reports",
    "types": ["started", "shipped", "note", "help"],
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


def metrics_path(cfg):
    return os.path.expanduser(os.path.join(cfg["vaultPath"], cfg["metricsFile"]))


def format_metric(name, value):
    return f"- {name}: {value}"


def parse_metric_value(raw):
    """Leading number of `raw` as a float ('7.2h' -> 7.2); None if unparseable."""
    m = re.match(r"\s*(-?\d+(?:\.\d+)?)", str(raw))
    return float(m.group(1)) if m else None


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


def parse_jira_list(raw):
    """Normalize `jira issue list --raw` output into shipped-entry dicts
    {date, type, ref, text}. Accepts the Jira search response ({"issues": [...]}),
    a bare list, or a JSON string. Date is the resolution/status-change/updated
    date, truncated to YYYY-MM-DD."""
    data = raw if isinstance(raw, (list, dict)) else json.loads(raw)
    issues = data.get("issues", []) if isinstance(data, dict) else data
    out = []
    for d in issues:
        f = d.get("fields") or {}
        raw_date = f.get("resolutiondate") or f.get("statuscategorychangedate") or f.get("updated") or ""
        key = d.get("key", "") or ""
        out.append({
            "date": raw_date[:10],
            "type": "shipped",
            "ref": key,
            "text": f"{key} — {f.get('summary', '') or ''}".strip(" —"),
        })
    return out


def parse_gitlab_mrs(raw):
    """Normalize `glab api /merge_requests?...` output (a JSON array of MRs, or a
    JSON string) into shipped-entry dicts. Date is `merged_at` (or `updated_at`),
    truncated to YYYY-MM-DD; ref is the full reference (e.g. group/proj!123)."""
    data = raw if isinstance(raw, (list, dict)) else json.loads(raw)
    if not isinstance(data, list):  # glab emits an object (e.g. {"message": "404"}) on errors
        data = []
    out = []
    for mr in data:
        raw_date = mr.get("merged_at") or mr.get("updated_at") or ""
        refs = mr.get("references") or {}
        ref = refs.get("full") or (f"!{mr.get('iid')}" if mr.get("iid") else "")
        out.append({
            "date": raw_date[:10],
            "type": "shipped",
            "ref": ref,
            "text": f"{ref} — {mr.get('title', '') or ''}".strip(" —"),
        })
    return out


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
    if cmd in ("parse-jira", "parse-gitlab"):
        text = sys.stdin.read().strip()
        try:
            data = json.loads(text) if text else []
        except json.JSONDecodeError:
            data = []  # a failed upstream jira/glab command -> empty, not a crash
        fn = parse_jira_list if cmd == "parse-jira" else parse_gitlab_mrs
        print(json.dumps(fn(data), indent=2))
        return 0
    if cmd == "metric":
        return _cmd_metric(rest)
    if cmd == "metrics":
        return _cmd_metrics(rest)
    print(f"unknown subcommand: {cmd}", file=sys.stderr)
    return 2


_METRIC_RE = re.compile(r"- ([\w-]+):\s*(-?\d+(?:\.\d+)?)\s*$")


def upsert_metric(content, date, name, value):
    """Insert-or-replace `- <name>: <value>` under the `## <date>` heading,
    newest day on top. Same name + same day replaces the value."""
    line = format_metric(name, value)
    preamble, days = _parse_days(content)
    by_date = {d[0]: d for d in days}
    if date in by_date:
        entries = by_date[date][1]
        for i, e in enumerate(entries):
            m = _METRIC_RE.match(e)
            if m and m.group(1) == name:
                entries[i] = line
                break
        else:
            entries.append(line)
    else:
        days.append([date, [line]])
    return _render_days(preamble, days)


def parse_metrics(content):
    out = []
    date = None
    for l in content.splitlines():
        if l.startswith("## "):
            date = l[3:].strip()
        elif date:
            m = _METRIC_RE.match(l.strip())
            if m:
                out.append({"date": date, "name": m.group(1), "value": float(m.group(2))})
    return out


def metric_series(content, since, until):
    series = {}
    for e in parse_metrics(content):
        if since <= e["date"] <= until:
            series.setdefault(e["name"], []).append((e["date"], e["value"]))
    for name in series:
        series[name].sort()
    return series


_SPARK = "▁▂▃▄▅▆▇█"


def summarize(points):
    vals = [v for _, v in points]
    return {
        "latest": vals[-1],
        "total": round(sum(vals), 2),
        "avg": round(sum(vals) / len(vals), 2),
        "min": min(vals),
        "max": max(vals),
        "count": len(vals),
    }


def sparkline(values):
    if not values:
        return ""
    lo, hi = min(values), max(values)
    span = hi - lo
    mid = (len(_SPARK) - 1) // 2   # index 3 -> ▄, used for a flat/single series
    return "".join(
        _SPARK[mid] if span == 0 else _SPARK[round((v - lo) / span * (len(_SPARK) - 1))]
        for v in values
    )


def count_events(content, type_, since, until):
    return sum(
        1 for e in parse(content)
        if e["type"] == type_ and since <= e["date"] <= until
    )


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


def _cmd_metric(rest):
    import argparse
    ap = argparse.ArgumentParser(prog="worklog.py metric")
    ap.add_argument("name")
    ap.add_argument("value")
    ap.add_argument("--date", default=None)
    a = ap.parse_args(rest)
    num = parse_metric_value(a.value)
    if num is None:
        print(f"worklog: metric value '{a.value}' is not numeric", file=sys.stderr)
        return 2
    if a.date is not None:
        try:
            datetime.date.fromisoformat(a.date)
        except ValueError:
            print(f"worklog: invalid --date '{a.date}' (expected YYYY-MM-DD)", file=sys.stderr)
            return 2
    date = a.date or datetime.date.today().isoformat()
    cfg = load_config(_default_config_path())
    path = metrics_path(cfg)
    if not os.path.isdir(os.path.dirname(path)):
        print(f"worklog: vault dir missing ({os.path.dirname(path)}) — configure worklog.vaultPath.",
              file=sys.stderr)
        return 1
    content = open(path).read() if os.path.exists(path) else ""
    # store as int when the value is integral (energy: 4, not 4.0)
    stored = int(num) if num == int(num) else num
    with open(path, "w") as f:
        f.write(upsert_metric(content, date, a.name, stored))
    print(f"metric: {a.name} = {stored} on {date}")
    return 0


def _cmd_metrics(rest):
    import argparse
    ap = argparse.ArgumentParser(prog="worklog.py metrics")
    ap.add_argument("--since", required=True)
    ap.add_argument("--until", required=True)
    a = ap.parse_args(rest)
    cfg = load_config(_default_config_path())
    mpath = metrics_path(cfg)
    wpath = worklog_path(cfg)
    mcontent = open(mpath).read() if os.path.exists(mpath) else ""
    wcontent = open(wpath).read() if os.path.exists(wpath) else ""
    series = metric_series(mcontent, a.since, a.until)
    metrics = {
        name: {"points": pts, "summary": summarize(pts), "sparkline": sparkline([v for _, v in pts])}
        for name, pts in series.items()
    }
    derived = {
        "help-count": count_events(wcontent, "help", a.since, a.until),
        "prs-merged": count_events(wcontent, "shipped", a.since, a.until),
    }
    print(json.dumps({"metrics": metrics, "derived": derived}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
