# worklog batch metric entry — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let `/worklog:metric` record several readings in one line as `name=value` tokens (atomic, shared `--date`), while the legacy `metric <name> <value>` form keeps working.

**Architecture:** A pure `parse_metric_pairs(tokens)` decides batch-vs-legacy and validates every token (raising `ValueError` naming the offender), so all the grammar rules are unit-testable. `_cmd_metric` calls it, then upserts each pair into `Metrics.md` in one read/write — rejecting the whole batch before any I/O if parsing fails.

**Tech Stack:** Python 3 stdlib + pytest, Claude Code plugin (SKILL.md + command file).

## Global Constraints

- Never commit to `main`; branch `50-batch-metric-entry`, squash-PR (issue #50).
- Stdlib-only Python, run via `python3`, no new deps. No `plugin.json` change (same command). No config change.
- **Batch form** = *every* positional token contains `=` (`name=value`). **Legacy form** = exactly two positional tokens, neither containing `=`. Any other shape is a `ValueError` pointing at the `name=value` form.
- Metric name grammar: `^[\w-]+$`. Value via the existing `parse_metric_value` (leading number, trailing unit allowed); `None` = not numeric.
- **Atomic:** any malformed token or non-numeric value → reject the whole batch, **write nothing**, name the offending token, return non-zero. Parsing raises before any file I/O.
- One shared `--date` (validated ISO as today); per-pair **upsert-per-day** unchanged; integral values stored bare (`energy: 4`, not `4.0`).
- Missing vault dir → the existing "configure `worklog.vaultPath`" error, `return 1`, before any write.
- Public repo — NO work-specific identifiers; generic examples only.

## File Structure

Modified:
- `plugins/worklog/bin/worklog.py` — add `_NAME_RE`, `_validate_name`, `_validate_value`, `parse_metric_pairs`; rewrite `_cmd_metric` (lines 317-347) to be multi-pair.
- `plugins/worklog/tests/test_worklog.py` — add `import pytest`; unit tests for `parse_metric_pairs`; batch CLI tests.
- `plugins/worklog/skills/worklog/SKILL.md` — the "Record a reading" step shows the batch form.
- `plugins/worklog/commands/metric.md` — `argument-hint` + body mention batch entry.
- `CLAUDE.md`, `README.md` — one clause that `/worklog:metric` accepts several `name=value` readings at once.

---

### Task 1: `parse_metric_pairs` (pure grammar + validation)

**Files:**
- Modify: `plugins/worklog/bin/worklog.py` (add functions just above `_cmd_metric` at line 317)
- Modify: `plugins/worklog/tests/test_worklog.py` (add `import pytest`; append tests)

**Interfaces:**
- Consumes: existing `parse_metric_value(raw) -> float | None`.
- Produces: `parse_metric_pairs(tokens) -> list[(name, value_float)]`, raising `ValueError` (message names the offending token) on any bad input.

- [ ] **Step 1: Add `import pytest` and write the failing tests**

At the top of `tests/test_worklog.py`, change line 1 from `import json, os, sys` to:

```python
import json, os, sys
import pytest
```

Then append these tests:

```python
def test_parse_metric_pairs_batch():
    assert wl.parse_metric_pairs(["work-hours=8", "focus-hours=4.5", "energy=4"]) == [
        ("work-hours", 8.0), ("focus-hours", 4.5), ("energy", 4.0)]


def test_parse_metric_pairs_legacy_single():
    assert wl.parse_metric_pairs(["work-hours", "8"]) == [("work-hours", 8.0)]


def test_parse_metric_pairs_trailing_unit_in_batch():
    assert wl.parse_metric_pairs(["sleep-hours=7.2h"]) == [("sleep-hours", 7.2)]


def test_parse_metric_pairs_bad_value_names_token():
    with pytest.raises(ValueError) as e:
        wl.parse_metric_pairs(["focus-hours=lots"])
    assert "focus-hours=lots" in str(e.value)


def test_parse_metric_pairs_bad_name_rejected():
    with pytest.raises(ValueError):
        wl.parse_metric_pairs(["=8"])


def test_parse_metric_pairs_mixed_form_rejected():
    with pytest.raises(ValueError):
        wl.parse_metric_pairs(["a=1", "b", "2"])


def test_parse_metric_pairs_empty_rejected():
    with pytest.raises(ValueError):
        wl.parse_metric_pairs([])


def test_parse_metric_pairs_duplicates_preserved_in_order():
    assert wl.parse_metric_pairs(["work-hours=8", "work-hours=9"]) == [
        ("work-hours", 8.0), ("work-hours", 9.0)]
```

- [ ] **Step 2: Run, expect failure**

Run: `cd plugins/worklog && python3 -m pytest tests/test_worklog.py -k parse_metric_pairs -q`
Expected: FAIL (`AttributeError: module 'worklog' has no attribute 'parse_metric_pairs'`).

- [ ] **Step 3: Implement**

In `plugins/worklog/bin/worklog.py`, immediately above `def _cmd_metric(rest):` (line 317), add:

```python
_NAME_RE = re.compile(r"^[\w-]+$")


def _validate_name(name, token):
    if not _NAME_RE.match(name):
        raise ValueError(f"invalid metric name in '{token}'")
    return name


def _validate_value(raw, token):
    v = parse_metric_value(raw)
    if v is None:
        raise ValueError(f"'{raw}' in '{token}' is not numeric")
    return v


def parse_metric_pairs(tokens):
    """Interpret positional `metric` tokens into [(name, value_float)].
    Batch form: every token is `name=value`. Legacy form: exactly two bare
    tokens `name value`. Raises ValueError (naming the offending token) on
    anything else, before any I/O — so a bad batch writes nothing."""
    if not tokens:
        raise ValueError("no metrics given")
    has_eq = ["=" in t for t in tokens]
    if all(has_eq):
        pairs = []
        for t in tokens:
            name, _, raw = t.partition("=")
            pairs.append((_validate_name(name, t), _validate_value(raw, t)))
        return pairs
    if len(tokens) == 2 and not any(has_eq):
        name, raw = tokens
        return [(_validate_name(name, name), _validate_value(raw, raw))]
    raise ValueError("use name=value tokens, e.g. work-hours=8 focus-hours=4.5")
```

(`re` is already imported at the top of the module.)

- [ ] **Step 4: Run, expect pass**

Run: `cd plugins/worklog && python3 -m pytest tests/test_worklog.py -k parse_metric_pairs -q`
Expected: PASS (8 tests).

- [ ] **Step 5: Full suite + commit**

```bash
cd plugins/worklog && python3 -m pytest tests -q   # all pass (existing + 8 new)
cd ~/code/claude-config
git add plugins/worklog/bin/worklog.py plugins/worklog/tests/test_worklog.py
git commit -m "worklog: add parse_metric_pairs (batch/legacy token grammar)"
```

---

### Task 2: multi-pair `_cmd_metric`

**Files:**
- Modify: `plugins/worklog/bin/worklog.py:317-347` (the `_cmd_metric` function)
- Modify: `plugins/worklog/tests/test_worklog.py` (append batch CLI tests)

**Interfaces:**
- Consumes: `parse_metric_pairs` (Task 1), existing `upsert_metric`, `metrics_path`, `load_config`, `_default_config_path`.
- Produces: `main(["metric", "a=1", "b=2", "--date", D])` writes both under day `D` in one call; a batch with any bad token writes nothing and returns non-zero; the legacy `main(["metric", name, value])` path is unchanged.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_worklog.py` (mirrors the existing metric e2e tests' fixture style):

```python
def test_cmd_metric_batch_writes_all_in_one_call(tmp_path, monkeypatch):
    vault = tmp_path / "v"; vault.mkdir()
    cfgdir = tmp_path / "c"; cfgdir.mkdir()
    (cfgdir / "start-work.json").write_text(json.dumps({"worklog": {"vaultPath": str(vault)}}))
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(cfgdir))

    rc = wl.main(["metric", "work-hours=8", "focus-hours=4.5", "energy=4", "--date", "2026-07-28"])
    assert rc == 0
    text = (vault / "Metrics.md").read_text()
    assert "## 2026-07-28" in text
    assert "- work-hours: 8\n" in text        # integral stored bare
    assert "- focus-hours: 4.5\n" in text
    assert "- energy: 4\n" in text


