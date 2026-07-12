<?php
/**
 * Title: Card section
 * Slug: starter/card-section
 * Categories: starter
 * Description: A "card" section (has a background + rounded corners), so its padding/margin/radius are baked INLINE on the div to match what the block generates. Mismatch here is what triggers "invalid content".
 */
?>
<!-- wp:group {"style":{"spacing":{"padding":{"top":"var:preset|spacing|medium","right":"var:preset|spacing|medium","bottom":"var:preset|spacing|medium","left":"var:preset|spacing|medium"},"margin":{"top":"var:preset|spacing|large"}},"border":{"radius":"10px"}},"backgroundColor":"surface","layout":{"type":"constrained"}} -->
<div class="wp-block-group has-surface-background-color has-background" style="border-radius:10px;margin-top:var(--wp--preset--spacing--large);padding-top:var(--wp--preset--spacing--medium);padding-right:var(--wp--preset--spacing--medium);padding-bottom:var(--wp--preset--spacing--medium);padding-left:var(--wp--preset--spacing--medium)"><!-- wp:heading -->
<h2 class="wp-block-heading">A card section</h2>
<!-- /wp:heading -->
<!-- wp:paragraph -->
<p>Because this group has a background and rounded corners, the padding/margin/radius are written into the inline <code>style</code> attribute, byte-for-byte matching the block's attributes.</p>
<!-- /wp:paragraph --></div>
<!-- /wp:group -->
