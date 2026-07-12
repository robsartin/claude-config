# Fonts

The starter ships **no** font files — it uses a system-ui fallback stack so it
renders everywhere with zero downloads.

To self-host a font:
1. Drop the `.woff2` files here (e.g. `my-body-400.woff2`).
2. Add a `fontFace` entry to the matching family in `../theme.json`
   (`settings.typography.fontFamilies[].fontFace[]`, `src: ["file:./assets/fonts/my-body-400.woff2"]`).
3. List the most-used files in `starter_preload_fonts()` in `../functions.php`.

`bin/check-font-fallbacks.py` verifies any `fontFace` you add points at a file
that actually exists.
