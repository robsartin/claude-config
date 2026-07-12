# Deploying to WordPress.com — the runbook

A practical, in-order walkthrough for getting this theme onto a WordPress.com
site and keeping it there through updates. Follow it top to bottom the first
time you deploy; jump to the relevant section on later fixes.

---

## 1. Upload

Uploading a theme zip requires the **Business** or **Commerce** plan — the
"Upload Theme" button is hidden on lower plans.

1. Build the zip first: `bin/package.sh`. It re-runs the static gates
   (`bin/check-all.sh`) before packaging, then writes `<slug>.zip` one
   directory above the theme, with a single top-level `<slug>/` folder and
   dev-only files (bin/, `.wp-env.json`, `phpcs.xml`) excluded.
2. In wp-admin: **Appearance → Themes → Add New Theme → Upload Theme**.
3. Choose the zip, click **Install**, then **Activate**.

### Shipping a fix to an already-uploaded theme

WordPress.com will not overwrite an installed theme in place from a re-upload
of the same slug. To ship an update:

1. **Appearance → Themes** → find the currently installed theme → delete it.
2. Upload the new zip as in steps 1–3 above.

Do this *before* touching any Site Editor customizations — see the
[re-upload-then-reset loop](#7-after-every-theme-fix-the-re-upload-then-reset-loop)
below for what to do immediately after the new zip is live.

---

## 2. Configure

Once the theme is active:

1. **Pick a style variation**: Appearance → Editor → Styles, choose one of
   the theme's shipped variations (or the default).
2. **Set Site Title and tagline**: Settings → General.

Nothing else should be required — per `block-markup-rules.md` rule 7, a
theme built from this starter bakes its baseline look into `theme.json`, so
it's fully styled the moment it's activated.

---

## 3. Editor-warning triage

If the block editor shows **"Block contains unexpected or invalid content"**
on a template, part, or pattern:

- **It's editor-only.** This warning does not affect the live front end —
  WordPress renders the saved HTML as-is regardless of validation state, so
  visitors see the page correctly either way. See `block-markup-rules.md`
  rule 4. Don't treat it as an outage and don't block a deploy on it — but do
  fix it before anyone next opens that content in the editor, since re-saving
  could bake in the wrong markup.
- **To clear it**, do one of:
  - Delete the affected block/pattern instance and re-insert the pattern
    fresh from the theme (this re-reads the theme's canonical markup).
  - Use **"Attempt Block Recovery"** if the editor offers it on that block.
- **"Attempt Block Recovery" can dead-end.** Sometimes it opens a "Convert to
  Blocks / Convert to HTML" dialog whose buttons are **inactive** — neither is
  selectable, so recovery via that path silently fails. Don't fight the dialog:
  fix the underlying markup instead — delete and re-insert the block/pattern, or
  correct the theme file and use "Clear customizations".

---

## 4. "Clear customizations" (stuck template parts after an update)

After you re-upload an updated theme, a previously-customized template part
can keep showing its **old** version even though the new zip is live. This is
expected — see `block-markup-rules.md` rule 5: once a template, template
part, or pattern instance has been opened/edited in the Site Editor,
WordPress freezes that content in the database, decoupled from the theme
file. Updating the file on disk no longer touches that saved copy.

To fix it:

1. Open the Site Editor's **template-parts list**.
2. Find the stuck part (it will show a "customized" indicator).
3. Use **"Clear customizations"** — this discards the saved database copy
   and reverts to the theme-file version in one step.

**Diagnosing whether this applies at all**: an **empty** template-parts list
(or entries with no "customized" indicator) means nothing is customized yet —
the site is rendering directly from the theme's file, so a re-upload takes
effect immediately with no reset needed. Only entries that *appear* in that
list with edits are frozen against theme updates.

---

## 5. Newsletter / Subscribe

The theme ships **only portable core blocks** (`block-markup-rules.md` rule
6) — it deliberately does not bake in a Jetpack Subscribe block, because:

- The Jetpack plugin might not be active on every site using the theme.
- Jetpack's block markup can change independently of the theme's release
  cadence.
- If Jetpack is deactivated, a baked-in Jetpack block becomes invalid on
  every page that used it.

So email capture is a **per-site** addition, not a theme feature:

1. Enable it: **Jetpack → Settings → Newsletter** (or **Settings →
   Newsletter**, depending on where WordPress.com surfaces it for your
   site).
2. In the Site Editor, insert WordPress.com's native **Subscribe** block
   wherever you want the signup form (e.g. in the footer, or on a dedicated
   page).

Because this lives entirely in the site's own content/database, it survives
theme updates automatically — no reset needed for the Subscribe block
itself. (If you also customized the template part it lives in, that part
still follows the normal rules in [section 4](#4-clear-customizations-stuck-template-parts-after-an-update).)

---

## 6. Site Editor "not supported"

If the Site Editor shows a message that the current theme is "not
supported" or otherwise refuses to load full-site editing:

- Treat this as a **transient glitch** first, not a verdict on the theme.
  It shows up even on valid, working block themes.
- Try, in order:
  1. Click the admin-bar **"Edit Site"** link (rather than navigating there
     directly) to re-enter the editor.
  2. Reload the page.
- Only suspect the theme itself (missing `theme.json`, missing
  `templates/index.html`, etc.) if the message persists after both of the
  above.

---

## 7. After every theme fix: the re-upload-then-reset loop

Saved content and Site Editor customizations live in the site's **database**,
completely independent of the theme's files (`block-markup-rules.md` rule
5). That means fixing a bug in the theme's files and re-uploading is only
half the job — the site may still be rendering the old, customized copies.
After **any** theme fix, in order:

1. **Re-upload** the new zip (delete the old theme first — see
   [section 1](#shipping-a-fix-to-an-already-uploaded-theme)).
2. **Reset affected template parts**: for every template part touched by the
   fix, go to the Site Editor's template-parts list and use **"Clear
   customizations"** (see [section 4](#4-clear-customizations-stuck-template-parts-after-an-update)) — unless the list shows it was never
   customized, in which case there's nothing to clear.
3. **Delete and re-insert** any already-placed instances of a pattern you
   fixed, so the page picks up the corrected markup instead of its frozen
   database copy.

Skipping steps 2–3 is the single most common reason a "fixed" theme still
appears broken on a live site after a fresh upload.