def test_cmd_metric_batch_atomic_on_bad_token(tmp_path, monkeypatch):
    vault = tmp_path / "v"; vault.mkdir()
    cfgdir = tmp_path / "c"; cfgdir.mkdir()
    (cfgdir / "start-work.json").write_text(json.dumps({"worklog": {"vaultPath": str(vault)}}))
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(cfgdir))

    rc = wl.main(["metric", "work-hours=8", "focus-hours=lots", "--date", "2026-07-28"])
    assert rc != 0
    assert not (vault / "Metrics.md").exists()   # nothing written — atomic
```

- [ ] **Step 2: Run, expect failure**

Run: `cd plugins/worklog && python3 -m pytest tests/test_worklog.py -k "metric_batch" -q`
Expected: FAIL — the current `_cmd_metric` uses a fixed `value` positional, so a 3-token batch errors out or the atomic-write assertion fails.

- [ ] **Step 3: Replace `_cmd_metric`**

Replace the entire `_cmd_metric` function (`plugins/worklog/bin/worklog.py:317-347`) with:

```python
def _cmd_metric(rest):
    import argparse
    ap = argparse.ArgumentParser(prog="worklog.py metric")
    ap.add_argument("tokens", nargs="+")
    ap.add_argument("--date", default=None)
    a = ap.parse_args(rest)
    try:
        pairs = parse_metric_pairs(a.tokens)
    except ValueError as e:
        print(f"worklog: {e}", file=sys.stderr)
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
    stored_pairs = []
    for name, num in pairs:
        # store as int when the value is integral (energy: 4, not 4.0)
        stored = int(num) if num == int(num) else num
        content = upsert_metric(content, date, name, stored)
        stored_pairs.append(f"{name}={stored}")
    with open(path, "w") as f:
        f.write(content)
    print(f"metric: {', '.join(stored_pairs)} on {date}")
    return 0
