---
name: wordpress-block-theme
description: Build a WordPress block theme (Full Site Editing) from a canonical, self-validating starter — and avoid the "invalid content" / Gutenberg block-validation gauntlet. Use when creating or editing a WordPress theme, block theme, FSE theme, Gutenberg theme, theme.json, block patterns/templates/template-parts, testing a theme with wp-env, or packaging/deploying a theme to WordPress.com.
---

# WordPress Block Theme

Build block themes that pass the block editor's validation the first time —
especially on sites running the bleeding-edge **Gutenberg plugin**, which
rejects anything but the plainest, most canonical block markup.

## Workflow

1. **Scaffold.** Copy `assets/starter/` to your new theme directory and rename
   it (directory = theme slug). Replace the `style.css` header, the design
   tokens in `theme.json`, and the `starter_`/`starter` prefixes in
   `functions.php`/`phpcs.xml`/pattern slugs with your theme's slug.
2. **Author blocks canonically.** Follow the two hard rules below and the full
   set in `references/block-markup-rules.md`. When in doubt, author a block in
   a real editor and copy its serialized markup — never hand-invent attributes.
3. **Test in wp-env.** Run `bin/check-all.sh` (static gates, no Docker), then
   `npx @wordpress/env start` + `bin/theme-check.sh` (live).
4. **(Optional) Screenshot.** `bin/screenshot.sh` captures a best-effort
   1200x900 homepage screenshot via headless Chrome — review it and replace
   with a curated capture before a real launch.
5. **Package.** `bin/package.sh` gates then builds `<slug>.zip` with a single
   top-level folder and dev files excluded.
6. **Deploy.** Follow `references/wordpress-com-deploy.md`.

## Hard rules (never violate)

**1. A group's serialized `style` must match its attributes — a padding-only
group is NOT "bare".** When a group declares `spacing.padding`/`margin`, the
editor saves the matching inline `style="…"` on the `<div>`, and only that
inline style renders on the front end. A `<div class="wp-block-group">` that
omits it (even while the block comment still lists the padding) is *accepted
by the validator but silently drops the spacing when rendered* — a bug no
editor warning catches. So carry whatever spacing a group declares in its
inline `style`; a group is only truly bare when it declares no spacing. A
"card" (background and/or `border-radius`) bakes those into the same inline
`style` too. See `assets/starter/patterns/card-section.php` (card) and
`plain-section.php` (plain).

**2. Keep template parts plainest — bare groups, spacing in CSS/`theme.json`.**
Don't put padding attributes on a part's wrapping groups (per rule 1 a bare group
can't carry them anyway); put spacing in CSS/`theme.json`. For a small dynamic
value (e.g. copyright year), a `render_block` filter on a plain paragraph is
simpler than a Block Binding and keeps the saved markup a plain paragraph. See
`assets/starter/parts/footer.html` + `starter_render_footer_copyright()` in
`functions.php`.

The remaining rules (editor-only warnings, theme-update vs saved content,
"Clear customizations", portable blocks, styled-on-activation, version-gap
recovery, WordPress.com quirks, pattern-nesting) are in
**`references/block-markup-rules.md`** and **`references/wordpress-com-deploy.md`**.

For site-owner/editor instructions (installing, configuring, using the Site
Editor day to day), see **`references/editor-guide.md`**. For developer
workflow (gates, wp-env, Theme Check, adding patterns/style variations,
packaging), see **`references/development.md`**.

## Maintaining this skill

`bin/update-starter.sh --source <theme>` refreshes `assets/starter/` from an
improved source theme (Class A auto-synced, Class B/C diffed for hand review).
See `MANIFEST.md`.
