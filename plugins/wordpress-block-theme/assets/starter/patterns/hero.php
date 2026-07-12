<?php
/**
 * Title: Hero
 * Slug: starter/hero
 * Categories: starter
 * Description: A simple hero section — site tagline, large headline, and intro paragraph. No background or rounded corners, so the group's only inline style is the padding it declares — carried on the div so it survives to the front end (a bare group would drop it).
 */
?>
<!-- wp:group {"style":{"spacing":{"padding":{"top":"var:preset|spacing|large","bottom":"var:preset|spacing|large"}}},"layout":{"type":"constrained"}} -->
<div class="wp-block-group" style="padding-top:var(--wp--preset--spacing--large);padding-bottom:var(--wp--preset--spacing--large)"><!-- wp:site-tagline {"style":{"typography":{"textTransform":"uppercase","letterSpacing":"0.14em"}},"textColor":"accent-text","fontSize":"small"} /-->
<!-- wp:heading {"level":1,"fontSize":"x-large"} -->
<h1 class="wp-block-heading has-x-large-font-size">Replace this headline with your own.</h1>
<!-- /wp:heading -->
<!-- wp:paragraph {"textColor":"muted"} -->
<p class="has-muted-color has-text-color">A short intro sentence goes here, setting the tone for the page below.</p>
<!-- /wp:paragraph --></div>
<!-- /wp:group -->