```

- [ ] **Step 4: Run, expect pass**

Run: `cd plugins/worklog && python3 -m pytest tests -q`
Expected: PASS — the two new batch tests, the pre-existing `test_cmd_metric_end_to_end_upsert` and `test_cmd_metric_rejects_non_numeric` (both use the legacy form and still pass), and everything else.

- [ ] **Step 5: Commit**

```bash
git add plugins/worklog/bin/worklog.py plugins/worklog/tests/test_worklog.py
git commit -m "worklog: multi-pair batch entry in _cmd_metric"
```

---

### Task 3: docs (SKILL + command + CLAUDE/README) + verify

**Files:**
- Modify: `plugins/worklog/skills/worklog/SKILL.md`, `plugins/worklog/commands/metric.md`, `CLAUDE.md`, `README.md`

- [ ] **Step 1: SKILL "Record a reading" shows the batch form**

In `plugins/worklog/skills/worklog/SKILL.md`, the "### Record a reading" block currently is:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/bin/worklog.py" metric <name> <value> [--date YYYY-MM-DD]
```

Replace that fenced command with:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/bin/worklog.py" metric <name=value> [<name=value> ...] [--date YYYY-MM-DD]
# one reading, or a whole day at once:
python3 "${CLAUDE_PLUGIN_ROOT}/bin/worklog.py" metric work-hours=8 focus-hours=4.5 energy=4
```

Then, in the paragraph right after it (the one starting "e.g. `metric work-hours 8`..."), append this sentence at the end of that paragraph:

```markdown
Pass several `name=value` tokens to record a whole day in one call; if any token is malformed or
non-numeric the **whole batch is rejected** and nothing is written, so a corrected line can be
re-entered. The bare `metric <name> <value>` form still works for a single reading.
```

- [ ] **Step 2: Command file mentions batch entry**

In `plugins/worklog/commands/metric.md`, change the `argument-hint` frontmatter line to:

```markdown
argument-hint: "<name=value> [<name=value> ...] [--date YYYY-MM-DD]"
```

And change the body to:

```markdown
Invoke the `worklog` skill's "Metrics — Record a reading" step with the user's arguments
($ARGUMENTS). Accepts one reading or several `name=value` tokens in one call (a whole day at once);
if nothing is given, ask. Values must be numeric — if any token is bad the whole batch is rejected
and nothing is written. Re-recording a metric for the same day replaces it.
```

(No unquoted colon-space in the frontmatter — the `argument-hint` value is quoted.)

- [ ] **Step 3: CLAUDE.md + README.md one-clause update**

In `CLAUDE.md` (`### worklog`) and `README.md` (`## The worklog plugin`), in the sentence that introduces `/worklog:metric`, note that it accepts **several `name=value` readings in one call** (e.g. `work-hours=8 focus-hours=4.5`). Keep it to a clause; do not restate the whole feature. Verify: `grep -c 'name=value' CLAUDE.md README.md plugins/worklog/skills/worklog/SKILL.md plugins/worklog/commands/metric.md`.

