# Starter provenance & update policy

`bin/update-starter.sh --source <theme>` refreshes `assets/starter/` from a
source block theme. Class A files are auto-synced (copy + slug rewrite); Class
B/C files are diff-only (reviewed and folded in by hand). The machine-readable
map is `bin/_manifest.tsv`.

## Why almost everything is Class B, not Class A

The obvious assumption is that every harness/config file bundled in
`assets/starter/` should be Class A ("it came from the source theme, so just
re-copy it with the slug swapped"). That assumption is wrong for most of these
files, and treating them as Class A would **regress** them:

- The four harness scripts derive the active theme's slug at runtime via
  `basename "$PWD"` / `basename "$(dirname ...)"` (see `theme-check.sh`,
  `theme-check-run.php`, `package.sh`, `check-all.sh`, `check-a11y.sh`). The
  source theme's equivalents hardcode `editorial-calm` (or, in
  `check-a11y.sh`'s case, reference it in prose/instructions). A slug-swap
  copy would silently replace the starter's `$(basename "$PWD")` derivation
  with a literal source-theme string wherever the pattern text happened to
  match, undoing the genericization.
- `.wp-env.json` differs **structurally**, not just by slug. The bundled
  starter's copy lives inside the theme directory itself and uses
  `"themes": ["."]` (so the harness works when the starter is the repo/theme
  root). The source's copy lives at the *source repo root* and uses
  `"themes": ["./editorial-calm"]` (a relative path into a themes
  subdirectory). These are two different files serving two different
  directory layouts; auto-syncing one over the other is not a slug
  substitution, it is data loss.
- `phpcs.xml`, `check-contrast.py`'s `EDIT` palette block, and the other
  check scripts were hand-genericized during authoring (semantic
  `paper`/`ink`/`accent` color slugs instead of the source's literal palette
  names, a merge-base-with-variation-overrides pattern, etc.) — real logic
  changes, not verbatim copies.

So only files that are **byte-identical to source apart from being
slug-agnostic** are Class A: `bin/_wcag.py` (pure WCAG contrast-ratio math,
never referenced a slug) and `bin/validate-theme-json.py` (structural JSON/
schema validator, never referenced a slug). Every other harness/config file
is Class B: it must be hand-reviewed against a printed diff on each sync,
because it diverges from source by more than a slug. `functions.php` is
Class C: a deliberately curated subset of the source, not a full copy.

## Provenance table

| Starter path | Source path | Class | Genericization / notes |
|---|---|---|---|
| `bin/_wcag.py` | `bin/_wcag.py` | A | Pure luminance/contrast-ratio math, no slug references. Verbatim; safe to auto-sync. |
| `bin/validate-theme-json.py` | `bin/validate-theme-json.py` | A | Structural JSON/`$schema`/version-3 validator over `theme.json` + `styles/*.json`, no slug references. Verbatim; safe to auto-sync. |
| `bin/check-templates.py` | `bin/check-templates.py` | B | Slug-agnostic already (uses `pathlib.Path(__file__).resolve().parents[1]`), but review on sync in case the source's expected-template set or wiring assertions change. |
| `bin/check-contrast.py` | `bin/check-contrast.py` | B | Palette pairings lifted into an `EDIT for your palette:` block using semantic slugs (`ink`/`muted`/`accent-text` over `paper`) instead of the source's literal color names; merges a style variation's palette over the base palette. |
| `bin/check-button-contrast.py` | `bin/check-button-contrast.py` | B | Resolves both `var(--wp--preset--color--X)` and `var:preset|color|X` syntax; falls back to the base button color when a variation doesn't override one. Palette/slug handling genericized like `check-contrast.py`. |
| `bin/check-font-fallbacks.py` | `bin/check-font-fallbacks.py` | B | Generic fallback-family check (sans-serif/serif/monospace suffix) with no theme-specific font names hardcoded; still worth diffing in case source adds new checks. |
| `bin/check-patterns.py` | `bin/check-patterns.py` | B | Generic Title/Slug/Categories header + namespaced-slug pattern check; no hardcoded theme slug, but namespace regex could change upstream. |
| `bin/check-frontpage.py` | `bin/check-frontpage.py` | B | Generic header/footer-wiring + namespaced-pattern-reference check for `front-page.html`; no hardcoded slug. |
| `bin/check-a11y.sh` | `bin/check-a11y.sh` | B | Faithful pa11y-based adaptation: every literal `editorial-calm` replaced with a runtime `SLUG="$(basename "$PWD")"`; the style-variation-merge instructions in its header comment were genericized to reference `theme.json` / `styles/example.json` instead of the source's hardcoded variation filenames. Structural rewrite, not a slug swap. |
| `bin/check-all.sh` | `bin/check-all.sh` | B | Aggregates all static gates + globs `styles/*.json` variations; slug-agnostic already but treated as diff-only since it orchestrates everything above. |
| `bin/theme-check.sh` | `bin/theme-check.sh` | B | Derives the active theme's slug via `basename "$PWD"` at runtime; source hardcodes `editorial-calm`. Auto-syncing would reintroduce the hardcoded slug. |
| `bin/theme-check-run.php` | `bin/theme-check-run.php` | B | Derives the slug via `basename( dirname( __DIR__ ) )` at runtime for the same reason as `theme-check.sh`. |
| `bin/package.sh` | `bin/package.sh` | B | Derives the slug via `basename "$PWD"` at runtime, then gates and zips; source hardcodes the slug in its zip-naming logic. |
| `.wp-env.json` | `../.wp-env.json` | B | Structurally different, not just a slug swap: bundled copy lives inside the theme dir with `"themes": ["."]`; source copy lives at the source repo root with `"themes": ["./editorial-calm"]`. Auto-sync would overwrite the correct in-theme-root layout with the wrong repo-root layout. |
| `phpcs.xml` | `phpcs.xml` | B | `text_domain` property is set to the starter's own slug (`starter`), and file list is starter-relative; review before folding in any new source rule changes. |
| `functions.php` | `functions.php` | C | Curated subset of the source's setup code (`title-tag`, `automatic-feed-links`, `wp-block-styles`, `responsive-embeds` theme supports; conditional font preloading). The source's multi-site-specific functions were deliberately dropped as out of scope for a generic single-site starter — never auto-synced, always hand-curated. |

## Authored for skill (no source sync)

These files have no source-theme counterpart at all — they were written directly for the starter as part of Tasks 1-4 and are outside `_manifest.tsv` entirely. `update-starter.sh` never touches them:

| Starter path | Notes |
|---|---|
| `patterns/*.php` | Authored for skill (no source sync). |
| `patterns/hero.php` | Authored for skill (no source sync). Genericized hero-section example (site tagline + headline + intro paragraph), adapted from the reference theme's `blog-home.php` hero portion; padding-only bare group per the card/plain markup rule. |
| `patterns/featured-posts.php` | Authored for skill (no source sync). Genericized Query Loop "featured posts" example, adapted from the reference theme's `patterns/featured-posts.php` with copy/slug genericized; canonical 3-up grid markup preserved verbatim. |
| `styles/dark.json` | Authored for skill (no source sync). Second style variation (dark mode), adapted from the reference theme's `styles/dark.json` dark palette values remapped onto the starter's palette slugs (including a new dark `surface` value not present in the source, since the starter has a `surface` slug the source dark variation didn't cover); WCAG AA verified via `check-contrast.py`/`check-button-contrast.py`. |
| `templates/*.html` | Authored for skill (no source sync). |
| `parts/header.html`, `parts/footer.html` | Authored for skill (no source sync). |
| `templates/home.html` | Authored for skill (no source sync); intentionally identical to `templates/index.html` per WordPress's template requirements. |
| `readme.txt` | Authored for skill (no source sync). |
| `screenshot.png` | Authored for skill (no source sync); placeholder — replace with a real homepage capture before shipping. |
| `bin/screenshot.sh` | Authored for skill (no source sync); optional, non-gated helper — captures a best-effort 1200x900 homepage screenshot by driving system Chrome headless (no npm/node_modules). Not in `bin/_manifest.tsv` (no source counterpart) and not run by `check-all.sh`. |
| `assets/fonts/README.md` | Authored for skill (no source sync). |

## Usage

```bash
bin/update-starter.sh --source /path/to/editorial-calm
```

- Class A files are copied from source into `assets/starter/` with the
  source theme's slug/prefix/display-name rewritten to `starter` /
  `Starter Block Theme`.
- Class B/C files print a unified diff (`bundled vs source`) to stdout and
  are never overwritten — fold in upstream changes by hand after reviewing
  the diff, re-applying the genericizations noted above.
- Run `bin/test-update-starter.sh` to smoke-test the sync/rewrite logic
  against a small fake source theme.
