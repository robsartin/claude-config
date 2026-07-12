# Block markup rules — the gotcha deep-dive

Gutenberg validates saved block markup against what the block itself would
generate. The bleeding-edge **Gutenberg plugin** is stricter than core, and a
theme that only gets tested against a stable WordPress install can look fine
for months and then start throwing **"Block contains unexpected or invalid
content"** the moment a site updates the plugin. Each rule below follows the
same shape: the symptom you'll see, the rule that prevents it, and a concrete
example from this repo's starter theme.

---

## 1. A group's inline `style` must match its declared spacing — this is a silent front-end bug, not a validator error

**Symptom:** A section's padding or margin is visibly missing on the *live
site* — the editor shows it correctly and throws **no** "invalid content"
warning at all, so nothing in the authoring flow flags the problem. It only
shows up when you compare the editor preview against the actual front end.

**Rule:** When a `core/group` block declares `style.spacing.padding` and/or
`style.spacing.margin` in its attributes, the **only** thing that renders
that spacing on the front end is a matching inline `style="…"` on the
wrapper `<div>`. The block-comment attributes are not, by themselves,
rendered — `do_blocks()` reads the saved HTML, not the JSON attributes. So:

- A group that declares spacing **and** carries the matching inline `style`
  renders that spacing correctly.
- A group that declares spacing but renders a **bare**
  `<div class="wp-block-group">` (no `style=""`, or one missing the relevant
  sides) is accepted by the block validator — both forms parse as valid,
  well-formed `core/group` markup — but silently drops that spacing at
  render time. No warning, no recovery prompt, just missing padding on the
  live page.
- A group is only legitimately **bare** when it declares **no** spacing at
  all. It's not a "plain section vs. card" distinction — a "card" (with a
  background and/or `border-radius`) just happens to also bake those extra
  properties into the same inline `style`.

This was verified directly against a bare-but-padding-declaring group: running
`do_blocks()` on

```html
<!-- wp:group {"style":{"spacing":{"padding":{"top":"var:preset|spacing|large","bottom":"var:preset|spacing|large"}}},"layout":{"type":"constrained"}} -->
<div class="wp-block-group">...</div>
<!-- /wp:group -->
```

emits `<div class="wp-block-group is-layout-constrained">` on the front end
— **no padding at all** — while the styled form (below) keeps it. Since both
forms are valid, well-formed block markup, this is explicitly **not** an
"invalid content" error (see Rule 4) — it's a silent regression that only
shows up by comparing rendered output. That's why this repo ships a static
gate, `bin/check-markup-consistency.py`, that fails the build if a group's
declared spacing isn't mirrored in its div's inline style.

**Example — the corrected, styled form**, from
`assets/starter/patterns/plain-section.php`:

```php
<!-- wp:group {"style":{"spacing":{"padding":{"top":"var:preset|spacing|large","bottom":"var:preset|spacing|large"}}},"layout":{"type":"constrained"}} -->
<div class="wp-block-group" style="padding-top:var(--wp--preset--spacing--large);padding-bottom:var(--wp--preset--spacing--large)"><!-- wp:heading -->
<h2 class="wp-block-heading">A plain section</h2>
<!-- /wp:heading -->
<!-- wp:paragraph -->
<p>No background and no rounded corners — but the padding it declares is baked into the group's inline style, so it survives to the front end. A group is only a bare <code>&lt;div class="wp-block-group"&gt;</code> when it declares no spacing at all.</p>
<!-- /wp:paragraph --></div>
<!-- /wp:group -->
```

**Contrast — a "card"**, from `assets/starter/patterns/card-section.php`,
which declares padding, margin, *and* a background/`border-radius`, and
bakes all of it into the same inline `style`:

```php
<!-- wp:group {"style":{"spacing":{"padding":{"top":"var:preset|spacing|medium","right":"var:preset|spacing|medium","bottom":"var:preset|spacing|medium","left":"var:preset|spacing|medium"},"margin":{"top":"var:preset|spacing|large"}},"border":{"radius":"10px"}},"backgroundColor":"surface","layout":{"type":"constrained"}} -->
<div class="wp-block-group has-surface-background-color has-background" style="border-radius:10px;margin-top:var(--wp--preset--spacing--large);padding-top:var(--wp--preset--spacing--medium);padding-right:var(--wp--preset--spacing--medium);padding-bottom:var(--wp--preset--spacing--medium);padding-left:var(--wp--preset--spacing--medium)"><!-- wp:heading -->
<h2 class="wp-block-heading">A card section</h2>
<!-- /wp:heading -->
<!-- wp:paragraph -->
<p>Because this group has a background and rounded corners, the padding/margin/radius are written into the inline <code>style</code> attribute, byte-for-byte matching the block's attributes.</p>
<!-- /wp:paragraph --></div>
<!-- /wp:group -->
```

