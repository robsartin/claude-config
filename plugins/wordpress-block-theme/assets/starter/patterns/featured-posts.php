<?php
/**
 * Title: Featured posts (3-up)
 * Slug: starter/featured-posts
 * Categories: starter
 * Description: A three-column grid of recent posts under a section heading. Canonical Query Loop markup — copy the block comments verbatim when adapting.
 */
?>
<!-- wp:group {"style":{"spacing":{"padding":{"top":"var:preset|spacing|large"}}},"layout":{"type":"constrained"}} -->
<div class="wp-block-group" style="padding-top:var(--wp--preset--spacing--large)"><!-- wp:heading {"level":2,"style":{"typography":{"textTransform":"uppercase","letterSpacing":"0.1em"}},"textColor":"muted","fontSize":"small"} -->
<h2 class="wp-block-heading has-muted-color has-text-color has-small-font-size" style="letter-spacing:0.1em;text-transform:uppercase">Featured</h2>
<!-- /wp:heading -->
<!-- wp:query {"queryId":10,"query":{"perPage":3,"postType":"post","order":"desc","orderBy":"date"},"align":"wide"} -->
<div class="wp-block-query alignwide"><!-- wp:post-template {"layout":{"type":"grid","columnCount":3}} -->
<!-- wp:post-featured-image {"isLink":true,"style":{"border":{"radius":"8px"}},"aspectRatio":"16/9"} /-->
<!-- wp:post-title {"isLink":true,"fontSize":"large"} /-->
<!-- wp:post-excerpt {"excerptLength":18,"fontSize":"small"} /-->
<!-- /wp:post-template --></div>
<!-- /wp:query --></div>
<!-- /wp:group -->
