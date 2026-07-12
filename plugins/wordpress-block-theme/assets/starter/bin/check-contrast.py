#!/usr/bin/env python3
"""WCAG AA contrast gate for text pairings.
Usage: check-contrast.py [styles/example.json]   (defaults to theme.json)"""
import json, sys, pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _wcag import ratio

root = pathlib.Path(__file__).resolve().parents[1]

# --- EDIT for your palette: (foreground_slug, background_slug, min_ratio, label) ---
CHECKS = [
    ("ink", "paper", 4.5, "body text"),
    ("muted", "paper", 4.5, "muted text"),
    ("accent-text", "paper", 4.5, "links / small accent text"),
]

def palette_of(path):
    data = json.loads(path.read_text())
    entries = data.get("settings", {}).get("color", {}).get("palette", [])
    return {c["slug"]: c["color"] for c in entries}

base = palette_of(root / "theme.json")
target = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else (root / "theme.json")
merged = {**base, **palette_of(target)}  # variation overrides base

errors = []
for fg, bg, minimum, label in CHECKS:
    if fg not in merged or bg not in merged:
        errors.append(f"{label}: missing slug {fg!r} or {bg!r}"); continue
    r = ratio(merged[fg], merged[bg])
    if r < minimum:
        errors.append(f"{label}: {merged[fg]} on {merged[bg]} = {r:.2f}:1 (< {minimum})")
if errors:
    print(f"FAIL {target.name}:\n" + "\n".join(errors)); sys.exit(1)
print(f"OK {target.name}: all text pairings meet WCAG AA")