The card adds `background-color`/`has-background` and `border-radius` on top
of the same padding/margin-mirroring rule — it isn't a different mechanism,
just more properties going into the same inline `style`.

---

## 2. Keep template-part groups bare — spacing via `theme.json`/CSS, not block padding

**Symptom:** You add padding to a header/footer group to space it out, and the
spacing silently vanishes on the front end — or you keep the group bare and the
part feels cramped with nowhere obvious to add breathing room.

**Rule:** Keep the wrapping groups in template parts (`parts/header.html`,
`parts/footer.html`) bare — declare **no** spacing on them — and put header/footer
spacing in `theme.json`/CSS instead. Two reasons: (1) per Rule 1, a bare group
*can't* carry a padding attribute without silently dropping it at render, so a
part that wants minimal markup must get its spacing elsewhere; (2) parts render on
every page and are the markup most likely to get hand-edited over time, so the
less baked into them, the less can drift. (A group with padding *and* its matching
inline style is perfectly valid inside a part — verified on WP 7.1-alpha +
Gutenberg 23.5.0 — so this is a keep-it-boring guideline, not an "invalid content"
rule.)

**Example**, the full `assets/starter/parts/footer.html`:

```html
<!-- wp:group {"tagName":"footer","layout":{"type":"constrained"}} -->
<footer class="wp-block-group"><!-- wp:group {"layout":{"type":"flex","justifyContent":"space-between","flexWrap":"wrap"}} -->
<div class="wp-block-group"><!-- wp:site-title {"level":0,"isLink":false,"fontSize":"small"} /-->
<!-- wp:paragraph {"fontSize":"small"} -->
<p class="has-small-font-size">© 2024 · Built with the Starter Block Theme</p>
<!-- /wp:paragraph --></div>
<!-- /wp:group --></footer>
<!-- /wp:group -->
```

Neither `<footer>` nor the inner `<div>` carries a `style=""` attribute — no
padding, no margin, nothing baked in. Both groups are bare wrappers.

---

## 3. For small computed values in parts, prefer a `render_block` filter over Block Bindings

**Symptom:** You want a small dynamic value (like a copyright year) in a template
part and reach for Block Bindings — but the value isn't post meta, so you'd have to
register a custom binding source, and you're baking binding metadata into the saved
markup for a one-line string.

**Rule:** For small *computed or global* dynamic text in parts, ship a plain,
static placeholder paragraph and rewrite its content at render time with a
`render_block` filter matched by a snippet of its own text. The saved markup stays
a plain paragraph — nothing for any editor or Gutenberg version to interpret — while
the front end gets the computed value. (Block Bindings are a stable, valid API on
current Gutenberg — a bound paragraph validates cleanly, verified on WP 7.1-alpha +
Gutenberg 23.5.0 — so this isn't about dodging an error; it's that the filter is
simpler and dependency-free for a computed value: no binding source to register, no
post meta, no extra block metadata to keep canonical.)

**Example**, the real `starter_render_footer_copyright` from
`assets/starter/functions.php`:

```php
if ( ! function_exists( 'starter_render_footer_copyright' ) ) {
	/**
	 * Fill the dynamic copyright year into the footer's copyright paragraph at
	 * render time. Uses a plain paragraph (identified by its text) instead of a
	 * Block Binding — the saved markup stays a plain paragraph with no binding
	 * source to register and no extra metadata for any Gutenberg version to
	 * interpret. Front-end only; the editor shows the static placeholder text,
	 * which is fine.
	 */
	function starter_render_footer_copyright( $block_content, $block ) {
		$name = isset( $block['blockName'] ) ? $block['blockName'] : '';
		if ( 'core/paragraph' === $name && false !== strpos( $block_content, 'Built with the Starter Block Theme' ) ) {
			$line          = '&#169; ' . starter_copyright_range() . ' &#183; Built with the Starter Block Theme';
			$block_content = preg_replace( '/(<p\b[^>]*>).*?(<\/p>)/s', '${1}' . $line . '${2}', $block_content, 1 );
		}
		return $block_content;
	}
}
add_filter( 'render_block', 'starter_render_footer_copyright', 10, 2 );
```

