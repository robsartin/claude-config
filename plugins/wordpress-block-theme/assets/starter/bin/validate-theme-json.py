#!/usr/bin/env python3
"""Validate theme.json and every styles/*.json: must be valid JSON with $schema and version 3."""
import json, sys, pathlib

root = pathlib.Path(__file__).resolve().parents[1]
targets = [root / "theme.json", *sorted((root / "styles").glob("*.json"))]
errors = []
for path in targets:
    if not path.exists():
        continue
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as e:
        errors.append(f"{path.name}: invalid JSON: {e}")
        continue
    if data.get("version") != 3:
        errors.append(f"{path.name}: version must be 3, got {data.get('version')!r}")
    if "$schema" not in data:
        errors.append(f"{path.name}: missing $schema")
if not (root / "theme.json").exists():
    errors.append("theme.json missing")
if errors:
    print("\n".join(errors)); sys.exit(1)
print(f"OK: validated {len([t for t in targets if t.exists()])} file(s)")
