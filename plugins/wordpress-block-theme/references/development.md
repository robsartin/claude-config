# Development guide — for the theme developer

Covers the theme/repo layout, running the static gates, running wp-env, the
headless Theme Check runner, the accessibility scan, adding patterns/style
variations, packaging, and the screenshot helper. For site-owner-facing
instructions (installing, configuring, using the Site Editor), see
`editor-guide.md`.

## Repo layout

```
<slug>/                          the theme itself — everything WordPress needs lives here
├── style.css                    theme header (name, version, description)
├── theme.json                   global settings/styles: palette, typography, spacing
├── functions.php                theme setup (supports, enqueues, filters)
├── templates/                   block templates (index, single, page, archive,
│                                 search, 404, front-page, home)
├── parts/                       template parts (header, footer)
├── patterns/                    the shared patterns (see "How to add a pattern" below)
├── styles/                      style variations (e.g. dark.json, example.json)
├── assets/fonts/                self-hosted WOFF2 font files, if any
├── bin/                         static quality-gate scripts + theme-check.sh + screenshot.sh
├── phpcs.xml                    WordPress Coding Standards ruleset
├── readme.txt                   WordPress.org-style theme readme
└── screenshot.png                Appearance → Themes screenshot (1200×900)
```

`.wp-env.json` lives at the theme root and is excluded from the packaged zip
(see "Packaging" below).

## Running the static quality gates

```bash
./bin/check-all.sh
```

This requires no Docker and no network — it's pure Python against the
theme's JSON/PHP/HTML source files. It runs, in order, and stops at the
first failure:

1. **`validate-theme-json.py`** — `theme.json` parses and matches the
   expected WordPress theme.json schema shape.
2. **`check-font-fallbacks.py`** — each declared font family declares a
   primary face plus a system-font fallback stack, so text stays readable
   before/if a webfont fails to load.
3. **`check-contrast.py`** (run once with no arguments for the base
   `theme.json`, then once per file under `styles/`) — body, muted, and
   link text colors meet WCAG AA contrast (≥ 4.5:1) against their
   backgrounds, for the base style and every shipped style variation.
4. **`check-button-contrast.py`** (same per-variation loop) — button text
   color meets WCAG AA contrast (≥ 4.5:1) against the button background
   color, for the base style and every shipped style variation.
5. **`check-templates.py`** — all required templates exist and the
   header/footer parts are wired into them.
6. **`check-patterns.py`** — all patterns have valid Title/Slug/Categories
   headers and parse as valid block markup.
7. **`check-markup-consistency.py`** — every group that declares
   `style.spacing.padding`/`margin` carries the matching inline `style` on
   its wrapper `<div>` (see `block-markup-rules.md` rule 1) — this is the
   gate that catches the "declares spacing but renders a bare div" bug
   before it ships.
8. **`check-frontpage.py`** — the shipped `front-page.html` template is
   actually composed from patterns (not a stub).

A clean run ends with `All static gates passed.` `check-contrast.py` and
`check-button-contrast.py` share their relative-luminance and contrast-ratio
math via `bin/_wcag.py` (not a gate itself — just a helper module both
scripts import).

## Running the accessibility scan

```bash
./bin/check-a11y.sh
```

Unlike `check-all.sh`, this **requires Docker** (wp-env) and a **local
Google Chrome install** — it is not part of `check-all.sh` and is not meant
to run in an environment without Docker. It runs [pa11y](https://pa11y.org/)
with the `WCAG2AA` standard against the system-installed Chrome (via
`PUPPETEER_SKIP_DOWNLOAD=1` + `PUPPETEER_EXECUTABLE_PATH`) instead of
downloading a bundled Chromium.

**Why pa11y instead of `@axe-core/cli`:** `@axe-core/cli`'s `chromedriver`
dependency requires Node ≥ 22 and refuses to install on older Node versions.
On Node 20, pa11y is used instead — it runs fine against the system Chrome
and covers the same `WCAG2AA` ruleset for this purpose.

It starts wp-env if needed, makes sure the theme is active, seeds a couple
of posts if none exist, then scans three URLs with
`npx -y pa11y --standard WCAG2AA --timeout 60000 <url>`: the homepage (`/`),
a single published post, and a bogus/nonexistent URL (to exercise the 404
template). pa11y exits non-zero if it finds any issues, which fails the
script.

The script only scans whichever style is currently baked into `theme.json`
(the base style). To also scan a style variation, temporarily merge its
palette and styles in, flush the cache, scan, then restore the file —
**never commit the temporary merge**:

1. Copy `settings.color.palette` (and `gradients`, if present) plus the
   top-level `styles.color`/`styles.elements` blocks from the variation's
   file under `styles/` into `theme.json`, overriding the base values.
2. `npx @wordpress/env run cli wp cache flush`
3. Re-run `./bin/check-a11y.sh` (or the `pa11y` commands directly).
4. Restore the original file: `git checkout theme.json`.

## Running WordPress locally

Requires Docker Desktop (or another Docker-compatible engine) running.

```bash
npx @wordpress/env start
```

This reads `.wp-env.json` at the theme root, spins up a WordPress + MySQL
container pair, mounts the theme directory as an available theme, and
installs the Theme Check plugin. On first start it also installs WordPress
core itself.

- Homepage: http://localhost:8888
- wp-admin: http://localhost:8888/wp-admin (default wp-env credentials:
  `admin` / `password`)