The match is against the literal text "Built with the Starter Block Theme" in
`footer.html`'s paragraph — rename that string consistently in both files if
you customize it, or the filter silently stops matching.

---

## 4. "Invalid content" warnings are editor-only

**Symptom:** Panic when the block editor shows a red "This block contains
unexpected or invalid content" notice — worry that the live site is broken.

**Rule:** This warning is purely a **block editor / validation** concern. It
means the saved markup doesn't match what the block would currently generate
from its attributes, so re-saving the post could change the output. It does
**not** mean the front end is broken — WordPress renders the saved HTML as-is
regardless of validation state, so visitors see the page correctly either way.
(Verified on WP 7.1-alpha + Gutenberg 23.5.0: a heading whose saved markup
mismatches its attributes reports `isValid: false` in the editor, yet
`do_blocks()` still emits its saved HTML unchanged.) Treat it as "this needs
your attention before you next edit this block," not
as an outage. Don't let it block a deploy; do fix it before someone next opens
that content in the editor and accidentally reformats it.

---

## 5. Theme updates don't rewrite saved content

**Symptom:** You ship a new version of a template part or pattern, expecting
the live site to pick up the change — but the site still shows the old
markup.

**Rule:** Once a template, template part, or pattern instance has been edited
(or even just opened and saved) in the Site Editor, WordPress stores that
content in the database as a **customization**, decoupled from the theme
file. Updating the theme's file on disk no longer touches that saved copy.
To pull in the new theme-shipped version, you must explicitly discard the
customization:

- **Delete + re-insert**: In the Site Editor, delete the customized
  template/part/pattern instance, then re-add it — WordPress re-reads the
  theme's file version.
- **"Attempt Recovery"**: Available on some invalid-content notices; if
  offered, it can also reset content back toward the theme's canonical
  markup.
- **"Clear customizations"**: On template/template-part list screens in the
  Site Editor, an item with saved edits shows a "Clear customizations"
  action — this discards the saved database copy and reverts to the
  theme-file version in one step.

**Tell**: on the Site Editor's Template Parts list, an **empty list** (or an
entry with no "customized" indicator) means there is no saved customization
for that part yet — the site is still rendering directly from the theme's
file, and a theme update will show up immediately. Once an entry appears
there with edits, it's frozen against theme updates until cleared.

*Verified on WP 7.1-alpha + Gutenberg 23.5.0:* the footer part's
`get_block_template()` source reads `theme` initially; inserting a
`wp_template_part` database record for it flips the source to `custom` and
serves the customized content; deleting that record ("Clear customizations")
reverts the source to `theme`.

---

## 6. Portable blocks only (the Jetpack Subscribe caveat)

**Symptom:** A pattern or template that uses a plugin-specific block (e.g. a
Jetpack "Subscribe" block) renders fine on the site it was built on, but
breaks, disappears, or shows as invalid on another install.

**Rule:** Only use blocks that are guaranteed to be available everywhere the
theme is used — core blocks, plus anything the theme itself registers. Avoid
baking plugin-provided blocks (Jetpack's Subscribe block being the canonical
example) directly into shipped patterns/templates, because:

- The plugin might not be active on every site using the theme.
- The plugin's block markup/attributes can change version to version, and the
  theme has no control over that plugin's release cadence.
- If the plugin is deactivated, the block becomes an unrecognized/invalid
  block on every page that used it.

If you need that functionality on one specific site, add it directly in that
site's Site Editor content (where it becomes a normal, site-specific
customization, see Rule 5) rather than shipping it in the theme's canonical
patterns/templates.

