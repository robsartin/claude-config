<?php
/**
 * Title: Plain section
 * Slug: starter/plain-section
 * Categories: starter
 * Description: A plain full-width section — no background or rounded corners, just padding. The padding it declares is carried in the group's inline style (what the editor saves and what actually renders); a bare wp-block-group would silently drop the padding on the front end.
 */
?>
<!-- wp:group {"style":{"spacing":{"padding":{"top":"var:preset|spacing|large","bottom":"var:preset|spacing|large"}}},"layout":{"type":"constrained"}} -->
<div class="wp-block-group" style="padding-top:var(--wp--preset--spacing--large);padding-bottom:var(--wp--preset--spacing--large)"><!-- wp:heading -->
<h2 class="wp-block-heading">A plain section</h2>
<!-- /wp:heading -->
<!-- wp:paragraph -->
<p>No background and no rounded corners — but the padding it declares is baked into the group's inline style, so it survives to the front end. A group is only a bare <code>&lt;div class="wp-block-group"&gt;</code> when it declares no spacing at all.</p>
<!-- /wp:paragraph --></div>
<!-- /wp:group -->
