#!/usr/bin/env python3
"""WCAG AA contrast gate for button text/background.
Usage: check-button-contrast.py [styles/example.json]   (defaults to theme.json)"""
import json, sys, pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _wcag import ratio

root = pathlib.Path(__file__).resolve().parents[1]

def load(path): return json.loads(path.read_text())
def palette_of(d): return {c["slug"]: c["color"] for c in d.get("settings", {}).get("color", {}).get("palette", [])}
def button_of(d): return d.get("styles", {}).get("elements", {}).get("button", {}).get("color")

def resolve(value, palette):
    value = value.strip()
    pre = "var(--wp--preset--color--"
    if value.startswith(pre) and value.endswith(")"):
        return palette[value[len(pre):-1]]
    if value.startswith("var:preset|color|"):
        return palette[value.split("|")[-1]]
    return value

base = load(root / "theme.json")
target = load(pathlib.Path(sys.argv[1])) if len(sys.argv) > 1 else base
name = pathlib.Path(sys.argv[1]).name if len(sys.argv) > 1 else "theme.json"
palette = {**palette_of(base), **palette_of(target)}
button = button_of(target) or button_of(base)
if not button:
    print(f"OK {name}: no button color defined"); sys.exit(0)

text = resolve(button["text"], palette)
background = resolve(button["background"], palette)
r = ratio(text, background)
if r < 4.5:
    print(f"FAIL {name}: button {text} on {background} = {r:.2f}:1 (< 4.5)"); sys.exit(1)
print(f"OK {name}: button contrast {r:.2f}:1 meets WCAG AA")