**The Subscribe/newsletter case, concretely:** the WordPress.com Subscribe
block (`wp:jetpack/subscriptions`) only renders where Jetpack (or
WordPress.com's built-in equivalent) is present. On a plain WordPress
install with no Jetpack — including a local `wp-env` — the block type is
unregistered, so the editor shows it as an **unsupported / "missing" block**
and it renders empty on the front end (verified on WP 7.1-alpha + Gutenberg
23.5.0: `wp:jetpack/subscriptions` parses as `core/missing` and `do_blocks()`
returns nothing). The distinct "invalid content" *validation* warning is the
version-drift case instead — Jetpack is present but the saved markup no longer
matches that Jetpack version's block — which you handle with the Rule 8
copy-fresh-markup technique. For a theme that only ever targets
WordPress.com, shipping the Subscribe block in a newsletter pattern is an
acceptable default; just document that it needs Jetpack/WordPress.com to
render. If you need the theme to be error-free on every install:

- **Detect and fall back.** Check block availability at render time (e.g.
  whether the block type is registered) and swap in a core button/link
  (e.g. "Subscribe via email" linking to a mailing-list signup URL) when
  Jetpack isn't present, so the pattern never ships an unrenderable block on
  a plain WordPress site.
- **Or keep the Subscribe block, but keep its markup fresh.** If you keep
  shipping the Jetpack block directly, treat its saved markup like any other
  version-gap risk (Rule 8): if it ever starts flagging as invalid content,
  open a fresh copy of the block on a site where Jetpack is active, switch
  it to **Code editor** / "Edit as HTML", and copy that markup back into the
  pattern verbatim — rather than hand-editing the block's attributes.

Both are more actionable than simply avoiding the block: the first keeps the
pattern portable everywhere, the second keeps a WordPress.com-only pattern's
markup canonical over time.

**Related one-liner — Archives block:** the core Archives block's
`displayAsDropdown` variant has similarly flagged block-validation issues on
some WordPress.com sites; test it on your actual target WordPress before
shipping it in a sidebar or footer. See `editor-guide.md`'s "Blog / posts
archive" section for the site-owner-facing version of this same caveat.

---

## 7. Styled-on-activation: bake base styles into `theme.json`

**Symptom:** A freshly activated theme looks unstyled or generic until someone
manually sets colors/typography in the Site Editor's Styles panel.

**Rule:** Put the theme's baseline look — background/text colors, base font
family, link/heading/button element styles — directly under `theme.json`'s
top-level `"styles"` key, not left to be configured after activation. That way
the theme is fully styled the moment it's activated, with zero required setup
steps, and the Styles panel becomes purely for optional customization on top
of a good default.

**Example**, `assets/starter/theme.json`'s `styles` block already does this:

```json
"styles": {
  "color": { "background": "var:preset|color|paper", "text": "var:preset|color|ink" },
  "typography": { "fontFamily": "var:preset|font-family|body", "lineHeight": "1.6" },
  "elements": {
    "link": { "color": { "text": "var:preset|color|accent-text" } },
    "heading": { "typography": { "fontFamily": "var:preset|font-family|heading", "fontWeight": "700", "lineHeight": "1.2" } },
    "button": {
      "color": { "background": "var:preset|color|accent", "text": "#ffffff" },
      "border": { "radius": "6px" }
    }
  }
}
```

Keep doing this for every new theme built from the starter: extend `styles`,
don't rely on someone visiting Appearance → Editor → Styles after activation.

*Verified on WP 7.1-alpha + Gutenberg 23.5.0:* with no user Global Styles edits
saved, `wp_get_global_styles()` returns the theme.json base values
(`var(--wp--preset--color--paper)` background, `--ink` text) and the generated
global stylesheet sets a body `background-color` rule — so the theme is fully
styled from the moment it's activated, no Styles-panel setup required.

---

## 8. Version-gap recovery: bake the site's own Code-editor markup back in

**Symptom:** The theme was authored/tested against one WordPress/Gutenberg
version. A site now running a newer version flags markup this doc's other
rules didn't anticipate — a new attribute Gutenberg now expects to see
inlined, a new default that changed what "canonical" markup looks like, etc.

**Rule:** Don't guess at the new expected markup by reading changelogs. Use
the environment itself as the source of truth:

1. On the **newer** WordPress site where the block is flagged, open the block
   in the Site Editor and switch it to the **Code editor** view (the
   `</>` icon, or List View → block options → "Edit as HTML").
2. Copy that block's markup exactly as the block editor on *that* version
   renders it. This is guaranteed to match what that version's validator
   expects, because it's the same code generating both.
3. Paste that markup back into the theme's pattern/template/part file
   verbatim, replacing your old version, and re-test.

This turns "a newer Gutenberg wants something slightly different" from a
guessing game into a copy operation — you're always working from ground
truth generated by the exact version you're targeting.

*(This is a recovery **technique**, not a falsifiable behavior claim, so
there's nothing to unit-test — but its premise is exactly what Rule 1's
investigation relied on: the block editor's serialized `save()` output is the
canonical, validator-accepted markup for the version producing it.)*

---

> **Rule 9 — WordPress.com deploy quirks** — lives in the companion runbook,
> [`wordpress-com-deploy.md`](wordpress-com-deploy.md) (Upload-Theme plan gating,
> "Clear customizations", the re-upload-then-reset loop, etc.), since it's about
> deployment rather than block markup. The numbering here is kept aligned with
> that doc.
>
> Unlike Rules 1–8 and 10, these are **WordPress.com-platform** behaviors
> observed on live WordPress.com sites — they can't be reproduced in a local
> `wp-env`, so they're reported from real deployment experience rather than
> verified against a running WordPress here.

---

## 10. Deep pattern nesting resolves now — but inline compositions anyway

**Symptom:** You build a front page by having one pattern reference other
patterns via `wp:pattern` (a template referencing pattern A, which itself
references pattern B), and you're unsure it will resolve reliably everywhere.

**Finding:** On current WordPress this nesting *does* resolve on the front end.
Verified on WP 7.1-alpha + Gutenberg 23.5.0: a pattern whose body is
`<!-- wp:pattern {"slug":"starter/card-section"} /-->`, referenced in turn from
a second pattern, expands **both** levels fully through `do_blocks()` — no empty
output, no dropped section. So two-level nesting is not a hard rendering failure
today. (An earlier version of this rule called it flatly "unreliable"; that
wasn't borne out on a current stack — corrected here.)

**Rule (still worth following):** Prefer **inlining** a composition's sections
directly into the parent pattern anyway, when you want it maximally robust and
editable:

- Inlined markup has no dependency on other pattern files being registered and
  resolving at render time.
- It's self-contained — the site owner edits one pattern, not a tree of them.
- It sidesteps nesting behavior that *has* varied across Gutenberg and
  WordPress.com releases historically, even though current core resolves it.

It costs some duplication; you buy self-containment and one less moving part.
(This is a preference, not a validity or rendering rule — nesting works.)

**Example**, `assets/starter/patterns/home.php` inlines its sections rather than
pulling them in via `<!-- wp:pattern {"slug":"starter/plain-section"} /-->`:

```php
/**
 * Title: Home (full page)
 * Slug: starter/home
 * Categories: starter
 * Description: The front-page composition. Sections are INLINED (not nested pattern references) so the page is self-contained and directly editable — nesting resolves on current WordPress, but inlining keeps the front page dependency-free.
 */
```

The body of `home.php` then repeats the plain-section and card-section markup
directly, instead of doing `<!-- wp:pattern {"slug":"starter/plain-section"} /-->`
+ `<!-- wp:pattern {"slug":"starter/card-section"} /-->`.

---

## Advanced: multi-site divergence (example, NOT in the starter)

> **This is an illustrative reference technique, not a shipped feature.** The
> starter theme in `assets/starter/` is single-site and does not contain any
> of this. Only add code like this to a theme if you actually need one theme
> to serve two (or more) sites that must diverge in specific, targeted ways —
> e.g. running the same theme codebase on both a personal blog and a business
> site, with a different header/homepage per host. Don't add this
> speculatively; add it when you have a real second site to serve.

> **Field caveat — this front-page swap was tried and abandoned.** In the
> project this skill came from, exactly this `get_block_template` hostname-swap
> (serving different *front-page content* per host from one unmodified template)
> was built, shipped, and then **torn out** — it proved fragile and hard to
> reason about. It was replaced with the boring, robust primitive: a normal
> static "Home" page per site (Settings → Reading → "A static page"), built in
> the page editor. Only the theme *chrome* (the header part and the copyright
> line) stayed swapped per host via the `render_block_data` hook below — and
> *that* held up fine. Lesson: don't bury long-lived **content** decisions in
> invisible PHP hostname conditionals; use standard WordPress primitives (static
> front pages) for content, and reserve host-based hooks for small, stable
> chrome. Keep the `get_block_template` example below only if you have a real,
> narrow need for it.

The technique: hook `render_block_data` to swap which template part is used
for a given slug, and hook `get_block_template` to swap in different content
for an *unmodified* theme-sourced template — both keyed off the current
site's hostname, both with a filter escape hatch, and both careful to leave
any site's own Site Editor customizations untouched.

```php
if ( ! function_exists( 'mytheme_brand_header' ) ) {
	/**
	 * On brand.example, render the "Header (Brand lockup)" part in place of
	 * the default header everywhere — so the brand identity needs zero Site
	 * Editor setup. Other sites keep the plain header. The
	 * `mytheme_use_brand_header` filter forces it on or off.
	 */
	function mytheme_brand_header( $parsed_block ) {
		if ( isset( $parsed_block['blockName'], $parsed_block['attrs']['slug'] )
			&& 'core/template-part' === $parsed_block['blockName']
			&& 'header' === $parsed_block['attrs']['slug'] ) {
			$host  = (string) wp_parse_url( home_url(), PHP_URL_HOST );
			$brand = ( false !== strpos( $host, 'brand.example' ) );
			$brand = (bool) apply_filters( 'mytheme_use_brand_header', $brand );
			if ( $brand ) {
				$parsed_block['attrs']['slug'] = 'header-brand';
			}
		}
		return $parsed_block;
	}
}
add_filter( 'render_block_data', 'mytheme_brand_header' );

if ( ! function_exists( 'mytheme_brand_front_page' ) ) {
	/**
	 * On brand.example, serve the brand homepage (a dedicated pattern) as the
	 * front page instead of the theme's default front-page template — so
	 * brand.example needs no Site Editor setup for its homepage.
	 *
	 * Only the untouched THEME template is swapped ('theme' source); once the
	 * front page is edited in the Site Editor it becomes a 'custom' template
	 * and this leaves it alone, so the user's own edits always win. Other
	 * sites are unaffected. The `mytheme_use_brand_front_page` filter forces
	 * it.
	 */
	function mytheme_brand_front_page( $block_template, $id, $template_type ) {
		if ( ! $block_template || 'wp_template' !== $template_type ) {
			return $block_template;
		}
		if ( ! isset( $block_template->slug ) || 'front-page' !== $block_template->slug ) {
			return $block_template;
		}
		if ( ! isset( $block_template->source ) || 'theme' !== $block_template->source ) {
			return $block_template;
		}
		$host  = (string) wp_parse_url( home_url(), PHP_URL_HOST );
		$brand = ( false !== strpos( $host, 'brand.example' ) );
		if ( ! apply_filters( 'mytheme_use_brand_front_page', $brand ) ) {
			return $block_template;
		}
		$block_template->content = '<!-- wp:template-part {"slug":"header","tagName":"header"} /-->'
			. "\n" . '<!-- wp:group {"tagName":"main","layout":{"type":"constrained"}} -->'
			. "\n" . '<main class="wp-block-group"><!-- wp:pattern {"slug":"mytheme/home-brand"} /--></main>'
			. "\n" . '<!-- /wp:group -->'
			. "\n" . '<!-- wp:template-part {"slug":"footer","tagName":"footer"} /-->';
		return $block_template;
	}
}
add_filter( 'get_block_template', 'mytheme_brand_front_page', 10, 3 );
```

Key points if you adapt this:

- **`render_block_data`** rewrites a parsed block *before* it renders — use it
  to redirect a `core/template-part` reference (by `slug`) to a different part
  based on runtime context (here, hostname).
- **`get_block_template`** rewrites the resolved template object — check
  `$template_type === 'wp_template'`, the specific `slug`, and critically
  `$block_template->source === 'theme'` before overriding, so that a site
  which has customized its own front page in the Site Editor (`source ===
  'custom'`) is left completely alone.
- Both hooks key off `wp_parse_url( home_url(), PHP_URL_HOST )` and expose a
  filter (`mytheme_use_brand_header`, `mytheme_use_brand_front_page`) so the
  behavior can be forced on/off without editing code — handy for staging
  domains or local development URLs that don't match the production host
  string.
