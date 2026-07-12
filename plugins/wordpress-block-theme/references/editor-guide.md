# Editor guide — for the site owner

For the site owner/editor using a theme built from this skill's starter. It
covers **installing** the theme, **configuring** the site, and **using** the
templates and patterns day to day. No code changes are needed for anything in
this guide — everything here is a setting you control from wp-admin.

For build/development details, see `development.md`.

---

## Part 1 — Install / upload

You need a **WordPress.com Business (or Commerce) plan**, or self-hosted
WordPress — custom theme upload isn't available on lower WordPress.com plans.

### Build the theme zip

From the theme's project, run:

```
./bin/package.sh
```

This produces `<slug>.zip` one directory above the theme (a clean build —
dev-only files like `bin/` and `.wp-env.json` are excluded). No WordPress
needed to build it.

### Upload and activate

1. **Appearance → Themes → Add New Theme → Upload Theme.**
2. Choose the zip → **Install Now** → **Activate**.

### Do it safely with a staging site (recommended)

Business plans include a free **staging site**. To try changes without
touching the live site:

1. Site dashboard → **Hosting → Staging Site → Add staging site**.
2. Upload/activate/configure the theme on staging.
3. When happy, **Push to production**.

### Updating later

Re-run `package.sh`, then re-upload the new zip (Appearance → Themes → delete
the old theme → upload the new one). **A theme update does not change content
you already placed on a page or a customized template part** — see "Clear
customizations" in Part 3.

---

## Part 2 — Configure the site

### 2.1 Style variation

The theme ships a base style plus named style variations (for example
`Dark` and `Example` — check **Appearance → Editor → Styles** for the exact
set shipped with your theme). Switch it: **Appearance → Editor → Styles**
(the brush icon) → choose the variation. It applies immediately, site-wide,
with no code changes.

### 2.2 Site title (drives the header + footer)

**Settings → General → Site Title.** The header and footer pull this
dynamically, so your site name appears correctly everywhere with no
hardcoding.

### 2.3 Site logo & favicon

The starter's header includes a **Site Logo** block, and the theme declares
`add_theme_support( 'custom-logo' )` — without that support, WordPress never
shows a Logo control at all, so the block would have no way to receive a logo.
Two things trip people up:

- **Where to set the logo.** Block themes hide the old "Appearance → Customize"
  menu entry, so the Site Identity → Logo control isn't obvious. Reach it
  directly at `/wp-admin/customize.php` (Site Identity → Logo), or edit the
  header template part in the Site Editor. The header ships the logo at a small
  width (48px) beside the site title; a large source image (e.g. 512×512) will
  otherwise render at its natural size — set the width you want on the Site Logo
  block.
- **Logo ≠ favicon.** The header logo and the browser-tab **Site Icon**
  (favicon) are two different settings. The favicon lives at **Settings →
  General → Site Icon**. A 512×512 PNG with a transparent background works for
  both.
- **Editor-configurable branding.** The header/footer use the core **Site Logo,
  Site Title, Site Tagline, and Navigation** blocks, which pull from Site
  Identity / Settings → General / Menus — so a site owner rebrands entirely from
  settings, with no code change.

### 2.4 Front page

The homepage is composed from patterns in the theme's pattern category
(check the **＋** inserter → **Patterns** tab for the category name — e.g.
"Starter"). A shipped "Home (full page)" pattern is a good starting point;
you can also build the front page from smaller section patterns (hero,
featured posts, etc.) instead.

Edit the Front Page template in the Site Editor (Templates → Front Page),
clear the default content if needed, and insert the pattern(s) you want.

### 2.5 Blog / posts archive

Give the site a dedicated Blog archive (all posts, paginated), separate from
the curated homepage:

1. **Pages → Add New → "Blog" → Publish** (leave empty).
2. **Settings → Reading → "A static page"** → Homepage = your curated home
   page, Posts page = **Blog**.
3. **"Blog pages show at most"** → set posts-per-page (e.g. 10).
4. Add **Blog** to the header nav (Site Editor → header → Navigation → ＋ →
   Blog).