- Activate the theme: wp-admin → Appearance → Themes → activate (or
  `npx @wordpress/env run cli wp theme activate <slug>`).
- Stop the environment: `npx @wordpress/env stop`.

## Theme Check — the headless runner, and why it's custom

```bash
./bin/theme-check.sh
```

The Theme Check plugin ships **no WP-CLI command** — it is admin-UI-only —
so there's nothing like `wp themecheck` to call. `bin/theme-check.sh`
instead drives the plugin's own check engine directly via `wp eval-file`:

1. It ensures wp-env is running and the `theme-check.latest-stable` plugin
   is installed/active (installing it via `wp-env start --update` from
   `.wp-env.json` if needed).
2. It runs `bin/theme-check-run.php` inside the container via
   `wp eval-file`. That harness loads the plugin's `checkbase.php` (which
   globs and loads every `checks/*.php`, registering each check into the
   global `$themechecks`), calls `run_themechecks_against_theme()` against
   the active theme, then reads each check's `getError()` and groups the
   messages by severity (REQUIRED / WARNING / RECOMMENDED / INFO).
3. The script prints the grouped results and exits non-zero only if there
   are **unexpected** REQUIRED findings.

**Known accepted finding:** Theme Check's `File_Check` blocklists any `*.sh`
file and reports it as a REQUIRED "Shell script file found" issue. In this
repo that's a dev-tree artifact only — `bin/*` is excluded from the
distributable zip by `bin/package.sh`. The runner recognizes this specific
message and does not fail the run on it alone; any *other* REQUIRED finding
still fails the script. So a clean run reports `1 REQUIRED` (the known `.sh`
finding) plus `PASS: no unexpected REQUIRED findings.` — that combination is
the expected "all good" result, not a signal to investigate.

## How to add a pattern

Drop a new file at `patterns/<name>.php` with a PHP header comment block:

```php
<?php
/**
 * Title: My New Pattern
 * Slug: <slug>/my-new-pattern
 * Categories: <slug>
 * Description: One line describing what it's for.
 */
?>
<!-- block markup goes here -->
```

WordPress 6.5+ auto-registers any well-formed pattern file found in the
theme's `patterns/` directory — no `register_block_pattern()` PHP call
needed. Keep the `Slug` namespaced under `<slug>/` and the `Categories`
value as the theme's own pattern category slug so it groups with the
theme's other patterns in the pattern inserter. Run `./bin/check-all.sh`
afterward — `check-patterns.py` will validate the new file's headers and
markup, and `check-markup-consistency.py` will catch any padding/style
mismatch (see `block-markup-rules.md` rule 1).

## How to add a style variation

Drop a new file at `styles/<name>.json`, using the same setting/style slugs
as `theme.json` (palette slugs, element keys, etc.) — see `styles/dark.json`
or `styles/example.json` for the shape. It's auto-picked-up by WordPress:
any well-formed JSON file in `styles/` shows up as a named variation under
Appearance → Editor → Styles, no registration code needed. The variation's
`title` key in the JSON becomes its name in that picker.

`bin/check-all.sh`'s contrast gates (`check-contrast.py` and
`check-button-contrast.py`) automatically loop over every file in `styles/`
in addition to the base `theme.json` — so a new variation's colors are
checked for WCAG AA contrast the next time you run the gates, with no
change needed to `check-all.sh` itself.

> **Caveat — variation custom CSS is finicky.** A style variation's own
> `styles.css` custom CSS can silently fail to apply, even after re-selecting the
> variation. For anything load-bearing (a brand accent bar, a header rule, etc.),
> put it in the theme's always-on stylesheet scoped by a class rather than
> trusting a variation's inline custom CSS.

## Packaging

```bash
./bin/package.sh
```

Re-runs the static gates (`bin/check-all.sh`) before packaging — so a
broken build never gets zipped — then writes `<slug>.zip` one directory
above the theme, containing a single top-level `<slug>/` folder with
dev-only files excluded (`bin/`, `.wp-env.json`, `phpcs.xml`, and other
non-runtime artifacts).

## Screenshot helper (best effort)

```bash
./bin/screenshot.sh
```

Requires Docker (wp-env) and a local Google Chrome install. It starts
wp-env if needed, makes sure the theme is active, seeds a post or two if
the site has none, then drives headless Chrome
(`--headless=new --window-size=1200,900`) against the homepage and writes a
1200×900 `screenshot.png` at the theme root.

Treat the result as a **best-effort starting point only** — it captures
whatever minimal seeded content exists in the local wp-env database. Review
it and replace it with a curated, hand-picked capture before a real launch.
If a newsletter/Subscribe pattern is present, note that a Jetpack-only block
inside it won't render under wp-env (Jetpack isn't installed there), so a
local capture may show that band with only its static text.
