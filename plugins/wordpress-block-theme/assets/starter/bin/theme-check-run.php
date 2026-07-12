<?php
/**
 * Headless Theme Check runner. Runs the Theme Check plugin's suite without the
 * wp-admin UI, driven by `wp eval-file` from bin/theme-check.sh.
 *
 * Exits 0 if no unexpected REQUIRED findings; the known dev-tree "Shell script
 * file found" finding for bin/*.sh is excluded (those are stripped by
 * package.sh).
 */
$plugin_dir = WP_PLUGIN_DIR . '/theme-check.latest-stable';
$checkbase  = $plugin_dir . '/checkbase.php';
if ( ! file_exists( $checkbase ) ) {
	echo "Theme Check plugin not found at {$plugin_dir}.\n";
	exit( 2 );
}
require_once $checkbase;

// Derive the slug from THIS file's location: <theme>/bin/theme-check-run.php.
$theme_slug = basename( dirname( __DIR__ ) );
$theme      = wp_get_theme( $theme_slug );
if ( ! $theme->exists() ) {
	echo "Theme '{$theme_slug}' not found.\n";
	exit( 2 );
}
run_themechecks_against_theme( $theme, $theme_slug );

global $themechecks;
$known_dev_tree_finding = 'Shell script file found';
$messages = array( 'REQUIRED' => array(), 'WARNING' => array(), 'RECOMMENDED' => array(), 'INFO' => array() );
$known_finding_count = 0;
foreach ( $themechecks as $check ) {
	if ( ! ( $check instanceof themecheck ) ) {
		continue;
	}
	foreach ( (array) $check->getError() as $error ) {
		$text = trim( preg_replace( '/\s+/', ' ', html_entity_decode( wp_strip_all_tags( $error ) ) ) );
		if ( preg_match( '/tc-required/', $error ) ) {
			$severity = 'REQUIRED';
		} elseif ( preg_match( '/tc-warning/', $error ) ) {
			$severity = 'WARNING';
		} elseif ( preg_match( '/tc-recommended/', $error ) ) {
			$severity = 'RECOMMENDED';
		} else {
			$severity = 'INFO';
		}
		if ( 'REQUIRED' === $severity && false !== strpos( $text, $known_dev_tree_finding ) ) {
			++$known_finding_count;
		}
		$messages[ $severity ][] = $text;
	}
}
foreach ( array( 'REQUIRED', 'WARNING', 'RECOMMENDED', 'INFO' ) as $severity ) {
	echo "\n{$severity} (" . count( $messages[ $severity ] ) . ")\n";
	foreach ( $messages[ $severity ] as $item ) {
		echo "  - {$item}\n";
	}
}
$unexpected_required = count( $messages['REQUIRED'] ) - $known_finding_count;
if ( $unexpected_required > 0 ) {
	echo "\nFAIL: {$unexpected_required} unexpected REQUIRED finding(s).\n";
	exit( 1 );
}
echo "\nPASS: no unexpected REQUIRED findings.\n";
exit( 0 );
