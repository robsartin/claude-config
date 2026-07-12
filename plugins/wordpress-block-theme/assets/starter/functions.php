<?php
/**
 * Starter Block Theme setup.
 *
 * @package starter
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

if ( ! function_exists( 'starter_setup' ) ) {
	function starter_setup() {
		add_theme_support( 'title-tag' );
		add_theme_support( 'automatic-feed-links' );
		add_theme_support( 'wp-block-styles' );
		add_theme_support( 'responsive-embeds' );
		// Required for the Site Logo block in parts/header.html to be settable:
		// without this, WordPress never shows a Logo control in Site Identity /
		// the Customizer, so the block has no way to receive a logo.
		add_theme_support(
			'custom-logo',
			array(
				'height'      => 48,
				'width'       => 48,
				'flex-height' => true,
				'flex-width'  => true,
			)
		);
	}
}
add_action( 'after_setup_theme', 'starter_setup' );

if ( ! function_exists( 'starter_preload_fonts' ) ) {
	/**
	 * Preload self-hosted font files IF they exist. The starter ships none, so
	 * this emits nothing until you add WOFF2 files under assets/fonts/ and list
	 * them here.
	 */
	function starter_preload_fonts() {
		$fonts = array(); // e.g. array( 'my-heading-600.woff2', 'my-body-400.woff2' );
		foreach ( $fonts as $file ) {
			if ( file_exists( get_theme_file_path( 'assets/fonts/' . $file ) ) ) {
				printf(
					'<link rel="preload" href="%s" as="font" type="font/woff2" crossorigin>' . "\n",
					esc_url( get_theme_file_uri( 'assets/fonts/' . $file ) )
				);
			}
		}
	}
}
add_action( 'wp_head', 'starter_preload_fonts', 1 );

if ( ! function_exists( 'starter_register_pattern_category' ) ) {
	function starter_register_pattern_category() {
		register_block_pattern_category(
			'starter',
			array( 'label' => __( 'Starter', 'starter' ) )
		);
	}
}
add_action( 'init', 'starter_register_pattern_category' );

if ( ! function_exists( 'starter_copyright_range' ) ) {
	/**
	 * "2020–2026" (or "2026" in the first year). Start year is filterable via
	 * `starter_copyright_start`; defaults to the oldest published post's year,
	 * else the current year.
	 */
	function starter_copyright_range() {
		$now   = (int) wp_date( 'Y' );
		$start = (int) apply_filters( 'starter_copyright_start', 0 );
		if ( $start <= 0 ) {
			$oldest = get_posts(
				array(
					'numberposts' => 1,
					'orderby'     => 'date',
					'order'       => 'ASC',
					'post_status' => 'publish',
					'fields'      => 'ids',
				)
			);
			$start = $oldest ? (int) get_the_date( 'Y', $oldest[0] ) : $now;
		}
		if ( $start <= 0 || $start > $now ) {
			$start = $now;
		}
		return ( $now > $start ) ? $start . '&#8211;' . $now : (string) $start;
	}
}

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

if ( ! function_exists( 'starter_paginated_rel_links' ) ) {
	function starter_paginated_rel_links() {
		if ( is_singular() ) {
			return;
		}
		global $wp_query;
		$paged = max( 1, (int) get_query_var( 'paged' ) );
		$max   = isset( $wp_query->max_num_pages ) ? (int) $wp_query->max_num_pages : 1;
		if ( $paged > 1 ) {
			$prev = get_previous_posts_page_link();
			if ( $prev ) {
				printf( '<link rel="prev" href="%s">' . "\n", esc_url( $prev ) );
			}
		}
		if ( $paged < $max ) {
			$next = get_next_posts_page_link( $max );
			if ( $next ) {
				printf( '<link rel="next" href="%s">' . "\n", esc_url( $next ) );
			}
		}
	}
}
add_action( 'wp_head', 'starter_paginated_rel_links' );

if ( ! function_exists( 'starter_month_nav' ) ) {
	/**
	 * [starter_month_nav] — on date archives, link to the nearest earlier and later
	 * month that has published posts ("prev/next month"). Empty on non-date views, or
	 * when no adjacent month has posts. Rendered via a core Shortcode block so the
	 * template markup stays canonical (see references/block-markup-rules.md).
	 */
	function starter_month_nav() {
		if ( ! is_date() ) {
			return '';
		}
		$year  = (int) get_query_var( 'year' );
		$month = (int) get_query_var( 'monthnum' );
		if ( ! $year || ! $month ) {
			return '';
		}
		$start = sprintf( '%04d-%02d-01 00:00:00', $year, $month );
		$end   = ( 12 === $month )
			? sprintf( '%04d-01-01 00:00:00', $year + 1 )
			: sprintf( '%04d-%02d-01 00:00:00', $year, $month + 1 );

		$prev = get_posts(
			array(
				'numberposts' => 1,
				'post_status' => 'publish',
				'orderby'     => 'date',
				'order'       => 'DESC',
				'fields'      => 'ids',
				'date_query'  => array( array( 'before' => $start ) ),
			)
		);
		$next = get_posts(
			array(
				'numberposts' => 1,
				'post_status' => 'publish',
				'orderby'     => 'date',
				'order'       => 'ASC',
				'fields'      => 'ids',
				'date_query'  => array( array( 'after' => $end, 'inclusive' => true ) ),
			)
		);
		if ( ! $prev && ! $next ) {
			return '';
		}

		$html = '<nav class="starter-month-nav" aria-label="' . esc_attr__( 'Adjacent months', 'starter' ) . '" style="display:flex;justify-content:space-between;gap:1rem;margin-block:1.5rem">';
		if ( $prev ) {
			$html .= sprintf(
				'<a rel="prev" href="%s">&#8592; %s</a>',
				esc_url( get_month_link( get_the_time( 'Y', $prev[0] ), get_the_time( 'n', $prev[0] ) ) ),
				esc_html( get_the_time( 'F Y', $prev[0] ) )
			);
		} else {
			$html .= '<span></span>';
		}
		if ( $next ) {
			$html .= sprintf(
				'<a rel="next" href="%s">%s &#8594;</a>',
				esc_url( get_month_link( get_the_time( 'Y', $next[0] ), get_the_time( 'n', $next[0] ) ) ),
				esc_html( get_the_time( 'F Y', $next[0] ) )
			);
		} else {
			$html .= '<span></span>';
		}
		$html .= '</nav>';
		return $html;
	}
}
if ( ! function_exists( 'starter_render_month_nav' ) ) {
	/**
	 * Fill the month-nav slot on date archives. The template ships an empty group
	 * with class "starter-month-nav-slot"; this replaces it with the prev/next-month
	 * links at render. A render_block filter (not a shortcode) — registering a shortcode is
	 * disallowed in themes by Theme Check.
	 */
	function starter_render_month_nav( $block_content, $block ) {
		$name  = isset( $block['blockName'] ) ? $block['blockName'] : '';
		$class = isset( $block['attrs']['className'] ) ? $block['attrs']['className'] : '';
		if ( 'core/paragraph' === $name && false !== strpos( $class, 'starter-month-nav-slot' ) ) {
			return starter_month_nav();
		}
		return $block_content;
	}
}
add_filter( 'render_block', 'starter_render_month_nav', 10, 2 );

