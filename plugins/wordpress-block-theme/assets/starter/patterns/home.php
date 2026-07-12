<?php
/**
 * Title: Home (full page)
 * Slug: starter/home
 * Categories: starter
 * Description: The front-page composition. Sections are INLINED (not nested pattern references) so the page is self-contained and directly editable — nesting resolves on current WordPress, but inlining keeps the front page dependency-free.
 */
?>
<!-- wp:group {"style":{"spacing":{"padding":{"top":"var:preset|spacing|large","bottom":"var:preset|spacing|large"}}},"layout":{"type":"constrained"}} -->
<div class="wp-block-group" style="padding-top:var(--wp--preset--spacing--large);padding-bottom:var(--wp--preset--spacing--large)"><!-- wp:heading {"level":1} -->
<h1 class="wp-block-heading">Welcome</h1>
<!-- /wp:heading -->
<!-- wp:paragraph -->
<p>Replace this hero with your own copy. Below are one plain section and one card section as canonical examples.</p>
<!-- /wp:paragraph --></div>
<!-- /wp:group -->

<!-- wp:group {"style":{"spacing":{"padding":{"top":"var:preset|spacing|large","bottom":"var:preset|spacing|large"}}},"layout":{"type":"constrained"}} -->
<div class="wp-block-group" style="padding-top:var(--wp--preset--spacing--large);padding-bottom:var(--wp--preset--spacing--large)"><!-- wp:heading -->
<h2 class="wp-block-heading">A plain section</h2>
<!-- /wp:heading -->
<!-- wp:paragraph -->
<p>The padding this group declares is carried in its inline style, so it survives to the front end.</p>
<!-- /wp:paragraph --></div>
<!-- /wp:group -->

<!-- wp:group {"style":{"spacing":{"padding":{"top":"var:preset|spacing|medium","right":"var:preset|spacing|medium","bottom":"var:preset|spacing|medium","left":"var:preset|spacing|medium"},"margin":{"top":"var:preset|spacing|large"}},"border":{"radius":"10px"}},"backgroundColor":"surface","layout":{"type":"constrained"}} -->
<div class="wp-block-group has-surface-background-color has-background" style="border-radius:10px;margin-top:var(--wp--preset--spacing--large);padding-top:var(--wp--preset--spacing--medium);padding-right:var(--wp--preset--spacing--medium);padding-bottom:var(--wp--preset--spacing--medium);padding-left:var(--wp--preset--spacing--medium)"><!-- wp:heading -->
<h2 class="wp-block-heading">A card section</h2>
<!-- /wp:heading -->
<!-- wp:paragraph -->
<p>Inline styles baked in.</p>
<!-- /wp:paragraph --></div>
<!-- /wp:group -->