- [ ] **Step 4: Verify + e2e + commit**

```bash
cd ~/code/claude-config
claude plugin validate plugins/worklog 2>&1 | tail -2          # passes (only no-version warning)
cd plugins/worklog && python3 -m pytest tests -q && rm -rf .pytest_cache tests/__pycache__ bin/__pycache__
cd ~/code/claude-config
rm -rf /tmp/bm && mkdir -p /tmp/bm/v /tmp/bm/c
printf '{"worklog":{"vaultPath":"/tmp/bm/v"}}' > /tmp/bm/c/start-work.json
CLAUDE_CONFIG_DIR=/tmp/bm/c python3 plugins/worklog/bin/worklog.py metric work-hours=8 focus-hours=4.5 energy=4 --date 2026-07-28
echo "--- Metrics.md ---"; cat /tmp/bm/v/Metrics.md
CLAUDE_CONFIG_DIR=/tmp/bm/c python3 plugins/worklog/bin/worklog.py metric work-hours=9.5 sleep=oops --date 2026-07-28; echo "exit: $?"
echo "--- after bad batch (work-hours must still be 8, no sleep) ---"; cat /tmp/bm/v/Metrics.md
rm -rf /tmp/bm
```
Expected: the first call writes all three under `## 2026-07-28` (`work-hours: 8`, `focus-hours: 4.5`, `energy: 4`); the second call exits non-zero and leaves the file unchanged (`work-hours` still `8`, no `sleep`, no `9.5`) — proving atomicity.

```bash
git add plugins/worklog/skills/worklog/SKILL.md plugins/worklog/commands/metric.md CLAUDE.md README.md
git commit -m "worklog: document batch name=value metric entry"
```

**STOP after Step 4.** Do not push or open a PR — the controller runs the final whole-branch review, then handles push/PR/CI.

---

## Self-Review

**Spec coverage:**
- `name=value` batch tokens + legacy single form → `parse_metric_pairs` (Task 1) + `_cmd_metric` (Task 2). ✓
- Atomic reject-whole-batch, offending token named → `parse_metric_pairs` raises before I/O; Task 2 atomic test. ✓
- Shared `--date`, upsert-per-day, integral bare storage → Task 2 `_cmd_metric`. ✓
- Grammar rules (empty, mixed, bad name, bad value, trailing unit, duplicates) → Task 1 tests. ✓
- Missing-vault-dir before any write → preserved in Task 2 `_cmd_metric`. ✓
- Docs: SKILL, command, CLAUDE/README → Task 3. ✓
- Out of scope (event-log batching, new command, config) → not built. ✓

**Placeholder scan:** every code/test/doc block is verbatim; example numbers illustrative; no TBD/TODO.

**Type/name consistency:** `parse_metric_pairs`, `_validate_name`, `_validate_value`, `_NAME_RE` spelled identically across function, tests, and `_cmd_metric`. The confirmation format `name=value` matches the input syntax. `tokens` (argparse `nargs="+"`) feeds `parse_metric_pairs` in both the code and the CLI tests.