The Posts page template shows Previous/numbers/Next pagination and emits
`<link rel="prev">` / `<link rel="next">` in the page head. For month
browsing, WordPress's date archives (e.g. `/2026/05/`) render via the
Archive template; you can add a core **Archives** block to a sidebar or
footer if you want a month picker.

> **Archives-block caveat:** the core Archives block's `displayAsDropdown`
> variant has flagged block-validation ("invalid content") issues on some
> WordPress.com sites. Test it on your actual target WordPress before
> shipping it in a sidebar or footer — if it flags there, use the
> non-dropdown (link list) display instead.

### 2.6 Newsletter / Subscribe

If a newsletter-signup pattern is part of the theme, it likely uses
WordPress.com's **Subscribe** block (email field + button) — it works out of
the box on WordPress.com. If it doesn't appear, enable it under **Jetpack →
Settings → Newsletter**. On a non-Jetpack site (e.g. a local test install)
this block can't render — that's expected off WordPress.com, not a bug in
the theme.

> **Finding the block:** search the inserter's **Blocks** tab for **"Subscribe"**
> (the WordPress.com/Jetpack email-capture block). The **Patterns** tab's
> "newsletter" results can include generic store/e-commerce "sign up for sales
> and offers" patterns that look similar but aren't real email capture.

### 2.7 Footer copyright

The footer copyright line is a plain paragraph, and the year is filled in
automatically when the page renders — nothing to configure by default. If
the theme's `functions.php` exposes a filter for the copyright start year
(check the theme's docs or source for the exact filter name, since this
varies by theme), you can use it in a code snippet to force a specific start
year; otherwise the behavior is whatever the theme's code implements
generically (e.g. defaulting to your oldest published post's year).

---

## Part 3 — Using the templates & Site Editor

Open the Site Editor at **Appearance → Editor** (or `…/wp-admin/site-editor.php`,
or "Edit Site" in the admin bar). Its sidebar has:

- **Styles** — the palette/typography (your style variation lives here).
- **Patterns → Template Parts** — the **Header** and **Footer** building
  blocks (and any others the theme ships).
- **Templates** — the page layouts:

| Template | Used for |
|----------|----------|
| Front Page | the site homepage (composed from patterns) |
| Blog Home | the Posts page — paginated post archive |
| Index | fallback listing |
| Single | one blog post |
| Page | a static page |
| Archive | category/tag/date archives |
| Search | search results |
| 404 | not-found page |

### Editing

Click into any template or part, edit blocks like a normal page, and **Save**.
Patterns are inserted with the **＋** inserter → **Patterns** tab → the
theme's pattern category.

### Clear customizations

Once you edit a template or template part in the Site Editor, your version is
saved in the site's database and **overrides the theme's** — so a later theme
upload won't change it. To go back to the theme's version: open the item in
the Site Editor (or Patterns → Template Parts) → **⋮ menu → "Clear
customizations."** This is the fix if a part looks stale or broken after a
theme update.

### "The front page isn't showing what I built"

Same symptom, several possible causes — check in this order:

1. **Is the right theme actually active?** Appearance → Themes. It's easy to
   leave a different theme active, so none of this theme's templates run at all.
   (Tell: the page source / template author isn't this theme.)
2. **A saved Front Page customization is overriding the theme file.** If the
   Front Page template was edited in the Site Editor, that database copy wins
   over the shipped `front-page.html` — clear it ("Clear customizations") to fall
   back to the theme's version.
3. **`front-page.html` always wins for the site's front page.** As long as the
   theme ships a `front-page.html`, a per-page "Template" assignment is ignored
   *for the front page specifically*. To use a page's own content as the
   homepage instead, set Settings → Reading → "A static page" and build that
   page from patterns.

### About "Block contains unexpected or invalid content"

If the editor flags a block after an upgrade, it's an **editor-only** warning
comparing older saved markup to the current block format — your live site
still renders correctly. Click **⋮ → Attempt Block Recovery** (then Save) to
clear it, or delete and re-insert the pattern. It doesn't affect what
visitors see.
